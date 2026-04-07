#!/usr/bin/env bash
###############################################################################
# CCTV Util 시작 스크립트
# 
# 사용법:
#   chmod +x start.sh
#   ./start.sh
###############################################################################

# 현재 스크립트 위치를 기준으로 작업
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 가상환경 확인
if [ ! -d ".venv" ]; then
    echo -e "${RED}[ERROR]${NC} 가상환경이 없습니다. 먼저 setup_and_run.sh를 실행하세요."
    echo -e "${BLUE}[INFO]${NC}  ./setup_and_run.sh --install"
    exit 1
fi

# 기존 환경 변수 제거 (충돌 방지)
unset PYTHONHOME
unset PYTHONPATH
unset PYTHONNOUSERSITE

# 가상환경 활성화
echo -e "${BLUE}[INFO]${NC} 가상환경 활성화 중..."
source .venv/bin/activate

# Python 버전 확인
echo -e "${GREEN}[SUCCESS]${NC} 가상환경 활성화 완료: $(python --version)"

# 애플리케이션 실행
echo -e "${BLUE}[INFO]${NC} 애플리케이션 시작..."
echo "=============================================="
python main.py
