# 모듈 단위 전체 흐름 플로우차트

## 모듈 구조 및 의존성

```mermaid
flowchart TB
    subgraph Entry["진입점"]
        MAIN[main.py]
    end

    subgraph Config["config/"]
        CFG[config.py<br/>AppConfig, RTSPConfig,<br/>CaptureConfig, StorageConfig,<br/>ProcessConfig, LogConfig, StatsConfig]
    end

    subgraph Manager["manager/"]
        PM[process_manager.py<br/>ProcessManager, WorkerInfo]
    end

    subgraph Worker["worker/"]
        CW[cctv_worker.py<br/>CCTVWorker]
        PL[process_lifecycle.py<br/>ProcessLifecycle]
        MH[message_handler.py<br/>MessageHandler]
        FCL[frame_capture_loop.py<br/>FrameCaptureLoop]
        HBM[heartbeat_manager.py<br/>HeartbeatManager]
        FS[frame_stats.py<br/>FrameStats]
    end

    subgraph RTSP["rtsp/"]
        RC[client.py<br/>RTSPClient, FrameInfo]
    end

    subgraph Storage["storage/"]
        IS[image_saver.py<br/>ImageSaver]
    end

    subgraph Communication["communication/"]
        MSG[message.py<br/>Message, MessageType]
    end

    subgraph Logger["logger/"]
        LOG[log_manager.py<br/>get_logger, setup_logger]
    end

    subgraph Utils["utils/"]
        HLP[helpers.py<br/>extract_camera_id_from_url]
    end

    %% 의존성 관계
    MAIN --> CFG
    MAIN --> PM
    MAIN --> LOG

    PM --> CFG
    PM --> CW
    PM --> MSG
    PM --> LOG

    CW --> CFG
    CW --> PL
    CW --> MH
    CW --> FCL
    CW --> HBM
    CW --> LOG
    CW --> HLP

    PL --> MSG

    MH --> MSG

    FCL --> RC
    FCL --> IS
    FCL --> FS
    FCL --> CFG

    HBM --> MH

    RC --> CFG

    IS --> CFG

    LOG --> CFG
```

## 데이터 흐름도

```mermaid
flowchart LR
    subgraph External["외부"]
        RTSP_STREAM[("RTSP 스트림<br/>(카메라)")]
        DISK[("디스크<br/>streaming_image/")]
        LOGFILE[("로그 파일<br/>logs/")]
    end

    subgraph Parent["부모 프로세스"]
        PM[ProcessManager]
        Q_TO[("to_manager_queue")]
    end

    subgraph Child["자식 프로세스 (카메라당 1개)"]
        CW[CCTVWorker]
        Q_FROM[("from_manager_queue")]
        
        subgraph Capture["프레임 수집"]
            RC[RTSPClient]
            FCL[FrameCaptureLoop]
            FS[FrameStats]
        end
        
        subgraph Save["저장"]
            IS[ImageSaver]
        end
        
        subgraph Comm["통신"]
            MH[MessageHandler]
            HB[HeartbeatManager]
        end
    end

    %% 데이터 흐름
    RTSP_STREAM -->|"프레임"| RC
    RC -->|"FrameInfo"| FCL
    FCL -->|"numpy.ndarray"| IS
    IS -->|"JPEG 저장"| DISK
    
    FCL -->|"성공/실패"| FS
    FS -->|"통계"| LOGFILE
    
    CW -->|"로그"| LOGFILE
    
    HB -->|"heartbeat"| MH
    MH -->|"Message"| Q_TO
    Q_TO -->|"수신"| PM
    
    PM -->|"명령"| Q_FROM
    Q_FROM -->|"Message"| MH
    MH -->|"명령 전달"| CW
```

## 프로세스 간 통신 흐름

```mermaid
flowchart TB
    subgraph Parent["부모 프로세스 (ProcessManager)"]
        PM_START[start]
        PM_MONITOR[_monitor_loop]
        PM_RECV[_receive_messages]
        PM_CHECK[_check_workers]
        PM_RESTART[_restart_worker]
    end

    subgraph IPC["프로세스 간 통신"]
        Q_TO[("to_manager_queue<br/>(공유)")]
        Q_FROM1[("from_manager_queue<br/>(워커1 전용)")]
        Q_FROM2[("from_manager_queue<br/>(워커2 전용)")]
    end

    subgraph Child1["자식 프로세스 1"]
        W1_RUN[_run]
        W1_LOOP[_main_loop]
        W1_MSG[MessageHandler]
    end

    subgraph Child2["자식 프로세스 2"]
        W2_RUN[_run]
        W2_LOOP[_main_loop]
        W2_MSG[MessageHandler]
    end

    PM_START -->|"fork"| W1_RUN
    PM_START -->|"fork"| W2_RUN
    PM_START --> PM_MONITOR

    PM_MONITOR --> PM_RECV
    PM_RECV --> PM_CHECK
    PM_CHECK --> PM_RESTART
    PM_RESTART --> PM_MONITOR

    W1_RUN --> W1_LOOP
    W2_RUN --> W2_LOOP

    W1_MSG -->|"HEARTBEAT<br/>READY<br/>STATUS<br/>ERROR"| Q_TO
    W2_MSG -->|"HEARTBEAT<br/>READY<br/>STATUS<br/>ERROR"| Q_TO

    Q_TO --> PM_RECV

    PM_RECV -->|"STOP<br/>PAUSE<br/>RESUME"| Q_FROM1
    PM_RECV -->|"STOP<br/>PAUSE<br/>RESUME"| Q_FROM2

    Q_FROM1 --> W1_MSG
    Q_FROM2 --> W2_MSG
```

## 모듈별 책임

```mermaid
flowchart TB
    subgraph Modules["모듈별 책임"]
        direction TB
        
        subgraph config["📁 config/"]
            C1["설정값 정의"]
            C2["데이터클래스 기반"]
            C3["타입 힌트 제공"]
        end
        
        subgraph manager["📁 manager/"]
            M1["워커 생성/관리"]
            M2["메시지 라우팅"]
            M3["장애 복구"]
        end
        
        subgraph worker["📁 worker/"]
            W1["프로세스 라이프사이클"]
            W2["프레임 캡처 루프"]
            W3["통계 수집"]
            W4["Heartbeat 전송"]
        end
        
        subgraph rtsp["📁 rtsp/"]
            R1["RTSP 연결 관리"]
            R2["프레임 읽기"]
            R3["재연결 처리"]
        end
        
        subgraph storage["📁 storage/"]
            S1["이미지 저장"]
            S2["디스크 공간 관리"]
            S3["오래된 파일 정리"]
        end
        
        subgraph communication["📁 communication/"]
            CM1["메시지 타입 정의"]
            CM2["메시지 생성 팩토리"]
        end
        
        subgraph logger["📁 logger/"]
            L1["프로세스별 로거"]
            L2["로그 파일 관리"]
            L3["로테이션 처리"]
        end
        
        subgraph utils["📁 utils/"]
            U1["카메라 ID 추출"]
            U2["공통 유틸리티"]
        end
    end
```

## 실행 순서 타임라인

```mermaid
flowchart LR
    subgraph T1["1️⃣ 초기화"]
        A1[config 로드] --> A2[logger 생성] --> A3[ProcessManager 생성]
    end
    
    subgraph T2["2️⃣ 워커 생성"]
        B1[URL 목록 순회] --> B2[CCTVWorker 생성] --> B3[Process.start fork]
    end
    
    subgraph T3["3️⃣ 자식 초기화"]
        C1[시그널 핸들러] --> C2[컴포넌트 생성] --> C3[READY 전송]
    end
    
    subgraph T4["4️⃣ 메인 루프"]
        D1[명령 처리] --> D2[RTSP 연결] --> D3[프레임 캡처] --> D4[이미지 저장] --> D5[통계 기록] --> D6[Heartbeat] --> D1
    end
    
    subgraph T5["5️⃣ 모니터링"]
        E1[메시지 수신] --> E2[워커 상태 체크] --> E3[타임아웃 감지] --> E4[재시작] --> E1
    end
    
    T1 --> T2 --> T3 --> T4
    T2 --> T5
```

## 파일 구조

```
cctv_util/
├── main.py                    # 진입점
├── config.py                  # 설정 정의
│
├── manager/                   # 부모 프로세스
│   ├── __init__.py
│   └── process_manager.py     # ProcessManager
│
├── worker/                    # 자식 프로세스
│   ├── __init__.py
│   ├── cctv_worker.py         # 메인 조율자
│   ├── process_lifecycle.py   # 프로세스 관리
│   ├── message_handler.py     # 메시지 송수신
│   ├── frame_capture_loop.py  # 프레임 캡처
│   ├── heartbeat_manager.py   # Heartbeat
│   └── frame_stats.py         # 통계
│
├── rtsp/                      # RTSP 연결
│   ├── __init__.py
│   └── client.py              # RTSPClient
│
├── storage/                   # 저장소
│   ├── __init__.py
│   └── image_saver.py         # ImageSaver
│
├── communication/             # 통신
│   ├── __init__.py
│   └── message.py             # Message, MessageType
│
├── logger/                    # 로깅
│   ├── __init__.py
│   └── log_manager.py         # 로거 설정
│
├── utils/                     # 유틸리티
│   ├── __init__.py
│   └── helpers.py             # 헬퍼 함수
│
├── streaming_image/           # 저장된 이미지
│   └── {camera_id}/           # 카메라별 폴더
│
└── logs/                      # 로그 파일
    └── {camera_id}/           # 카메라별 로그
```

## 모듈 간 호출 관계 요약

| 호출하는 모듈 | 호출되는 모듈                                         | 목적           |
| ------------- | ----------------------------------------------------- | -------------- |
| `main.py`     | `config`, `manager`, `logger`                         | 시스템 시작    |
| `manager`     | `worker`, `communication`, `config`                   | 워커 관리      |
| `worker`      | `rtsp`, `storage`, `communication`, `logger`, `utils` | 프레임 수집    |
| `rtsp`        | `config`                                              | RTSP 연결 설정 |
| `storage`     | `config`                                              | 저장 설정      |
| `logger`      | `config`                                              | 로그 설정      |
