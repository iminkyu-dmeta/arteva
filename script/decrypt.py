import base64
import os
import urllib.parse

import hashlib;

import array
import binascii

class ARIA:
    """
    KISA(한국인터넷진흥원) ARIA 암호 알고리즘 표준 명세를 바탕으로 구현된 클래스입니다.
    ARIA-256 비트 암호화 및 복호화를 지원하며, ECB 모드를 기본으로 합니다.
    """

    # ARIA S-boxes
    S1 = [
        0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
        0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
        0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
        0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
        0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
        0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
        0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
        0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
        0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
        0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
        0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
        0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
        0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
        0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
        0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
        0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
    ]
    S2 = [
        0xE2, 0x4E, 0x54, 0xFC, 0x94, 0xC2, 0x4A, 0xCC, 0x62, 0x0D, 0x6A, 0x46, 0x3C, 0x4D, 0x8B, 0xD1,
        0x5E, 0xFA, 0x64, 0xCB, 0xB4, 0x97, 0xBE, 0x2B, 0xBC, 0x77, 0x2E, 0x03, 0xD3, 0x19, 0x59, 0xC1,
        0x1D, 0x06, 0x41, 0x6B, 0x55, 0xF0, 0x99, 0x69, 0xEA, 0x9C, 0x18, 0xAE, 0x63, 0xDF, 0xE7, 0xBB,
        0x00, 0x73, 0x66, 0xFB, 0x96, 0x4C, 0x85, 0xE4, 0x3A, 0x09, 0x45, 0xAA, 0x0F, 0xEE, 0x10, 0xEB,
        0x2D, 0x7F, 0xF4, 0x29, 0xAC, 0xCF, 0xAD, 0x91, 0x8D, 0x78, 0xC8, 0x95, 0xF9, 0x2F, 0xCE, 0xCD,
        0x08, 0x7A, 0x88, 0x38, 0x5C, 0x83, 0x2A, 0x28, 0x47, 0xDB, 0xB8, 0xC7, 0x93, 0xA4, 0x12, 0x53,
        0xFF, 0x87, 0x0E, 0x31, 0x36, 0x21, 0x58, 0x48, 0x01, 0x8E, 0x37, 0x74, 0x32, 0xCA, 0xE9, 0xB1,
        0xB7, 0xAB, 0x0C, 0xD7, 0xC4, 0x56, 0x42, 0x26, 0x07, 0x98, 0x60, 0xD9, 0xB6, 0xB9, 0x11, 0x40,
        0xEC, 0x20, 0x8C, 0xBD, 0xA0, 0xC9, 0x84, 0x04, 0x49, 0x23, 0xF1, 0x4F, 0x50, 0x1F, 0x13, 0xDC,
        0xD8, 0xC0, 0x9E, 0x57, 0xE3, 0xC3, 0x7B, 0x65, 0x3B, 0x02, 0x8F, 0x3E, 0xE8, 0x25, 0x92, 0xE5,
        0x15, 0xDD, 0xFD, 0x17, 0xA9, 0xBF, 0xD4, 0x9A, 0x7E, 0xC5, 0x39, 0x67, 0xFE, 0x76, 0x9D, 0x43,
        0xA7, 0xE1, 0xD0, 0xF5, 0x68, 0xF2, 0x1B, 0x34, 0x70, 0x05, 0xA3, 0x8A, 0xD5, 0x79, 0x86, 0xA8,
        0x30, 0xC6, 0x51, 0x4B, 0x1E, 0xA6, 0x27, 0xF6, 0x35, 0xD2, 0x6E, 0x24, 0x16, 0x82, 0x5F, 0xDA,
        0xE6, 0x75, 0xA2, 0xEF, 0x2C, 0xB2, 0x1C, 0x9F, 0x5D, 0x6F, 0x80, 0x0A, 0x72, 0x44, 0x9B, 0x6C,
        0x90, 0x0B, 0x5B, 0x33, 0x7D, 0x5A, 0x52, 0xF3, 0x61, 0xA1, 0xF7, 0xB0, 0xD6, 0x3F, 0x7C, 0x6D,
        0xED, 0x14, 0xE0, 0xA5, 0x3D, 0x22, 0xB3, 0xF8, 0x89, 0xDE, 0x71, 0x1A, 0xAF, 0xBA, 0xB5, 0x81
    ]
    @classmethod
    def _init_static(cls):
        cls.X1 = [cls.S1[i] for i in range(256)]
        cls.X2 = [cls.S2[i] for i in range(256)]
        cls.Y1 = [0] * 256
        cls.Y2 = [0] * 256
        for i in range(256):
            cls.Y1[cls.X1[i]] = i
            cls.Y2[cls.X2[i]] = i

    KR = {128: 12, 192: 14, 256: 16}

    def __init__(self, key):
        """
        키를 초기화하고 라운드 키를 생성합니다.
        :param key: 128, 192, 256비트 바이트 키
        """
        if not hasattr(self, 'Y1'):
            self._init_static()
        self.key = list(key)
        self.bits = len(key) * 8
        self.rounds = self.KR[self.bits]
        self.enc_round_keys = self._expand_key(self.key)
        self.dec_round_keys = self._expand_dec_key(self.enc_round_keys)

    def _expand_key(self, key):
        C = [
            [0x51, 0x7c, 0xc1, 0xb7, 0x27, 0x22, 0x0a, 0x94, 0xfe, 0x13, 0xab, 0xe8, 0xfa, 0x9a, 0x6e, 0xe0],
            [0x6d, 0xb1, 0x4a, 0xcc, 0x9e, 0x21, 0xc8, 0x20, 0xff, 0x28, 0xb1, 0xd5, 0xef, 0x5d, 0xe2, 0xb0],
            [0xdb, 0x92, 0x37, 0x1d, 0x21, 0x26, 0xe9, 0x70, 0x03, 0x24, 0x97, 0x75, 0x04, 0xe8, 0xc9, 0x0e]
        ]

        w0 = key[:16]
        w1 = [0] * 16
        idx = (self.bits // 64) - 2

        temp = [0] * 16
        for i in range(4):
            temp[4*i] = self.S1[C[idx][4*i] ^ w0[4*i]]
            temp[4*i+1] = self.S2[C[idx][4*i+1] ^ w0[4*i+1]]
            temp[4*i+2] = self.Y1[C[idx][4*i+2] ^ w0[4*i+2]]
            temp[4*i+3] = self.Y2[C[idx][4*i+3] ^ w0[4*i+3]]

        w1 = self._diff_layer(temp)
        if self.bits >= 192:
            for i in range(8): w1[i] ^= key[16+i]
        if self.bits == 256:
            for i in range(8): w1[8+i] ^= key[24+i]

        idx = (idx + 1) % 3
        for i in range(4):
            temp[4*i] = self.Y1[C[idx][4*i] ^ w1[4*i]]
            temp[4*i+1] = self.Y2[C[idx][4*i+1] ^ w1[4*i+1]]
            temp[4*i+2] = self.S1[C[idx][4*i+2] ^ w1[4*i+2]]
            temp[4*i+3] = self.S2[C[idx][4*i+3] ^ w1[4*i+3]]
        w2 = self._diff_layer(temp)
        for i in range(16): w2[i] ^= w0[i]

        idx = (idx + 1) % 3
        for i in range(4):
            temp[4*i] = self.S1[C[idx][4*i] ^ w2[4*i]]
            temp[4*i+1] = self.S2[C[idx][4*i+1] ^ w2[4*i+1]]
            temp[4*i+2] = self.Y1[C[idx][4*i+2] ^ w2[4*i+2]]
            temp[4*i+3] = self.Y2[C[idx][4*i+3] ^ w2[4*i+3]]
        w3 = self._diff_layer(temp)
        for i in range(16): w3[i] ^= w1[i]

        rk = []
        for i in range(self.rounds + 1): rk.append([0]*16)

        for i in range(16):
            rk[0][i] = w0[i] ^ self._rot_right(w1, 19)[i]
            rk[1][i] = w1[i] ^ self._rot_right(w2, 19)[i]
            rk[2][i] = w2[i] ^ self._rot_right(w3, 19)[i]
            rk[3][i] = w3[i] ^ self._rot_right(w0, 19)[i]
            rk[4][i] = w0[i] ^ self._rot_right(w1, 31)[i]
            rk[5][i] = w1[i] ^ self._rot_right(w2, 31)[i]
            rk[6][i] = w2[i] ^ self._rot_right(w3, 31)[i]
            rk[7][i] = w3[i] ^ self._rot_right(w0, 31)[i]
            rk[8][i] = w0[i] ^ self._rot_right(w1, 67)[i]
            rk[9][i] = w1[i] ^ self._rot_right(w2, 67)[i]
            rk[10][i] = w2[i] ^ self._rot_right(w3, 67)[i]
            rk[11][i] = w3[i] ^ self._rot_right(w0, 67)[i]
            rk[12][i] = w0[i] ^ self._rot_right(w1, 97)[i]
            if self.rounds > 12:
                rk[13][i] = w1[i] ^ self._rot_right(w2, 97)[i]
                rk[14][i] = w2[i] ^ self._rot_right(w3, 97)[i]
            if self.rounds > 14:
                rk[15][i] = w3[i] ^ self._rot_right(w0, 97)[i]
                rk[16][i] = w0[i] ^ self._rot_right(w1, 109)[i]
        return rk

    def _expand_dec_key(self, rk):
        drk = [[0]*16 for _ in range(self.rounds + 1)]
        drk[0] = rk[self.rounds][:]
        for i in range(1, self.rounds):
            drk[i] = self._diff_layer(rk[self.rounds - i])
        drk[self.rounds] = rk[0][:]
        return drk

    def _diff_layer(self, i):
        o = [0] * 16
        t = i[3] ^ i[4] ^ i[9] ^ i[14]
        o[0] = i[6] ^ i[8] ^ i[13] ^ t
        o[5] = i[1] ^ i[10] ^ i[15] ^ t
        o[11] = i[2] ^ i[7] ^ i[12] ^ t
        o[14] = i[0] ^ i[5] ^ i[11] ^ t
        t = i[2] ^ i[5] ^ i[8] ^ i[15]
        o[1] = i[7] ^ i[9] ^ i[12] ^ t
        o[4] = i[0] ^ i[11] ^ i[14] ^ t
        o[10] = i[3] ^ i[6] ^ i[13] ^ t
        o[15] = i[1] ^ i[4] ^ i[10] ^ t
        t = i[1] ^ i[6] ^ i[11] ^ i[12]
        o[2] = i[4] ^ i[10] ^ i[15] ^ t
        o[7] = i[3] ^ i[8] ^ i[13] ^ t
        o[9] = i[0] ^ i[5] ^ i[14] ^ t
        o[12] = i[2] ^ i[7] ^ i[9] ^ t
        t = i[0] ^ i[7] ^ i[10] ^ i[13]
        o[3] = i[5] ^ i[11] ^ i[14] ^ t
        o[6] = i[2] ^ i[9] ^ i[12] ^ t
        o[8] = i[1] ^ i[4] ^ i[15] ^ t
        o[13] = i[3] ^ i[6] ^ i[8] ^ t
        return o

    def _rot_right(self, w, n):
        res = [0] * 16
        q, r = divmod(n, 8)
        for i in range(16):
            res[(i+q)%16] ^= (w[i] >> r)
            if r != 0:
                res[(i+q+1)%16] ^= ((w[i] << (8-r)) & 0xFF)
        return res

    def decrypt(self, data):
        """
        데이터를 복호화합니다.
        :param data: 16바이트의 배수인 암호화된 바이트 데이터
        :return: 복호화된 바이트 데이터
        """
        res = b''
        for i in range(0, len(data), 16):
            res += bytes(self._crypt(list(data[i:i+16]), self.dec_round_keys))
        return res

    def _crypt(self, block, rk):
        c = block[:]
        t = [0] * 16
        for i in range(self.rounds // 2):
            # Odd round
            for j in range(4):
                t[4*j] = self.S1[rk[2*i][4*j] ^ c[4*j]]
                t[4*j+1] = self.S2[rk[2*i][4*j+1] ^ c[4*j+1]]
                t[4*j+2] = self.Y1[rk[2*i][4*j+2] ^ c[4*j+2]]
                t[4*j+3] = self.Y2[rk[2*i][4*j+3] ^ c[4*j+3]]
            c = self._diff_layer(t)
            # Even round
            for j in range(4):
                t[4*j] = self.Y1[rk[2*i+1][4*j] ^ c[4*j]]
                t[4*j+1] = self.Y2[rk[2*i+1][4*j+1] ^ c[4*j+1]]
                t[4*j+2] = self.S1[rk[2*i+1][4*j+2] ^ c[4*j+2]]
                t[4*j+3] = self.S2[rk[2*i+1][4*j+3] ^ c[4*j+3]]
            c = self._diff_layer(t)

        final = self._diff_layer(c)
        for i in range(16):
            final[i] ^= rk[self.rounds][i]
        return final

def ansi_x923_pad(data, block_size):
    """
    ANSI X.923 패딩을 추가합니다. (Java AnsiX923Padding 호환)
    """
    padding_cnt = block_size - (len(data) % block_size)
    return data + b'\x00' * (padding_cnt - 1) + bytes([padding_cnt])

def ansi_x923_unpad(data):
    """
    ANSI X.923 패딩을 제거합니다.
    """
    padding_len = data[-1]
    return data[:-padding_len]

def printBlock(s, end='\n'):
    """
    Input: Byte array 's' of size 16, string 'end'
    Output: None
    Print the byte array 's' in nice hex format. Between each bytes, it has a space.
    After printing all of bytes in 's', print 'end' at end of it.
    """
    for byte in s:
        print("0"*[0,1][byte<16]+hex(byte)[2:], end=' ' )


    print(end)

def decrypt_password(enc_url_str, password=None):
    """
    전자정부 프레임워크(Java) 방식의 ARIA-256-ECB 복호화를 수행합니다.
    """
    if password is None:
        raise ValueError("password environment variable is not set")

    # 1. URL 및 Base64 디코딩
    enc_str = urllib.parse.unquote(enc_url_str)
    data = base64.b64decode(enc_str)

    print("enc_url_str : %s" % enc_url_str)
    print()
    print("enc_str : %s" % enc_str)
    print()
    print("data : %s" % data)
    print()
    # 2. 키 생성 (패스워드를 32바이트 ANSI X.923 패딩하여 키로 사용)
    key = ansi_x923_pad(password.encode('utf-8'), 32)

    print("key_pad : %s" % key)
    print()
    # 3. 복호화
    aria = ARIA(key)
    decrypted = aria.decrypt(data)

    print("decrypted: %s" % decrypted)
    # 4. 패딩 제거 및 반환
    return ansi_x923_unpad(decrypted).decode('utf-8')

def encrypt_password(enc_url_str, password=None):

    #hex_string=hashlib.md5(password.encode()).hexdigest()
    #key = bytearray.fromhex(hex_string)
    
    key = ansi_x923_pad(password.encode('utf-8'), 32)
    plain = array.array('B', enc_url_str.ljust(16).encode())

    print("key")    
    print(key)    
    print("plain")
    print(plain)

    #roundkeys = aria._expand_key(key)
    aria = ARIA(key)
    print("Encryption")
    c = aria._crypt(plain, key)
    print("Cipher Text:")
    printBlock(c)


if __name__ == "__main__":
    #aria_key="dmeta123!"
    #password="asdQWE12!@"
    ARIA_KEY="uM7bagPCbzjT72YadTgvAg%3D%3D"
    password = "xlQNUmlODEG4Ce5p%2B9406A%3D%3D"
    aria_key=decrypt_password(ARIA_KEY,"dmeta123!")  # 패스워드 복호화
    print(aria_key)
    res_password = decrypt_password(password,aria_key)  # 패스워드 복호화
    #res_password = encrypt_password(password,aria_key)  

    print(password)
    print(res_password)
