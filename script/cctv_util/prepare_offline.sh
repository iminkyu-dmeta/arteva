#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# 오프라인 설치 패키지 준비 스크립트
# 
# 인터넷이 되는 환경에서 이 스크립트를 실행하면:
# 1. Python Standalone Build 다운로드 (Linux 서버용 - 설치 없이 바로 실행 가능)
# 2. pip 패키지들을 wheel 파일로 다운로드 (현재 시스템 Python 사용)
# 
# 사용법:
#   chmod +x prepare_offline.sh
#   ./prepare_offline.sh
#
# 그 후 전체 폴더를 폐쇄망 서버로 복사하면 됩니다.
###############################################################################

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 설정값
PYTHON_VERSION="3.9.18"
PYTHON_BUILD_VERSION="20240107"  # python-build-standalone 릴리즈 날짜
OFFLINE_DIR="offline_packages"
PYTHON_DIR="$OFFLINE_DIR/python"
WHEELS_DIR="$OFFLINE_DIR/wheels"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

###############################################################################
# 현재 시스템 Python 확인
###############################################################################

check_local_python() {
    log_info "현재 시스템 Python 확인 중..."
    
    # 사용 가능한 Python 찾기
    for cmd in python3.9 python3.10 python3.11 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            LOCAL_PYTHON="$cmd"
            log_success "사용할 Python: $LOCAL_PYTHON ($($LOCAL_PYTHON --version))"
            return 0
        fi
    done
    
    log_error "Python을 찾을 수 없습니다. Python 3.x를 설치해주세요."
    exit 1
}

###############################################################################
# 디렉터리 생성
###############################################################################

prepare_dirs() {
    log_info "오프라인 패키지 디렉터리 생성 중..."
    mkdir -p "$PYTHON_DIR"
    mkdir -p "$WHEELS_DIR"
    log_success "디렉터리 생성 완료"
}

###############################################################################
# Python Standalone 다운로드 (Linux 서버용)
###############################################################################

download_python() {
    log_info "Python Standalone Build 다운로드 중 (Linux x86_64 용)..."
    
    # python-build-standalone 릴리즈 URL
    # https://github.com/indygreg/python-build-standalone/releases
    PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/${PYTHON_BUILD_VERSION}/cpython-${PYTHON_VERSION}+${PYTHON_BUILD_VERSION}-x86_64-unknown-linux-gnu-install_only.tar.gz"
    
    PYTHON_ARCHIVE="$OFFLINE_DIR/python-${PYTHON_VERSION}-linux-x86_64.tar.gz"
    
    if [ -f "$PYTHON_ARCHIVE" ]; then
        log_warning "Python 아카이브가 이미 존재합니다: $PYTHON_ARCHIVE"
        log_info "다시 다운로드하려면 먼저 삭제하세요: rm $PYTHON_ARCHIVE"
    else
        log_info "다운로드 URL: $PYTHON_URL"
        curl -L -o "$PYTHON_ARCHIVE" "$PYTHON_URL"
        log_success "Python 다운로드 완료"
    fi
    
    # 압축 해제 전 아카이브 구조 확인
    log_info "아카이브 구조 확인 중..."
    local top_dir
    top_dir=$(tar -tzf "$PYTHON_ARCHIVE" | head -1 | cut -d'/' -f1)
    log_info "아카이브 최상위 디렉토리: $top_dir"
    
    # 아카이브 내 lib/python3.9 존재 확인
    if tar -tzf "$PYTHON_ARCHIVE" | grep -q "lib/python3.9/"; then
        log_success "아카이브에 lib/python3.9 디렉토리 존재 확인"
    else
        log_error "아카이브에 lib/python3.9 디렉토리가 없습니다!"
        log_info "아카이브 내용 일부:"
        tar -tzf "$PYTHON_ARCHIVE" | head -20
        exit 1
    fi
    
    # 압축 해제
    log_info "Python 압축 해제 중..."
    rm -rf "$PYTHON_DIR"
    mkdir -p "$PYTHON_DIR"
    
    # --strip-components 없이 압축 해제 후 이동
    local temp_extract="$OFFLINE_DIR/python_temp"
    rm -rf "$temp_extract"
    mkdir -p "$temp_extract"
    tar -xzf "$PYTHON_ARCHIVE" -C "$temp_extract"
    
    # 압축 해제된 구조 확인
    log_info "압축 해제된 구조:"
    ls -la "$temp_extract/"
    
    # 최상위 디렉토리가 있으면 그 내용을 이동
    if [ -d "$temp_extract/python" ]; then
        mv "$temp_extract/python/"* "$PYTHON_DIR/"
    elif [ -d "$temp_extract/$top_dir" ]; then
        mv "$temp_extract/$top_dir/"* "$PYTHON_DIR/"
    else
        # 최상위 디렉토리 없이 바로 풀린 경우
        mv "$temp_extract/"* "$PYTHON_DIR/"
    fi
    rm -rf "$temp_extract"
    
    log_success "Python 압축 해제 완료: $PYTHON_DIR"
    
    # 압축 해제 결과 확인
    log_info "압축 해제 결과 확인..."
    log_info "  bin/: $(ls "$PYTHON_DIR/bin/" 2>/dev/null | wc -l) 파일"
    log_info "  lib/: $(ls "$PYTHON_DIR/lib/" 2>/dev/null)"
    
    # lib/python3.9 존재 확인
    if [ -d "$PYTHON_DIR/lib/python3.9" ]; then
        log_success "lib/python3.9 디렉토리 존재 확인"
        log_info "  lib/python3.9/: $(ls "$PYTHON_DIR/lib/python3.9/" 2>/dev/null | head -10 | tr '\n' ' ')"
        
        # encodings 모듈 확인
        if [ -d "$PYTHON_DIR/lib/python3.9/encodings" ]; then
            log_success "encodings 모듈 존재 확인"
        else
            log_error "encodings 모듈이 없습니다!"
            exit 1
        fi
    else
        log_error "lib/python3.9 디렉토리가 없습니다!"
        log_info "lib/ 디렉토리 내용:"
        ls -la "$PYTHON_DIR/lib/" 2>/dev/null || echo "lib 디렉토리 없음"
        exit 1
    fi
    
    # Linux용이므로 현재 시스템(macOS)에서는 실행 불가 - 확인만
    if [ -f "$PYTHON_DIR/bin/python3" ]; then
        log_success "Python 실행 파일 존재 확인: $PYTHON_DIR/bin/python3"
        log_info "(Linux용이므로 macOS에서는 실행되지 않습니다)"
    else
        log_error "Python 실행 파일을 찾을 수 없습니다."
        exit 1
    fi
}

###############################################################################
# pip 패키지 다운로드 (wheel 파일) - 현재 시스템 Python 사용
###############################################################################

download_wheels() {
    log_info "pip 패키지 wheel 파일 다운로드 중..."
    log_info "현재 시스템 Python 사용: $LOCAL_PYTHON"
    
    # wheel 패키지 다운로드 (Linux x86_64 용)
    log_info "Linux x86_64용 wheel 다운로드 중..."
    $LOCAL_PYTHON -m pip download \
        --dest "$WHEELS_DIR" \
        --platform linux_x86_64 \
        --platform manylinux2014_x86_64 \
        --platform manylinux_2_17_x86_64 \
        --python-version 39 \
        --only-binary=:all: \
        -r requirements.txt || true
    
    # 순수 Python 패키지용 (any platform) - 소스 배포판
    log_info "순수 Python 패키지 다운로드 중..."
    $LOCAL_PYTHON -m pip download \
        --dest "$WHEELS_DIR" \
        -r requirements.txt 2>/dev/null || true
    
    log_success "wheel 파일 다운로드 완료"
}

###############################################################################
# pip 자체도 wheel로 다운로드
###############################################################################

download_pip_wheel() {
    log_info "pip, setuptools, wheel 다운로드 중..."
    
    $LOCAL_PYTHON -m pip download \
        --dest "$WHEELS_DIR" \
        --platform linux_x86_64 \
        --platform manylinux2014_x86_64 \
        --python-version 39 \
        --only-binary=:all: \
        pip setuptools wheel || true
    
    # any platform 버전도 다운로드
    $LOCAL_PYTHON -m pip download \
        --dest "$WHEELS_DIR" \
        pip setuptools wheel 2>/dev/null || true
    
    log_success "pip 관련 패키지 다운로드 완료"
}

###############################################################################
# 설치 확인용 테스트
###############################################################################

verify_downloads() {
    log_info "다운로드 확인 중..."
    
    echo
    echo "=== Python (Linux용) ==="
    ls -la "$PYTHON_DIR/bin/python3" 2>/dev/null || echo "Python 파일 없음"
    
    echo
    echo "=== Wheel 파일 ==="
    ls -la "$WHEELS_DIR"/*.whl 2>/dev/null | head -20 || echo "wheel 파일 없음"
    
    echo
    echo "=== 다운로드된 패키지 목록 ==="
    ls "$WHEELS_DIR" | grep -E "\.whl$|\.tar\.gz$" | head -30
    
    echo
    log_success "오프라인 패키지 준비 완료!"
    echo
    log_info "전체 폴더 크기:"
    du -sh "$OFFLINE_DIR"
    echo
    log_info "=============================================="
    log_info "  다음 단계"
    log_info "=============================================="
    log_info "1. 이 전체 디렉터리를 폐쇄망 서버로 복사"
    log_info "   scp -r $(pwd) user@server:/path/to/destination"
    log_info ""
    log_info "2. 서버에서 실행:"
    log_info "   chmod +x setup_and_run.sh"
    log_info "   ./setup_and_run.sh"
    log_info "=============================================="
}

###############################################################################
# 메인 실행
###############################################################################

echo "=============================================="
echo "  오프라인 설치 패키지 준비"
echo "=============================================="
echo

check_local_python
prepare_dirs
download_python
download_pip_wheel
download_wheels
verify_downloads
