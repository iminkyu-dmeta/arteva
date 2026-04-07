"""
프로세스별 로그 관리
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import LogConfig


class LogManager:
    """로그 매니저 - 프로세스별 로그 파일 관리"""
    
    _instances: dict = {}
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.config.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_logger(
        self,
        name: str,
        camera_id: Optional[str] = None,
    ) -> logging.Logger:
        """
        로거 인스턴스 반환
        
        Args:
            name: 로거 이름
            camera_id: 카메라 ID (있으면 별도 폴더에 로그 저장)
        """
        logger_key = f"{name}_{camera_id}" if camera_id else name
        
        if logger_key in self._instances:
            return self._instances[logger_key]
        
        logger = logging.getLogger(logger_key)
        logger.setLevel(getattr(logging, self.config.level))
        logger.handlers.clear()
        
        # 포매터 설정
        formatter = logging.Formatter(
            fmt=self.config.format,
            datefmt=self.config.date_format,
        )
        
        # 파일 핸들러 설정
        if camera_id:
            log_dir = self.config.base_path / camera_id
        else:
            log_dir = self.config.base_path
        
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}.log"
        
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=self.config.max_file_size_mb * 1024 * 1024,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 콘솔 핸들러 (메인 프로세스만)
        if not camera_id:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        self._instances[logger_key] = logger
        return logger


# 전역 로그 매니저 인스턴스
_log_manager: Optional[LogManager] = None


def get_logger(
    name: str,
    camera_id: Optional[str] = None,
    config: Optional[LogConfig] = None,
) -> logging.Logger:
    """
    로거 인스턴스 반환 (편의 함수)
    
    Args:
        name: 로거 이름
        camera_id: 카메라 ID
        config: 로그 설정 (없으면 전역 설정 사용)
    """
    global _log_manager
    
    if _log_manager is None:
        if config is None:
            from config import config as app_config
            config = app_config.log
        _log_manager = LogManager(config)
    
    return _log_manager.get_logger(name, camera_id)
