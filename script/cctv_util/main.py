#!/usr/bin/env python3
"""
CCTV 프레임 수집 시스템 - 메인 엔트리포인트
"""
import sys
from pathlib import Path
from typing import List

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from manager import ProcessManager
from logger import get_logger


def get_camera_urls_from_db() -> List[str]:
    """데이터베이스에서 카메라 URL 조회"""
    from database import DatabaseClient, CameraRepository
    
    logger = get_logger("main")
    db_config = config.database
    
    logger.info(f"데이터베이스 연결 중: {db_config.host}:{db_config.port}/{db_config.database}")
    
    # DB 연결
    db_client = DatabaseClient(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        database=db_config.database,
        charset=db_config.charset
    )
    
    if not db_client.connect():
        raise ConnectionError("데이터베이스 연결 실패")
    
    try:
        # 카메라 저장소 생성
        repo = CameraRepository(db_client, table_name=db_config.camera_table)
        repo.set_column_mapping(db_config.column_mapping)
        
        # 카메라 조회
        if not db_config.camera_ids:
            raise ValueError("CAMERA_IDS가 비어있습니다. config.py에서 수집할 카메라 ID를 설정하세요.")
        
        # 지정된 카메라 ID로 조회
        cameras = repo.get_cameras_by_ids(db_config.camera_ids)
        
        if not cameras:
            raise ValueError("조회된 카메라가 없습니다")
        
        # 카메라 정보 로그
        for cam in cameras:
            logger.info(f"  - [{cam.camera_id}] {cam.camera_name}: {cam.rtsp_url[:50]}...")
        
        return [cam.rtsp_url for cam in cameras]
        
    finally:
        db_client.disconnect()


def main():
    """메인 함수"""
    logger = get_logger("main")
    
    # 설정 정보 출력
    logger.info("=" * 60)
    logger.info("CCTV 프레임 수집 시스템")
    logger.info("=" * 60)
    
    # 카메라 URL 가져오기 (모드에 따라 다르게 처리)
    logger.info(f"카메라 소스 모드: {config.camera_source_mode.upper()}")
    
    if config.use_database:
        # Database 모드: DB에서 카메라 ID로 URL 조회
        logger.info("데이터베이스에서 카메라 정보 조회...")
        logger.info(f"  조회할 카메라 ID: {config.database.camera_ids}")
        try:
            urls = get_camera_urls_from_db()
            # config에 URL 설정 (DB에서 가져온 전체 URL 사용)
            config.rtsp.urls = urls
            config.rtsp.use_base_url = False  # DB에서 전체 URL을 가져오므로
        except Exception as e:
            logger.error(f"카메라 정보 조회 실패: {e}")
            logger.error("config.py의 CAMERA_IDS 설정을 확인하세요.")
            return
    else:
        # Manual 모드: 직접 입력한 URL 사용 (BASE_URL 조합 포함)
        logger.info("Manual 모드: 직접 설정된 RTSP URL 사용")
        if config.use_base_url:
            logger.info(f"  Base URL: {config.base_url}")
        urls = config.get_manual_urls()
        config.rtsp.urls = urls
        config.rtsp.use_base_url = False
    
    if not urls:
        logger.error("수집할 카메라 URL이 없습니다. config.py 설정을 확인하세요.")
        return
    
    # 설정된 URL 목록 출력
    logger.info("-" * 60)
    logger.info(f"📹 등록된 카메라 URL ({len(urls)}개):")
    for i, url in enumerate(urls, 1):
        # 비밀번호 마스킹
        import re
        masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
        logger.info(f"  [{i}] {masked_url}")
    logger.info("-" * 60)
    
    logger.info(f"초당 프레임 수: {config.capture.frames_per_second}")
    logger.info(f"저장 경로: {config.storage.base_path}")
    logger.info(f"로그 경로: {config.log.base_path}")
    logger.info(f"Heartbeat 간격: {config.process.heartbeat_interval}초")
    logger.info("=" * 60)
    
    # 프로세스 매니저 생성 및 실행
    manager = ProcessManager(config)
    
    try:
        manager.run_forever()
    except Exception as e:
        logger.error(f"시스템 오류: {e}")
        raise
    finally:
        logger.info("시스템 종료됨")


if __name__ == "__main__":
    main()
