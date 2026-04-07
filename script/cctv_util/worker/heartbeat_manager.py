"""
Heartbeat 관리
"""
import time
from typing import Callable


class HeartbeatManager:
    """Heartbeat 주기적 전송 관리"""
    
    def __init__(
        self,
        interval: float,
        send_callback: Callable[[dict], bool],
        stats_callback: Callable[[], dict],
    ):
        """
        Args:
            interval: Heartbeat 전송 간격 (초)
            send_callback: Heartbeat 전송 콜백
            stats_callback: 통계 조회 콜백
        """
        self._interval = interval
        self._send_callback = send_callback
        self._stats_callback = stats_callback
        self._last_sent_time: float = time.time()
    
    def check_and_send(self) -> bool:
        """
        Heartbeat 전송 시간 확인 및 전송
        
        Returns:
            True if heartbeat was sent
        """
        current_time = time.time()
        
        if current_time - self._last_sent_time >= self._interval:
            stats = self._stats_callback()
            self._send_callback(stats)
            self._last_sent_time = current_time
            return True
        
        return False
    
    def reset(self) -> None:
        """타이머 리셋"""
        self._last_sent_time = time.time()
