"""
이미지 저장 모듈
"""
import cv2
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from logging import Logger
from typing import Optional, List

from config import StorageConfig
from utils.helpers import ensure_dir, check_disk_space, get_timestamp_str


class ImageSaver:
    """이미지 저장 관리"""
    
    def __init__(
        self,
        camera_id: str,
        config: StorageConfig,
        logger: Logger,
    ):
        self.camera_id = camera_id
        self.config = config
        self.logger = logger
        
        # 저장 경로 설정
        self.save_dir = ensure_dir(self.config.base_path / self.camera_id)
        self._saved_count: int = 0
        self._file_list: List[Path] = []
        
        self.logger.info(f"이미지 저장 경로: {self.save_dir}")
    
    @property
    def saved_count(self) -> int:
        """저장된 이미지 수"""
        return self._saved_count
    
    def save(
        self,
        frame: np.ndarray,
        frame_id: int,
        timestamp: Optional[datetime] = None,
    ) -> Optional[Path]:
        """
        프레임 저장
        
        Args:
            frame: 저장할 이미지 프레임
            frame_id: 프레임 ID
            timestamp: 타임스탬프 (없으면 현재 시간)
        
        Returns:
            저장된 파일 경로 또는 None
        """
        # 디스크 공간 확인
        if not check_disk_space(self.save_dir, self.config.min_disk_space_gb):
            self.logger.warning("디스크 공간 부족!")
            self._cleanup_old_files()
        
        # 파일명 생성
        timestamp = timestamp or datetime.now()
        filename = self._generate_filename(frame_id, timestamp)
        filepath = self.save_dir / filename
        
        try:
            # 이미지 저장
            encode_params = self._get_encode_params()
            success = cv2.imwrite(str(filepath), frame, encode_params)
            
            if success:
                self._saved_count += 1
                self._file_list.append(filepath)
                
                # 최대 파일 수 제한 확인
                if self.config.max_files_per_camera > 0:
                    self._enforce_max_files()
                
                return filepath
            else:
                self.logger.error(f"이미지 저장 실패: {filepath}")
                return None
                
        except Exception as e:
            self.logger.error(f"이미지 저장 중 오류: {e}")
            return None
    
    def _generate_filename(self, frame_id: int, timestamp: datetime) -> str:
        """파일명 생성"""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 밀리초까지만
        return self.config.filename_format.format(
            timestamp=timestamp_str,
            frame_id=frame_id,
            format=self.config.image_format,
        )
    
    def _get_encode_params(self) -> list:
        """이미지 인코딩 파라미터"""
        if self.config.image_format.lower() in ("jpg", "jpeg"):
            return [cv2.IMWRITE_JPEG_QUALITY, self.config.jpeg_quality]
        elif self.config.image_format.lower() == "png":
            return [cv2.IMWRITE_PNG_COMPRESSION, 3]
        return []
    
    def _enforce_max_files(self) -> None:
        """최대 파일 수 제한 적용 (오래된 파일 삭제)"""
        max_files = self.config.max_files_per_camera
        
        if len(self._file_list) > max_files:
            files_to_remove = len(self._file_list) - max_files
            for _ in range(files_to_remove):
                old_file = self._file_list.pop(0)
                try:
                    if old_file.exists():
                        old_file.unlink()
                        self.logger.debug(f"오래된 파일 삭제: {old_file.name}")
                except Exception as e:
                    self.logger.warning(f"파일 삭제 실패: {e}")
    
    def _cleanup_old_files(self, keep_count: int = 100) -> None:
        """오래된 파일 정리"""
        try:
            files = sorted(self.save_dir.glob(f"*.{self.config.image_format}"))
            
            if len(files) > keep_count:
                for f in files[:-keep_count]:
                    f.unlink()
                self.logger.info(f"오래된 파일 {len(files) - keep_count}개 삭제됨")
                
        except Exception as e:
            self.logger.error(f"파일 정리 중 오류: {e}")
    
    def get_stats(self) -> dict:
        """저장 통계 반환"""
        return {
            "saved_count": self._saved_count,
            "save_dir": str(self.save_dir),
            "current_files": len(list(self.save_dir.glob(f"*.{self.config.image_format}"))),
        }
