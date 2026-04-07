"""
부모-자식 프로세스 간 통신 메시지 정의
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional


class MessageType(Enum):
    """메시지 타입 정의"""
    # Worker -> Manager
    HEARTBEAT = auto()          # 생존 신호
    STATUS_UPDATE = auto()      # 상태 업데이트
    FRAME_CAPTURED = auto()     # 프레임 캡처 완료
    ERROR = auto()              # 에러 발생
    WORKER_READY = auto()       # 워커 준비 완료
    WORKER_STOPPED = auto()     # 워커 종료
    
    # Manager -> Worker
    COMMAND_STOP = auto()       # 종료 명령
    COMMAND_PAUSE = auto()      # 일시정지 명령
    COMMAND_RESUME = auto()     # 재개 명령
    COMMAND_UPDATE_CONFIG = auto()  # 설정 업데이트
    
    # 양방향
    ACK = auto()                # 확인 응답
    PING = auto()               # 연결 확인


@dataclass
class Message:
    """프로세스 간 통신 메시지"""
    type: MessageType
    camera_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Optional[Any] = None
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "type": self.type.name,
            "camera_id": self.camera_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """딕셔너리에서 생성"""
        return cls(
            type=MessageType[data["type"]],
            camera_id=data["camera_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data.get("payload"),
        )
    
    @classmethod
    def heartbeat(cls, camera_id: str, stats: Optional[dict] = None) -> "Message":
        """Heartbeat 메시지 생성"""
        return cls(
            type=MessageType.HEARTBEAT,
            camera_id=camera_id,
            payload=stats or {},
        )
    
    @classmethod
    def error(cls, camera_id: str, error_msg: str) -> "Message":
        """에러 메시지 생성"""
        return cls(
            type=MessageType.ERROR,
            camera_id=camera_id,
            payload={"error": error_msg},
        )
    
    @classmethod
    def status_update(cls, camera_id: str, status: str, details: Optional[dict] = None) -> "Message":
        """상태 업데이트 메시지 생성"""
        return cls(
            type=MessageType.STATUS_UPDATE,
            camera_id=camera_id,
            payload={"status": status, "details": details or {}},
        )
    
    @classmethod
    def command_stop(cls, camera_id: str) -> "Message":
        """종료 명령 메시지 생성"""
        return cls(
            type=MessageType.COMMAND_STOP,
            camera_id=camera_id,
        )
