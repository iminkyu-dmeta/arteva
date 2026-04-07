"""
CCTV 워커 프로세스 - 개별 카메라 스트림 처리 (메인 조율 클래스)
"""
import time
import traceback
from multiprocessing import Queue
from typing import Optional

from config import AppConfig
from communication import MessageType
from logger import get_logger
from utils import extract_camera_id_from_url

from worker.process_lifecycle import ProcessLifecycle
from worker.message_handler import MessageHandler
from worker.frame_capture_loop import FrameCaptureLoop
from worker.heartbeat_manager import HeartbeatManager


class CCTVWorker:
    """CCTV 스트림 수집 워커 프로세스"""
    
    def __init__(
        self,
        url: str,
        config: AppConfig,
        to_manager_queue: Queue,
        from_manager_queue: Queue,
    ):
        self.url = url
        self.config = config
        self.to_manager_queue = to_manager_queue
        self.from_manager_queue = from_manager_queue
        
        # 카메라 ID 추출
        self.camera_id = extract_camera_id_from_url(url)
        
        # 프로세스 라이프사이클 관리
        self._lifecycle = ProcessLifecycle(
            name=f"CCTV-Worker-{self.camera_id}",
            target=self._run,
            from_manager_queue=from_manager_queue,
        )
    
    def start(self) -> None:
        """워커 프로세스 시작"""
        self._lifecycle.start()
    
    def stop(self) -> None:
        """워커 프로세스 중지"""
        self._lifecycle.stop(self.camera_id)
    
    def is_alive(self) -> bool:
        """프로세스 생존 여부"""
        return self._lifecycle.is_alive()
    
    @property
    def pid(self) -> Optional[int]:
        """프로세스 ID"""
        return self._lifecycle.pid
    
    def _run(self) -> None:
        """워커 메인 루프 (자식 프로세스에서 실행)"""
        # 시그널 핸들러 설정
        self._lifecycle.setup_signal_handlers(self._signal_handler)
        
        # 로거 초기화 (프로세스별 별도 로그)
        logger = get_logger("worker", self.camera_id, self.config.log)
        logger.info(f"워커 프로세스 시작 - Camera: {self.camera_id}, PID: {self._lifecycle.pid}")
        
        self._lifecycle.is_running = True
        
        # 메시지 핸들러 초기화
        message_handler = MessageHandler(
            camera_id=self.camera_id,
            to_manager_queue=self.to_manager_queue,
            from_manager_queue=self.from_manager_queue,
            logger=logger,
        )
        
        # 명령 핸들러 등록
        self._register_command_handlers(message_handler)
        
        # 프레임 캡처 루프 초기화
        capture_loop = FrameCaptureLoop(
            camera_id=self.camera_id,
            url=self.url,
            rtsp_config=self.config.rtsp,
            capture_config=self.config.capture,
            storage_config=self.config.storage,
            video_config=self.config.video,
            save_mode_config=self.config.save_mode,
            message_handler=message_handler,
            logger=logger,
            sampling_period=float(self.config.stats.sampling_period),
        )
        
        # Heartbeat 매니저 초기화
        heartbeat = HeartbeatManager(
            interval=self.config.process.heartbeat_interval,
            send_callback=message_handler.send_heartbeat,
            stats_callback=capture_loop.get_stats,
        )
        
        # 통계 로깅 설정 (config에서 가져오기)
        last_stats_log_time = time.time()
        stats_log_interval = float(self.config.stats.log_interval)
        
        # 준비 완료 알림
        pid = self._lifecycle.pid or 0
        message_handler.send_ready(pid)
        
        try:
            self._main_loop(
                message_handler, 
                capture_loop, 
                heartbeat, 
                logger,
                last_stats_log_time,
                stats_log_interval,
            )
        except Exception as e:
            logger.error(f"워커 오류: {e}\n{traceback.format_exc()}")
            message_handler.send_error(str(e))
        finally:
            stats = capture_loop.cleanup()
            message_handler.send_stopped(stats)
            logger.info("워커 프로세스 종료")
    
    def _main_loop(
        self,
        message_handler: MessageHandler,
        capture_loop: FrameCaptureLoop,
        heartbeat: HeartbeatManager,
        logger,
        last_stats_log_time: float,
        stats_log_interval: float,
    ) -> None:
        """메인 이벤트 루프"""
        while self._lifecycle.is_running:
            # 1. 명령 처리
            message_handler.process_commands()
            
            if not self._lifecycle.is_running:
                break
            
            # 2. RTSP 연결 확인
            connection_result = capture_loop.ensure_connected()
            
            if connection_result is None:
                # 최대 재연결 시도 초과 - 종료
                break
            elif connection_result is False:
                # 재연결 대기 중 - 다음 루프
                continue
            
            # 3. 프레임 캡처
            capture_loop.capture_frame()
            
            # 4. Heartbeat 확인 및 전송
            heartbeat.check_and_send()
            
            # 5. 통계 로깅 (config 설정 간격마다)
            current_time = time.time()
            if current_time - last_stats_log_time >= stats_log_interval:
                period_stats = capture_loop.get_period_stats_and_reset()
                logger.info(
                    f"[{int(stats_log_interval)}초 통계] "
                    f"샘플 수: {period_stats['sample_count']}개, "
                    f"수집: {period_stats['frames_collected']}개, "
                    f"저장: {period_stats['frames_saved']}개, "
                    f"실패: {period_stats['frames_failed']}개, "
                    f"평균 FPS: {period_stats['avg_fps']:.2f}, "
                    f"최소 FPS: {period_stats['min_fps']:.2f}, "
                    f"최대 FPS: {period_stats['max_fps']:.2f}, "
                    f"저장 성공률: {period_stats['save_success_rate']:.1f}%"
                )
                last_stats_log_time = current_time
            
            # CPU 과부하 방지
            time.sleep(0.001)
    
    def _register_command_handlers(self, message_handler: MessageHandler) -> None:
        """명령 핸들러 등록"""
        message_handler.register_handler(
            MessageType.COMMAND_STOP,
            lambda msg: setattr(self._lifecycle, 'is_running', False),
        )
        
        message_handler.register_handler(
            MessageType.COMMAND_PAUSE,
            self._handle_pause,
        )
        
        message_handler.register_handler(
            MessageType.COMMAND_RESUME,
            self._handle_resume,
        )
        
        message_handler.register_handler(
            MessageType.COMMAND_UPDATE_CONFIG,
            self._handle_update_config,
        )
    
    def _handle_pause(self, msg) -> None:
        """일시정지 처리"""
        # TODO: 구현
        pass
    
    def _handle_resume(self, msg) -> None:
        """재개 처리"""
        # TODO: 구현
        pass
    
    def _handle_update_config(self, msg) -> None:
        """설정 업데이트 처리"""
        # TODO: 구현
        pass
    
    def _signal_handler(self, signum, frame) -> None:
        """시그널 핸들러"""
        self._lifecycle.is_running = False
