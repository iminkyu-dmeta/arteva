"""
프레임 캡처 루프 로직
"""
import time
from datetime import datetime
from logging import Logger
from typing import Optional, Tuple

from config import RTSPConfig, CaptureConfig, StorageConfig, VideoConfig, SaveModeConfig
from rtsp import RTSPClient
from storage import ImageSaver, VideoSaver
from worker.message_handler import MessageHandler
from worker.frame_stats import FrameStats


class FrameCaptureLoop:
    """RTSP 프레임 캡처 루프"""
    
    def __init__(
        self,
        camera_id: str,
        url: str,
        rtsp_config: RTSPConfig,
        capture_config: CaptureConfig,
        storage_config: StorageConfig,
        video_config: VideoConfig,
        save_mode_config: SaveModeConfig,
        message_handler: MessageHandler,
        logger: Logger,
        sampling_period: float = 1.0,
    ):
        self.camera_id = camera_id
        self.url = url
        self._rtsp_config = rtsp_config
        self._capture_config = capture_config
        self._save_mode = save_mode_config
        self._message_handler = message_handler
        self._logger = logger
        
        # RTSP 클라이언트
        self._rtsp_client = RTSPClient(
            url=url,
            rtsp_config=rtsp_config,
            capture_config=capture_config,
            logger=logger,
        )
        
        # 이미지 저장기 (save_mode에 따라)
        self._image_saver: Optional[ImageSaver] = None
        if self._save_mode.save_images:
            self._image_saver = ImageSaver(
                camera_id=camera_id,
                config=storage_config,
                logger=logger,
            )
            self._logger.info("이미지 저장 모드 활성화")
        
        # 비디오 저장기 (save_mode에 따라)
        self._video_saver: Optional[VideoSaver] = None
        if self._save_mode.save_videos and video_config.enabled:
            self._video_saver = VideoSaver(
                camera_id=camera_id,
                video_config=video_config,
                capture_config=capture_config,
                logger=logger,
            )
            self._logger.info("비디오 저장 모드 활성화")
        
        # 상태
        self._reconnect_attempts: int = 0
        self._last_capture_time: float = 0.0
        
        # 통계
        self._stats = FrameStats()
        self._stats.set_sampling_period(sampling_period)
        
        self._logger.info(f"저장 모드: {self._save_mode.mode}")
    
    @property
    def rtsp_client(self) -> RTSPClient:
        return self._rtsp_client
    
    @property
    def image_saver(self) -> Optional[ImageSaver]:
        return self._image_saver
    
    @property
    def video_saver(self) -> Optional[VideoSaver]:
        return self._video_saver
    
    @property
    def frame_interval(self) -> float:
        """프레임 캡처 간격 (초)"""
        return 1.0 / self._capture_config.frames_per_second
    
    def ensure_connected(self) -> Optional[bool]:
        """
        RTSP 연결 보장
        
        Returns:
            True: 연결됨 또는 연결 성공
            False: 재연결 필요 (대기 후 재시도)
            None: 최대 시도 초과 (종료 필요)
        """
        if self._rtsp_client.is_connected:
            return True
        
        if self._rtsp_client.connect():
            self._reconnect_attempts = 0
            self._message_handler.send_status("connected")
            return True
        
        # 연결 실패
        self._reconnect_attempts += 1
        max_attempts = self._rtsp_config.max_reconnect_attempts
        
        if max_attempts > 0 and self._reconnect_attempts >= max_attempts:
            self._logger.error(f"최대 재연결 시도 횟수 초과: {max_attempts}")
            self._message_handler.send_error("최대 재연결 시도 횟수 초과")
            return None  # 종료 신호
        
        self._message_handler.send_status("reconnecting", {
            "attempt": self._reconnect_attempts,
        })
        time.sleep(self._rtsp_config.reconnect_delay)
        return False
    
    def capture_frame(self) -> bool:
        """
        프레임 캡처 및 저장 (간격 체크 포함)
        
        Returns:
            True: 정상 처리, False: 연결 끊김
        """
        current_time = time.time()
        
        # 간격 체크
        if current_time - self._last_capture_time < self.frame_interval:
            return True
        
        # 프레임 읽기
        success, frame_info = self._rtsp_client.read_frame()
        
        if not success or not frame_info:
            self._message_handler.send_status("disconnected")
            self._logger.warning("프레임 읽기 실패 - 재연결 시도")
            return False
        
        save_success = False
        
        # 이미지 저장 (활성화된 경우)
        if self._image_saver is not None:
            saved_path = self._image_saver.save(
                frame=frame_info.frame,
                frame_id=frame_info.frame_id,
            )
            if saved_path:
                save_success = True
        
        # 비디오 저장 (활성화된 경우)
        if self._video_saver is not None:
            video_success = self._video_saver.write_frame(frame_info.frame)
            if video_success:
                save_success = True
        
        if save_success:
            self._last_capture_time = current_time
            self._stats.record_success()
        else:
            self._stats.record_failure()
        
        return True
    
    def get_stats(self) -> dict:
        """현재 통계 반환"""
        stats = {
            "is_connected": self._rtsp_client.is_connected,
            "frame_count": self._rtsp_client.frame_count,
            "timestamp": datetime.now().isoformat(),
            **self._stats.get_summary(),
        }
        
        # 이미지 저장 통계
        if self._image_saver is not None:
            stats["image_saved_count"] = self._image_saver.saved_count
        
        # 비디오 저장 통계
        if self._video_saver is not None:
            video_stats = self._video_saver.get_stats()
            stats["video_segments"] = video_stats["saved_segments"]
            stats["video_frames"] = video_stats["total_frames"]
        
        return stats
    
    def get_period_stats_and_reset(self) -> dict:
        """주기별 통계 반환 및 초기화"""
        return self._stats.reset_samples()
    
    def cleanup(self) -> dict:
        """리소스 정리 및 최종 통계 반환"""
        self._rtsp_client.disconnect()
        
        result = {}
        
        # 이미지 저장기 통계
        if self._image_saver is not None:
            result["image"] = self._image_saver.get_stats()
        
        # 비디오 저장기 종료
        if self._video_saver is not None:
            result["video"] = self._video_saver.finalize()
        
        return result
