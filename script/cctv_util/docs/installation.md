# CCTV Util 설치 가이드

본 문서는 CCTV 프레임 수집 시스템의 상세 설치 가이드입니다.

## 목차

- [시스템 요구사항](#시스템-요구사항)
- [온라인 환경 설치](#온라인-환경-설치)
- [폐쇄망 환경 설치](#폐쇄망-환경-설치)
- [데이터베이스 설정](#데이터베이스-설정)
- [FFmpeg SHA-256 패치](#ffmpeg-sha-256-패치)
- [설치 확인](#설치-확인)

---

## 시스템 요구사항

### 하드웨어

- **CPU**: 2 cores 이상 권장
- **RAM**: 4GB 이상 권장
- **디스크**:
  - 시스템: 최소 1GB
  - 오프라인 패키지: ~500MB
  - 이미지 저장: 사용량에 따라 다름

### 소프트웨어

- **OS**: Linux (x86_64)
  - Ubuntu 18.04, 20.04, 22.04
  - CentOS 7, 8
  - RHEL 8, 9
  - Rocky Linux 8, 9
  - 기타 Linux 배포판 (테스트 안 됨)
- **Python**: 3.9 이상 (자동 설치 가능)
- **MariaDB/MySQL**: 카메라 정보 저장용 (외부 서버 가능)
- **네트워크**: RTSP 카메라 및 DB 서버 접근 가능

---

## 온라인 환경 설치

인터넷이 연결된 환경에서 설치하는 방법입니다.

### 1. 프로젝트 배포

```bash
# 압축 파일 복사 후 압축 해제
tar -xzf cctv_util.tar.gz
cd cctv_util

# 또는 git clone (사용 가능한 경우)
git clone <repository-url>
cd cctv_util
```

### 2. 설치 스크립트 실행

```bash
# 실행 권한 부여
chmod +x setup_and_run.sh

# 설치만 수행
./setup_and_run.sh --install
```

### 3. 설치 과정

스크립트가 자동으로 다음을 수행합니다:

#### 3.1. Python 확인 및 설치

```
[INFO] Python 버전 확인 중...
```

- Python 3.9+ 자동 탐지 (python3.9, python3.10, python3.11, python3 순서)
- 없으면 자동 설치 제안:
  ```
  Python 3.9를 자동으로 설치하시겠습니까? (sudo 권한 필요) (Y/n):
  ```

**수동 설치:**

```bash
# Ubuntu/Debian
sudo apt update
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9 python3.9-venv python3.9-dev

# CentOS/RHEL 8+
sudo dnf install python39 python39-devel

# CentOS 7
sudo yum install epel-release
sudo yum install python39 python39-devel
```

#### 3.2. 가상환경 생성

```
[INFO] 가상환경 생성 중...
[SUCCESS] 가상환경 생성 완료: .venv
```

`.venv` 디렉터리에 Python 가상환경이 생성됩니다.

#### 3.3. 패키지 설치

```
[INFO] pip 업그레이드 중...
[INFO] 필수 패키지 설치 중...
```

`requirements.txt`의 패키지가 설치됩니다:

- opencv-python >= 4.10.0
- numpy >= 1.24.0
- typing-extensions >= 4.5.0

#### 3.4. FFmpeg 패치

```
[INFO] FFmpeg SO 파일 패치 시작...
[INFO] OpenCV libs 디렉터리 탐색 중...
[SUCCESS] OpenCV libs 디렉터리 발견: .../opencv_python.libs
[INFO] 실제 파일 이름 매핑 중...
[INFO] 커스텀 FFmpeg SO 파일 복사 중...
[INFO] 심볼릭 링크 생성 중...
[SUCCESS] FFmpeg SO 패치 완료!
```

OpenCV의 FFmpeg 라이브러리를 SHA-256 인증을 지원하는 커스텀 버전으로 교체합니다.

### 4. 설치 완료

```
[SUCCESS] ==============================================
[SUCCESS]   설치 완료!
[SUCCESS] ==============================================

[INFO] 실행 방법:
[INFO]   source .venv/bin/activate
[INFO]   python main.py

[INFO] 또는:
[INFO]   ./setup_and_run.sh --run
```

---

## 폐쇄망 환경 설치

인터넷이 없는 폐쇄망 환경에서 설치하는 방법입니다.

### 단계 요약

1. **인터넷 환경**: `prepare_offline.sh` 실행 → 오프라인 패키지 생성
2. **파일 복사**: 전체 폴더를 폐쇄망 서버로 복사
3. **폐쇄망 환경**: `setup_and_run.sh` 실행 → 자동으로 오프라인 모드 감지 및
   설치

### 1단계: 오프라인 패키지 준비 (인터넷 환경)

#### 1.1. 스크립트 실행

```bash
cd cctv_util
chmod +x prepare_offline.sh
./prepare_offline.sh
```

#### 1.2. 다운로드 과정

```
==============================================
  오프라인 설치 패키지 준비
==============================================

[INFO] 현재 시스템 Python 확인 중...
[SUCCESS] 사용할 Python: python3 (Python 3.12.7)

[INFO] 오프라인 패키지 디렉터리 생성 중...
[SUCCESS] 디렉터리 생성 완료

[INFO] Python Standalone Build 다운로드 중 (Linux x86_64 용)...
[SUCCESS] Python 다운로드 완료

[INFO] Python 압축 해제 중...
[SUCCESS] Python 압축 해제 완료: offline_packages/python

[INFO] pip, setuptools, wheel 다운로드 중...
[SUCCESS] pip 관련 패키지 다운로드 완료

[INFO] pip 패키지 wheel 파일 다운로드 중...
[INFO] Linux x86_64용 wheel 다운로드 중...
[SUCCESS] wheel 파일 다운로드 완료

[SUCCESS] 오프라인 패키지 준비 완료!

[INFO] 전체 폴더 크기:
232M    offline_packages
```

#### 1.3. 생성된 구조

```
offline_packages/
├── python/                                # Python 3.9.18 Standalone (~25MB)
│   ├── bin/
│   │   ├── python3 -> python3.9
│   │   ├── python3.9
│   │   ├── pip
│   │   └── ...
│   └── lib/
│       └── python3.9/
│
├── wheels/                                # pip wheel 파일 (~100MB)
│   ├── opencv_python-4.12.0.88-...-manylinux_x86_64.whl
│   ├── numpy-2.0.2-cp39-...-manylinux_x86_64.whl
│   ├── typing_extensions-4.15.0-py3-none-any.whl
│   ├── pip-25.3-py3-none-any.whl
│   ├── setuptools-80.9.0-py3-none-any.whl
│   └── wheel-0.45.1-py3-none-any.whl
│
└── python-3.9.18-linux-x86_64.tar.gz     # 원본 압축 파일 (백업)
```

### 2단계: 폐쇄망 서버로 복사

전체 `cctv_util` 폴더를 폐쇄망 서버로 복사합니다.

#### 방법 1: scp 사용

```bash
# 인터넷 환경에서
scp -r cctv_util user@192.168.x.x:/home/user/

# 압축해서 복사 (더 빠름)
tar -czf cctv_util.tar.gz cctv_util/
scp cctv_util.tar.gz user@192.168.x.x:/home/user/

# 폐쇄망 서버에서 압축 해제
ssh user@192.168.x.x
cd /home/user
tar -xzf cctv_util.tar.gz
```

#### 방법 2: USB 또는 파일 공유

```bash
# USB 마운트
sudo mount /dev/sdb1 /mnt/usb

# 복사
cp -r cctv_util /mnt/usb/

# 폐쇄망 서버에서 USB 마운트 후 복사
sudo mount /dev/sdb1 /mnt/usb
cp -r /mnt/usb/cctv_util /home/user/
```

### 3단계: 폐쇄망 서버에서 설치

#### 3.1. 설치 실행

```bash
cd /home/user/cctv_util
chmod +x setup_and_run.sh
./setup_and_run.sh --install
```

#### 3.2. 오프라인 모드 자동 감지

```
==============================================
  CCTV Util 설치 스크립트
==============================================

[SUCCESS] 오프라인 패키지 감지됨 - 오프라인 모드로 실행
```

스크립트가 `offline_packages/` 폴더를 자동으로 감지하고 오프라인 모드로
실행됩니다.

#### 3.3. 오프라인 설치 과정

```
[INFO] Python 버전 확인 중...
[INFO] 오프라인 Python 설정 중...
[INFO] Python 실행 권한 설정 중...
[SUCCESS] 오프라인 Python 사용: Python 3.9.18

[INFO] 가상환경 생성 중...
[SUCCESS] 가상환경 생성 완료: .venv

[INFO] 가상환경 활성화 중...
[SUCCESS] 가상환경 활성화 완료

[INFO] 필수 패키지 설치 중 (오프라인)...
[INFO] pip 업그레이드 중 (오프라인)...
Looking in links: /home/user/cctv_util/offline_packages/wheels
Successfully installed pip-25.3 setuptools-80.9.0 wheel-0.45.1

[INFO] wheel 파일에서 패키지 설치 중...
Looking in links: /home/user/cctv_util/offline_packages/wheels
Successfully installed numpy-2.0.2 opencv-python-4.12.0.88 typing-extensions-4.15.0

[SUCCESS] 패키지 설치 완료 (오프라인)

[INFO] FFmpeg SO 파일 패치 시작...
[INFO] OpenCV libs 디렉터리 탐색 중...
[SUCCESS] OpenCV libs 디렉터리 발견: .../opencv_python.libs
[INFO] 커스텀 FFmpeg SO 파일 복사 중...
[INFO] 심볼릭 링크 생성 중...
[SUCCESS] FFmpeg SO 파일 패치 완료!

[SUCCESS] ==============================================
[SUCCESS]   설치 완료!
[SUCCESS] ==============================================
```

---

## FFmpeg SHA-256 패치

### 패치 목적

일반 FFmpeg는 RTSP URL의 SHA-256 기반 인증을 지원하지 않습니다. 본 시스템은
`httpauth.c` 파일을 수정하여 SHA-256 인증을 추가한 커스텀 FFmpeg 라이브러리를
사용합니다.

### 패치 과정

설치 스크립트가 자동으로 다음을 수행합니다:

#### 1. OpenCV의 FFmpeg 라이브러리 위치 탐지

```python
# venv/lib/python3.9/site-packages/opencv_python.libs/
```

#### 2. 기존 FFmpeg SO 파일 이름 확인

```bash
libavcodec-e0dd92b8.so.59.37.100      # 해시 값이 포함된 파일명
libavformat-d296e685.so.59.27.100
libavutil-734d06dd.so.57.28.100
libswscale-95ddd674.so.6.7.100
libswresample-3e7db482.so.4.7.100
```

#### 3. 커스텀 FFmpeg 파일로 교체

```bash
# ffmpeg_SHA256_lib/libavcodec.so.59.37.100
# → opencv_python.libs/libavcodec-e0dd92b8.so.59.37.100
```

기존 해시 파일명을 유지하면서 내용만 커스텀 파일로 교체합니다.

#### 4. 심볼릭 링크 생성

```bash
ln -sf libavcodec-e0dd92b8.so.59.37.100 libavcodec.so.59
ln -sf libavformat-d296e685.so.59.27.100 libavformat.so.59
ln -sf libavutil-734d06dd.so.57.28.100 libavutil.so.57
ln -sf libswscale-95ddd674.so.6.7.100 libswscale.so.6
ln -sf libswresample-3e7db482.so.4.7.100 libswresample.so.4
```

OpenCV가 버전 번호만 있는 파일명으로 라이브러리를 찾을 수 있도록 심볼릭 링크를
생성합니다.

### 수동 패치

자동 패치가 실패하거나 재패치가 필요한 경우:

```bash
# 방법 1: 스크립트 사용
./setup_and_run.sh --patch

# 방법 2: 수동 패치
cd .venv/lib/python3.9/site-packages/opencv_python.libs/

# 파일 복사
cp ~/cctv_util/ffmpeg_SHA256_lib/libavcodec.so.59.37.100 libavcodec-*.so.59.37.100
cp ~/cctv_util/ffmpeg_SHA256_lib/libavformat.so.59.27.100 libavformat-*.so.59.27.100
cp ~/cctv_util/ffmpeg_SHA256_lib/libavutil.so.57.28.100 libavutil-*.so.57.28.100
cp ~/cctv_util/ffmpeg_SHA256_lib/libswscale.so.6.7.100 libswscale-*.so.6.7.100
cp ~/cctv_util/ffmpeg_SHA256_lib/libswresample.so.4.7.100 libswresample-*.so.4.7.100

# 심볼릭 링크 생성
ln -sf libavcodec-*.so.59.37.100 libavcodec.so.59
ln -sf libavformat-*.so.59.27.100 libavformat.so.59
ln -sf libavutil-*.so.57.28.100 libavutil.so.57
ln -sf libswscale-*.so.6.7.100 libswscale.so.6
ln -sf libswresample-*.so.4.7.100 libswresample.so.4

# 실행 권한 부여
chmod +x lib*.so.*
```

---

## 데이터베이스 설정

본 시스템은 MariaDB/MySQL에서 카메라 정보를 조회하여 RTSP URL을 동적으로 가져올
수 있습니다.

### 데이터베이스 연결 설정

`config.py` 파일에서 데이터베이스 연결 정보를 설정합니다:

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class DatabaseConfig:
    """데이터베이스 연결 설정"""
    host: str = "192.168.1.100"           # DB 서버 주소
    port: int = 3306                       # MariaDB 포트
    user: str = "cctv_user"               # DB 사용자
    password: str = "your_password"       # DB 비밀번호
    database: str = "cctv_db"             # 데이터베이스 이름
    camera_table: str = "cameras"         # 카메라 정보 테이블
    
    # 조회할 카메라 ID 목록 (빈 리스트면 전체 조회)
    camera_ids: List[str] = field(default_factory=list)
    
    # 활성화된 카메라만 조회할지 여부
    only_active: bool = True
    
    # 테이블 컬럼 매핑 (실제 테이블 구조에 맞게 수정)
    column_mapping: Dict[str, str] = field(default_factory=lambda: {
        "id": "camera_id",
        "name": "camera_name", 
        "rtsp_url": "rtsp_url",
        "is_active": "is_active"
    })
```

### 테이블 스키마 예시

카메라 정보를 저장하는 테이블 예시입니다:

```sql
CREATE TABLE cameras (
    camera_id VARCHAR(50) PRIMARY KEY,
    camera_name VARCHAR(100),
    rtsp_url VARCHAR(500) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 예시 데이터 삽입
INSERT INTO cameras (camera_id, camera_name, rtsp_url, is_active) VALUES
('CAM001', '1층 로비', 'rtsp://admin:password@192.168.1.10:554/Streaming/Channels/101', 1),
('CAM002', '2층 복도', 'rtsp://admin:password@192.168.1.11:554/Streaming/Channels/101', 1),
('CAM003', '주차장', 'rtsp://admin:password@192.168.1.12:554/Streaming/Channels/101', 0);
```

### 컬럼 매핑 설정

실제 테이블의 컬럼 이름이 다른 경우 `column_mapping`을 수정합니다:

```python
# 실제 테이블 컬럼 이름에 맞게 수정
column_mapping: Dict[str, str] = field(default_factory=lambda: {
    "id": "cam_id",          # 카메라 ID 컬럼
    "name": "cam_name",      # 카메라 이름 컬럼
    "rtsp_url": "stream_url", # RTSP URL 컬럼
    "is_active": "enabled"   # 활성화 상태 컬럼 (Optional)
})
```

### 특정 카메라만 조회

특정 카메라 ID만 조회하려면 `camera_ids`를 설정합니다:

```python
# 특정 카메라만 조회
camera_ids: List[str] = field(default_factory=lambda: [
    "CAM001", "CAM002", "CAM005"
])
```

### 데이터베이스 사용 비활성화

정적 URL 목록을 사용하려면 `use_database`를 `False`로 설정합니다:

```python
@dataclass
class AppConfig:
    # 데이터베이스 사용 여부 (False면 rtsp_urls 사용)
    use_database: bool = False
    
    # 정적 RTSP URL 목록 (use_database=False일 때 사용)
    rtsp_urls: List[str] = field(default_factory=lambda: [
        "rtsp://admin:password@192.168.1.10:554/Streaming/Channels/101",
        "rtsp://admin:password@192.168.1.11:554/Streaming/Channels/101"
    ])
```

### 연결 테스트

데이터베이스 연결을 테스트하려면:

```bash
source .venv/bin/activate
python -c "
from database import DatabaseClient, CameraRepository
from config import AppConfig

config = AppConfig()
client = DatabaseClient(config.database)

try:
    with client.get_connection() as conn:
        print('✓ 데이터베이스 연결 성공!')
        repo = CameraRepository(conn, config.database)
        cameras = repo.get_all_cameras()
        print(f'✓ 발견된 카메라: {len(cameras)}개')
        for cam in cameras:
            print(f'  - {cam.id}: {cam.name or \"이름없음\"}')
except Exception as e:
    print(f'✗ 연결 실패: {e}')
"
```

---

## 설치 확인

### 1. 가상환경 확인

```bash
ls -la .venv/
# .venv 디렉터리가 존재해야 함
```

### 2. Python 버전 확인

```bash
source .venv/bin/activate
python --version
# Python 3.9.x 이상이어야 함
```

### 3. 패키지 확인

```bash
pip list | grep -E "opencv-python|numpy"
# opencv-python  4.12.0.88
# numpy          2.0.2
```

### 4. FFmpeg 패치 확인

```bash
ls -la .venv/lib/python3.9/site-packages/opencv_python.libs/libsw*.so.4
# 심볼릭 링크가 존재해야 함
```

### 5. 실행 테스트

```bash
# config.py에서 테스트용 RTSP URL 설정 후
./start.sh
```

정상적으로 실행되면 설치 완료!

---

## 문제 해결

설치 중 문제가 발생한 경우 [troubleshooting.md](troubleshooting.md)를
참조하세요.
