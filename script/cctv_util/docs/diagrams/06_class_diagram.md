# 클래스 구조 다이어그램

```mermaid
classDiagram
    class ProcessManager {
        -_config: AppConfig
        -_workers: Dict~str, WorkerInfo~
        -_to_manager_queue: Queue
        -_is_running: bool
        -_logger: Logger
        +start()
        +stop()
        -_start_worker(url: str)
        -_monitor_loop()
        -_receive_messages()
        -_check_workers()
        -_restart_worker(camera_id: str)
        -_on_worker_ready(msg: Message)
        -_on_worker_stopped(msg: Message)
    }
    
    class WorkerInfo {
        <<dataclass>>
        +worker: CCTVWorker
        +from_manager_queue: Queue
        +last_heartbeat: float
        +is_ready: bool
    }
    
    class CCTVWorker {
        +url: str
        +config: AppConfig
        +camera_id: str
        -_lifecycle: ProcessLifecycle
        +start()
        +stop()
        +is_alive(): bool
        +pid: Optional~int~
        -_run()
        -_main_loop()
        -_register_command_handlers()
        -_signal_handler()
    }
    
    class ProcessLifecycle {
        -_process: Optional~Process~
        -_name: str
        -_target: Callable
        +is_running: bool
        +start()
        +stop(camera_id: str)
        +is_alive(): bool
        +pid: Optional~int~
        +setup_signal_handlers(handler: Callable)
    }
    
    class MessageHandler {
        -_camera_id: str
        -_to_manager_queue: Queue
        -_from_manager_queue: Queue
        -_command_handlers: Dict
        -_logger: Logger
        +send_message(msg: Message)
        +send_heartbeat()
        +send_ready(pid: int)
        +send_status(status: str, data: dict)
        +send_error(error: str)
        +send_stopped(stats: dict)
        +process_commands()
        +register_handler(msg_type, handler)
    }
    
    class FrameCaptureLoop {
        +camera_id: str
        +url: str
        -_rtsp_client: RTSPClient
        -_image_saver: ImageSaver
        -_stats: FrameStats
        -_reconnect_attempts: int
        -_last_capture_time: float
        +frame_interval: float
        +ensure_connected(): Optional~bool~
        +capture_frame(): bool
        +get_stats(): dict
        +get_period_stats_and_reset(): dict
        +cleanup(): dict
    }
    
    class HeartbeatManager {
        -_interval: float
        -_last_heartbeat: float
        -_send_callback: Callable
        -_stats_callback: Callable
        +check_and_send()
    }
    
    class FrameStats {
        +total_frames: int
        +saved_frames: int
        +failed_frames: int
        +start_time: float
        +sampling_period: float
        -fps_samples: List~float~
        -saved_samples: List~int~
        -failed_samples: List~int~
        +set_sampling_period(period: float)
        +record_success()
        +record_failure()
        -_check_sample_period()
        +get_average_fps(): float
        +get_min_fps(): float
        +get_max_fps(): float
        +reset_samples(): dict
        +get_summary(): dict
    }
    
    class RTSPClient {
        -_url: str
        -_capture: Optional~VideoCapture~
        -_frame_count: int
        +is_connected: bool
        +frame_count: int
        +connect(): bool
        +disconnect()
        +read_frame(): Tuple~bool, Optional~FrameInfo~~
    }
    
    class ImageSaver {
        -_camera_id: str
        -_config: StorageConfig
        -_save_dir: Path
        -_saved_count: int
        +saved_count: int
        +save(frame, frame_id): Optional~str~
        -_cleanup_old_images()
        -_check_disk_space(): bool
    }
    
    class Message {
        <<dataclass>>
        +type: MessageType
        +camera_id: str
        +timestamp: float
        +payload: Optional~dict~
        +heartbeat(camera_id, stats)$ Message
        +ready(camera_id, pid)$ Message
        +status(camera_id, status, data)$ Message
        +error(camera_id, error)$ Message
        +stopped(camera_id, stats)$ Message
        +command(camera_id, cmd, data)$ Message
    }
    
    class MessageType {
        <<enumeration>>
        HEARTBEAT
        READY
        STATUS
        ERROR
        STOPPED
        COMMAND_STOP
        COMMAND_PAUSE
        COMMAND_RESUME
        COMMAND_UPDATE_CONFIG
    }
    
    ProcessManager "1" --> "*" WorkerInfo : manages
    WorkerInfo --> CCTVWorker : contains
    CCTVWorker --> ProcessLifecycle : uses
    CCTVWorker --> MessageHandler : uses
    CCTVWorker --> FrameCaptureLoop : uses
    CCTVWorker --> HeartbeatManager : uses
    FrameCaptureLoop --> RTSPClient : uses
    FrameCaptureLoop --> ImageSaver : uses
    FrameCaptureLoop --> FrameStats : uses
    MessageHandler --> Message : sends/receives
    Message --> MessageType : has
```

## 클래스 관계 설명

### 부모 프로세스 (ProcessManager)

| 클래스           | 역할                                |
| ---------------- | ----------------------------------- |
| `ProcessManager` | 전체 워커 프로세스 관리 및 모니터링 |
| `WorkerInfo`     | 개별 워커의 상태 정보 저장          |

### 자식 프로세스 (CCTVWorker)

| 클래스             | 역할                               |
| ------------------ | ---------------------------------- |
| `CCTVWorker`       | 워커 프로세스 메인 조율자 (Facade) |
| `ProcessLifecycle` | 프로세스 생명주기 관리             |
| `MessageHandler`   | IPC 메시지 송수신                  |
| `FrameCaptureLoop` | RTSP 연결 및 프레임 캡처           |
| `HeartbeatManager` | 주기적 heartbeat 전송              |
| `FrameStats`       | 프레임 수집 통계                   |

### 외부 연동

| 클래스       | 역할                            |
| ------------ | ------------------------------- |
| `RTSPClient` | OpenCV 기반 RTSP 스트림 연결    |
| `ImageSaver` | 이미지 파일 저장 및 디스크 관리 |

### 통신

| 클래스        | 역할                   |
| ------------- | ---------------------- |
| `Message`     | IPC 메시지 데이터 구조 |
| `MessageType` | 메시지 타입 열거형     |
