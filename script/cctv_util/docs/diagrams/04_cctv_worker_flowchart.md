# 자식 프로세스 (CCTVWorker) 플로우차트

```mermaid
flowchart TB
    subgraph Init["_run() 초기화"]
        A[시그널 핸들러 설정] --> B[logger 초기화]
        B --> C[MessageHandler 생성]
        C --> D[FrameCaptureLoop 생성]
        D --> E[HeartbeatManager 생성]
        E --> F[send_ready 전송]
    end
    
    subgraph MainLoop["_main_loop()"]
        F --> G{is_running?}
        G -->|No| END[cleanup & 종료]
        G -->|Yes| H[process_commands]
        
        H --> I{STOP 명령?}
        I -->|Yes| END
        I -->|No| J[ensure_connected]
        
        J --> K{연결 상태}
        K -->|None: 최대시도 초과| END
        K -->|False: 재연결 중| G
        K -->|True: 연결됨| L[capture_frame]
        
        L --> M[read_frame]
        M --> N{프레임 읽기 성공?}
        N -->|No| O[재연결 필요]
        O --> G
        N -->|Yes| P[save 이미지]
        
        P --> Q{저장 성공?}
        Q -->|Yes| R[record_success]
        Q -->|No| S[record_failure]
        
        R --> T[check_and_send heartbeat]
        S --> T
        
        T --> U{log_interval 경과?}
        U -->|Yes| V[통계 로깅]
        U -->|No| G
        V --> G
    end
```

## 설명

### 워커 구성 요소

| 컴포넌트         | 파일                    | 역할                           |
| ---------------- | ----------------------- | ------------------------------ |
| ProcessLifecycle | `process_lifecycle.py`  | 프로세스 시작/중지/시그널 처리 |
| MessageHandler   | `message_handler.py`    | 부모-자식 간 메시지 송수신     |
| FrameCaptureLoop | `frame_capture_loop.py` | RTSP 연결 및 프레임 캡처       |
| HeartbeatManager | `heartbeat_manager.py`  | 주기적 heartbeat 전송          |
| FrameStats       | `frame_stats.py`        | 프레임 수집 통계 관리          |

### 연결 상태 반환값

| 반환값  | 의미           | 동작             |
| ------- | -------------- | ---------------- |
| `True`  | 연결됨         | 프레임 캡처 진행 |
| `False` | 재연결 중      | 대기 후 재시도   |
| `None`  | 최대 시도 초과 | 프로세스 종료    |
