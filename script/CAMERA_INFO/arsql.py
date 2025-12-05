## Select last insert id 
LAST_INSERT_SQL="SELECT LAST_INSERT_ID()"

## Select 화상 v_camera_info_ex tale
SELECT_CAMERA_INFO_EX_SQL="select * from v_camera_info_ex;"
SELECT_CAMERA_INFO_EX_STATION_SQL="select * from v_camera_info_ex where station_id = '{}';"

## row['카메라고유번호'],          # camera number
## row['역사명'],                  # Station name
## row['역사아이디'],              # Station ID
## row['카메라명'],                # camera name
## row['카메라아이피'],            # camera IP
## row['RTSPURL주소'],             # RTSP URL
## row['제조사명'],                # made
## row['모델명'],                  # model name
## row['장애상태코드']             # error

## Insert NVR URL
INSERT_CAMERA_INFO_EX_SQL="insert into v_camera_info_ex (`idx`, `station_name`, `station_id`, `camera_name`, `camera_ipaddr`, `nvr_rtsp_url`) values (%s, %s, %s, %s, %s, %s)"
#INSERT_CAMERA_INFO_EX_SQL="insert into v_camera_info_ex (`카메라고유번호`, `역사명`, `역사아이디`, `카메라명`, `카메라아이피`, `NVR RTSP주소`) values (%s, %s, %s, %s, %s, %s)"

### CCTV
## Insert CCTV infomation
INSERT_CAMERA_INFO_SQL="insert t_arteva_camera_info (name, url, active, resolution, comment, create_time, update_time, create_user, update_user) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
SELECT_CAMERA_INFO_ID_SQL="select id from t_arteva_camera_info where name = '{}'"

## Update CCTV infomation
SELECT_ID_CAMERA_INFO_SQL="select name, url from t_arteva_camera_info where url = '{}';" 
UPDATE_CAMERA_INFO_SQL="update t_arteva_camera_info set url = '{}' where name = '{}';" 

## Insert Camera event 
INSERT_CAMERA_EVENT_BID_SQL="insert t_arteva_camera_event_conf (camera_id, event_type, active, detect_start_time, detect_end_time, accuracy, duration, broadcast_area_code, broadcast_id, param, expire_duration, create_time, update_time, create_user, update_user ) "
INSERT_CAMERA_EVENT_SQL="insert t_arteva_camera_event_conf (camera_id, event_type, active, detect_start_time, detect_end_time, accuracy, duration, broadcast_id, param, expire_duration, create_time, update_time, create_user, update_user ) "
UPDATE_CAMERA_EVENT_BID_SQL="update t_arteva_camera_event_conf set broadcast_area_code = '{}', broadcast_id = {} where camera_id = {} and event_type = '{}'"

## Select Camera envent type 
SELECT_EVENT_CONF_BID_SQL="select {}, a.code, case when code in {} then '1' else '0' end, b.detect_start_time, b.detect_end_time, ifnull(b.accuracy, 0), ifnull(b.duration, 0), {}, {}, b.param, b.expire_duration, '{}', '{}', '{}', '{}' from lettccmmndetailcode a left outer join t_arteva_event_conf b on a.code = b.EVENT_TYPE where a.code_id = 'EVENT'"
SELECT_EVENT_CONF_SQL="select {}, a.code, case when code in {} then '1' else '0' end, b.detect_start_time, b.detect_end_time, ifnull(b.accuracy, 0), ifnull(b.duration, 0), b.broadcast_id, b.param, b.expire_duration, '{}', '{}', '{}', '{}' from lettccmmndetailcode a left outer join t_arteva_event_conf b on a.code = b.EVENT_TYPE where a.code_id = 'EVENT'"

SELECT_FULL_CAMERA_INFO_SQL="select * from t_arteva_camera_info;"
SELECT_CAMERA_INFO_SQL="select id, name, url, active, resolution from t_arteva_camera_info;"
SELECT_FULL_CAMERA_EVENT_CONF_SQL="select * from t_arteva_camera_event_conf;"
SELECT_ACT_CAMERA_EVENT_CONF_SQL="select * from t_arteva_camera_event_conf where ACTIVE = 1;"
SELECT_CAMERA_EVENT_CONF_SQL="select camera_id, event_type, accuracy, active, duration, broadcast_area_code, broadcast_id from t_arteva_camera_event_conf;"

COUNT_CAMERA_INFO_SQL="select count(*) from t_arteva_camera_info;"

DEL_CAMERA_INFO_SQL="delete from t_arteva_camera_info where id = {};"
DEL_CAMERA_EVENT_CONF= "delete from t_arteva_camera_event_conf where camera_id = {};"

ALTER_CAMERA_INFO_AUTO_INCREMENT_INIT="alter table t_arteva_camera_info auto_increment =1;"

TRUNCATE_CAMERA_INFO_ARCHIVE="truncate table t_arteva_camera_info_archive;"
TRUNCATE_CAMERA_EVENT_CONF_ARCHIVE="truncate table t_arteva_camera_event_conf_archive;"

SELECT_CAMERA_STATUS="select ID, ACTIVE from t_arteva_camera_info where ACTIVE = '{}';"

UPDATE_CAMERA_ACTIVE="update t_arteva_camera_info set active = '{}' where id = {};"

UPDATE_CAMERA_INFO_BROADCAST="update t_arteva_camera_info set broadcast_area_code = '{}', broadcast_id = '{}' where event_type = '{}' and camera_id = {};"

CAMERA_EVENT_CODE="SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'EVENT' AND USE_AT = 'Y' ORDER BY CODE_NM;"

CAMERA_BROADCAST_AREA="SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'BRAREA' AND USE_AT = 'Y' ORDER BY CODE_NM;"

BROADCAST_INFO_CODE="SELECT a.id , a.broadcast_title FROM t_arteva_broadcast_info a inner join t_arteva_extern_info b on a.extern_id = b.id and b.active = 'A' WHERE a.active ='A';"

### EXTERN
## Insert Extern server 
INSERT_EXTERN_INFO_SQL="insert t_arteva_extern_info (name, active, type, request_url,address, port, login_id, password, comment, create_time, update_time, create_user, update_user) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, '{0}', '{0}', '{1}', '{1}')"

SELECT_FULL_EXTERN_SQL="select * from t_arteva_extern_info;"

SELECT_EXTERN_INFO_SQL="select a.id as extSystemId, a.name as extSystemName, DATE_FORMAT(IFNULL(a.update_time, a.create_time), '%Y-%m-%d') as createTime, b.CODE_NM as systemTypeName, c.code_nm as activeName from t_arteva_extern_info a inner join lettccmmndetailcode b on a.type = b.code and b.code_id ='EXTSYS' inner join lettccmmndetailcode c on a.active = c.code and c.code_id ='STATUS' order by systemTypeName, extSystemName;"

COUNT_EXTERN_INFO_SQL="select count(*) from t_arteva_extern_info;"

DEL_EXTERN_INFO_SQL="delete from t_arteva_extern_info where id = {};"

ALTER_EXTERN_INFO_AUTO_INCREMENT_INIT="alter table t_arteva_extern_info auto_increment =1;"

SELECT_EXTERN_STATUS="select ID, ACTIVE from t_arteva_extern_info where ACTIVE = '{}';"

UPDATE_EXTERN_ACTIVE="update t_arteva_extern_info set active = '{}' where id = {};"

SELECT_EXTERN_INFO_BC="select id, type from t_arteva_extern_info where type = 'BC';"


### BROADCAST 
## Broadcat
INSERT_BROADCAST_INFO_SQL="insert t_arteva_broadcast_info ( extern_id, ext_broadcast_id, broadcast_title, broadcast_text, start_time, end_time, active, create_time, update_time, create_user, update_user) values ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

SELECT_FULL_BROADCAST_SQL="select * from t_arteva_broadcast_info;"

SELECT_BROADCAST_INFO_SQL="select a.id as brdContentId, a.broadcast_title as brdContentTitle, a.extern_id as brdSystemId, a.active, a.ext_broadcast_id as extBroadcastId, DATE_FORMAT(IFNULL(a.update_time, a.create_time), '%Y-%m-%d') as createTime, b.name as brdSystemName,c.code_nm as activeName from t_arteva_broadcast_info a inner join t_arteva_extern_info b on a.extern_id = b.id and b.active = 'A' inner join lettccmmndetailcode c on a.active = c.code and c.code_id ='STATUS' order by brdContentTitle;"

COUNT_BROADCAST_INFO_SQL="select count(*) from t_arteva_broadcast_info;"

DEL_BROADCAST_INFO_SQL="delete from t_arteva_broadcast_info where id = {};"

ALTER_BROADCAST_INFO_AUTO_INCREMENT="alter table t_arteva_broadcast_info auto_increment =1;"
TRUNCATE_BROADCAST_INFO_ARCHIVE="truncate table t_arteva_broadcast_info_archive;"

SELECT_BROADCAST_STATUS="select ID, ACTIVE from t_arteva_broadcast_info where ACTIVE = '{}';"

UPDATE_BROADCAST_ACTIVE="update t_arteva_broadcast_info set active = '{}' where id = {};"

EVENT_SQL= "SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'EVENT' AND USE_AT = 'Y' ORDER BY CODE_NM"
BRAREA_SQL= "SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'BRAREA' AND USE_AT = 'Y' ORDER BY CODE_NM"

