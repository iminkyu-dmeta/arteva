/*
 * HTTP authentication
 * Copyright (c) 2010 Martin Storsjo
 *
 * This file is part of FFmpeg.
 *
 * FFmpeg is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * FFmpeg is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with FFmpeg; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
/* 참조:   https://ffmpeg.org/pipermail/ffmpeg-devel/2024-April/325073.html */

#include "httpauth.h"
#include "libavutil/base64.h"
#include "libavutil/avstring.h"
#include "libavutil/mem.h"
#include "internal.h"
#include "libavutil/random_seed.h"
#include "libavutil/md5.h"
#include "libavutil/hash.h"  // 2025.02.07 추가된 부분 (SHA-256 사용)
#include "libavutil/log.h" // av_log 사용을 위해 추가
#include "urldecode.h"

static void handle_basic_params(HTTPAuthState *state, const char *key,
                                int key_len, char **dest, int *dest_len)
{
    if (!strncmp(key, "realm=", key_len)) {
        *dest     =        state->realm;
        *dest_len = sizeof(state->realm);
    }
}

static void handle_digest_params(HTTPAuthState *state, const char *key,
                                 int key_len, char **dest, int *dest_len)
{
    DigestParams *digest = &state->digest_params;

    if (!strncmp(key, "realm=", key_len)) {
        *dest     =        state->realm;
        *dest_len = sizeof(state->realm);
    } else if (!strncmp(key, "nonce=", key_len)) {
        *dest     =        digest->nonce;
        *dest_len = sizeof(digest->nonce);
    } else if (!strncmp(key, "opaque=", key_len)) {
        *dest     =        digest->opaque;
        *dest_len = sizeof(digest->opaque);
    } else if (!strncmp(key, "algorithm=", key_len)) {
        *dest     =        digest->algorithm;
        *dest_len = sizeof(digest->algorithm);
    } else if (!strncmp(key, "qop=", key_len)) {
        *dest     =        digest->qop;
        *dest_len = sizeof(digest->qop);
    } else if (!strncmp(key, "stale=", key_len)) {
        *dest     =        digest->stale;
        *dest_len = sizeof(digest->stale);
    }
}

static void handle_digest_update(HTTPAuthState *state, const char *key,
                                 int key_len, char **dest, int *dest_len)
{
    DigestParams *digest = &state->digest_params;

    if (!strncmp(key, "nextnonce=", key_len)) {
        *dest     =        digest->nonce;
        *dest_len = sizeof(digest->nonce);
    }
}

static void choose_qop(char *qop, int size)
{
    char *ptr = strstr(qop, "auth");
    char *end = ptr + strlen("auth");

    if (ptr && (!*end || av_isspace(*end) || *end == ',') &&
        (ptr == qop || av_isspace(ptr[-1]) || ptr[-1] == ',')) {
        av_strlcpy(qop, "auth", size);
    } else {
        qop[0] = 0;
    }
}

void ff_http_auth_handle_header(HTTPAuthState *state, const char *key,
                                const char *value)
{
    av_log(NULL, AV_LOG_INFO, "### ff_http_auth_handle_header detected ###\n");
    if (!av_strcasecmp(key, "WWW-Authenticate") || !av_strcasecmp(key, "Proxy-Authenticate")) {
        const char *p;
        if (av_stristart(value, "Basic ", &p) &&
            state->auth_type <= HTTP_AUTH_BASIC) {
                av_log(NULL, AV_LOG_INFO, "### Basic authentication detected ###\n");
            state->auth_type = HTTP_AUTH_BASIC;
            state->realm[0] = 0;
            state->stale = 0;
            ff_parse_key_value(p, (ff_parse_key_val_cb) handle_basic_params,
                               state);
        } else if (av_stristart(value, "Digest ", &p) &&
                   state->auth_type <= HTTP_AUTH_DIGEST) {

            av_log(NULL, AV_LOG_INFO, "### WWW-Authenticate raw: '%s'\n", value);

            state->auth_type = HTTP_AUTH_DIGEST;
            memset(&state->digest_params, 0, sizeof(DigestParams));
            state->realm[0] = 0;
            state->stale = 0;
            ff_parse_key_value(p, (ff_parse_key_val_cb) handle_digest_params,
                               state);
            av_log(NULL, AV_LOG_INFO,
            "### before choose_qop: qop='%s'\n",
            state->digest_params.qop);

            choose_qop(state->digest_params.qop,
                       sizeof(state->digest_params.qop));

            av_log(NULL, AV_LOG_INFO,
            "### after choose_qop: qop='%s'\n",
            state->digest_params.qop);

            if (!av_strcasecmp(state->digest_params.stale, "true"))
                state->stale = 1;
        } else {
            av_log(NULL, AV_LOG_INFO,
            "### unsupported authentication type: '%s'\n",
            value);
        }
    } else if (!av_strcasecmp(key, "Authentication-Info")) {
        av_log(NULL, AV_LOG_INFO, "### Authentication-Info detected ###\n");
        ff_parse_key_value(value, (ff_parse_key_val_cb) handle_digest_update,
                           state);
    } else {
        av_log(NULL, AV_LOG_INFO,
        "### unsupported key: '%s'\n",
        key);
    }
}


static void update_md5_strings(struct AVMD5 *md5ctx, ...)
{
    va_list vl;

    va_start(vl, md5ctx);
    while (1) {
        const char* str = va_arg(vl, const char*);
        if (!str)
            break;
        av_md5_update(md5ctx, str, strlen(str));
    }
    va_end(vl);
}

/* Generate a digest reply, according to RFC 2617. */
static char *make_digest_auth(HTTPAuthState *state, const char *username,
                              const char *password, const char *uri,
                              const char *method)
{
    DigestParams *digest = &state->digest_params;
    int len;
    uint32_t cnonce_buf[2];
    char cnonce[17];
    char nc[9];
    int i;
    char A1hash[33], A2hash[33], response[33];
    struct AVMD5 *md5ctx;
    uint8_t hash[16];
    char *authstr;

    digest->nc++;
    snprintf(nc, sizeof(nc), "%08x", digest->nc);

    /* Generate a client nonce. */
    for (i = 0; i < 2; i++)
        cnonce_buf[i] = av_get_random_seed();
    ff_data_to_hex(cnonce, (const uint8_t*) cnonce_buf, sizeof(cnonce_buf), 1);

    md5ctx = av_md5_alloc();
    if (!md5ctx)
        return NULL;

    av_md5_init(md5ctx);
    update_md5_strings(md5ctx, username, ":", state->realm, ":", password, NULL);
    av_md5_final(md5ctx, hash);
    ff_data_to_hex(A1hash, hash, 16, 1);

    if (!strcmp(digest->algorithm, "") || !strcmp(digest->algorithm, "MD5")) {
    } else if (!strcmp(digest->algorithm, "MD5-sess")) {
        av_md5_init(md5ctx);
        update_md5_strings(md5ctx, A1hash, ":", digest->nonce, ":", cnonce, NULL);
        av_md5_final(md5ctx, hash);
        ff_data_to_hex(A1hash, hash, 16, 1);
    } else {
        /* Unsupported algorithm */
        av_free(md5ctx);
        return NULL;
    }

    av_md5_init(md5ctx);
    update_md5_strings(md5ctx, method, ":", uri, NULL);
    av_md5_final(md5ctx, hash);
    ff_data_to_hex(A2hash, hash, 16, 1);

    av_md5_init(md5ctx);
    update_md5_strings(md5ctx, A1hash, ":", digest->nonce, NULL);
    if (!strcmp(digest->qop, "auth") || !strcmp(digest->qop, "auth-int")) {
        update_md5_strings(md5ctx, ":", nc, ":", cnonce, ":", digest->qop, NULL);
    }
    update_md5_strings(md5ctx, ":", A2hash, NULL);
    av_md5_final(md5ctx, hash);
    ff_data_to_hex(response, hash, 16, 1);

    av_free(md5ctx);

    if (!strcmp(digest->qop, "") || !strcmp(digest->qop, "auth")) {
    } else if (!strcmp(digest->qop, "auth-int")) {
        /* qop=auth-int not supported */
        return NULL;
    } else {
        /* Unsupported qop value. */
        return NULL;
    }

    len = strlen(username) + strlen(state->realm) + strlen(digest->nonce) +
              strlen(uri) + strlen(response) + strlen(digest->algorithm) +
              strlen(digest->opaque) + strlen(digest->qop) + strlen(cnonce) +
              strlen(nc) + 150;

    authstr = av_malloc(len);
    if (!authstr)
        return NULL;
    snprintf(authstr, len, "Authorization: Digest ");

    /* TODO: Escape the quoted strings properly. */
    av_strlcatf(authstr, len, "username=\"%s\"",   username);
    av_strlcatf(authstr, len, ", realm=\"%s\"",     state->realm);
    av_strlcatf(authstr, len, ", nonce=\"%s\"",     digest->nonce);
    av_strlcatf(authstr, len, ", uri=\"%s\"",       uri);
    av_strlcatf(authstr, len, ", response=\"%s\"",  response);

    // we are violating the RFC and use "" because all others seem to do that too.
    if (digest->algorithm[0])
        av_strlcatf(authstr, len, ", algorithm=\"%s\"",  digest->algorithm);

    if (digest->opaque[0])
        av_strlcatf(authstr, len, ", opaque=\"%s\"", digest->opaque);
    if (digest->qop[0]) {
        av_log(NULL, AV_LOG_INFO, "### qop detected ###\n");
        av_log(NULL, AV_LOG_INFO, "### qop='%s'\n", digest->qop);
        av_strlcatf(authstr, len, ", qop=\"%s\"",    digest->qop);
        av_log(NULL, AV_LOG_INFO, "### cnonce='%s'\n", cnonce);
        av_strlcatf(authstr, len, ", cnonce=\"%s\"", cnonce);
        av_log(NULL, AV_LOG_INFO, "### nc='%s'\n", nc);
        av_strlcatf(authstr, len, ", nc=%s",         nc);
    }

    av_strlcatf(authstr, len, "\r\n");
    av_log(NULL, AV_LOG_INFO, "### final authstr: %s\n", authstr);
    return authstr;
}


/*
 * HTTP Digest 인증 알고리즘의 이름을 표준화하는 함수.
 * '-' 문자를 제거하고 대문자로 변환하여 FFmpeg의 해시 라이브러리가 올바르게 인식하도록 함.
 */
static void normalize_algorithm(char *dst, const char *src, int dst_size)
{
    char original_algorithm[32]; // 원본 알고리즘 저장
    av_strlcpy(original_algorithm, src, sizeof(original_algorithm));

    int j = 0;
    for (int i = 0; src[i] && j < dst_size - 1; i++) {
        if (src[i] != '-') // "-" 제거
            dst[j++] = av_toupper(src[i]); // 대문자로 변환
    }
    dst[j] = '\0';

    // 특수 케이스: "SHA512256"을 "SHA512/256"으로 변환
    if (!strcmp(dst, "SHA512256")) {
        av_strlcpy(dst, "SHA512/256", dst_size);
    }
    // 추가 변환: "SHA256"으로 변환
    else if (!strcmp(dst, "SHA256")) {
        av_strlcpy(dst, "SHA256", dst_size);
    }

    // 변경 전후의 알고리즘 이름을 로그로 출력
    //av_log(NULL, AV_LOG_INFO, "Algorithm before normalization: %s\n", original_algorithm);
    //av_log(NULL, AV_LOG_INFO, "Algorithm after normalization: %s\n", dst);
}


/*
 * SHA-256 기반 Digest 인증 생성 함수 (RFC7616 기반)
 * 사용자의 ID 및 비밀번호를 이용해 서버의 요구사항을 충족하는 인증 문자열을 생성
 */
static char *make_digest_auth_sha(HTTPAuthState *state, const char *username,
                                  const char *password, const char *uri,
                                  const char *method, const char *algorithm)
{
    DigestParams *digest = &state->digest_params;
    char cnonce[33];
    char nc[9];
    char a1_hash[65], a2_hash[65], response[65];
    struct AVHashContext *hashctx;
    uint8_t hash[64];
    char *authstr;
    int ret;

    digest->nc++;
    snprintf(nc, sizeof(nc), "%08x", digest->nc);

    // 클라이언트 난스(cnonce) 생성
    uint32_t cnonce_buf[2];
    for (int i = 0; i < 2; i++)
        cnonce_buf[i] = av_get_random_seed();
    ff_data_to_hex(cnonce, (const uint8_t *)cnonce_buf, sizeof(cnonce_buf), 1);

    // 알고리즘 이름 표준화 
    char normalized_algorithm[16];
	normalize_algorithm(normalized_algorithm, algorithm, sizeof(normalized_algorithm));

	if ((ret = av_hash_alloc(&hashctx, normalized_algorithm)) < 0) {
		av_log(NULL, AV_LOG_ERROR, "Unsupported hash algorithm: %s\n", algorithm);
		return NULL;
	}

    // A1 해시 계산 (username:realm:password)
    av_hash_init(hashctx);
    av_hash_update(hashctx, (const uint8_t *)username, strlen(username));
    av_hash_update(hashctx, (const uint8_t *)":", 1);
    av_hash_update(hashctx, (const uint8_t *)state->realm, strlen(state->realm));
    av_hash_update(hashctx, (const uint8_t *)":", 1);
    av_hash_update(hashctx, (const uint8_t *)password, strlen(password));
    av_hash_final(hashctx, hash);
    ff_data_to_hex(a1_hash, hash, av_hash_get_size(hashctx), 1);

    // A2 해시 계산 (method:uri)
    av_hash_init(hashctx);
    av_hash_update(hashctx, (const uint8_t *)method, strlen(method));
    av_hash_update(hashctx, (const uint8_t *)":", 1);
    av_hash_update(hashctx, (const uint8_t *)uri, strlen(uri));
    av_hash_final(hashctx, hash);
    ff_data_to_hex(a2_hash, hash, av_hash_get_size(hashctx), 1);
    
	// 응답 해시(response) 계산
    av_hash_init(hashctx);
    av_hash_update(hashctx, (const uint8_t *)a1_hash, strlen(a1_hash));
    av_hash_update(hashctx, (const uint8_t *)":", 1);
    av_hash_update(hashctx, (const uint8_t *)digest->nonce, strlen(digest->nonce));

    if (digest->qop[0]) {
        // qop 있는 경우 (auth, auth-int 등)
        av_hash_update(hashctx, (const uint8_t *)":", 1);
        av_hash_update(hashctx, (const uint8_t *)nc, strlen(nc));
        av_hash_update(hashctx, (const uint8_t *)":", 1);
        av_hash_update(hashctx, (const uint8_t *)cnonce, strlen(cnonce));
        av_hash_update(hashctx, (const uint8_t *)":", 1);
        av_hash_update(hashctx, (const uint8_t *)digest->qop, strlen(digest->qop));
    }

    av_hash_update(hashctx, (const uint8_t *)":", 1);
    av_hash_update(hashctx, (const uint8_t *)a2_hash, strlen(a2_hash));
    av_hash_final(hashctx, hash);

    // av_hash_init(hashctx);
    // av_hash_update(hashctx, (const uint8_t *)a1_hash, strlen(a1_hash));
    // av_hash_update(hashctx, (const uint8_t *)":", 1);
    // av_hash_update(hashctx, (const uint8_t *)digest->nonce, strlen(digest->nonce));
    // av_hash_update(hashctx, (const uint8_t *)":", 1);
    // av_hash_update(hashctx, (const uint8_t *)nc, strlen(nc));
    // av_hash_update(hashctx, (const uint8_t *)":", 1);
    // av_hash_update(hashctx, (const uint8_t *)cnonce, strlen(cnonce));
    // av_hash_update(hashctx, (const uint8_t *)":", 1);
    // av_hash_update(hashctx, (const uint8_t *)digest->qop, strlen(digest->qop));
    // av_hash_update(hashctx, (const uint8_t *)":", 1);
    // av_hash_update(hashctx, (const uint8_t *)a2_hash, strlen(a2_hash));
    // av_hash_final(hashctx, hash);

    ff_data_to_hex(response, hash, av_hash_get_size(hashctx), 1);

    av_hash_freep(&hashctx);
    if (digest->qop[0]) {
        // qop 있는 서버 (나중에 다른 장비용)
        authstr = av_asprintf(
            "Authorization: Digest username=\"%s\", realm=\"%s\", "
            "nonce=\"%s\", uri=\"%s\", response=\"%s\", "
            "algorithm=\"%s\", qop=\"%s\", nc=%s, cnonce=\"%s\"\r\n",
            username, state->realm, digest->nonce, uri, response,
            algorithm, digest->qop, nc, cnonce);
    } else {
        // 지금 이 카메라: qop 없음
        authstr = av_asprintf(
            "Authorization: Digest username=\"%s\", realm=\"%s\", "
            "nonce=\"%s\", uri=\"%s\", response=\"%s\", "
            "algorithm=\"%s\"\r\n",
            username, state->realm, digest->nonce, uri, response,
            algorithm);
    }

    if (authstr)
        av_log(NULL, AV_LOG_INFO, "### sha: final authstr: %s\n", authstr);
    else
        av_log(NULL, AV_LOG_ERROR, "### sha: failed to alloc authstr\n");

    return authstr;

   
//    if (authstr) {
//        av_log(NULL, AV_LOG_INFO, "Generated Digest Auth: %s\n", authstr);
//    } else {
//        av_log(NULL, AV_LOG_ERROR, "Failed to generate Digest Auth string.\n");
//    }
	
    return authstr;
}

char *ff_http_auth_create_response(HTTPAuthState *state, const char *auth,
                                   const char *path, const char *method)
{
    char *authstr = NULL;

    /* Clear the stale flag, we assume the auth is ok now. It is reset
     * by the server headers if there's a new issue. */
    state->stale = 0;
    if (!auth || !strchr(auth, ':'))
        return NULL;

    if (state->auth_type == HTTP_AUTH_BASIC) {
        int auth_b64_len, len;
        char *ptr, *decoded_auth = ff_urldecode(auth, 0);

        if (!decoded_auth)
            return NULL;

        auth_b64_len = AV_BASE64_SIZE(strlen(decoded_auth));
        len = auth_b64_len + 30;

        authstr = av_malloc(len);
        if (!authstr) {
            av_free(decoded_auth);
            return NULL;
        }

        snprintf(authstr, len, "Authorization: Basic ");
        ptr = authstr + strlen(authstr);
        av_base64_encode(ptr, auth_b64_len, decoded_auth, strlen(decoded_auth));
        av_strlcat(ptr, "\r\n", len - (ptr - authstr));
        av_free(decoded_auth);
    } else if (state->auth_type == HTTP_AUTH_DIGEST) {
        char *username = ff_urldecode(auth, 0), *password;

        if (!username)
            return NULL;

        if ((password = strchr(username, ':'))) {
            *password++ = 0;
            
			/* SHA-256 지원 추가 modified by khkim 2025.02.07 */
            if (!strcmp(state->digest_params.algorithm, "SHA-256")) {
                authstr = make_digest_auth_sha(state, username, password, path, method, "SHA-256");
            } else if (!strcmp(state->digest_params.algorithm, "SHA-512-256")) {
                authstr = make_digest_auth_sha(state, username, password, path, method, "SHA-512-256");
            } else {
                authstr = make_digest_auth(state, username, password, path, method);
            }
			/* 기존 코드 modified by khkim 2025.02.07
            /* authstr = make_digest_auth(state, username, password, path, method); */
        }
        av_free(username);
    }
    return authstr;
}
