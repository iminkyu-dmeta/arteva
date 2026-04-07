"""
유틸리티 함수들
"""
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def extract_camera_id_from_url(url: str) -> str:
    """
    RTSP URL에서 카메라 ID 추출 (endpoint 기반)
    
    예시:
        rtsp://admin:pass@192.168.1.100:554/stream1 -> stream1
        rtsp://192.168.1.101/Channels/101 -> Channels_101
        rtsp://192.168.1.101/live/main -> live_main
    """
    try:
        parsed = urlparse(url)
        path = parsed.path or ""
        
        # 경로가 있으면 경로를 사용 (맨 앞 / 제거)
        if path:
            # 슬래시를 언더스코어로 변환
            camera_id = path.lstrip("/").replace("/", "_")
            # 특수문자를 언더스코어로 변환
            camera_id = re.sub(r"[^a-zA-Z0-9_]", "_", camera_id)
            # 연속된 언더스코어 제거
            camera_id = re.sub(r"_+", "_", camera_id)
            # 앞뒤 언더스코어 제거
            camera_id = camera_id.strip("_")
            return camera_id if camera_id else "unknown"
        
        # 경로가 없으면 IP 주소 사용 (fallback)
        host = parsed.hostname or "unknown"
        camera_id = host.replace(".", "_").replace("-", "_")
        camera_id = re.sub(r"[^a-zA-Z0-9_]", "", camera_id)
        return camera_id if camera_id else "unknown"
        
    except Exception:
        return "unknown"


def get_timestamp_str(fmt: str = "%Y%m%d_%H%M%S_%f") -> str:
    """현재 타임스탬프 문자열 반환"""
    return datetime.now().strftime(fmt)


def ensure_dir(path: Path) -> Path:
    """디렉토리 생성 (존재하지 않으면)"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def check_disk_space(path: Path, min_gb: float) -> bool:
    """
    디스크 여유 공간 확인
    
    Args:
        path: 확인할 경로
        min_gb: 최소 필요 공간 (GB)
    
    Returns:
        True if 충분한 공간 있음
    """
    try:
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024 ** 3)
        return free_gb >= min_gb
    except Exception:
        return True  # 확인 실패 시 계속 진행


def sanitize_filename(name: str) -> str:
    """파일명에서 안전하지 않은 문자 제거"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def format_bytes(bytes_val: int) -> str:
    """바이트를 읽기 쉬운 형식으로 변환"""
    value = float(bytes_val)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"
