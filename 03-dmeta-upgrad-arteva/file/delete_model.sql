DELETE FROM t_arteva_ai_model_conf where id = 4;
-- alter table t_arteva_ai_model_conf auto_increment =4;
UPDATE t_arteva_ai_engine_conf set DETECT_MODEL_ID = 1 where NAME = 'prod';
