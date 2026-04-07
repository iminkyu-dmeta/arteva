# 시스템 시작 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant Main as main.py
    participant PM as ProcessManager
    participant Worker as CCTVWorker
    participant Lifecycle as ProcessLifecycle
    participant MsgHandler as MessageHandler
    participant CaptureLoop as FrameCaptureLoop
    participant RTSP as RTSPClient
    participant Saver as ImageSaver
    participant HB as HeartbeatManager

    Main->>PM: ProcessManager(config)
    Main->>PM: start()
    
    loop 각 카메라 URL마다
        PM->>Worker: CCTVWorker(url, config, queues)
        PM->>Worker: start()
        Worker->>Lifecycle: start()
        Lifecycle-->>Lifecycle: Process.start() (fork)
        
        Note over Worker: 자식 프로세스 시작
        Worker->>Lifecycle: setup_signal_handlers()
        Worker->>MsgHandler: MessageHandler(camera_id, queues)
        Worker->>CaptureLoop: FrameCaptureLoop(...)
        CaptureLoop->>RTSP: RTSPClient(url, config)
        CaptureLoop->>Saver: ImageSaver(camera_id, config)
        Worker->>HB: HeartbeatManager(interval, callbacks)
        
        MsgHandler->>PM: send_ready(pid)
        PM-->>PM: _on_worker_ready()
    end
```

## 설명

1. `main.py`에서 `ProcessManager`를 생성하고 `start()` 호출
2. 각 카메라 URL에 대해 `CCTVWorker` 생성
3. 워커가 자식 프로세스로 fork되어 독립 실행
4. 자식 프로세스에서 필요한 컴포넌트들 초기화
5. 준비 완료 후 부모에게 `READY` 메시지 전송
