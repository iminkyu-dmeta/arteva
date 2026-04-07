# 부모 프로세스 (ProcessManager) 플로우차트

```mermaid
flowchart TB
    subgraph Init["초기화"]
        A[ProcessManager 생성] --> B[config 로드]
        B --> C[logger 초기화]
        C --> D[to_manager_queue 생성]
    end
    
    subgraph Start["start()"]
        D --> E[각 URL에 대해]
        E --> F[CCTVWorker 생성]
        F --> G[worker.start]
        G --> H[WorkerInfo 저장]
        H --> E
        E --> I[_monitor_loop 시작]
    end
    
    subgraph Monitor["_monitor_loop()"]
        I --> J{is_running?}
        J -->|No| Z[종료]
        J -->|Yes| K[_receive_messages]
        K --> L[_check_workers]
        L --> M{죽은 워커?}
        M -->|Yes| N[_restart_worker]
        N --> O{heartbeat 타임아웃?}
        M -->|No| O
        O -->|Yes| P[워커 재시작]
        P --> J
        O -->|No| J
    end
    
    subgraph Messages["메시지 처리"]
        K --> K1{메시지 타입}
        K1 -->|READY| K2[_on_worker_ready]
        K1 -->|HEARTBEAT| K3[last_heartbeat 갱신]
        K1 -->|STATUS| K4[로그 출력]
        K1 -->|ERROR| K5[에러 로그]
        K1 -->|STOPPED| K6[_on_worker_stopped]
    end
```

## 설명

### 주요 책임

| 함수                  | 역할                                      |
| --------------------- | ----------------------------------------- |
| `start()`             | 모든 워커 프로세스 생성 및 시작           |
| `stop()`              | 모든 워커에 종료 명령 전송                |
| `_monitor_loop()`     | 워커 상태 모니터링 루프                   |
| `_receive_messages()` | 워커로부터 메시지 수신 처리               |
| `_check_workers()`    | 워커 생존 여부 및 heartbeat 타임아웃 확인 |
| `_restart_worker()`   | 죽은 워커 재시작                          |

### 워커 관리

- **WorkerInfo**: 각 워커의 상태 정보 (worker 객체, 큐, 마지막 heartbeat 시간
  등)
- **자동 재시작**: 워커가 죽거나 heartbeat 타임아웃 시 자동 재시작
