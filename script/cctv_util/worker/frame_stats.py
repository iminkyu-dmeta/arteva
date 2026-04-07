"""
프레임 수집 통계 추적
"""
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FrameStats:
    """프레임 수집 통계"""
    total_frames: int = 0
    saved_frames: int = 0
    failed_frames: int = 0
    start_time: float = field(default_factory=time.time)
    
    # 샘플링 관련
    sampling_period: float = 1.0  # 샘플링 주기 (초)
    last_sample_time: float = field(default_factory=time.time)
    current_sample_frames: int = 0  # 현재 샘플링 주기 동안 수집된 프레임
    current_sample_saved: int = 0
    current_sample_failed: int = 0
    
    # 샘플 기록 (각 샘플링 주기의 FPS 기록)
    fps_samples: List[float] = field(default_factory=list)
    saved_samples: List[int] = field(default_factory=list)
    failed_samples: List[int] = field(default_factory=list)
    
    def set_sampling_period(self, period: float) -> None:
        """샘플링 주기 설정"""
        self.sampling_period = period
    
    def record_success(self) -> None:
        """프레임 저장 성공 기록"""
        self.total_frames += 1
        self.saved_frames += 1
        self.current_sample_frames += 1
        self.current_sample_saved += 1
        self._check_sample_period()
    
    def record_failure(self) -> None:
        """프레임 저장 실패 기록"""
        self.total_frames += 1
        self.failed_frames += 1
        self.current_sample_frames += 1
        self.current_sample_failed += 1
        self._check_sample_period()
    
    def _check_sample_period(self) -> None:
        """샘플링 주기 체크 및 샘플 기록"""
        current_time = time.time()
        elapsed = current_time - self.last_sample_time
        
        if elapsed >= self.sampling_period:
            # 이 샘플링 주기의 FPS 계산
            fps = self.current_sample_frames / elapsed if elapsed > 0 else 0.0
            
            # 샘플 기록
            self.fps_samples.append(fps)
            self.saved_samples.append(self.current_sample_saved)
            self.failed_samples.append(self.current_sample_failed)
            
            # 현재 샘플 초기화
            self.current_sample_frames = 0
            self.current_sample_saved = 0
            self.current_sample_failed = 0
            self.last_sample_time = current_time
    
    def get_average_fps(self) -> float:
        """샘플들의 평균 FPS"""
        if not self.fps_samples:
            return 0.0
        return sum(self.fps_samples) / len(self.fps_samples)
    
    def get_min_fps(self) -> float:
        """최소 FPS"""
        return min(self.fps_samples) if self.fps_samples else 0.0
    
    def get_max_fps(self) -> float:
        """최대 FPS"""
        return max(self.fps_samples) if self.fps_samples else 0.0
    
    def get_total_elapsed_time(self) -> float:
        """총 경과 시간 (초)"""
        return time.time() - self.start_time
    
    def get_save_success_rate(self) -> float:
        """저장 성공률"""
        total_saved = sum(self.saved_samples)
        total_failed = sum(self.failed_samples)
        total = total_saved + total_failed
        if total > 0:
            return (total_saved / total) * 100
        return 0.0
    
    def reset_samples(self) -> dict:
        """샘플 초기화 및 통계 반환"""
        # 현재 진행 중인 샘플도 기록
        if self.current_sample_frames > 0:
            elapsed = time.time() - self.last_sample_time
            fps = self.current_sample_frames / elapsed if elapsed > 0 else 0.0
            self.fps_samples.append(fps)
            self.saved_samples.append(self.current_sample_saved)
            self.failed_samples.append(self.current_sample_failed)
        
        stats = {
            "sample_count": len(self.fps_samples),
            "frames_collected": sum(self.saved_samples) + sum(self.failed_samples),
            "frames_saved": sum(self.saved_samples),
            "frames_failed": sum(self.failed_samples),
            "avg_fps": self.get_average_fps(),
            "min_fps": self.get_min_fps(),
            "max_fps": self.get_max_fps(),
            "save_success_rate": self.get_save_success_rate(),
        }
        
        # 샘플 초기화
        self.fps_samples.clear()
        self.saved_samples.clear()
        self.failed_samples.clear()
        self.current_sample_frames = 0
        self.current_sample_saved = 0
        self.current_sample_failed = 0
        self.last_sample_time = time.time()
        
        return stats
    
    def get_summary(self) -> dict:
        """전체 통계 요약"""
        return {
            "total_frames": self.total_frames,
            "saved_frames": self.saved_frames,
            "failed_frames": self.failed_frames,
            "current_avg_fps": self.get_average_fps(),
            "total_elapsed_seconds": self.get_total_elapsed_time(),
        }
