"""
RTSP 클라이언트 - OpenCV 기반 RTSP 스트림 연결 및 프레임 캡처
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from logging import Logger

from config import RTSPConfig, CaptureConfig


@dataclass
class FrameInfo:
    """캡처된 프레임 정보"""
    frame: np.ndarray
    frame_id: int
    width: int
    height: int
    timestamp: float


class RTSPClient:
    """RTSP 스트림 클라이언트"""
    
    def __init__(
        self,
        url: str,
        rtsp_config: RTSPConfig,
        capture_config: CaptureConfig,
        logger: Logger,
    ):
        self.url = url
        self.rtsp_config = rtsp_config
        self.capture_config = capture_config
        self.logger = logger
        
        self._capture: Optional[cv2.VideoCapture] = None
        self._frame_count: int = 0
        self._is_connected: bool = False
    
    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._is_connected and self._capture is not None and self._capture.isOpened()
    
    @property
    def frame_count(self) -> int:
        """총 캡처된 프레임 수"""
        return self._frame_count
    
    def connect(self) -> bool:
        """
        RTSP 스트림 연결
        
        Returns:
            연결 성공 여부
        """
        try:
            self.logger.info(f"RTSP 연결 시도: {self._mask_url(self.url)}")
            
            # 기존 연결 해제
            self.disconnect()
            
            # VideoCapture 생성
            self._capture = cv2.VideoCapture(self.url)
            
            # 캡처 옵션 설정
            self._set_capture_options()
            
            # 연결 확인 (첫 프레임 읽기 시도)
            if self._capture and self._capture.isOpened():
                ret, _ = self._capture.read()
                if ret:
                    self._is_connected = True
                    self._log_stream_info()
                    self.logger.info("RTSP 연결 성공")
                    return True
            
            self.logger.warning("RTSP 연결 실패 - 스트림을 열 수 없습니다")
            self._is_connected = False
            return False
            
        except Exception as e:
            self.logger.error(f"RTSP 연결 중 오류: {e}")
            self._is_connected = False
            return False
    
    def disconnect(self) -> None:
        """연결 해제"""
        if self._capture is not None:
            try:
                self._capture.release()
            except Exception as e:
                self.logger.warning(f"연결 해제 중 오류: {e}")
            finally:
                self._capture = None
                self._is_connected = False
    
    def read_frame(self) -> Tuple[bool, Optional[FrameInfo]]:
        """
        프레임 읽기
        
        Returns:
            (성공 여부, FrameInfo or None)
        """
        if not self.is_connected:
            return False, None
        
        try:
            if not self._capture:
                return False, None
                
            ret, frame = self._capture.read()
            
            if not ret or frame is None:
                self._is_connected = False
                return False, None
            
            self._frame_count += 1
            
            # 리사이즈 (설정된 경우)
            frame = self._resize_frame(frame)
            
            frame_info = FrameInfo(
                frame=frame,
                frame_id=self._frame_count,
                width=frame.shape[1],
                height=frame.shape[0],
                timestamp=cv2.getTickCount() / cv2.getTickFrequency(),
            )
            
            return True, frame_info
            
        except Exception as e:
            self.logger.error(f"프레임 읽기 오류: {e}")
            self._is_connected = False
            return False, None
    
    def get_stream_info(self) -> dict:
        """스트림 정보 반환"""
        if not self._capture:
            return {}
        
        return {
            "width": int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self._capture.get(cv2.CAP_PROP_FPS),
            "backend": self._capture.getBackendName(),
        }
    
    def _set_capture_options(self) -> None:
        """캡처 옵션 설정"""
        if self._capture is None:
            return
        
        # 버퍼 크기 설정
        self._capture.set(
            cv2.CAP_PROP_BUFFERSIZE,
            self.capture_config.buffer_size,
        )
        
        # 타임아웃 설정 (OpenCV 빌드에 따라 지원 여부 다름)
        try:
            self._capture.set(
                cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                self.capture_config.read_timeout_ms,
            )
        except Exception:
            pass  # 지원하지 않는 경우 무시
    
    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """프레임 리사이즈"""
        target_w = self.capture_config.target_width
        target_h = self.capture_config.target_height
        
        if target_w and target_h:
            return cv2.resize(frame, (target_w, target_h))
        return frame
    
    def _log_stream_info(self) -> None:
        """스트림 정보 로깅"""
        info = self.get_stream_info()
        self.logger.info(
            f"스트림 정보 - 해상도: {info.get('width')}x{info.get('height')}, "
            f"FPS: {info.get('fps'):.2f}, Backend: {info.get('backend')}"
        )
    
    def _mask_url(self, url: str) -> str:
        """URL에서 비밀번호 마스킹"""
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
