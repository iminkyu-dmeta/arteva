INSERT INTO t_arteva_ai_model_conf (ID, NAME, MODEL_CATEGORY, VERSION, PATH, CREATE_TIME, UPDATE_TIME, CREATE_USER, UPDATE_USER) VALUES (4, 'Detect_v3', 'detect', 3, '/apps/arteva/ai_engine/ai_process/model/weights/v3/detect/yolov8_nano_l4_fp16_train11_8522_v3.engine', now(), now(), 'admin', 'admin');
UPDATE t_arteva_ai_engine_conf set DETECT_MODEL_ID = 4 where NAME = 'prod';
