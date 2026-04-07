# 트러블슈팅 가이드

CCTV 프레임 수집 시스템 사용 중 발생할 수 있는 문제와 해결 방법입니다.

## 목차

- [설치 관련](#설치-관련)
- [실행 관련](#실행-관련)
- [RTSP 연결 관련](#rtsp-연결-관련)
- [데이터베이스 관련](#데이터베이스-관련)
- [성능 관련](#성능-관련)
- [저장 관련](#저장-관련)

---

## 설치 관련

### 1. Python을 찾을 수 없음


**증상:**

```
[ERROR] Python을 찾을 수 없습니다.
```


**원인:**

- Python 3.9 이상이 설치되지 않음


**해결:**

**Ubuntu/Debian:**

```bash
sudo apt update
sudo add-apt-repository ppa:deadsnakes/ppa

sudo apt install python3.9 python3.9-venv python3.9-dev
```

**CentOS/RHEL 8+:**


```bash
sudo dnf install python39 python39-devel
```

**CentOS 7:**


```bash
sudo yum install epel-release
sudo yum install python39 python39-devel
```

**확인:**

```bash
python3.9 --version
# Python 3.9.x

```

---

### 2. pip 설치 실패


**증상:**

```
ERROR: Could not find a version that satisfies the requirement opencv-python
```

**원인:**

- 인터넷 연결 문제
- pip 버전 낮음
- 잘못된 Python 버전

**해결:**

```bash

# pip 업그레이드
source .venv/bin/activate
python -m pip install --upgrade pip

# 패키지 재설치
pip install -r requirements.txt
```

**폐쇄망 환경:**


```bash
# 오프라인 wheel 사용
pip install --no-index --find-links=offline_packages/wheels -r requirements.txt
```


---

### 3. FFmpeg SO 파일 오류


**증상:**

```
ImportError: libswresample.so.4: cannot open shared object file: No such file or directory
```


**원인:**

- FFmpeg 패치가 완료되지 않음
- 심볼릭 링크가 없음

**해결 1: 자동 패치**

```bash
./setup_and_run.sh --patch
```

**해결 2: 수동 패치**

```bash
cd .venv/lib/python3.9/site-packages/opencv_python.libs/

# 현재 파일 확인
ls -la libsw*.so.*


# 심볼릭 링크 생성
ln -sf libswresample-*.so.4.7.100 libswresample.so.4
ln -sf libswscale-*.so.6.7.100 libswscale.so.6
ln -sf libavcodec-*.so.59.37.100 libavcodec.so.59
ln -sf libavformat-*.so.59.27.100 libavformat.so.59
ln -sf libavutil-*.so.57.28.100 libavutil.so.57

# 확인
ls -la libsw*.so.4
# lrwxrwxrwx ... libswresample.so.4 -> libswresample-3e7db482.so.4.7.100
```

**해결 3: 파일 복사 재실행**

```bash
cd .venv/lib/python3.9/site-packages/opencv_python.libs/

# 기존 파일 이름 확인
AVCODEC=$(ls libavcodec-*.so.59.37.100)
AVFORMAT=$(ls libavformat-*.so.59.27.100)
AVUTIL=$(ls libavutil-*.so.57.28.100)
SWSCALE=$(ls libswscale-*.so.6.7.100)
SWRESAMPLE=$(ls libswresample-*.so.4.7.100)

# 커스텀 파일로 교체

cp ~/cctv_util/ffmpeg_SHA256_lib/libavcodec.so.59.37.100 "$AVCODEC"
cp ~/cctv_util/ffmpeg_SHA256_lib/libavformat.so.59.27.100 "$AVFORMAT"
cp ~/cctv_util/ffmpeg_SHA256_lib/libavutil.so.57.28.100 "$AVUTIL"
cp ~/cctv_util/ffmpeg_SHA256_lib/libswscale.so.6.7.100 "$SWSCALE"
cp ~/cctv_util/ffmpeg_SHA256_lib/libswresample.so.4.7.100 "$SWRESAMPLE"


# 실행 권한 부여
chmod +x lib*.so.*
```


---

### 4. 오프라인 Python 실행 권한 오류

**증상:**

```
[ERROR] 오프라인 Python 실행 파일을 찾을 수 없습니다.
```

**원인:**

- 파일 복사 시 실행 권한 손실
- tar 압축 해제 시 권한 손실


**해결:**

```bash
# Python 실행 권한 부여
chmod +x offline_packages/python/bin/python3.9

chmod +x offline_packages/python/bin/python3
chmod +x offline_packages/python/bin/pip*

# 확인

ls -la offline_packages/python/bin/python3.9
# -rwxr-xr-x ... python3.9
```

---

### 5. OpenCV 버전 충돌

**증상:**

```
ImportError: OpenCV version mismatch
```

**원인:**

- 여러 버전의 OpenCV 설치됨
- opencv-python과 opencv-python-headless 동시 설치

**해결:**


```bash
source .venv/bin/activate

# 기존 OpenCV 제거
pip uninstall opencv-python opencv-python-headless opencv-contrib-python -y


# 재설치
pip install opencv-python>=4.10.0


# 패치 재실행
./setup_and_run.sh --patch
```

---

## 실행 관련

### 1. 가상환경 활성화 실패

**증상:**

```bash
./start.sh
[ERROR] 가상환경이 없습니다.
```


**원인:**

- 설치가 완료되지 않음
- `.venv` 디렉터리 손상


**해결:**

```bash
# 설치 재실행

./setup_and_run.sh --install

# 또는 가상환경만 재생성
rm -rf .venv
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./setup_and_run.sh --patch
```

---

### 2. 모듈을 찾을 수 없음

**증상:**

```

ModuleNotFoundError: No module named 'cv2'
```

**원인:**


- 가상환경이 활성화되지 않음
- 패키지 설치 안 됨


**해결:**

```bash
# 가상환경 활성화 확인
which python
# /path/to/cctv_util/.venv/bin/python 이어야 함

# 패키지 확인
pip list | grep opencv

# 없으면 재설치
pip install -r requirements.txt
```

---


### 3. 권한 거부 (Permission Denied)

**증상:**

```
PermissionError: [Errno 13] Permission denied: 'streaming_image'

```

**원인:**


- 저장 경로 쓰기 권한 없음

**해결:**

```bash
# 디렉터리 권한 확인
ls -ld streaming_image/

# 권한 부여
chmod 755 streaming_image/

# 또는 소유자 변경
sudo chown $USER:$USER streaming_image/
```

---

### 4. 프로세스가 즉시 종료됨


**증상:**

```
[INFO] 워커 프로세스 생성...
[ERROR] 워커 프로세스 사망 감지

```

**원인:**

- RTSP URL 설정 오류
- config.py 문법 오류


**해결:**

```bash
# config.py 확인
python -c "import config; print(config.rtsp_config.urls)"

# 로그 확인

tail -f logs/camera_0.log

# 수동 실행으로 에러 확인
source .venv/bin/activate
python main.py
```

---

## RTSP 연결 관련

### 1. RTSP 연결 실패


**증상:**

```
[ERROR] RTSP 연결 실패: rtsp://...
```


**원인:**

- 잘못된 RTSP URL
- 네트워크 문제
- 카메라 인증 실패

**해결:**

**1. RTSP URL 형식 확인:**


```python
# config.py
rtsp_url = "rtsp://username:password@192.168.1.100:554/stream1"
#          프로토콜  사용자명 비밀번호  IP주소        포트  스트림경로
```


**2. 네트워크 연결 확인:**

```bash
# ping 테스트
ping 192.168.1.100


# 포트 확인
nc -zv 192.168.1.100 554

# 또는
telnet 192.168.1.100 554
```


**3. ffprobe로 RTSP URL 테스트:**

```bash
source .venv/bin/activate
ffprobe -rtsp_transport tcp "rtsp://username:password@192.168.1.100:554/stream1"
```

**4. 인증 정보 확인:**

- 사용자명, 비밀번호 정확한지 확인

- 특수문자가 있으면 URL 인코딩 필요
  - `@` → `%40`
  - `:` → `%3A`
  - `/` → `%2F`


---

### 2. RTSP 타임아웃

**증상:**

```

[WARNING] RTSP 읽기 타임아웃
```

**원인:**


- 네트워크 지연
- 카메라 응답 느림
- read_timeout_ms 설정 짧음

**해결:**

**config.py에서 타임아웃 증가:**

```python
@dataclass

class CaptureConfig:
    read_timeout_ms: int = 10000  # 5000 → 10000 (10초)
```

**TCP 전송 모드 사용:**

```python
# RTSP URL에 옵션 추가
"rtsp://...?tcp"
```


---

### 3. 프레임 캡처 안 됨


**증상:**

```
[INFO] Heartbeat: Worker[0] - 0 frames captured
```


**원인:**

- RTSP 스트림 문제
- 코덱 지원 안 됨
- FPS 설정 오류

**해결:**

**1. VLC로 스트림 확인:**


```bash
vlc "rtsp://username:password@192.168.1.100:554/stream1"
```

**2. OpenCV에서 직접 테스트:**

```python
import cv2


cap = cv2.VideoCapture("rtsp://...")
ret, frame = cap.read()
print(f"Read success: {ret}, Frame shape: {frame.shape if ret else None}")
cap.release()

```

**3. FPS 설정 확인:**

```python
# config.py

frames_per_second: int = 1  # 너무 크면 프레임 누락 가능
```

---

### 4. SHA-256 인증 실패


**증상:**

```
[ERROR] 401 Unauthorized
```


**원인:**

- FFmpeg 패치가 안 됨
- 잘못된 인증 방식

**해결:**

**1. FFmpeg 패치 확인:**

```bash
# 패치된 라이브러리 확인
ls -la .venv/lib/python3.9/site-packages/opencv_python.libs/libav*.so.*


# 패치 재실행
./setup_and_run.sh --patch
```

**2. 인증 방식 확인:**


- 카메라가 SHA-256을 지원하는지 확인
- 일반 Digest 인증이면 표준 FFmpeg 사용

---


## 데이터베이스 관련

### 1. 데이터베이스 연결 실패

**증상:**


```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '192.168.1.100' ([Errno 111] Connection refused)")
```

**원인:**


- DB 서버 주소 또는 포트 잘못됨
- DB 서버가 실행 중이 아님
- 방화벽으로 차단됨

**해결:**

```bash
# DB 서버 연결 테스트
nc -zv 192.168.1.100 3306

# 또는
telnet 192.168.1.100 3306


# config.py 확인
cat config.py | grep -A5 "DatabaseConfig"
```

**방화벽 확인:**


```bash
# 폐쇄망 서버에서 DB 서버로의 3306 포트 허용 필요
sudo firewall-cmd --list-ports
```


---

### 2. 인증 실패

**증상:**


```
pymysql.err.OperationalError: (1045, "Access denied for user 'cctv_user'@'192.168.1.50'")
```

**원인:**


- 사용자 이름 또는 비밀번호 잘못됨
- 해당 사용자에게 원격 접속 권한 없음

**해결:**

**1. 사용자 권한 확인 (DB 서버에서):**

```sql
-- MariaDB/MySQL에서
SELECT user, host FROM mysql.user WHERE user = 'cctv_user';

-- 원격 접속 허용
CREATE USER 'cctv_user'@'%' IDENTIFIED BY 'your_password';

GRANT SELECT ON cctv_db.cameras TO 'cctv_user'@'%';
FLUSH PRIVILEGES;
```

**2. 비밀번호 재확인:**


```python
# config.py에서 특수문자 이스케이프 확인
password: str = "pass@word#123"  # 특수문자는 그대로 사용 가능
```


---

### 3. 데이터베이스/테이블을 찾을 수 없음

**증상:**


```
pymysql.err.ProgrammingError: (1049, "Unknown database 'cctv_db'")
```

또는


```
pymysql.err.ProgrammingError: (1146, "Table 'cctv_db.cameras' doesn't exist")
```

**원인:**

- 데이터베이스 이름 잘못됨
- 테이블이 생성되지 않음

**해결:**

```bash
# DB에서 확인
mysql -u cctv_user -p -h 192.168.1.100

# 데이터베이스 목록
SHOW DATABASES;

# 테이블 목록
USE cctv_db;
SHOW TABLES;


# 테이블 구조 확인
DESCRIBE cameras;
```

---


### 4. 컬럼 이름 불일치

**증상:**

```
KeyError: 'rtsp_url'

```

또는

```
pymysql.err.ProgrammingError: (1054, "Unknown column 'rtsp_url' in 'field list'")
```

**원인:**

- 실제 테이블 컬럼 이름과 config.py의 column_mapping이 일치하지 않음

**해결:**

```bash
# 실제 테이블 컬럼 확인
mysql -u cctv_user -p -h 192.168.1.100 cctv_db -e "DESCRIBE cameras;"
```

**config.py 수정:**

```python
# 실제 컬럼 이름에 맞게 수정
column_mapping: Dict[str, str] = field(default_factory=lambda: {
    "id": "cam_id",           # 실제 컬럼명
    "name": "camera_name",    # 실제 컬럼명
    "rtsp_url": "stream_url", # 실제 컬럼명
    "is_active": "enabled"    # 실제 컬럼명
})
```

---

### 5. 카메라 URL이 조회되지 않음

**증상:**

```
[WARNING] 데이터베이스에서 카메라 URL을 가져올 수 없습니다.
```

**원인:**

- 테이블에 데이터가 없음
- `only_active=True`인데 모든 카메라가 비활성화됨
- `camera_ids`에 잘못된 ID가 지정됨

**해결:**

```bash
# 테이블 데이터 확인
mysql -u cctv_user -p -h 192.168.1.100 cctv_db -e "SELECT * FROM cameras;"

# 활성화된 카메라 확인
mysql -u cctv_user -p -h 192.168.1.100 cctv_db -e "SELECT * FROM cameras WHERE is_active = 1;"
```

**config.py에서 전체 카메라 조회:**

```python
# 모든 카메라 조회 (비활성화 포함)
only_active: bool = False

# 특정 ID 필터 제거
camera_ids: List[str] = field(default_factory=list)  # 빈 리스트 = 전체
```

---

### 6. PyMySQL 패키지 없음

**증상:**

```
ModuleNotFoundError: No module named 'pymysql'
```

**원인:**

- pymysql 패키지가 설치되지 않음
- 오프라인 환경에서 wheel 파일 누락

**해결:**

**온라인 환경:**

```bash
source .venv/bin/activate
pip install pymysql>=1.1.0
```

**오프라인 환경:**

```bash
# 인터넷 환경에서 wheel 다운로드
pip download pymysql>=1.1.0 -d offline_packages/wheels/ \
    --platform manylinux2014_x86_64 \
    --python-version 39 \
    --only-binary :all:

# 폐쇄망에서 설치
pip install --no-index --find-links=offline_packages/wheels pymysql
```

---

### 7. 연결 테스트

데이터베이스 연결 상태를 확인하는 스크립트:

```bash
source .venv/bin/activate
python -c "
from database import DatabaseClient, CameraRepository
from config import AppConfig

config = AppConfig()
print(f'DB Host: {config.database.host}')
print(f'DB Port: {config.database.port}')
print(f'Database: {config.database.database}')
print(f'Table: {config.database.camera_table}')
print()

client = DatabaseClient(config.database)
try:
    with client.get_connection() as conn:
        print('✓ 연결 성공!')
        
        # 카메라 조회
        repo = CameraRepository(conn, config.database)
        cameras = repo.get_all_cameras()
        print(f'✓ 조회된 카메라: {len(cameras)}개')
        
        for cam in cameras:
            status = '활성' if cam.is_active else '비활성'
            print(f'  [{status}] {cam.id}: {cam.name or \"이름없음\"}')
            print(f'         URL: {cam.rtsp_url[:50]}...')
            
except Exception as e:
    print(f'✗ 오류: {e}')
"
```

---

## 성능 관련

### 1. CPU 사용률이 높음

**증상:**

- CPU 100% 사용
- 시스템이 느려짐

**원인:**

- 프레임 처리 과부하
- 너무 많은 카메라 동시 처리

**해결:**

**1. FPS 낮추기:**

```python
# config.py
frames_per_second: int = 1  # 5 → 1
```

**2. 해상도 줄이기:**

```python
# config.py
target_width: int = 640   # None → 640
target_height: int = 480  # None → 480
```

**3. 카메라 수 줄이기:**

```python
# config.py - 일부 URL 주석 처리
urls: List[str] = field(default_factory=lambda: [
    "192.168.1.100:554/stream1",
    # "192.168.1.101:554/stream1",  # 주석 처리
])
```

---

### 2. 메모리 부족

**증상:**

```
MemoryError
```

**원인:**

- 이미지 버퍼 누적
- 메모리 누수

**해결:**

**1. 버퍼 크기 줄이기:**

```python
# config.py
buffer_size: int = 1  # 최소값
```

**2. 이미지 압축률 높이기:**

```python
# config.py
jpeg_quality: int = 75  # 95 → 75
```

**3. 시스템 메모리 확인:**

```bash
free -h
# 여유 메모리 확인
```

---

## 저장 관련

### 1. 디스크 공간 부족

**증상:**

```
[ERROR] 디스크 공간 부족
OSError: [Errno 28] No space left on device
```

**원인:**

- 이미지가 계속 쌓임
- 자동 삭제 설정 안 됨

**해결:**

**1. 최대 파일 수 설정:**

```python
# config.py
max_files_per_camera: int = 10000  # 0 → 10000
```

**2. 최소 여유 공간 설정:**

```python
# config.py
min_disk_space_gb: float = 5.0  # 1.0 → 5.0
```

**3. 수동 정리:**

```bash
# 오래된 파일 삭제 (7일 이상)
find streaming_image/ -type f -mtime +7 -delete

# 디스크 사용량 확인
du -sh streaming_image/*/
```

---

### 2. 파일 저장 실패

**증상:**

```
[ERROR] 이미지 저장 실패
```

**원인:**

- 디렉터리 권한 문제
- 파일명 문제

**해결:**

**1. 권한 확인:**

```bash
ls -ld streaming_image/
chmod 755 streaming_image/
```

**2. 저장 경로 확인:**

```python
# config.py
base_path: Path = Path("streaming_image")  # 절대 경로 사용 가능
```

**3. 로그 확인:**

```bash
tail -f logs/camera_0.log
```

---

## 로그 분석

### 로그 위치

```
logs/
├── main.log          # 메인 프로세스 로그
├── camera_0.log      # 워커 0 로그
├── camera_1.log      # 워커 1 로그
└── ...
```

### 주요 로그 패턴

**정상 동작:**

```
[INFO] RTSP 연결 성공
[INFO] 프레임 캡처 시작
[INFO] Heartbeat 전송
```

**연결 문제:**

```
[ERROR] RTSP 연결 실패
[WARNING] 재연결 시도 중...
```

**성능 문제:**

```
[WARNING] 프레임 처리 지연
[WARNING] 메모리 사용량 높음
```

---

## 추가 지원

위 해결 방법으로 문제가 해결되지 않으면:

1. **로그 수집:**
   ```bash
   tar -czf logs_$(date +%Y%m%d).tar.gz logs/
   ```

2. **시스템 정보 수집:**
   ```bash
   uname -a > system_info.txt
   python --version >> system_info.txt
   pip list >> system_info.txt
   ```

3. **관리자에게 문의** (로그 및 시스템 정보 첨부)
