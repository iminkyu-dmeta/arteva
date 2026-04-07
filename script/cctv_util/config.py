"""
CCTV 프레임 수집 시스템 설정
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path


# =============================================================================
# 🎥 카메라 수집 설정 (여기만 수정하면 됩니다!)
# =============================================================================

# -----------------------------------------------------------------------------
# 📌 수집 모드 선택
# -----------------------------------------------------------------------------
# "database" : DB에서 카메라 ID로 URL 조회 (CAMERA_IDS 사용)
# "manual"   : 직접 URL 입력 (MANUAL_RTSP_URLS 사용)
CAMERA_SOURCE_MODE: str = "database"

# -----------------------------------------------------------------------------
# 📌 모드 1: Database 모드 설정 (CAMERA_SOURCE_MODE = "database")
# -----------------------------------------------------------------------------
# 수집할 카메라 ID 리스트 (t_arteva_camera_info 테이블의 ID 값)
# 예: [1, 2, 3, 4, 5] 또는 [10, 20, 30]
CAMERA_IDS: List[int] = [1, 22, 33, 4]

# -----------------------------------------------------------------------------
# 📌 모드 2: Manual 모드 설정 (CAMERA_SOURCE_MODE = "manual")
# -----------------------------------------------------------------------------
# Base URL 사용 여부
# True : BASE_URL + endpoint 조합 (예: "rtsp://admin:pass@192.168.1.100:554/" + "Channels/101")
# False: MANUAL_RTSP_URLS를 전체 URL로 사용
USE_BASE_URL: bool = True

# 공통 Base URL (USE_BASE_URL = True 일 때 사용)
BASE_URL: str = "rtsp://admin:dmeta1234@192.168.132.141:554/Streaming/"

# RTSP URL 또는 Endpoint 리스트
# USE_BASE_URL = True  → endpoint만 입력 (예: "Channels/101")
# USE_BASE_URL = False → 전체 URL 입력 (예: "rtsp://admin:pass@...")
MANUAL_RTSP_URLS: List[str] = [
    "Channels/101",
    "Channels/201",
    "Channels/301",
    "Channels/401",
    # 필요한 만큼 추가...
]

# =============================================================================


@dataclass
class DatabaseConfig:
    """MariaDB 데이터베이스 설정"""
    # 데이터베이스 연결 정보
    host: str = "192.168.132.143"
    port: int = 3306
    user: str = "dmeta"
    password: str = "dmeta!@34"
    database: str = "dmeta_arteva"
    charset: str = "utf8mb4"
    
    # 카메라 테이블 설정 (t_arteva_camera_info 테이블 사용)
    camera_table: str = "t_arteva_camera_info"
    
    # 컬럼 매핑 (t_arteva_camera_info 테이블 구조)
    # ID: int (PK, auto_increment) - 카메라 아이디
    # NAME: varchar(256) - 카메라명
    # URL: varchar(512) - 카메라 접속 URL
    # ACTIVE: char default 'A' - 카메라 사용 여부
    # RESOLUTION: varchar(15) - 해상도
    # COMMENT: varchar(512) - 코멘트
    column_mapping: Dict[str, str] = field(default_factory=lambda: {
        "camera_id": "ID",            # 카메라 ID 컬럼 (int, PK)
        "camera_name": "NAME",        # 카메라명 컬럼
        "rtsp_url": "URL",            # RTSP URL 컬럼
        "active": "ACTIVE",           # 활성화 여부 ('A' = Active)
        "resolution": "RESOLUTION",  # 해상도
        "comment": "COMMENT"          # 코멘트
    })
    
    # 수집할 카메라 ID 리스트 (상단 CAMERA_IDS 사용)
    # - ID가 지정되면: 해당 ID의 카메라만 조회
    # - 빈 리스트면: 에러 발생 후 종료
    camera_ids: List[int] = field(default_factory=lambda: CAMERA_IDS.copy())


@dataclass
class RTSPConfig:
    """RTSP 연결 설정"""
    # 실제 사용할 URL 리스트 (main.py에서 동적으로 설정됨)
    # - database 모드: DB에서 조회한 URL
    # - manual 모드: 상단 MANUAL_RTSP_URLS
    urls: List[str] = field(default_factory=list)
    
    # URL 조합 여부 (레거시, 현재는 False로 고정 사용)
    use_base_url: bool = False
    
    # 연결 타임아웃 (초)
    connection_timeout: int = 10
    # 재연결 대기 시간 (초)
    reconnect_delay: int = 3
    # 최대 재연결 시도 횟수 (0 = 무한)
    max_reconnect_attempts: int = 0


@dataclass
class CaptureConfig:
    """프레임 캡처 설정"""
    # 초당 수집할 프레임 수 (1 = 1초에 1프레임)
    frames_per_second: int = 10
    # 프레임 해상도 (None = 원본 유지)
    target_width: int = 1920
    target_height: int = 1080
    # OpenCV 버퍼 크기
    buffer_size: int = 1
    # 읽기 타임아웃 (ms)
    read_timeout_ms: int = 5000


@dataclass
class StorageConfig:
    """저장 설정"""
    # 기본 저장 경로
    base_path: Path = field(default_factory=lambda: Path("streaming_image"))
    # 이미지 포맷
    image_format: str = "jpg"
    # JPEG 품질 (0-100)
    jpeg_quality: int = 95
    # 파일명 포맷 (timestamp 기반)
    filename_format: str = "{timestamp}_{frame_id}.{format}"
    # 최대 저장 파일 수 (0 = 무제한)
    max_files_per_camera: int = 0
    # 저장 디스크 용량 체크 (GB)
    min_disk_space_gb: float = 1.0


@dataclass
class ProcessConfig:
    """프로세스 설정"""
    # Heartbeat 전송 간격 (초)
    heartbeat_interval: int = 10
    # Heartbeat 타임아웃 (초) - 이 시간 동안 응답 없으면 프로세스 재시작
    heartbeat_timeout: int = 30
    # 프로세스 시작 지연 (초) - 순차 시작 시 간격
    process_start_delay: float = 0.5
    # 메시지 큐 크기
    message_queue_size: int = 100


@dataclass
class LogConfig:
    """로깅 설정"""
    # 로그 기본 경로
    base_path: Path = field(default_factory=lambda: Path("logs"))
    # 로그 레벨
    level: str = "INFO"
    # 로그 파일 최대 크기 (MB)
    max_file_size_mb: int = 10
    # 백업 파일 개수
    backup_count: int = 5
    # 로그 포맷
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    # 날짜 포맷
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class StatsConfig:
    """통계 설정"""
    # 샘플링 주기 (초) - 이 주기마다 FPS를 샘플링하여 기록
    sampling_period: int = 1
    # 통계 로그 간격 (초) - 이 간격마다 샘플들의 평균 통계를 로그에 출력
    log_interval: int = 60


@dataclass
class VideoConfig:
    """비디오 저장 설정"""
    # 비디오 저장 활성화
    enabled: bool = True
    # 비디오 저장 경로
    base_path: Path = field(default_factory=lambda: Path("streaming_video"))
    # 세그먼트 길이 (초) - 이 시간마다 새 비디오 파일 생성
    segment_duration: int = 300
    # 코덱 선택: 'mp4v' (무난), 'MJPG' (빠름), 'avc1' (H.264, 작은 용량)
    codec: str = "mp4v"
    # 컨테이너 포맷 (확장자)
    container: str = "mp4"
    # 파일명 포맷
    filename_format: str = "{date}_{time}.{container}"
    # 최대 저장 파일 수 (0 = 무제한)
    max_files_per_camera: int = 0
    # 최소 디스크 공간 (GB)
    min_disk_space_gb: float = 5.0


@dataclass
class SaveModeConfig:
    """저장 모드 설정"""
    # 저장 모드: 'image', 'video', 'both'
    mode: str = "both"
    
    @property
    def save_images(self) -> bool:
        """이미지 저장 여부"""
        return self.mode in ("image", "both")
    
    @property
    def save_videos(self) -> bool:
        """비디오 저장 여부"""
        return self.mode in ("video", "both")


@dataclass
class AppConfig:
    """애플리케이션 전체 설정"""
    # 데이터베이스 설정 (카메라 URL을 DB에서 가져올 때 사용)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # 카메라 소스 모드 (상단 CAMERA_SOURCE_MODE 사용)
    # "database": DB에서 카메라 ID로 URL 조회
    # "manual": 직접 URL 입력
    camera_source_mode: str = CAMERA_SOURCE_MODE
    
    # Manual 모드 설정 (상단 설정 사용)
    use_base_url: bool = USE_BASE_URL
    base_url: str = BASE_URL
    manual_rtsp_urls: List[str] = field(default_factory=lambda: MANUAL_RTSP_URLS.copy())
    
    @property
    def use_database(self) -> bool:
        """DB 사용 여부 (camera_source_mode가 'database'면 True)"""
        return self.camera_source_mode.lower() == "database"
    
    def get_manual_urls(self) -> List[str]:
        """Manual 모드의 전체 URL 리스트 반환"""
        if self.use_base_url:
            return [f"{self.base_url}{url}" for url in self.manual_rtsp_urls]
        return self.manual_rtsp_urls
    
    rtsp: RTSPConfig = field(default_factory=RTSPConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    save_mode: SaveModeConfig = field(default_factory=SaveModeConfig)
    process: ProcessConfig = field(default_factory=ProcessConfig)
    log: LogConfig = field(default_factory=LogConfig)
    stats: StatsConfig = field(default_factory=StatsConfig)
    
    @classmethod
    def load(cls) -> "AppConfig":
        """설정 로드 (향후 파일/환경변수에서 로드 가능)"""
        return cls()


# 전역 설정 인스턴스
config = AppConfig.load()
