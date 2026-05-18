#!/usr/bin/env python3

import csv
import os, sys
import yaml
import datetime
import pymysql
import re
import time
import configparser
import argparse
import socket
import subprocess

## CCTV.csv
# 역별 이벤트 CCTV
cctv_csv_data = []
# 전체역 CCTV
cctv_csv_all_data = []
# 역별 이벤트 CCTV Dict
#by_data = {}

camera_info_ex_sql_rows = []
arteva_camera_info_sql_rows = []

camera_sql_rows = []
extern_sql_rows = []
broadcast_sql_rows = []

now = datetime.datetime.now()
now = now.strftime('%Y-%m-%d %H:%M:%S')
NL = '\r\n'

## dmeta_arteva sql 
import arsql

#STATIONID = ['100', '101', '102', '103', '104', '105', '106', '107']

URL_REGEX = re.compile(
    r'^rtsp://'								# rtsp://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # 도메인
	r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' 	# IPv4
	r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' 			# IPv6
	r'(?::\d+)?' 							# Port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class MysqlDBAcc:
    def __init__(self, config):
        self.conn = pymysql.connect(**config)
        self.curs = self.conn.cursor()

    def select_sql(self, sql=None, fetchall=False, size=None):
        self.curs.execute(sql)

        if fetchall:
            rows = self.curs.fetchall()
            desc = self.curs.description
        elif not fetchall and size:
            rows = self.curs.fetchmany(size)
            desc = self.curs.description
        else:
            rows = self.curs.fetchone()
            desc = self.curs.description

        return desc, rows 

    def select_row_sql(self, sql=None):
        self.curs.execute(sql)

        rows = self.curs.fetchone()

        return rows

    def insert_many_sql(self, sql=None, many=None):
        if many:
            self.curs.executemany(sql, many)
        else:
            self.curs.execute(sql)

        self.conn.commit()

    def insert_args_sql(self, sql=None, args=None):
        if args:
            self.curs.execute(sql, args)
        else:
            self.curs.execute(sql)

        self.conn.commit()

    def delete_sql(self, sql=None, param=None):
        if param:
            self.curs.execute(sql, param)
        else:
            self.curs.execute(sql)

        self.conn.commit()

    def close_conn(self):
        self.conn.close()

def ims_connect_db(conf):
    config = {
            'host':conf["ims_primary"], 
            'user':conf["ims_user"],
            'passwd':conf["ims_passwd"],
            'database':conf["ims_database"],
            'port':int(conf["ims_port"]), 
            'charset':'utf8'
    }

    return MysqlDBAcc(config)

def connect_db(conf, host=None):
    if host:
        config = {
                'host':host,
                'user':conf["user"],
                'passwd':conf["passwd"],
                'database':conf["database"],
                'port':int(conf["port"]),
                'charset':'utf8'
        }
    else:
        config = {
                'host':'localhost',
                'user':conf["user"],
                'passwd':conf["passwd"],
                'database':conf["database"],
                'port':int(conf["port"]),
                'charset':'utf8'
        }

    return MysqlDBAcc(config)

class CameraInfo:
    # 역별 이벤트 CCTV Dict
    #STATIONID = ['100', '101', '102', '103', '104', '105', '106', '107']

    def __init__(self, conf, args):
        self.conf = conf
        self.args = args
        self.hostname = socket.gethostname()
        #self.sid = conf[self.hostname]
        self.sid = args.sid
        self.classname = __class__.__name__
        self.by_data = {}
        self.STATIONID = conf["STATIONID"].split(',')

    def select_camera_info_ex(self, db):
        ## 화상Interface Camera Information (mariadb)
        ## Daatabase: ims_v2
        ## Table : v_camera_info_ex
        ## (idx, station_name, station_id, camera_name, camera_ipaddr, nvr_rtsp_url, manufacturer, model, status)
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 

        desc, rows = db.select_sql(arsql.SELECT_CAMERA_INFO_EX_SQL, fetchall=True)
    
        de, data = tupletodict(desc, rows)
    
        filename = os.path.join('.', self.conf["csvdir"], self.conf["cctvfile"])
        write_csv_file(de, data, filename)
    
        return de, data

    def select_camera_info_ex_station(self, db):
        ## 화상Interface Camera Information (mariadb)
        ## Daatabase: ims_v2
        ## Table : v_camera_info_ex
        ## (idx, station_name, station_id, camera_name, camera_ipaddr, nvr_rtsp_url, manufacturer, model, status)
        ## ======================
        ## 역사별 저장
        ## hostname = "YS-VDOAN-1", "YS-TNMS-VDOAN-101" - "YS-TNMS-VDOAN-107"
        ## ======================

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 

        for sid in self.STATIONID:
            desc, rows = db.select_sql(arsql.SELECT_CAMERA_INFO_EX_STATION_SQL.format(sid), fetchall=True)
    
            de, data = tupletodict(desc, rows)
    
            filename = sid + '.csv'
            filepath=os.path.join('.', self.conf["csvdir"], filename)
            write_csv_file(de, data, filepath)

    def select_camera_info_ex_stationid(self, db, sid):
        ## 화상Interface Camera Information (mariadb)
        ## Daatabase: ims_v2
        ## Table : v_camera_info_ex
        ## (idx, station_name, station_id, camera_name, camera_ipaddr, nvr_rtsp_url, manufacturer, model, status)
        ## ======================
        ## 역사 저장
        ## hostname = "YS-VDOAN-1"
        ## ======================

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 
    
        desc, rows = db.select_sql(arsql.SELECT_CAMERA_INFO_EX_STATION_SQL.format(sid), fetchall=True)
    
        de, data = tupletodict(desc, rows)
    
        filename = sid + '.csv'
        filepath=os.path.join('.', self.conf["cctvdir"], filename)
        write_csv_file(de, data, filepath)

    def read_cctv_csv_data(self, filename):
        ## 0.idx , 1.station_name, 2.station_id, 3.camera_name, 4.camera_ipaddr, 5.nvr_rtsp_url, 6.port, 7.guid,
        ## 8.channel, 9.id, 10.pw, 11.type, 12.use, 13.nvr_ipaddr, 14.broadcast_area, 15.broadcast_id, 16.cctv_id, 
        ## 17.elevator, 18. floor

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 
    
        hd = read_csv_header(filename)
        fd = hd.index('type')
        column_name = hd.index('station_id')
    
        with open(filename, "r") as cf:
            reader = csv.DictReader(cf, fieldnames=hd)
            next(reader)
    
            for r in reader:
                row_all = {}
                for i, h in enumerate(hd):
                    if h:
                        row_all[hd[i]] = r[hd[i]]
    
                if r[hd[fd]]:
                    row = {}
                    for i, h in enumerate(hd):
                        if h:
                            row[hd[i]] = r[hd[i]]

                    cctv_csv_data.append(row)
                cctv_csv_all_data.append(row_all)
    
        WLOG("{}  Event CCTV Count : {}".format(FNC, len(cctv_csv_data)))
    
        for sid in self.STATIONID:
            station = []
            for r in cctv_csv_data:
                if r[hd[column_name]] == sid:
                    station.append(r)
            self.by_data[sid] = station
    
        return hd

    def prefare_t_arteva_camera_info(self, de, data):
        # hostname = "YS-VDOAN-1"
        # hostname = socket.gethostname()
        # stationid = conf[hostname]
        # arteva_camera_info_sql_rows
        # de, data : description, ims_v2 v_camera_info_ex
        ## csv column name
        ## 0.idx , 1.station_name, 2.station_id, 3.camera_name, 4.camera_ipaddr, 5.nvr_rtsp_url, 6.port, 7.guid,
        ## 8.channel, 9.id, 10.pw, 11.type, 12.use, 13.nvr_ipaddr, 14.broadcast_area, 15.broadcast_id, 16.cctv_id
        ## 17. elevator, 18. floor

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 

        # cctv.csv description
        hd = []
        arteva_camera_info_rows = {}
    
        for k in cctv_csv_data[0]:
            hd.append(k)
    
        ## index
        hd_nu_idx = hd.index('idx')
        hd_ur_idx = hd.index('nvr_rtsp_url')
        hd_na_idx = hd.index('station_name')
        hd_si_idx = hd.index('station_id')
        hd_ca_idx = hd.index('camera_name')
        hd_ip_idx = hd.index('camera_ipaddr')
        hd_nv_idx = hd.index('nvr_ipaddr')
        hd_id_idx = hd.index('id')
        hd_pw_idx = hd.index('pw')
        hd_ty_idx = hd.index('type')
        hd_us_idx = hd.index('use')
        hd_el_idx = hd.index('elevator')
        hd_fl_idx = hd.index('floor')
        hd_ba_idx = hd.index('broadcast_area')
        hd_bi_idx = hd.index('broadcast_id')
        hd_cc_idx = hd.index('cctv_id')
        de_nu_idx = de.index('idx')
        de_cc_idx = de.index('nvr_rtsp_url')
    
        # 역별 이벤트 CCTV Dict
        for key, val in self.by_data.items():
            by_row = []
            num = 1
            for v in val:
                for dt in data:
                    if dt[de[de_nu_idx]] == int(v[hd[hd_nu_idx]]):
                        NAME = ""
                        URL =  ""
                        ACTIVE = "S"
                        if v[hd[hd_cc_idx]]:
                            NAME = v[hd[hd_cc_idx]]
                            #NAME = 'CCTV' + '-' + v[hd[hd_si_idx]] + '-' + str(num).zfill(3)
                        if is_valid_url_regex(dt[de[de_cc_idx]]):
                            idx = dt[de[de_cc_idx]].find(v[hd[hd_nv_idx]])
                            #URL = "rtsp://" + v[hd[hd_id_idx]] + ":" + v[hd[hd_pw_idx]] + '@' + dt[de[de_cc_idx]][idx:]
                            # // password 분리
                            URL = dt[de[de_cc_idx]]
                            LOGIN_ID = v[hd[hd_id_idx]]
                            PASSWORD = v[hd[hd_pw_idx]]
                            ACTIVE = "A"
                        COMMENT = v[hd[hd_na_idx]] + "(" + v[hd[hd_si_idx]] + ") 역사, \
                            카메라 이름: " + v[hd[hd_ca_idx]] + ", \
                            용도: " + v[hd[hd_us_idx]]

                        # elevator call
                        elevator = v[hd[hd_el_idx]]
                        floor = v[hd[hd_fl_idx]]
                        # change to tuple
                        event = v[hd[hd_ty_idx]].split(',')
                        event_type = v[hd[hd_ty_idx]]
                        # broadcast area id
                        if len(event) == 1:
                            event.append("NE")
                            event_type = ','.join(event)

                        if v[hd[hd_ba_idx]]:
                            broad_area = v[hd[hd_ba_idx]]
                        else:
                            broad_area = None

                        if v[hd[hd_bi_idx]]:
                            broad_id = v[hd[hd_bi_idx]]
                        else:
                            broad_id = None

                        sql_row = [
                            NAME,                       # 1. name(CCTV name)
                            URL,                        # 2. url(rtsp url)
                            ACTIVE,                     # 3. active(Active)
                            LOGIN_ID,                   # 4. Login id 
                            PASSWORD,                   # 5. password
                            self.conf["RESOLUTION"],    # 6. resolution(FHD)
                            COMMENT,                    # 7. comment
                            now,                        # 8. create_time
                            now,                        # 9. update_time
                            self.conf["adminuser"],     # 10. create_user
                            self.conf["adminuser"],     # 11. update_user
                            elevator,                   # 17. elevator
                            floor,                      # 18. floor
                            event_type,                 # 12. event_type
                            broad_area,                 # 13. broadcast area
                            broad_id                    # 14. broadcast id 
                            ]
    
                        num+=1

                        
                        by_row.append(sql_row)

            arteva_camera_info_rows[key] = by_row

        return arteva_camera_info_rows

    def insert_t_arteva_camera_info(self, db, rows, args):
        ## Insert CCTV Registration 

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 

        des, row = db.select_sql(arsql.COUNT_CAMERA_INFO_SQL)
        user = self.conf["adminuser"]
    
        if int(row[0]) > 0:
            des, res = db.select_sql(arsql.SELECT_FULL_CAMERA_INFO_SQL, fetchall=True)
            WLOG("{} Exist CCTV ".format(FNC))
            for r in res:
                WLOG(r)
    
            exit(1)

        WLOG("{}  ARTEVA CCTV Registration start : {} STATION".format(FNC, self.sid))
        param = rows[self.sid]

        '''
        |--------|-----|--------|--------|
        |code_id |code |code_nm |code_dc |
        |--------|-----|--------|--------|
        |EVENT   |WD   |배회    |배회    |
        |EVENT   |PS   |사람    |사람    |
        |EVENT   |FT   |싸움    |싸움    |
        |EVENT   |DR   |쓰러짐  |쓰러짐  |
        |EVENT   |ST   |유모차  |유모차  |
        |EVENT   |BC   |자전거  |자전거  |
        |EVENT   |TP   |침입    |침입    |
        |EVENT   |WC   |휠체어  |휠체어  |
        |--------|-----|--------|--------|
        |--------|-----|------------|---------------------|
        |code_id |code |code_nm     |code_dc              |
        |--------|-----|------------|---------------------|
        |BRAREA  |WR   |대합실      |역내대합실           |
        |BRAREA  |UF   |상행선플랫폼|상행선플랫폼         |
        |BRAREA  |AA   |전역사      |전역사 방송 구역 코드|
        |BRAREA  |DP   |하행선플랫폼|하행선플랫폼         |
        |--------|-----|------------|---------------------|
        +----+-----------+------------------+-----------------+
        | ID | EXTERN_ID | EXT_BROADCAST_ID | BROADCAST_TITLE |
        +----+-----------+------------------+-----------------+
        |  1 |         2 | 1                | 쓰러짐(DR)      |
        |  2 |         2 | 2                | 침입  (TP)      |
        |  3 |         2 | 3                | 훨체어(WC)      |
        |  4 |         2 | 4                | 훨체어(WC)      |
        |  5 |         2 | 5                | 유모차(ST)      |
        |  6 |         2 | 6                | 자전거(BC)      |
        +----+-----------+------------------+-----------------+

        '''

        tp = args.evt
        for row in param:
            broadcast = {}
            cctv_id = row[0]
            broadcast['bid'] = row.pop()
            broadcast['barea'] = row.pop()
            event = tuple(row.pop().split(','))
            event_list = list(event)
            if tp:
                add_tp = list(event)
                add_tp.append(tp.upper())
                event = tuple(add_tp)
            if 'NE' in event_list:
                event_list.remove('NE')
            broadcast['event'] = event_list
            floor = row.pop()
            elevator = row.pop()
    
            '''
            alter table t_arteva_camera_info auto_increment =1;
            insert t_arteva_camera_info table
            name, url, active, resolution, comment,
            create_time, update_time, create_user, update_user
    
            '''
            
            WLOG("{} CCTV Camara 추가: {} EVENT : {}".format(FNC, row[0], event))
            WLOG(tuple(row))
            db.insert_args_sql(arsql.INSERT_CAMERA_INFO_SQL, tuple(row))
    
            camera_id = db.select_row_sql(arsql.SELECT_CAMERA_INFO_ID_SQL.format(cctv_id))
    
            '''
    
            CAMERA_ID
            EVENT TYPE
            DATETIME
            USER
            '''
            ### Insert t_arteva_camera_event
            WLOG("{}  camera_id : {}".format(FNC, camera_id[0]))
            SQL = arsql.INSERT_CAMERA_EVENT_SQL + arsql.SELECT_EVENT_CONF_SQL.format(camera_id[0], event, now, now, user, user)
            db.insert_args_sql(SQL)
            if tp:
                EVT_SQL = arsql.UPDATE_CAMERA_EVENT_TIME_SQL.format(args.sti, args.eti, tp.upper())
                db.insert_args_sql(EVT_SQL)

            # update t_arteva_camera_event_conf set broadcast_area_code = '{}', broadcast_id = {} where camera_id = {} and event_type = '{}';
            if broadcast['bid'] and broadcast['barea']:
                broad_id = broadcast['bid'].split(',')
                broad_ar = broadcast['barea'].split(',')
                broad_et = broadcast['event']
                for bd, ba, et in zip(broad_id, broad_ar, broad_et):
                    WLOG("{} broad_id : {}, broad_area {}, broad_event {}".format(FNC, bd, ba, et))
                    SQL = arsql.UPDATE_CAMERA_EVENT_BID_SQL.format(ba, bd, camera_id[0], et)

                    db.insert_args_sql(SQL)

            if elevator:
                WLOG("{} elevator call cctv_id : {}, floor : {}".format(FNC, row[0], floor))
                regi = floor.split(',')

                print(regi)
                SEL_SQL = arsql.SELECT_ELEVATOR_ID.format(elevator, regi[0])
                ID = db.select_row_sql(SEL_SQL)

                ## set elevator id (poor transportation) WC, ST 
                PT = ['WC', 'ST']
                for t in PT:
                    SQL = arsql.UPDATE_CAMERA_EVENT_EL_SQL.format(ID[0], camera_id[0], t)
                    db.insert_args_sql(SQL)
    
        self.select_camera_info(db)

    def write_cctv_csv_data(self, filename, update_rows):
        ## csv column name
        ## 0.idx , 1.station_name, 2.station_id, 3.camera_name, 4.camera_ipaddr, 5.nvr_rtsp_url, 6.port, 7.guid,
        ## 8.channel, 9.id, 10.pw, 11.type, 12.use, 13.nvr_ipaddr, 14.broadcast_area, 15.broadcast_id, 16.cctv_id

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 
    
        hd = read_csv_header(filename)
    
        update_num = []
        update_data = []
        for val in update_rows.values():
            for v in val:
                update_num.append(v[0])
    
        with open(filename, "r") as cf:
            reader = csv.DictReader(cf, fieldnames=hd)
            next(reader)
    
            for r in reader:
                num = r['idx']
                match_n = [n for n in update_num if n == num ]
                if match_n:
                    for value in update_rows.values():
                        for v in value :
                            if v[0] == num:
                                r['nvr_rtsp_url'] = v[1]
                                update_data.append(r)
                else:
                    update_data.append(r)
    
        write_csv_file(hd, update_data, filename)


    def check_t_arteva_camera_info(self, de, data):
        # hostname = "YS-VDOAN-1"
        # hostname = socket.gethostname()
        # stationid = conf[hostname]
        # by_data {}

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 
    
        hd = []
    
        for k in cctv_csv_data[0]:
            hd.append(k)
    
        ## csv column name
        ## 0.idx , 1.station_name, 2.station_id, 3.camera_name, 4.camera_ipaddr, 5.nvr_rtsp_url, 6.port, 7.guid,
        ## 8.channel, 9.id, 10.pw, 11.type, 12.use, 13.nvr_ipaddr, 14.broadcast_area, 15.broadcast_id, 16.cctv_id
        ## index
        hd_nu_idx = hd.index('idx')
        hd_ip_idx = hd.index('camera_ipaddr')
        hd_nv_idx = hd.index('nvr_ipaddr')
        hd_id_idx = hd.index('id')
        hd_pw_idx = hd.index('pw')
        hd_cc_idx = hd.index('nvr_rtsp_url')
        hd_cd_idx = hd.index('cctv_id')
        de_nu_idx = de.index('idx')
        de_cc_idx = de.index('nvr_rtsp_url')
    
        update_camera_info_url = {}
        for key, val in self.by_data.items():
            by_row = []
            for v in val:
                for dt in data:
                    rows = []
                    if dt[de[de_nu_idx]] == int(v[hd[hd_nu_idx]]): 
                        url = v[hd[hd_cc_idx]]
    
                        if dt[de[de_cc_idx]] == url:
                            continue
                        else:
                            if dt[de[de_cc_idx]]:
                                #URL = "rtsp://" + v[hd[hd_id_idx]] + ":" + v[hd[hd_pw_idx]] + '@' + dt[de[de_cc_idx]][7:]
                                URL = dt[de[de_cc_idx]]
                                rows = [v[hd[hd_nu_idx]], URL, v[hd[hd_cd_idx]]]

                    if rows:
                        by_row.append(rows)
    
            if by_row:
                update_camera_info_url[key]= by_row
    
        #for k, v in update_camera_info_url.items():
        #    print(k)
        #    print(v)
    
        return update_camera_info_url

    def update_camera_info(self, db, update_rows):
        # hostname = "YS-VDOAN-1"
        # hostname = socket.gethostname()
        # stationid = conf[hostname]

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 
    
        is_update = False
        for r in update_rows:
            #"select name from t_arteva_camera_info where url = '{}';"
            print(r)
            SQL = arsql.SELECT_ID_CAMERA_INFO_SQL.format(r[2])
            des, row = db.select_sql(SQL)
    
            WLOG(row)
            if row:
                WLOG("{} update_camera_info : {} , {}".format(FNC, r[2], r[1]))
                if r[1]:
                    db.insert_args_sql(arsql.UPDATE_CAMERA_INFO_SQL.format(r[1], 'A', r[2]))
                    is_update = True
                else:
                    db.insert_args_sql(arsql.UPDATE_CAMERA_INFO_SQL.format(r[1], 'S', r[2]))
                    is_update = True
    
        return is_update

    def delete_camera_info(self, db):
        '''
        '''

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 
        
        desc, rows = db.select_sql(arsql.SELECT_CAMERA_INFO_SQL, fetchall=True)
    
        for row in rows:
            WLOG("{}  Delete CCTV : {}".format(FNC, row[0]))
            db.delete_sql(arsql.DEL_CAMERA_INFO_SQL.format(row[0]))
            db.delete_sql(arsql.DEL_CAMERA_EVENT_CONF.format(row[0]))
    
        db.delete_sql(arsql.ALTER_CAMERA_INFO_AUTO_INCREMENT_INIT)
        if self.args.job == 'adel':
            WLOG(FNC + " " + self.args.job)
            db.delete_sql(arsql.TRUNCATE_CAMERA_INFO_ARCHIVE)
            db.delete_sql(arsql.TRUNCATE_CAMERA_EVENT_CONF_ARCHIVE)
    
        self.select_camera_info(db)
    
    def act_camera_info(self, db, status):
        '''
        '''

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)
        
        if status == 'A':
            srh = 'S'
        elif status == 'S':
            srh = 'A'
    
        desc, rows = db.select_sql(arsql.SELECT_CAMERA_STATUS.format(srh), fetchall=True)
        if rows:
            for row in rows:
                db.insert_args_sql(arsql.UPDATE_CAMERA_ACTIVE.format(status, row[0]))

    def select_camera_info(self, db):
        '''
        '''

        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC) 

        info_desc, info_rows = db.select_sql(arsql.SELECT_FULL_CAMERA_INFO_SQL, fetchall=True)
        conf_desc, conf_rows = db.select_sql(arsql.SELECT_ACT_CAMERA_EVENT_CONF_SQL, fetchall=True)

        WLOG("{} Select camera_info LIST".format(FNC))
        if info_rows:
            display_select(info_desc, info_rows)
        else:
            WLOG("{}  Empty".format(FNC))
    
        WLOG("{}  Select camera_event_conf".format(FNC))
        if conf_rows:
            display_select(conf_desc, conf_rows)
        else:
            WLOG("{}  Empty".format(FNC))


class ExternInfo:
    def __init__(self, conf, args):
        self.conf = conf
        self.args = args
        self.hostname = socket.gethostname()
        if args.sid:
            self.sid = args.sid
        else:
            self.sid = conf[self.hostname]
        self.classname = __class__.__name__

    def read_extern_csv(self, filename):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        hd = read_csv_header(filename)

        with open(filename, "r") as cf:
            reader = csv.DictReader(cf, fieldnames=hd)
            #reader = csv.reader(csvfile)
            next(reader)
    
            for r in reader:
                row_all = {}
                for i, h in enumerate(hd):
                    #if h and r[hd[i]]:
                    if h :
                        row_all[hd[i]] = r[hd[i]]
    
                extern_sql_rows.append(row_all)

        WLOG(extern_sql_rows)

    def add_extern_info(self, db):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        user = self.conf["adminuser"]
    
        desc, rows = db.select_sql(arsql.COUNT_EXTERN_INFO_SQL)
    
        if int(rows[0]) > 0:
            desc, rows = db.select_sql(arsql.SELECT_FULL_EXTERN_SQL, fetchall=True)
            display_select(desc, rows)
            exit(1)
    
        WLOG("{} Extern System Registration Start ".format(FNC))
        for row in extern_sql_rows:
    
            '''
            alter table t_arteva_extern_info auto_increment =1;
            insert t_arteva_extern_info
            (name, active, type, request_url, address, port, login_id, password, 
            modbus_unit_id, modbus_reigster, modbus_value1, modbus_on_value, modbus_off_value, comment,
                create_time, update_time, create_user, update_user)
            values
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now(), %s, %s)
    
            '''
            if row['시스템종류'] == 'TN':
                sql_row = [
                    row['시스템명'], # NAME
                    row['ACTIVE'], # ACTIVE
                    row['시스템종류'], # Type
                    row['URL'], # URL
                    row['IP'], # Address
                    row['PORT'], # Port
                    row['ID'], # login ID
                    row['PW'], # login password
                    row['COMMENT'],# Comment
                ]

                WLOG("{} Extern System Add : {}".format(FNC, sql_row[0]))
                db.insert_args_sql(arsql.INSERT_EXTERN_INFO_SQL.format(now, user), tuple(sql_row))

            if self.sid == row['역사'] and row['시스템종류'] == 'BC':
                sql_row = [
                    row['시스템명'], # NAME
                    row['ACTIVE'], # ACTIVE
                    row['시스템종류'], # Type
                    row['URL'], # URL
                    row['IP'], # Address
                    row['PORT'], # Port
                    row['ID'], # login ID
                    row['PW'], # login password
                    row['COMMENT'],# Comment
                ]
                WLOG("{} Extern System Add : {}".format(FNC, sql_row[0]))
                db.insert_args_sql(arsql.INSERT_EXTERN_INFO_SQL.format(now, user), tuple(sql_row))

            if self.sid == row['역사'] and row['시스템종류'] == 'EL':
                sql_row = [
                    row['시스템명'], # NAME
                    row['ACTIVE'], # ACTIVE
                    row['시스템종류'], # Type
                    row['URL'], # URL
                    row['IP'], # Address
                    row['PORT'], # Port
                    row['ID'], # login ID
                    row['PW'], # login password
                    row['MODBUS_UNIT_ID'], # elevator id
                    row['MODBUS_REGISTER'], # elevatro control address
                    row['MODBUS_VALUE'], # elevatro control high address
                    row['MODBUS_ON_VALUE'], # elevatro control on value
                    row['MODBUS_OFF_VALUE'], # elevatro control off value
                    row['COMMENT'],# Comment
                ]
                WLOG("{} Extern System Add : {}".format(FNC, sql_row[0]))
                db.insert_args_sql(arsql.INSERT_EXTERN_MODBUS_INFO_SQL.format(now, user), tuple(sql_row))
    
        self.select_extern_info(db)
    
    def delete_extern_info(self, db):
        '''
        '''
        FNC = "[[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        desc, rows = db.select_sql(arsql.SELECT_FULL_EXTERN_SQL, fetchall=True)
    
        for row in rows:
            WLOG("{} Delete Extern System: {} ".format(FNC, row[1]))
            db.delete_sql(arsql.DEL_EXTERN_INFO_SQL.format(row[0]))
    
        db.delete_sql(arsql.ALTER_EXTERN_INFO_AUTO_INCREMENT_INIT)
    
        self.select_extern_info(db)

    def update_extern_info(self, db, status):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        if status == 'A':
            srh = 'S'
        elif status == 'S':
            srh = 'A'
    
        desc, rows = db.select_sql(arsql.SELECT_EXTERN_STATUS.format(srh), fetchall=True)
        if rows:
            for row in rows:
                db.insert_args_sql(arsql.UPDATE_EXTERN_ACTIVE.format(status, row[0]))
    
    
    def select_extern_info(self, db):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        desc, rows = db.select_sql(arsql.SELECT_FULL_EXTERN_SQL, fetchall=True)
        display_select(desc, rows)


class BroadCastInfo:
    def __init__(self, conf, args):
        self.conf = conf
        self.args = args
        self.hostname = socket.gethostname()
        self.sid = conf[self.hostname]
        self.classname = __class__.__name__

    def read_broadcast_csv(self, filename):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        # 0. 번호, 1. 방송멘트ID, 2. 방송제목, 3. 방송내용, 4. ACTIVE, 5. START, 6. END

        hd = read_csv_header(filename)
        with open(filename, "r") as cf:
            reader = csv.DictReader(cf, fieldnames=hd)
            next(reader)
    
            for r in reader:
                row_all = {}
                for i, h in enumerate(hd):
                    if h:
                        row_all[hd[i]] = r[hd[i]]

                broadcast_sql_rows.append(row_all)

    def update_broadcast_camera_info(self, db):
        ## arsql.BRAREA_SQL
        '''
        BROADCAST_ID
        for row in camera_sql_rows:
            event = row[len(row) -1]
            event_type = row.pop().split(',')
            #event_type = tuple(row.pop().split(','))
    
            cctv_id = int(re.sub(r'[^0-9]', '', row[0]))
            for etype in event_type:
                db.insert_sql(arsql.UPDATE_CAMERA_INFO_BROADCAST.format(,,etype,cctv_id))
    
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

    def add_broadcast_info(self, db):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        user = self.conf["adminuser"]
    
        desc, rows = db.select_sql(arsql.COUNT_BROADCAST_INFO_SQL)
    
        time = lambda x:x if x else None 

        if int(rows[0]) > 0:
            desc, rows = db.select_sql(arsql.SELECT_FULL_BROADCAST_SQL, fetchall=True)
            display_select(desc, rows)
            exit(1)
    
        desc, extern_id = db.select_sql(arsql.SELECT_EXTERN_INFO_BC)
        if extern_id:
            WLOG("{} Broadcast System Registration Start".format(FNC))
            e_id = extern_id[0]
            for row in broadcast_sql_rows:
    
                '''
                alter table t_arteva_broadcast_info auto_increment =1;
                insert t_arteva_broadcast_info
                ( extern_id, ext_broadcast_id, broadcast_title, broadcast_text,
                start_time, end_time, active, create_time, update_time, create_user, update_user)
                values
                (%s', %s, %s, %s,
                case when '06:00' = '' then null else '06:00' end,
                case when '12:00' = '' then null else '12:00' end,
                %s, %s, %s, %s, %s)
    
                '''
                # 0. 번호, 1. 방송멘트ID, 2. 방송제목, 3. 방송내용, 4. ACTIVE, 5. START, 6. END
                sql_row = [
                    int(e_id),          # extern id
                    row['방송멘트ID'],  # broadcast id
                    row['방송제목'],    # broadcast title
                    row['방송내용'],    # broadcast text
                    time(row['START']), # broadcast Start time
                    time(row['END']),   # broadcast END time
                    row['ACTIVE'],      # broadcast status
                    now,                # Create time
                    now,                # Update time
                    user,               # broadcast status
                    user                # broadcast status
                ]

                WLOG("{} Extern System Add : {} {}".format(FNC, sql_row[0], sql_row[2]))
                #WLOG(tuple(sql_row))

                db.insert_args_sql(arsql.INSERT_BROADCAST_INFO_SQL, tuple(sql_row))
        else:
            WLOG("{} register broadcast server(extern)".format(FNC))
            sys.exit(0)
    
        self.select_broadcast_info(db)

    def delete_broadcast_info(self, db):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        desc, rows = db.select_sql(arsql.SELECT_FULL_BROADCAST_SQL, fetchall=True)
    
        for row in rows:
            WLOG("{} Delete Broadcast Text: {} ".format(FNC, row[1]))
            db.delete_sql(arsql.DEL_BROADCAST_INFO_SQL.format(row[0]))
    
        db.delete_sql(arsql.ALTER_BROADCAST_INFO_AUTO_INCREMENT)
        if self.args.job == 'adel':
            WLOG(FNC + " " + self.args.job)
            db.delete_sql(arsql.TRUNCATE_BROADCAST_INFO_ARCHIVE)
    
        self.select_broadcast_info(db)
    
    def update_broadcast_info(self, db, status):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        if status == 'A':
            srh = 'S'
        elif status == 'S':
            srh = 'A'
    
        desc, rows = db.select_sql(arsql.SELECT_BROADCAST_STATUS.format(srh), fetchall=True)
        if rows:
            for row in rows:
                db.insert_args_sql(arsql.UPDATE_BROADCAST_ACTIVE.format(status, row[0]))
    
    def select_broadcast_info(self, db):
        '''
        '''
        FNC = "[{}::{}] ".format(self.classname ,sys._getframe().f_code.co_name)
        WLOG(FNC)

        desc, rows = db.select_sql(arsql.SELECT_FULL_BROADCAST_SQL, fetchall=True)
        display_select(desc, rows)

class BackupData():
    def __init__(self, conf, args):
        self.conf = conf
        self.args = args
        self.hostname = socket.gethostname()
        self.sid = conf[self.hostname]
        self.classname = __class__.__name__
        self.db_host = self.conf["host"]
        self.db_user = self.conf["user"]
        self.db_pass = self.conf["passwd"]
        self.db_name = self.conf["database"]
        self.BACKUP_FILE = f"bakup_{self.db_name}_{self.hostname}.sql"

    def backup(self):
        # Construct the mariadb-dump command
        # -h: host -u: user -p: password
        #-A, --all-databases Dump all the databases. This will be same as --databases
        #              with all databases selected.
        #-T, --tab=name      Create tab-separated textfile for each table to given
        #              path. (Create .sql and .txt files.) NOTE: This only works
        #              if mysqldump is run on the same machine as the mysqld
        #              server.
        command = [
                "mariadb-dump",
                f"-h {self.db_host}",
                f"-u {self.db_user}",
                f"-p'{self.db_pass}'",
                "--single-transaction",
                "--routines",
                "--triggers",
                "--events",
                self.db_name,
                f"> {self.BACKUP_FILE}"
        ]
        try:
            # Execute the mysqldump command
            subprocess.run(" ".join(command), shell=True, check=True)
            WLOG(f"Database '{self.db_name}' backed up successfully to '{self.BACKUP_FILE}'")
        except subprocess.CalledProcessError as e:
            WLOG(f"Error during backup: {e}")
        except FileNoFoundError:
            WLOG("Error mysqldump command not found. Ensure mysql client tools are installed and in your system's PATH.")

    def restore(self):
        # Construct the mariadb command            
        command = [
                "mariadb",
                f"-h {self.db_host}",
                f"-u root",
                #f"-u {self.db_user}",
                f"-p'{self.db_pass}'",
                self.db_name,
                f"< {self.BACKUP_FILE}"
        ]
        try:
            # Execute the mysqldump command
            subprocess.run(" ".join(command), shell=True, check=True)
            WLOG(f"Database '{self.db_name}' restored up successfully to '{self.BACKUP_FILE}'")
        except subprocess.CalledProcessError as e:
            WLOG(f"Error during backup: {e}")
        except FileNoFoundError:
            WLOG("Error mariadb command not found. Ensure mysql client tools are installed and in your system's PATH.")


## ============================================================
## for Test 
def select_ims_v_camera_info_ex(db):
    desc, rows = db.select_sql(arsql.SELECT_CAMERA_INFO_EX_SQL, fetchall=True)

    for row in rows:
        WLOG(row)


def insert_ims_v_camera_info_ex(db, hd):
    ## cct_csv_all_data
    ## 0.idx, 1.station_name, 2.station_id, 3.camera_name, 4.camera_ipaddr, 5.nvr_rtsp_url, 6.prot, 7.guid,
    ## 8.channel, 9.id, 10.pw, 11.type, 12.use, 13.nvr_ipaddr, 14.broadcast_area, 15.broadcast_id, 16.cctv_id

    desc = db.select_sql(arsql.SELECT_CAMERA_INFO_EX_SQL)

    column = []
    WLOG("Test Camera info insert start : ims_v2 v_camera_info_ex")
    for row in cctv_csv_all_data:
        '''
        insert v_camera_info_ex  
        (idx, station_name, station_id, camera_name, camera_ipaddr, nvr_rtsp_url, manufacturer, model, status)
        '''
        #if row['guid'] :
        #    start = row['nvr_rtsp_url'].find(row['id'])
        #    end = row['nvr_rtsp_url'].find(row['nvr_ipaddr'])

        #    if start > 0 and end > 0:
        #        nvr_url = row['nvr_rtsp_url'][:start] + row['nvr_rtsp_url'][end:]
        #        row['nvr_rtsp_url'] = nvr_url

        if row['idx']:
            WLOG("CCTV 추가: {} {}".format(row['idx'], row['nvr_rtsp_url']))
            column = []
            for de in desc:
                try:
                    for d in de:
                        match_c = [h for h in hd if h == d[0]]
                        if match_c :
                            column.append(row[match_c[0]])
                except TypeError:
                    # None iterable
                    pass

            WLOG(arsql.INSERT_CAMERA_INFO_EX_SQL)
            WLOG(tuple(column))
            db.insert_args_sql(arsql.INSERT_CAMERA_INFO_EX_SQL, tuple(column))

    select_ims_v_camera_info_ex(db)


## ============================================================
## UTIL

def WLOG(S):
    import inspect
    ### line number
    cf = inspect.currentframe()
    linenu = cf.f_back.f_lineno
    #pathdir =os.path.dirname(os.path.abspath(__file__))
    filename = os.path.basename(__file__)
    wnow = datetime.datetime.now()
    TS = "{} {} ({}:{})".format(wnow, S, filename, linenu)
    print(TS)

def write_csv_file(de, data, filename):
    ## write csv file
    FNC = "[{}] ".format(sys._getframe().f_code.co_name)
    WLOG("{} WRITE::CSV::FILE {} ".format(FNC, filename))

    with open(filename, 'w') as wf:
        writer = csv.DictWriter(wf, fieldnames=de)

        writer.writeheader()
        for row in data:
            writer.writerow(row)


def read_csv_header(filename):
    with open(filename, 'r', encoding='utf-8-sig') as cf:
        reader = csv.reader(cf)
        header = next(reader)

        return header 


def select_db(db):
    desc, rows = db.select_sql(arsql.LAST_INSERT_SQL)

    return rows 


def display_select(desc, rows):
    ## read description and print Field name, size
    kv = {}
    lines = []
    pstr = []
    lows = ""

    for dc in desc:
        kv[dc[0].upper()] = len(dc[0])

    for i, k in enumerate(kv.keys()) :
        for rw in rows:
            if len(str(rw[i])) > kv[k] :
                #    if check_korean(str(rw[i])):
                kv[k] = len(str(rw[i]))

    for k, v in kv.items():
        pstr.append('+')
        s = '-'.rjust(v+2, '-')
        pstr.append(s)

        lows += "| %-" + str(v+1) + "s"

    pst = ''.join(pstr) + '+'
    low = lows + '|'

    lines.append(pst)
    lines.append(low % tuple(kv.keys()))
    lines.append(pst)

    for r in rows:
        lines.append(low % tuple(r))
    lines.append(pst)

    for l in lines:
        print(l)


def print_csv(data):
    print(data)

    for d in cctv_csv_all_data:
        print(d)

def tupletodict(desc, rows):
    data = []
    de = []
    for d in desc:
        de.append(d[0])

    for r in rows:
        row = {}
        for i, d in enumerate(de):
            row[de[i]] = r[i]

        data.append(row)

    return de, data


def tupletolist(desc, rows):
    data = []
    de = []
    for dc in desc:
        de.append(dc[0])

    data.append(de)
    
    for row in rows:
        data.append(list(row))

    return data


def check_korean(kstr):
    p = re.compile('[ㄱ-힣]')
    r = p.search(kstr)
    if r is None:
        return False
    else:
        return True


def getIPAddress(name):
    FNC = "[{}] ".format(sys._getframe().f_code.co_name)
    try:
        ip = socket.gethostbyname(name)
        WLOG("{} localhost의 IP 주소: {}".format(FNC, ip))
        return True
    except socket.gaierror as e:
        WLOG("{} IP 주소를 조회할 수 없습니다: {}".format(FNC, e))
        return False


def is_valid_url_regex(url):
    return bool(URL_REGEX.match(url))


def line_info():
    import inspect

    info = {}
    # line number, Call to Function name
    cf = inspect.currentframe()
    info['line_num'] = cf.f_back.f_lineno
    info['fun_name'] = cf.f_back.f_code.co_name

    # The filename name that called this
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    info['file_name'] = module.__file__

    return info

def CameraInfoWork(conf, args):
    FNC = "[{}::{}] ".format(args.eqpt[0].upper() ,sys._getframe().f_code.co_name)
    WLOG(FNC)
    WLOG("{} RUN : {} -- {} ".format(FNC, args.eqpt, args.job))

    hostname = socket.gethostname()
    if args.sid:
        sid = args.sid
    else:
        sid = conf[hostname]
        args.sid = sid

    ims_db = ims_connect_db(conf)

    Camera = CameraInfo(conf, args)

    if conf[sid]:
        db = connect_db(conf, conf[sid])
    else:
        db = connect_db(conf)
    
    if args.job == 'get':
        de, data = Camera.select_camera_info_ex(ims_db)
        Camera.select_camera_info_ex_station(ims_db)

    if args.job == 'add':
        ims_de, ims_data = Camera.select_camera_info_ex(ims_db)
        filename = os.path.join('.', conf['cctvdir'], conf['cctvfile'])
        hd = Camera.read_cctv_csv_data(filename)

        insert_rows = Camera.prefare_t_arteva_camera_info(ims_de, ims_data)

        Camera.insert_t_arteva_camera_info(db, insert_rows, args)

    if args.job == 'chk':
        ims_de, ims_data = Camera.select_camera_info_ex(ims_db)

        filename = os.path.join('.', conf['cctvdir'], conf['cctvfile'])
        hd = Camera.read_cctv_csv_data(filename)

        update_rows = Camera.check_t_arteva_camera_info(ims_de, ims_data)

        if update_rows and update_rows.get(sid):
            update = update_rows.get(sid)
            result = Camera.update_camera_info(db, update)

            if result:
                Camera.write_cctv_csv_data(filename, update_rows)
                Camera.select_camera_info_ex(ims_db)
                for key in update_rows.keys():
                    Camera.select_camera_info_ex_stationid(ims_db, key)

        else:
            WLOG("{}  Same".format(FNC))

    if args.job == 'read':
        filename = os.path.join('.', conf['cctvdir'], conf['cctvfile'])
        hd = Camera.read_cctv_csv_data(filename)
        print_csv(hd)

    if args.job == 'del' or args.job == 'adel' :
        Camera.delete_camera_info(db)

    if args.job == 'sel':
        Camera.select_camera_info(db)

    if args.job == 'act':
        Camera.act_camera_info(db, 'A')

    if args.job == 'sby':
        Camera.act_camera_info(db, 'S')

    if args.job == 'hid':
        filename = os.path.join('.', conf['cctvdir'], conf['cctvfile'])
        hd = Camera.read_cctv_csv_data(filename)
        insert_ims_v_camera_info_ex(ims_db, hd)
        select_ims_v_camera_info_ex(ims_db)

    #select_db(db)

def ExternInfoWork(conf, args):
    FNC = "[{}::{}]".format(args.eqpt ,sys._getframe().f_code.co_name)
    WLOG(FNC)
    WLOG("{} RUN : {} -- {}".format(FNC, args.eqpt, args.job))

    hostname = socket.gethostname()
    if args.sid:
        sid = args.sid
    else:
        sid = conf[hostname]
        args.sid = sid
    #sid = conf[hostname]

    Extern = ExternInfo(conf, args)

    if conf[sid]:
        db = connect_db(conf, conf[sid])
    else:
        db = connect_db(conf)

    if args.job == 'sel':
        Extern.select_extern_info(db)
    if args.job == 'add':
        filename = os.path.join('.', args.eqpt[0].upper() + '.csv')
        Extern.read_extern_csv(filename)
        Extern.add_extern_info(db)
    if args.job == 'del':
        Extern.delete_extern_info(db)
    if args.job == 'act':
        Extern.update_extern_info(db, 'A')
    if args.job == 'sby':
        Extern.update_extern_info(db, 'S')


def BroadCastInfoWork(conf, args):
    FNC = "[{}::{}]".format(args.eqpt ,sys._getframe().f_code.co_name)
    WLOG(FNC)
    WLOG("{} RUN : {} -- {}".format(FNC, args.eqpt, args.job))

    hostname = socket.gethostname()
    if args.sid:
        sid = args.sid
    else:
        sid = conf[hostname]
        args.sid = sid
    #sid = conf[hostname]

    WLOG("{} DB : {} -- {}".format(FNC, args.sid, args.job))

    Broad = BroadCastInfo(conf, args)

    if conf[sid]:
        db = connect_db(conf, conf[sid])
    else:
        db = connect_db(conf)

    if args.job == 'sel':
        Broad.select_broadcast_info(db)
    if args.job == 'add':
        filename = os.path.join('.', args.eqpt[0].upper() + '.csv')
        Broad.read_broadcast_csv(filename)
        Broad.add_broadcast_info(db)
    if args.job == 'del' or args.job == 'adel' :
        Broad.delete_broadcast_info(db)
    if args.job == 'act':
        Broad.update_broadcast_info(db, 'A')
    if args.job == 'sby':
        Broad.update_broadcast_info(db, 'S')

def BackupDB(conf, args):
    FNC = "[{}::{}]".format(args.eqpt ,sys._getframe().f_code.co_name)
    WLOG(FNC)
    WLOG("{} RUN : {} -- {}".format(FNC, args.eqpt, args.job))

    hostname = socket.gethostname()
    sid = conf[hostname]

    Back = BackupData(conf, args)
    if args.job == 'back':
        Back.backup()
    if args.job == 'restore':
        Back.restore()

def do_arteva(conf, args):
    equip = args.eqpt[0]
    if 'cctv' in equip:
        CameraInfoWork(conf, args)
    elif 'extern' in equip:
        ExternInfoWork(conf, args)
    elif 'broadcast' in equip :
        BroadCastInfoWork(conf, args)
    elif 'backup' in equip :
        BackupDB(conf, args)


def main():
    parser = argparse.ArgumentParser(description="ARTEVA NVR RTSP ")
    parser.add_argument('eqpt', nargs='+')
    parser.add_argument("--job", dest='job', default='get', help="NVR RSTP Register ")
    parser.add_argument("--sid", dest='sid', help="server ID")
    parser.add_argument("--evt", dest='evt', default=None, help="Add event type")
    parser.add_argument("--sti", dest='sti', default='00:30:00', help="detect start time")
    parser.add_argument("--eti", dest='eti', default='05:30:00', help="detect end time")
    parser.parse_args(['cctv', 'extern', 'broadcast'])

    args = parser.parse_args()
        
    properties = configparser.ConfigParser()
    properties.read('camera-info.ini')
    conf = properties["default"]
    do_arteva(conf, args)


if __name__=='__main__':
    main()
