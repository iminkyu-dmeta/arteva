"""
MariaDB/MySQL 데이터베이스 클라이언트
카메라 정보 조회 및 관리
"""
import pymysql
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from logger import get_logger


@dataclass
class CameraInfo:
    """카메라 정보 데이터 클래스"""
    camera_id: str
    camera_name: str
    rtsp_url: str
    is_active: bool = True
    description: str = ""
    
    def __repr__(self):
        return f"CameraInfo(id={self.camera_id}, name={self.camera_name}, active={self.is_active})"


class DatabaseClient:
    """MariaDB 데이터베이스 클라이언트"""
    
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        charset: str = "utf8mb4"
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection: Optional[pymysql.Connection] = None
        self.logger = get_logger("database")
    
    def connect(self) -> bool:
        """데이터베이스 연결"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            self.logger.info(f"데이터베이스 연결 성공: {self.host}:{self.port}/{self.database}")
            return True
        except pymysql.Error as e:
            self.logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("데이터베이스 연결 해제")
            except Exception as e:
                self.logger.warning(f"연결 해제 중 오류: {e}")
            finally:
                self.connection = None
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        if self.connection is None:
            return False
        try:
            self.connection.ping(reconnect=True)
            return True
        except pymysql.Error:
            return False
    
    def ensure_connection(self) -> bool:
        """연결 보장 (끊어졌으면 재연결)"""
        if not self.is_connected():
            return self.connect()
        return True
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """쿼리 실행 및 결과 반환"""
        if not self.ensure_connection():
            raise ConnectionError("데이터베이스에 연결할 수 없습니다.")
        
        try:
            with self.connection.cursor() as cursor:  # type: ignore
                cursor.execute(query, params)
                return cursor.fetchall()  # type: ignore
        except pymysql.Error as e:
            self.logger.error(f"쿼리 실행 오류: {e}")
            raise
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class CameraRepository:
    """
    카메라 정보 저장소 - DB에서 카메라 정보 조회
    
    t_arteva_camera_info 테이블 구조:
    - ID: int (PK, auto_increment) - 카메라 아이디
    - NAME: varchar(256) - 카메라명
    - URL: varchar(512) - 카메라 접속 URL
    - ACTIVE: char default 'A' - 카메라 사용 여부
    - RESOLUTION: varchar(15) - 해상도
    - COMMENT: varchar(512) - 코멘트
    - CREATE_TIME, UPDATE_TIME, CREATE_USER, UPDATE_USER
    """
    
    def __init__(self, db_client: DatabaseClient, table_name: str = "t_arteva_camera_info"):
        self.db = db_client
        self.table_name = table_name
        self.logger = get_logger("camera_repository")
        
        # 컬럼 매핑 (t_arteva_camera_info 테이블 기준)
        self.column_mapping = {
            "camera_id": "ID",            # 카메라 ID 컬럼 (int, PK)
            "camera_name": "NAME",        # 카메라명 컬럼
            "rtsp_url": "URL",            # RTSP URL 컬럼
            "active": "ACTIVE",           # 활성화 여부 ('A' = Active)
            "resolution": "RESOLUTION",  # 해상도
            "comment": "COMMENT"          # 코멘트
        }
    
    def set_column_mapping(self, mapping: Dict[str, str]):
        """컬럼 매핑 설정 (실제 테이블 컬럼명에 맞게 설정)"""
        self.column_mapping.update(mapping)
    
    def get_all_cameras(self, only_active: bool = True) -> List[CameraInfo]:
        """
        모든 카메라 정보 조회
        
        Args:
            only_active: True면 ACTIVE='A'인 카메라만 조회
        """
        try:
            cols = self.column_mapping
            
            query = f"""
                SELECT 
                    {cols['camera_id']} as camera_id,
                    {cols['camera_name']} as camera_name,
                    {cols['rtsp_url']} as rtsp_url,
                    {cols['active']} as active,
                    {cols['resolution']} as resolution,
                    {cols['comment']} as comment
                FROM {self.table_name}
            """
            
            if only_active:
                # ACTIVE = 'A' 인 카메라만 조회
                query += f" WHERE {cols['active']} = 'A'"
            
            results = self.db.execute_query(query)
            
            cameras = []
            for row in results:
                active = row.get('active', 'A')
                resolution = row.get('resolution', 'FHD')
                comment = row.get('comment', '')
                cameras.append(CameraInfo(
                    camera_id=str(row['camera_id']),
                    camera_name=row.get('camera_name', ''),
                    rtsp_url=row['rtsp_url'],
                    is_active=(active == 'A'),
                    description=f"{resolution} - {comment}" if comment else resolution
                ))
            
            self.logger.info(f"카메라 {len(cameras)}대 조회 완료")
            return cameras
            
        except Exception as e:
            self.logger.error(f"카메라 조회 실패: {e}")
            raise
    
    def get_camera_by_id(self, camera_id: int) -> Optional[CameraInfo]:
        """카메라 ID로 조회 (ID는 int 타입)"""
        try:
            cols = self.column_mapping
            
            query = f"""
                SELECT 
                    {cols['camera_id']} as camera_id,
                    {cols['camera_name']} as camera_name,
                    {cols['rtsp_url']} as rtsp_url,
                    {cols['active']} as active,
                    {cols['resolution']} as resolution,
                    {cols['comment']} as comment
                FROM {self.table_name}
                WHERE {cols['camera_id']} = %s
            """
            
            results = self.db.execute_query(query, (camera_id,))
            
            if results:
                row = results[0]
                active = row.get('active', 'A')
                resolution = row.get('resolution', 'FHD')
                comment = row.get('comment', '')
                return CameraInfo(
                    camera_id=str(row['camera_id']),
                    camera_name=row.get('camera_name', ''),
                    rtsp_url=row['rtsp_url'],
                    is_active=(active == 'A'),
                    description=f"{resolution} - {comment}" if comment else resolution
                )
            return None
            
        except Exception as e:
            self.logger.error(f"카메라 조회 실패 (ID: {camera_id}): {e}")
            raise
    
    def get_cameras_by_ids(self, camera_ids: List[int]) -> List[CameraInfo]:
        """
        지정된 카메라 ID 리스트로 조회
        
        Args:
            camera_ids: 조회할 카메라 ID 리스트 (int)
        
        Note:
            ID가 명시적으로 지정되면 ACTIVE 상태와 관계없이 조회합니다.
        """
        try:
            if not camera_ids:
                self.logger.warning("조회할 카메라 ID가 없습니다.")
                return []
            
            cols = self.column_mapping
            placeholders = ', '.join(['%s'] * len(camera_ids))
            
            query = f"""
                SELECT 
                    {cols['camera_id']} as camera_id,
                    {cols['camera_name']} as camera_name,
                    {cols['rtsp_url']} as rtsp_url,
                    {cols['active']} as active,
                    {cols['resolution']} as resolution,
                    {cols['comment']} as comment
                FROM {self.table_name}
                WHERE {cols['camera_id']} IN ({placeholders})
            """
            
            # 쿼리 로깅 (디버깅용)
            self.logger.debug(f"실행 쿼리: {query}")
            self.logger.debug(f"파라미터: {camera_ids}")
            
            results = self.db.execute_query(query, tuple(camera_ids))
            
            if not results:
                self.logger.warning(f"조회 결과 없음. 요청 ID: {camera_ids}")
                self.logger.warning(f"테이블 '{self.table_name}'에 해당 ID가 존재하는지 확인하세요.")
                return []
            
            cameras = []
            for row in results:
                active = row.get('active', 'A')
                resolution = row.get('resolution', 'FHD')
                comment = row.get('comment', '')
                cameras.append(CameraInfo(
                    camera_id=str(row['camera_id']),
                    camera_name=row.get('camera_name', ''),
                    rtsp_url=row['rtsp_url'],
                    is_active=(active == 'A'),
                    description=f"{resolution} - {comment}" if comment else resolution
                ))
            
            self.logger.info(f"카메라 {len(cameras)}대 조회 완료 (요청: {len(camera_ids)}대)")
            
            # 조회된 카메라 정보 로깅
            for cam in cameras:
                status = "Active" if cam.is_active else "Inactive"
                self.logger.debug(f"  - [{cam.camera_id}] {cam.camera_name} ({status})")
            
            return cameras
            
        except Exception as e:
            self.logger.error(f"카메라 조회 실패: {e}")
            raise
    
    def get_rtsp_urls(self, only_active: bool = True) -> List[str]:
        """RTSP URL 리스트만 조회"""
        cameras = self.get_all_cameras(only_active=only_active)
        return [cam.rtsp_url for cam in cameras]
