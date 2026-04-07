"""
부모-자식 프로세스 간 메시지 처리
"""
from datetime import datetime
from logging import Logger
from multiprocessing import Queue
from queue import Empty, Full
from typing import Callable, Dict, Optional

from communication import Message, MessageType


class MessageHandler:
    """메시지 송수신 핸들러"""
    
    def __init__(
        self,
        camera_id: str,
        to_manager_queue: Queue,
        from_manager_queue: Queue,
        logger: Logger,
    ):
        self.camera_id = camera_id
        self._to_manager = to_manager_queue
        self._from_manager = from_manager_queue
        self._logger = logger
        
        # 명령 핸들러 등록
        self._command_handlers: Dict[MessageType, Callable] = {}
    
    def register_handler(self, msg_type: MessageType, handler: Callable) -> None:
        """명령 핸들러 등록"""
        self._command_handlers[msg_type] = handler
    
    def process_commands(self) -> None:
        """수신된 명령 처리"""
        try:
            while True:
                msg: Message = self._from_manager.get_nowait()
                self._handle_command(msg)
        except Empty:
            pass
    
    def _handle_command(self, msg: Message) -> None:
        """개별 명령 처리"""
        handler = self._command_handlers.get(msg.type)
        
        if handler:
            try:
                handler(msg)
            except Exception as e:
                self._logger.error(f"명령 처리 오류: {msg.type} - {e}")
        else:
            self._logger.debug(f"핸들러 미등록 명령: {msg.type}")
    
    def send(self, msg: Message, timeout: float = 1.0) -> bool:
        """메시지 전송"""
        try:
            self._to_manager.put(msg, timeout=timeout)
            return True
        except Full:
            self._logger.warning(f"메시지 전송 실패 (큐 가득 참): {msg.type}")
            return False
    
    def send_status(self, status: str, details: Optional[dict] = None) -> bool:
        """상태 업데이트 전송"""
        return self.send(Message.status_update(
            self.camera_id,
            status,
            details,
        ))
    
    def send_heartbeat(self, stats: dict) -> bool:
        """Heartbeat 전송"""
        return self.send(Message.heartbeat(self.camera_id, stats))
    
    def send_error(self, error_msg: str) -> bool:
        """에러 메시지 전송"""
        return self.send(Message.error(self.camera_id, error_msg))
    
    def send_ready(self, pid: int) -> bool:
        """준비 완료 알림"""
        return self.send(Message(
            type=MessageType.WORKER_READY,
            camera_id=self.camera_id,
            payload={"pid": pid},
        ))
    
    def send_stopped(self, stats: dict) -> bool:
        """종료 알림"""
        return self.send(Message(
            type=MessageType.WORKER_STOPPED,
            camera_id=self.camera_id,
            payload=stats,
        ))
