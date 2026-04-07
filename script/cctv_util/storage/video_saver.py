"""
비디오 저장 모듈
"""
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from logging import Logger
from typing import Optional, List, Tuple

from config import VideoConfig, CaptureConfig
from utils.helpers import ensure_dir, check_disk_space


class VideoSaver:
    """비디오 저장 관리"""
    
    # 지원되는 코덱 매핑
    CODEC_MAP = {
        "mp4v": ("mp4v", "mp4"),    # MPEG-4 - 무난한 호환성
        "MJPG": ("MJPG", "avi"),    # Motion JPEG - 빠름, 파일 큼
        "avc1": ("avc1", "mp4"),    # H.264 - 작은 용량 (플랫폼 의존)
        "XVID": ("XVID", "avi"),    # XVID - 오픈소스
        "X264": ("X264", "mp4"),    # x264 - H.264 대안
    }
    
    def __init__(
        self,
        camera_id: str,
        video_config: VideoConfig,
        capture_config: CaptureConfig,
        logger: Logger,
    ):
        self.camera_id = camera_id
        self.config = video_config
        self.capture_config = capture_config
        self.logger = logger
        
        # 저장 경로 설정
        self.save_dir = ensure_dir(self.config.base_path / self.camera_id)
        
        # VideoWriter 상태
        self._writer: Optional[cv2.VideoWriter] = None
        self._current_file: Optional[Path] = None
        self._segment_start_time: Optional[float] = None
        self._frame_count_in_segment: int = 0
        
        # 통계
        self._saved_segments: int = 0
        self._total_frames: int = 0
        self._file_list: List[Path] = []
        
        # 해상도
        self._frame_size: Tuple[int, int] = (
            capture_config.target_width,
            capture_config.target_height
        )
        
        self.logger.info(f"비디오 저장 경로: {self.save_dir}")
        self.logger.info(f"세그먼트 길이: {self.config.segment_duration}초, 코덱: {self.config.codec}")
    
    @property
    def fps(self) -> float:
        """프레임 레이트"""
        return float(self.capture_config.frames_per_second)
    
    @property
    def is_recording(self) -> bool:
        """녹화 중 여부"""
        return self._writer is not None
    
    @property
    def saved_segments(self) -> int:
        """저장된 세그먼트 수"""
        return self._saved_segments
    
    @property
    def total_frames(self) -> int:
        """저장된 총 프레임 수"""
        return self._total_frames
    
    def write_frame(self, frame: np.ndarray) -> bool:
        """
        프레임을 비디오에 기록
        
        Args:
            frame: 저장할 이미지 프레임
        
        Returns:
            성공 여부
        """
        import time
        current_time = time.time()
        
        # 디스크 공간 확인
        if not check_disk_space(self.save_dir, self.config.min_disk_space_gb):
            self.logger.warning("비디오 저장용 디스크 공간 부족!")
            self._cleanup_old_files()
        
        # 새 세그먼트 필요 여부 확인
        if self._should_start_new_segment(current_time):
            self._finalize_current_segment()
            self._start_new_segment()
        
        # 프레임 기록
        if self._writer is None:
            self._start_new_segment()
        
        # writer 생성 실패 체크
        if self._writer is None:
            self.logger.error("VideoWriter 생성 실패")
            return False
        
        try:
            # 프레임 크기 조정 (필요시)
            if frame.shape[1] != self._frame_size[0] or frame.shape[0] != self._frame_size[1]:
                frame = cv2.resize(frame, self._frame_size)
            
            self._writer.write(frame)
            self._frame_count_in_segment += 1
            self._total_frames += 1
            return True
            
        except Exception as e:
            self.logger.error(f"비디오 프레임 기록 실패: {e}")
            return False
    
    def _should_start_new_segment(self, current_time: float) -> bool:
        """새 세그먼트 시작 필요 여부"""
        if self._segment_start_time is None:
            return True
        
        elapsed = current_time - self._segment_start_time
        return elapsed >= self.config.segment_duration
    
    def _start_new_segment(self) -> None:
        """새 비디오 세그먼트 시작"""
        import time
        
        # 파일명 생성
        now = datetime.now()
        filename = self.config.filename_format.format(
            date=now.strftime("%Y%m%d"),
            time=now.strftime("%H%M%S"),
            container=self.config.container,
        )
        filepath = self.save_dir / filename
        
        # 코덱 설정
        fourcc = self._get_fourcc()
        
        try:
            self._writer = cv2.VideoWriter(
                str(filepath),
                fourcc,
                self.fps,
                self._frame_size,
            )
            
            if not self._writer.isOpened():
                self.logger.error(f"VideoWriter 열기 실패: {filepath}")
                self._writer = None
                return
            
            self._current_file = filepath
            self._segment_start_time = time.time()
            self._frame_count_in_segment = 0
            
            self.logger.info(f"새 비디오 세그먼트 시작: {filepath.name}")
            
        except Exception as e:
            self.logger.error(f"비디오 세그먼트 시작 실패: {e}")
            self._writer = None
    
    def _finalize_current_segment(self) -> None:
        """현재 세그먼트 종료"""
        if self._writer is None:
            return
        
        try:
            self._writer.release()
            self._saved_segments += 1
            
            if self._current_file:
                self._file_list.append(self._current_file)
                self.logger.info(
                    f"비디오 세그먼트 완료: {self._current_file.name} "
                    f"({self._frame_count_in_segment} 프레임)"
                )
                
                # 최대 파일 수 제한 확인
                if self.config.max_files_per_camera > 0:
                    self._enforce_max_files()
            
        except Exception as e:
            self.logger.error(f"비디오 세그먼트 종료 실패: {e}")
        
        finally:
            self._writer = None
            self._current_file = None
    
    def _get_fourcc(self) -> int:
        """FourCC 코덱 코드 반환"""
        codec = self.config.codec
        
        # 코덱 매핑에서 찾기
        if codec in self.CODEC_MAP:
            fourcc_str = self.CODEC_MAP[codec][0]
        else:
            fourcc_str = codec
        
        # cv2.VideoWriter_fourcc 호출 (타입 힌트 무시)
        fourcc_func = getattr(cv2, 'VideoWriter_fourcc')
        return fourcc_func(*fourcc_str)
    
    def _enforce_max_files(self) -> None:
        """최대 파일 수 제한 적용"""
        max_files = self.config.max_files_per_camera
        
        if len(self._file_list) > max_files:
            files_to_remove = len(self._file_list) - max_files
            for _ in range(files_to_remove):
                old_file = self._file_list.pop(0)
                try:
                    if old_file.exists():
                        old_file.unlink()
                        self.logger.debug(f"오래된 비디오 삭제: {old_file.name}")
                except Exception as e:
                    self.logger.warning(f"비디오 파일 삭제 실패: {e}")
    
    def _cleanup_old_files(self) -> None:
        """디스크 공간 부족 시 오래된 파일 정리"""
        if not self._file_list:
            return
        
        # 가장 오래된 파일 삭제
        old_file = self._file_list.pop(0)
        try:
            if old_file.exists():
                old_file.unlink()
                self.logger.info(f"디스크 공간 확보를 위해 삭제: {old_file.name}")
        except Exception as e:
            self.logger.warning(f"파일 삭제 실패: {e}")
    
    def finalize(self) -> dict:
        """녹화 종료 및 최종 통계 반환"""
        self._finalize_current_segment()
        
        return {
            "saved_segments": self._saved_segments,
            "total_frames": self._total_frames,
            "save_dir": str(self.save_dir),
        }
    
    def get_stats(self) -> dict:
        """현재 통계 반환"""
        return {
            "saved_segments": self._saved_segments,
            "total_frames": self._total_frames,
            "current_segment_frames": self._frame_count_in_segment,
            "is_recording": self.is_recording,
        }
