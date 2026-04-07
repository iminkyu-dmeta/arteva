# 메인 루프 시퀀스 다이어그램

```mermaid
sequenceDiagram
    participant PM as ProcessManager
    participant Worker as CCTVWorker._main_loop
    participant MsgHandler as MessageHandler
    participant CaptureLoop as FrameCaptureLoop
    participant RTSP as RTSPClient
    participant Saver as ImageSaver
    participant HB as HeartbeatManager
    participant Stats as FrameStats

    loop while is_running
        Worker->>MsgHandler: process_commands()
        MsgHandler-->>MsgHandler: from_manager_queue.get()
        
        Worker->>CaptureLoop: ensure_connected()
        CaptureLoop->>RTSP: is_connected / connect()
        RTSP-->>CaptureLoop: True/False/None
        
        alt 연결 성공
            Worker->>CaptureLoop: capture_frame()
            CaptureLoop->>RTSP: read_frame()
            RTSP-->>CaptureLoop: (success, FrameInfo)
            CaptureLoop->>Saver: save(frame, frame_id)
            Saver-->>CaptureLoop: saved_path
            
            alt 저장 성공
                CaptureLoop->>Stats: record_success()
            else 저장 실패
                CaptureLoop->>Stats: record_failure()
            end
            
            Stats-->>Stats: _check_sample_period()
        end
        
        Worker->>HB: check_and_send()
        alt 10초 경과
            HB->>MsgHandler: send_heartbeat()
            MsgHandler->>PM: to_manager_queue.put(HEARTBEAT)
        end
        
        alt 60초 경과 (log_interval)
            Worker->>CaptureLoop: get_period_stats_and_reset()
            CaptureLoop->>Stats: reset_samples()
            Stats-->>Worker: {avg_fps, min_fps, max_fps, ...}
            Worker-->>Worker: logger.info(통계)
        end
    end
```

## 설명

### 메인 루프 단계

1. **명령 처리**: 부모로부터 받은 명령(STOP, PAUSE 등) 확인
2. **연결 확인**: RTSP 스트림 연결 상태 확인 및 재연결
3. **프레임 캡처**: 프레임 읽기 → 이미지 저장 → 통계 기록
4. **Heartbeat**: 10초마다 부모에게 생존 신호 전송
5. **통계 로깅**: 60초마다 수집된 샘플의 평균 통계 출력
