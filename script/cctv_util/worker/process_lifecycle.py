"""
프로세스 생명주기 관리
"""
import signal
from multiprocessing import Process, Queue
from queue import Full
from typing import Optional, Callable

from communication import Message


class ProcessLifecycle:
    """워커 프로세스 생명주기 관리"""
    
    def __init__(
        self,
        name: str,
        target: Callable,
        from_manager_queue: Queue,
    ):
        self.name = name
        self._target = target
        self._from_manager_queue = from_manager_queue
        self._process: Optional[Process] = None
        self._running: bool = False
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @is_running.setter
    def is_running(self, value: bool):
        self._running = value
    
    @property
    def pid(self) -> Optional[int]:
        """프로세스 ID"""
        return self._process.pid if self._process else None
    
    def is_alive(self) -> bool:
        """프로세스 생존 여부"""
        return self._process is not None and self._process.is_alive()
    
    def start(self) -> None:
        """프로세스 시작"""
        self._process = Process(
            target=self._target,
            name=self.name,
            daemon=False,
        )
        self._process.start()
    
    def stop(self, camera_id: str) -> None:
        """프로세스 종료"""
        if not self._process or not self._process.is_alive():
            return
        
        # 종료 명령 전송
        try:
            self._from_manager_queue.put(
                Message.command_stop(camera_id),
                timeout=1,
            )
        except Full:
            pass
        
        # 프로세스 종료 대기
        self._process.join(timeout=5)
        
        # 강제 종료
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2)
    
    def setup_signal_handlers(self, handler: Callable) -> None:
        """시그널 핸들러 설정"""
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
