"""
프로세스 매니저 - 자식 프로세스(워커) 관리
"""
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime
from multiprocessing import Queue
from queue import Empty
from threading import Thread
from typing import Dict, List, Optional

from config import AppConfig
from communication import Message, MessageType
from logger import get_logger
from worker import CCTVWorker
from utils import extract_camera_id_from_url


@dataclass
class WorkerInfo:
    """워커 정보"""
    worker: CCTVWorker
    camera_id: str
    url: str
    to_worker_queue: Queue
    from_worker_queue: Queue
    status: str = "unknown"
    last_heartbeat: Optional[datetime] = None
    stats: dict = field(default_factory=dict)


class ProcessManager:
    """CCTV 워커 프로세스 관리자"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = get_logger("manager")
        
        # 워커 관리
        self._workers: Dict[str, WorkerInfo] = {}
        
        # 메시지 수신 스레드
        self._message_receiver_thread: Optional[Thread] = None
        self._running: bool = False
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self) -> None:
        """매니저 시작 - 모든 카메라 워커 생성"""
        self.logger.info("=" * 60)
        self.logger.info("CCTV 프레임 수집 시스템 시작")
        self.logger.info("=" * 60)
        
        self._running = True
        
        # 메시지 수신 스레드 시작
        self._message_receiver_thread = Thread(
            target=self._message_receiver_loop,
            name="MessageReceiver",
            daemon=True,
        )
        self._message_receiver_thread.start()
        
        # 각 RTSP URL에 대해 워커 생성
        # (main.py에서 config.rtsp.urls에 전체 URL이 설정됨)
        for url in self.config.rtsp.urls:
            try:
                self._create_worker(url)
                time.sleep(self.config.process.process_start_delay)
            except Exception as e:
                self.logger.error(f"워커 생성 실패: {url} - {e}")
        
        self.logger.info(f"총 {len(self._workers)}개 워커 시작됨")
    
    def stop(self) -> None:
        """매니저 종료 - 모든 워커 정지"""
        self.logger.info("시스템 종료 시작...")
        self._running = False
        
        # 모든 워커 종료
        for camera_id, info in list(self._workers.items()):
            self.logger.info(f"워커 종료 중: {camera_id}")
            info.worker.stop()
        
        self._workers.clear()
        self.logger.info("시스템 종료 완료")
    
    def run_forever(self) -> None:
        """메인 루프 실행"""
        self.start()
        
        try:
            while self._running:
                self._check_workers_health()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Ctrl+C 감지")
        finally:
            self.stop()
    
    def get_status(self) -> Dict[str, dict]:
        """전체 상태 조회"""
        return {
            camera_id: {
                "status": info.status,
                "last_heartbeat": info.last_heartbeat.isoformat() if info.last_heartbeat else None,
                "is_alive": info.worker.is_alive(),
                "pid": info.worker.pid,
                "stats": info.stats,
            }
            for camera_id, info in self._workers.items()
        }
    
    def restart_worker(self, camera_id: str) -> bool:
        """특정 워커 재시작"""
        if camera_id not in self._workers:
            self.logger.warning(f"워커를 찾을 수 없음: {camera_id}")
            return False
        
        info = self._workers[camera_id]
        self.logger.info(f"워커 재시작: {camera_id}")
        
        # 기존 워커 종료
        info.worker.stop()
        
        # 새 워커 생성
        self._create_worker(info.url)
        return True
    
    def add_camera(self, url: str) -> bool:
        """카메라 추가"""
        camera_id = extract_camera_id_from_url(url)
        
        if camera_id in self._workers:
            self.logger.warning(f"이미 존재하는 카메라: {camera_id}")
            return False
        
        self._create_worker(url)
        return True
    
    def remove_camera(self, camera_id: str) -> bool:
        """카메라 제거"""
        if camera_id not in self._workers:
            return False
        
        info = self._workers.pop(camera_id)
        info.worker.stop()
        self.logger.info(f"카메라 제거됨: {camera_id}")
        return True
    
    def _create_worker(self, url: str) -> None:
        """워커 생성 및 시작"""
        camera_id = extract_camera_id_from_url(url)
        
        # 통신 큐 생성
        to_worker_queue = Queue(maxsize=self.config.process.message_queue_size)
        from_worker_queue = Queue(maxsize=self.config.process.message_queue_size)
        
        # 워커 생성
        worker = CCTVWorker(
            url=url,
            config=self.config,
            to_manager_queue=from_worker_queue,  # 워커 -> 매니저
            from_manager_queue=to_worker_queue,  # 매니저 -> 워커
        )
        
        # 워커 정보 저장
        self._workers[camera_id] = WorkerInfo(
            worker=worker,
            camera_id=camera_id,
            url=url,
            to_worker_queue=to_worker_queue,
            from_worker_queue=from_worker_queue,
        )
        
        # 워커 시작
        worker.start()
        self.logger.info(f"워커 생성됨: {camera_id} (URL: {self._mask_url(url)})")
    
    def _message_receiver_loop(self) -> None:
        """메시지 수신 루프 (별도 스레드)"""
        while self._running:
            for camera_id, info in list(self._workers.items()):
                try:
                    while True:
                        msg: Message = info.from_worker_queue.get_nowait()
                        self._handle_message(camera_id, msg)
                except Empty:
                    pass
            
            time.sleep(0.1)
    
    def _handle_message(self, camera_id: str, msg: Message) -> None:
        """수신 메시지 처리"""
        if camera_id not in self._workers:
            return
        
        info = self._workers[camera_id]
        
        if msg.type == MessageType.HEARTBEAT:
            info.last_heartbeat = msg.timestamp
            info.stats = msg.payload or {}
            info.status = "running"
            self.logger.debug(
                f"Heartbeat - {camera_id}: "
                f"frames={info.stats.get('frame_count', 0)}, "
                f"saved={info.stats.get('saved_count', 0)}"
            )
            
        elif msg.type == MessageType.STATUS_UPDATE:
            payload = msg.payload or {}
            info.status = payload.get("status", "unknown")
            self.logger.info(f"상태 업데이트 - {camera_id}: {info.status}")
            
        elif msg.type == MessageType.ERROR:
            payload = msg.payload or {}
            self.logger.error(f"워커 에러 - {camera_id}: {payload.get('error')}")
            info.status = "error"
            
        elif msg.type == MessageType.WORKER_READY:
            info.status = "ready"
            payload = msg.payload or {}
            self.logger.info(f"워커 준비 완료 - {camera_id} (PID: {payload.get('pid')})")
            
        elif msg.type == MessageType.WORKER_STOPPED:
            info.status = "stopped"
            self.logger.info(f"워커 종료됨 - {camera_id}: {msg.payload}")
    
    def _check_workers_health(self) -> None:
        """워커 상태 체크 및 자동 재시작"""
        current_time = datetime.now()
        timeout = self.config.process.heartbeat_timeout
        
        for camera_id, info in list(self._workers.items()):
            # 프로세스 사망 체크
            if not info.worker.is_alive():
                self.logger.warning(f"워커 프로세스 사망 감지: {camera_id}")
                info.status = "dead"
                self.restart_worker(camera_id)
                continue
            
            # Heartbeat 타임아웃 체크
            if info.last_heartbeat:
                elapsed = (current_time - info.last_heartbeat).total_seconds()
                if elapsed > timeout:
                    self.logger.warning(
                        f"Heartbeat 타임아웃: {camera_id} "
                        f"(마지막 수신: {elapsed:.1f}초 전)"
                    )
                    self.restart_worker(camera_id)
    
    def _signal_handler(self, signum, frame) -> None:
        """시그널 핸들러"""
        self.logger.info(f"시그널 수신: {signum}")
        self._running = False
    
    def _mask_url(self, url: str) -> str:
        """URL 비밀번호 마스킹"""
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
