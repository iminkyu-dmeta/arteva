#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# CCTV Util 자동 설치 및 실행 스크립트 (오프라인/온라인 모드 지원)
# 
# 사용법:
#   chmod +x setup_and_run.sh
#   ./setup_and_run.sh              # 설치 + 실행 (자동 모드 감지)
#   ./setup_and_run.sh --install    # 설치만
#   ./setup_and_run.sh --run        # 실행만 (이미 설치된 경우)
#   ./setup_and_run.sh --patch      # FFmpeg 패치만 재실행
#
# 오프라인 모드:
#   offline_packages/ 폴더가 있으면 자동으로 오프라인 모드로 실행
###############################################################################

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 스크립트 위치를 기준으로 작업
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 설정값
VENV_DIR=".venv"
PYTHON_CMD=""  # 자동 탐지됨
REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=9
FFMPEG_LIB_DIR="$SCRIPT_DIR/ffmpeg_SHA256_lib"

# 오프라인 모드 설정
OFFLINE_DIR="$SCRIPT_DIR/offline_packages"
OFFLINE_PYTHON_DIR="$OFFLINE_DIR/python"
OFFLINE_WHEELS_DIR="$OFFLINE_DIR/wheels"
OFFLINE_MODE=false

###############################################################################
# 유틸리티 함수
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

###############################################################################
# 오프라인 모드 감지
###############################################################################

detect_offline_mode() {
    if [ -d "$OFFLINE_WHEELS_DIR" ]; then
        OFFLINE_MODE=true
        log_success "오프라인 패키지 감지됨 - 오프라인 모드로 실행"
    else
        OFFLINE_MODE=false
        log_info "온라인 모드로 실행"
    fi
}

###############################################################################
# 오프라인 Python 설정 (폐쇄망 전용)
###############################################################################

setup_offline_python() {
    log_info "오프라인 Python 설정 중..."
    
    # 오프라인 Python 디렉토리 확인
    if [ ! -d "$OFFLINE_PYTHON_DIR" ]; then
        log_error "오프라인 Python 디렉토리가 없습니다: $OFFLINE_PYTHON_DIR"
        log_error "prepare_offline.sh를 먼저 실행하여 Python을 다운로드하세요."
        exit 1
    fi
    
    # lib/python3.9 디렉토리 확인
    if [ ! -d "$OFFLINE_PYTHON_DIR/lib/python3.9" ]; then
        log_error "Python 라이브러리 디렉토리가 없습니다: $OFFLINE_PYTHON_DIR/lib/python3.9"
        log_info "offline_packages/python 디렉토리 구조:"
        ls -la "$OFFLINE_PYTHON_DIR/" 2>/dev/null || echo "디렉터리 없음"
        exit 1
    fi
    
    # 실행 권한 부여 (tar 압축 해제 시 권한이 사라질 수 있음)
    log_info "Python 실행 권한 설정 중..."
    chmod -R +x "$OFFLINE_PYTHON_DIR/bin/"
    
    # 기존 환경 변수 제거 (충돌 방지)
    unset PYTHONHOME
    unset PYTHONPATH
    unset PYTHONNOUSERSITE
    
    # python3.9 실행 파일 찾기
    if [ -x "$OFFLINE_PYTHON_DIR/bin/python3.9" ]; then
        PYTHON_CMD="$OFFLINE_PYTHON_DIR/bin/python3.9"
    elif [ -x "$OFFLINE_PYTHON_DIR/bin/python3" ]; then
        PYTHON_CMD="$OFFLINE_PYTHON_DIR/bin/python3"
    else
        log_error "오프라인 Python 실행 파일을 찾을 수 없습니다."
        log_info "확인할 경로: $OFFLINE_PYTHON_DIR/bin/"
        ls -la "$OFFLINE_PYTHON_DIR/bin/" 2>/dev/null || echo "디렉터리 없음"
        exit 1
    fi
    
    # Python standalone이 제대로 동작하는지 테스트
    log_info "오프라인 Python 테스트 중..."
    
    # 먼저 디렉토리 구조 출력 (디버깅용)
    log_info "Python 디렉토리 구조 확인..."
    log_info "  bin/: $(ls "$OFFLINE_PYTHON_DIR/bin/" 2>/dev/null | head -5 | tr '\n' ' ')"
    log_info "  lib/: $(ls "$OFFLINE_PYTHON_DIR/lib/" 2>/dev/null | head -5 | tr '\n' ' ')"
    
    # encodings 모듈 확인
    if [ ! -d "$OFFLINE_PYTHON_DIR/lib/python3.9/encodings" ]; then
        log_error "encodings 모듈이 없습니다!"
        log_error "Python 패키지가 손상되었거나 불완전합니다."
        log_info "tar 파일을 다시 다운로드하여 압축 해제해주세요."
        exit 1
    fi
    
    # 테스트 실행
    local test_output
    test_output=$("$PYTHON_CMD" -c "import sys; print(f'Python {sys.version}')" 2>&1) || {
        log_error "오프라인 Python 실행 실패"
        log_error "에러 메시지: $test_output"
        log_info ""
        log_info "=== 디버그 정보 ==="
        log_info "Python 경로: $PYTHON_CMD"
        log_info "file 명령어 결과:"
        file "$PYTHON_CMD" 2>/dev/null || echo "file 명령어 없음"
        log_info ""
        log_info "ldd 결과 (공유 라이브러리 의존성):"
        ldd "$PYTHON_CMD" 2>/dev/null || echo "ldd 명령어 없음"
        log_info ""
        log_info "현재 시스템 아키텍처: $(uname -m)"
        exit 1
    }
    
    log_success "오프라인 Python 사용: $test_output"
}

###############################################################################
# OS 타입 감지
###############################################################################

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_TYPE="$ID"
        OS_VERSION="$VERSION_ID"
    elif [ -f /etc/redhat-release ]; then
        OS_TYPE="rhel"
    elif [ -f /etc/debian_version ]; then
        OS_TYPE="debian"
    else
        OS_TYPE="unknown"
    fi
    log_info "감지된 OS: $OS_TYPE"
}

###############################################################################
# Python 설치 (sudo 권한 필요)
###############################################################################

install_python() {
    local version="$1"
    log_info "Python $version 설치 시도 중..."
    
    detect_os
    
    case "$OS_TYPE" in
        ubuntu|debian)
            log_info "Ubuntu/Debian 환경 감지 - apt 사용"
            sudo apt-get update
            sudo apt-get install -y software-properties-common
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt-get update
            sudo apt-get install -y python${version} python${version}-venv python${version}-dev
            ;;
        centos|rhel|rocky|almalinux)
            log_info "CentOS/RHEL 환경 감지 - yum/dnf 사용"
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python${version//./} python${version//./}-devel
            else
                sudo yum install -y epel-release
                sudo yum install -y python${version//./} python${version//./}-devel
            fi
            ;;
        fedora)
            log_info "Fedora 환경 감지 - dnf 사용"
            sudo dnf install -y python${version} python${version}-devel
            ;;
        *)
            log_error "지원되지 않는 OS입니다: $OS_TYPE"
            log_info "수동으로 Python $version을 설치해주세요."
            exit 1
            ;;
    esac
    
    log_success "Python $version 설치 완료"
}

###############################################################################
# Python 버전 확인 및 자동 탐지/설치
###############################################################################

check_python() {
    log_info "Python 버전 확인 중..."
    
    # 오프라인 모드면 오프라인 Python 사용
    if [ "$OFFLINE_MODE" = true ]; then
        setup_offline_python
        return 0
    fi
    
    # 사용 가능한 Python 버전들 탐색 (우선순위: 3.9 > 3.10 > 3.11 > 3.12 > 3.8 > python3)
    PYTHON_CANDIDATES=("python3.9" "python3.10" "python3.11" "python3.12" "python3.8" "python3")
    
    for candidate in "${PYTHON_CANDIDATES[@]}"; do
        if command -v "$candidate" &> /dev/null; then
            # 버전 확인
            version_output=$("$candidate" --version 2>&1)
            major=$(echo "$version_output" | sed 's/Python //' | cut -d'.' -f1)
            minor=$(echo "$version_output" | sed 's/Python //' | cut -d'.' -f2)
            
            if [ "$major" -ge "$REQUIRED_PYTHON_MAJOR" ] && [ "$minor" -ge "$REQUIRED_PYTHON_MINOR" ]; then
                PYTHON_CMD="$candidate"
                log_success "사용할 Python: $PYTHON_CMD ($version_output)"
                return 0
            fi
        fi
    done
    
    # Python을 찾지 못한 경우
    log_warning "Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR} 이상을 찾을 수 없습니다."
    log_info "현재 시스템에 설치된 Python 버전:"
    which python3 python3.* 2>/dev/null || echo "  설치된 python3 없음"
    echo
    
    read -p "Python 3.9를 자동으로 설치하시겠습니까? (sudo 권한 필요) (Y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        install_python "3.9"
        PYTHON_CMD="python3.9"
        
        # 설치 확인
        if ! command -v "$PYTHON_CMD" &> /dev/null; then
            log_error "Python 설치에 실패했습니다."
            exit 1
        fi
        
        log_success "Python 설치 완료: $($PYTHON_CMD --version)"
    else
        log_error "Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR} 이상이 필요합니다."
        log_info ""
        log_info "수동 설치 방법:"
        log_info "  Ubuntu/Debian:"
        log_info "    sudo apt update"
        log_info "    sudo add-apt-repository ppa:deadsnakes/ppa"
        log_info "    sudo apt install python3.9 python3.9-venv python3.9-dev"
        log_info ""
        log_info "  CentOS/RHEL:"
        log_info "    sudo yum install epel-release"
        log_info "    sudo yum install python39 python39-devel"
        log_info ""
        exit 1
    fi
}

###############################################################################
# 가상환경 생성
###############################################################################

create_venv() {
    log_info "가상환경 생성 중..."
    
    if [ -d "$VENV_DIR" ]; then
        log_warning "기존 가상환경이 존재합니다: $VENV_DIR"
        read -p "기존 가상환경을 삭제하고 새로 생성하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
            log_info "기존 가상환경 삭제 완료"
        else
            log_info "기존 가상환경 유지"
            return 0
        fi
    fi
    
    $PYTHON_CMD -m venv "$VENV_DIR"
    log_success "가상환경 생성 완료: $VENV_DIR"
}

###############################################################################
# 가상환경 활성화
###############################################################################

activate_venv() {
    log_info "가상환경 활성화 중..."
    
    if [ ! -d "$VENV_DIR" ]; then
        log_error "가상환경이 없습니다. 먼저 설치를 실행하세요."
        exit 1
    fi
    
    source "$VENV_DIR/bin/activate"
    log_success "가상환경 활성화 완료"
}

###############################################################################
# 패키지 설치
###############################################################################

install_packages() {
    if [ "$OFFLINE_MODE" = true ]; then
        install_packages_offline
    else
        install_packages_online
    fi
}

install_packages_online() {
    log_info "pip 업그레이드 중..."
    pip install --upgrade pip
    
    log_info "필수 패키지 설치 중 (온라인)..."
    pip install -r requirements.txt
    
    log_success "패키지 설치 완료"
}

install_packages_offline() {
    log_info "필수 패키지 설치 중 (오프라인)..."
    
    # pip 먼저 업그레이드 (오프라인 wheel 사용)
    log_info "pip 업그레이드 중 (오프라인)..."
    pip install --no-index --find-links="$OFFLINE_WHEELS_DIR" --upgrade pip setuptools wheel 2>/dev/null || true
    
    # 패키지 설치 (오프라인 wheel 사용)
    log_info "wheel 파일에서 패키지 설치 중..."
    pip install --no-index --find-links="$OFFLINE_WHEELS_DIR" -r requirements.txt
    
    log_success "패키지 설치 완료 (오프라인)"
}

###############################################################################
# OpenCV libs 디렉터리 자동 탐지
###############################################################################

find_opencv_libs_dir() {
    # 로그는 stderr로 출력 (반환값 오염 방지)
    echo -e "${BLUE}[INFO]${NC} OpenCV libs 디렉터리 탐색 중..." >&2
    
    # venv 내 site-packages 경로 찾기
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
    
    # opencv_python.libs 또는 opencv_python_headless.libs 찾기
    OPENCV_LIBS_DIR=""
    
    if [ -d "$SITE_PACKAGES/opencv_python.libs" ]; then
        OPENCV_LIBS_DIR="$SITE_PACKAGES/opencv_python.libs"
    elif [ -d "$SITE_PACKAGES/opencv_python_headless.libs" ]; then
        OPENCV_LIBS_DIR="$SITE_PACKAGES/opencv_python_headless.libs"
    fi
    
    if [ -z "$OPENCV_LIBS_DIR" ]; then
        echo -e "${RED}[ERROR]${NC} OpenCV libs 디렉터리를 찾을 수 없습니다." >&2
        echo -e "${BLUE}[INFO]${NC} site-packages 경로: $SITE_PACKAGES" >&2
        echo -e "${BLUE}[INFO]${NC} 사용 가능한 opencv 관련 디렉터리:" >&2
        ls -d "$SITE_PACKAGES"/opencv* 2>/dev/null || echo "  없음" >&2
        exit 1
    fi
    
    echo -e "${GREEN}[SUCCESS]${NC} OpenCV libs 디렉터리 발견: $OPENCV_LIBS_DIR" >&2
    echo "$OPENCV_LIBS_DIR"
}

###############################################################################
# FFmpeg SO 파일 패치
###############################################################################

patch_ffmpeg() {
    log_info "FFmpeg SO 파일 패치 시작..."
    
    # OpenCV libs 디렉터리 찾기
    OPENCV_LIB_DIR=$(find_opencv_libs_dir)
    
    if [ ! -d "$FFMPEG_LIB_DIR" ]; then
        log_error "FFmpeg 라이브러리 디렉터리가 없습니다: $FFMPEG_LIB_DIR"
        exit 1
    fi
    
    cd "$OPENCV_LIB_DIR"
    
    # 현재 opencv-python.libs 안의 ffmpeg 관련 파일 목록 출력
    log_info "현재 OpenCV libs 내 FFmpeg 파일:"
    ls -1 libav*.so.* libsw*.so.* 2>/dev/null || log_warning "FFmpeg 관련 파일 없음"
    echo
    
    # 동적으로 실제 파일 이름 찾기
    log_info "실제 파일 이름 매핑 중..."
    
    # 각 라이브러리에 대해 실제 파일 이름 찾기
    AVCODEC_FILE=$(ls libavcodec-*.so.59.* 2>/dev/null | head -1 || echo "")
    AVFORMAT_FILE=$(ls libavformat-*.so.59.* 2>/dev/null | head -1 || echo "")
    AVUTIL_FILE=$(ls libavutil-*.so.57.* 2>/dev/null | head -1 || echo "")
    SWSCALE_FILE=$(ls libswscale-*.so.6.* 2>/dev/null | head -1 || echo "")
    SWRESAMPLE_FILE=$(ls libswresample-*.so.4.* 2>/dev/null | head -1 || echo "")
    
    # 파일 존재 확인
    MISSING=0
    for var in AVCODEC_FILE AVFORMAT_FILE AVUTIL_FILE SWSCALE_FILE SWRESAMPLE_FILE; do
        value="${!var}"
        if [ -z "$value" ]; then
            log_error "$var 파일을 찾을 수 없습니다."
            MISSING=1
        else
            log_info "  발견: $value"
        fi
    done
    
    if [ "$MISSING" -ne 0 ]; then
        log_error "일부 FFmpeg 파일을 찾을 수 없습니다."
        log_info "OpenCV 버전이 다르거나 headless 버전일 수 있습니다."
        exit 1
    fi
    
    # 커스텀 FFmpeg SO 복사 (기존 파일 덮어쓰기)
    log_info "커스텀 FFmpeg SO 파일 복사 중..."
    cp -f "$FFMPEG_LIB_DIR/libavcodec.so.59.37.100"    "$AVCODEC_FILE"
    cp -f "$FFMPEG_LIB_DIR/libavformat.so.59.27.100"   "$AVFORMAT_FILE"
    cp -f "$FFMPEG_LIB_DIR/libavutil.so.57.28.100"     "$AVUTIL_FILE"
    cp -f "$FFMPEG_LIB_DIR/libswscale.so.6.7.100"      "$SWSCALE_FILE"
    cp -f "$FFMPEG_LIB_DIR/libswresample.so.4.7.100"   "$SWRESAMPLE_FILE"
    
    # 실행 권한 부여
    chmod +x "$AVCODEC_FILE" "$AVFORMAT_FILE" "$AVUTIL_FILE" "$SWSCALE_FILE" "$SWRESAMPLE_FILE"
    
    # 심볼릭 링크 생성 (OpenCV가 버전 없는 파일명으로 찾을 수 있도록)
    log_info "심볼릭 링크 생성 중..."
    ln -sf "$(basename "$AVCODEC_FILE")" libavcodec.so.59
    ln -sf "$(basename "$AVFORMAT_FILE")" libavformat.so.59
    ln -sf "$(basename "$AVUTIL_FILE")" libavutil.so.57
    ln -sf "$(basename "$SWSCALE_FILE")" libswscale.so.6
    ln -sf "$(basename "$SWRESAMPLE_FILE")" libswresample.so.4
    
    log_success "FFmpeg SO 파일 패치 완료!"
    
    # 패치 결과 확인
    log_info "패치된 파일 확인:"
    ls -la "$AVCODEC_FILE" "$AVFORMAT_FILE" "$AVUTIL_FILE" "$SWSCALE_FILE" "$SWRESAMPLE_FILE"
    log_info "심볼릭 링크 확인:"
    ls -la libavcodec.so.59 libavformat.so.59 libavutil.so.57 libswscale.so.6 libswresample.so.4
    
    cd "$SCRIPT_DIR"
}

###############################################################################
# 애플리케이션 실행
###############################################################################

run_app() {
    log_info "애플리케이션 실행 중..."
    python main.py
}

###############################################################################
# 전체 설치 프로세스
###############################################################################

full_install() {
    echo "=============================================="
    echo "  CCTV Util 설치 스크립트"
    echo "=============================================="
    echo
    
    detect_offline_mode
    check_python
    create_venv
    activate_venv
    install_packages
    patch_ffmpeg
    
    echo
    log_success "=============================================="
    log_success "  설치 완료!"
    log_success "=============================================="
    echo
    log_info "실행 방법:"
    log_info "  source $VENV_DIR/bin/activate"
    log_info "  python main.py"
    echo
    log_info "또는:"
    log_info "  ./setup_and_run.sh --run"
    echo
}

###############################################################################
# 메인 로직
###############################################################################

case "${1:-}" in
    --install)
        full_install
        ;;
    --run)
        activate_venv
        run_app
        ;;
    --patch)
        activate_venv
        patch_ffmpeg
        ;;
    --help|-h)
        echo "사용법: $0 [옵션]"
        echo
        echo "옵션:"
        echo "  (없음)      설치 후 실행"
        echo "  --install   설치만 수행"
        echo "  --run       실행만 수행 (이미 설치된 경우)"
        echo "  --patch     FFmpeg 패치만 재실행"
        echo "  --help      도움말 표시"
        ;;
    *)
        full_install
        echo
        read -p "지금 바로 애플리케이션을 실행하시겠습니까? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            run_app
        fi
        ;;
esac
