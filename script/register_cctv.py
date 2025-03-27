#!/usr/bin/env python3

import csv
import os, sys
import yaml
import datetime
import pymysql
import re
import time
import configparser

camera_sql_rows = []
extern_sql_rows = []
broadcast_sql_rows = []

now = datetime.datetime.now()
now = now.strftime('%Y-%m-%d %H:%M:%S')

## CAMERA
insert_camera_info_sql = 'insert t_arteva_camera_info (name, url, active, resolution, comment, create_time, update_time, create_user, update_user) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'

insert_camera_event_sql = 'insert t_arteva_camera_event_conf (camera_id, event_type, active, detect_start_time, detect_end_time, accuracy, duration, broadcast_id, param, expire_duration, create_time, update_time, create_user, update_user ) '

insert_select_camera_sql = "select {}, a.code, case when code in {} then '1' else '0' end, b.detect_start_time, b.detect_end_time, ifnull(b.accuracy, 0), ifnull(b.duration, 0), b.broadcast_id, b.param, b.expire_duration, '{}', '{}', '{}', '{}' from lettccmmndetailcode a left outer join t_arteva_event_conf b on a.code = b.EVENT_TYPE where a.code_id = 'EVENT'"

select_full_camera_info_sql = 'select * from t_arteva_camera_info;'
select_camera_info_sql = 'select id, name, url, active, resolution from t_arteva_camera_info;'
select_full_camera_evnet_conf_sql = 'select * from t_arteva_camera_event_conf;'
select_camera_evnet_conf_sql = 'select camera_id, event_type, accuracy, active, duration, broadcast_area_code, broadcast_id from t_arteva_camera_event_conf;'

## Extern
insert_extern_info_sql = "insert t_arteva_extern_info (name, active, type, address, port, login_id, password, comment, create_time, update_time, create_user, update_user) values (%s, %s, %s, %s, %s, %s, %s, %s, '{0}', '{0}', '{1}', '{1}')"
insert_extern_info_to_sql = "insert t_arteva_extern_info (name, active, type, request_url, address, port, login_id, password, comment, create_time, update_time, create_user, update_user) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, '{0}', '{0}', '{1}', '{1}')"

select_full_extern_sql = 'select * from t_arteva_extern_info;'

select_extern_info_sql = "select a.id as extSystemId, a.name as extSystemName, DATE_FORMAT(IFNULL(a.update_time, a.create_time), '%Y-%m-%d') as createTime, b.CODE_NM as systemTypeName, c.code_nm as activeName from t_arteva_extern_info a inner join lettccmmndetailcode b on a.type = b.code and b.code_id ='EXTSYS' inner join lettccmmndetailcode c on a.active = c.code and c.code_id ='STATUS' order by systemTypeName, extSystemName;"

## Broadcat

#insert_broadcast_info_sql = "insert t_arteva_broadcast_info ( extern_id, ext_broadcast_id, broadcast_title, broadcast_text, active, create_time, update_time, create_user, update_user) values ( '{2}', %s, %s, %s, %s, '{0}', '{0}', '{1}', '{1}' )"
insert_broadcast_info_sql = "insert t_arteva_broadcast_info ( extern_id, ext_broadcast_id, broadcast_title, broadcast_text, start_time, end_time, active, create_time, update_time, create_user, update_user) values ( '{2}', %s, %s, %s, %s, %s, %s, '{0}', '{0}', '{1}', '{1}' )"

select_full_broadcast_sql = 'select * from t_arteva_broadcast_info;'

select_broadcast_info_sql = "select a.id as brdContentId, a.broadcast_title as brdContentTitle, a.extern_id as brdSystemId, a.active, a.ext_broadcast_id as extBroadcastId, DATE_FORMAT(IFNULL(a.update_time, a.create_time), '%Y-%m-%d') as createTime, b.name as brdSystemName,c.code_nm as activeName from t_arteva_broadcast_info a inner join t_arteva_extern_info b on a.extern_id = b.id and b.active = 'A' inner join lettccmmndetailcode c on a.active = c.code and c.code_id ='STATUS' order by brdContentTitle;"

event_sql = "SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'EVENT' AND USE_AT = 'Y' ORDER BY CODE_NM"

brarea_sql = "SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'BRAREA' AND USE_AT = 'Y' ORDER BY CODE_NM"

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

def connect_db(conf):
    config = {
            'host':conf["hostip"], 
            'user':conf["user"],
            'passwd':conf["passwd"],
            'database':conf["database"],
            'port':int(conf["port"]), 
            'charset':'utf8'
    }

    return MysqlDBAcc(config)

def read_camera_csv(filename, conf):
    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            sql_row = [
                    'CCTV' + row[0].zfill(2), 
                    row[6], 
                    conf["ACTIVE"], 
                    conf["RESOLUTION"], 
                    row[2] + ", 채널 번호: " + row[4] + ", 용도: " + row[5], 
                    now, 
                    now, 
                    conf["adminuser"], 
                    conf["adminuser"], 
                    row[9]
                ]
            camera_sql_rows.append(sql_row)

def read_extern_csv(filename, conf):
    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            sql_row = [
                    row[2], # NAME
                    row[9], # ACTIVE
                    row[3], # Type
                    row[4], # URL
                    row[5], # Address
                    row[6], # Port
                    row[7], # login ID
                    row[8], # login password
                    row[10],# Comment
                ]
            extern_sql_rows.append(sql_row)

def read_broadcast_csv(filename, conf):
    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        for row in reader:
            if row[5]:
                row5 = row[5] 
            else:
                row5 = None
            if row[6]:
                row6 = row[6]
            else:
                row6 = None
            sql_row = [
                    row[1].zfill(2), # ID
                    row[2], # Title
                    row[3], # Text
                    row5, #"case when '" + row[5] + "' = '' then null else '" + row[5] + "' end", 
                    row6, #"case when '" + row[6] + "' = '' then null else '" + row[6] + "' end",
                    row[4] # ACTIVE
                ]
            broadcast_sql_rows.append(sql_row)

SQL = 'SELECT LAST_INSERT_ID()'
def select_db(db):
    desc, rows = db.select_sql(SQL)

    return rows 

def add_camera_info(db, conf):
    ## Check CCTV INFO
    index_sql = 'select count(*) from t_arteva_camera_info;'
    desc, rows = db.select_sql(index_sql)
    camera_sql = 'select * from t_arteva_camera_info;'
    user = conf["adminuser"]

    if int(rows[0]) > 0:
        des, res = db.select_sql(camera_sql, fetchall=True)
        print("Exist CCTV ")
        for row in res:
            print(row)

        exit(1)
            
    print("USER : %s, TIME: %s" % (user, now))
    print("CCTV Registration start ")
    for row in camera_sql_rows:
        event = row[len(row) -1]
        event_type = tuple(row.pop().split(','))

        '''
        alter table t_arteva_camera_info auto_increment =1;
        insert t_arteva_camera_info table 
        name, url, active, resolution, comment, 
        create_time, update_time, create_user, update_user

        '''
        print("CCTV Camara 추가: {}".format(row[0]))
        print(row)
        print("EVENT : {}".format(event_type))
        print()
        db.insert_args_sql(insert_camera_info_sql, tuple(row))

        '''
        CAMERA_ID
        EVENT TYPE 
        DATETIME
        USER
        '''
        ### Insert t_arteva_camera_info
        cctv_id = int(re.sub(r'[^0-9]', '', row[0]))
        print("CCTV ID: %s" % cctv_id)
        SQL = insert_camera_event_sql + insert_select_camera_sql.format(cctv_id, event_type, now, now, user, user)
        print(SQL)
        db.insert_args_sql(SQL)

        time.sleep(2)
        
    sel_camera_info(db)

def delete_camera_info(db):
    '''
    '''
    desc, rows = db.select_sql(select_camera_info_sql, fetchall=True)

    for row in rows:
        del_camera_info_sql = 'delete from t_arteva_camera_info where id = {};'
        del_camera_event_conf = 'delete from t_arteva_camera_event_conf where camera_id = {};'
        print("Delete CCTV : %s" % row[0])
        db.delete_sql(del_camera_info_sql.format(row[0]))
        db.delete_sql(del_camera_event_conf.format(row[0]))

    db.delete_sql('alter table t_arteva_camera_info auto_increment =1;')

    sel_camera_info(db)
    
def update_camera_info(db, status):
    if status == 'A':
        srh = 'S'
    elif status == 'S':
        srh = 'A'

    status_cctv = "select ID, ACTIVE from t_arteva_camera_info where ACTIVE = '{}';"
    desc, rows = db.select_sql(status_cctv.format(srh), fetchall=True)
    if rows:
        update_sql = 'update t_arteva_camera_info set active = "{}" where id = {};'
        for row in rows:
            db.insert_args_sql(update_sql.format(status, row[0]))

def update_broadcast_camera_info(db):
    br_area = "SELECT CODE_ID, CODE, CODE_NM, CODE_DC FROM LETTCCMMNDETAILCODE WHERE CODE_ID = 'BRAREA' AND USE_AT = 'Y' ORDER BY CODE_NM;"
    

    '''
    BROADCAST_ID
    for row in camera_sql_rows:
        event = row[len(row) -1]
        event_type = row.pop().split(',')
        #event_type = tuple(row.pop().split(','))

        cctv_id = int(re.sub(r'[^0-9]', '', row[0]))
        for etype in event_type:
            update_sql = 'update t_arteva_camera_info set broadcast_area_code = "{}", broadcast_id = "{}" where event_type = "{}" and camera_id = {};'

            db.insert_sql(update_sql.format(,,etype,cctv_id))

    '''

def select_camera_info(db):
    info_desc, info_rows = db.select_sql(select_full_camera_info_sql, fetchall=True)
    conf_desc, conf_rows = db.select_sql(select_full_camera_evnet_conf_sql, fetchall=True)
    print("Select camera_info LIST")
    if info_rows:
        display_select(info_desc, info_rows)
    else:
        print("Empty")

    print()
    print("Select camera_event_conf ")
    if conf_rows:
        display_select(conf_desc, conf_rows)
    else:
        print("Empty")

def add_extern_info(db, conf, tags):
    user = conf["adminuser"]

    index_sql = 'select count(*) from t_arteva_extern_info;'
    desc, rows = db.select_sql(index_sql)

    if int(rows[0]) > 0:
        desc, rows = db.select_sql(select_full_extern_sql, fetchall=True)
        display_select(desc, rows)
        exit(1)

    print("Extern System Registration Start ")
    print()
    for row in extern_sql_rows:

        '''
        alter table t_arteva_extern_info auto_increment =1;
        insert t_arteva_extern_info 
        (name, active, type, request_url, address, port, login_id, password, comment, 
            create_time, update_time, create_user, update_user) 
        values 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, now(), now(), %s, %s)

        '''
        print("Extern System Add : {}".format(row[0]))
        if tags == "add":
            db.insert_args_sql(insert_extern_info_to_sql.format(now, user), tuple(row))
        elif tags == "add2":
            db.insert_args_sql(insert_extern_info_sql.format(now, user), tuple(row))
    
    print()
    select_extern_info(db)

def delete_extern_info(db):
    '''
    '''
    desc, rows = db.select_sql(select_full_extern_sql, fetchall=True)

    for row in rows:
        del_extern_info_sql = 'delete from t_arteva_extern_info where id = {};'
        print("Delete Extern System: %s" % row[1])
        db.delete_sql(del_extern_info_sql.format(row[0]))

    db.delete_sql('alter table t_arteva_extern_info auto_increment =1;')

    select_extern_info(db)

def update_extern_info(db, status):
    if status == 'A':
        srh = 'S'
    elif status == 'S':
        srh = 'A'

    status_extern = "select ID, ACTIVE from t_arteva_extern_info where ACTIVE = '{}';"
    desc, rows = db.select_sql(status_extern.format(srh), fetchall=True)
    if rows:
        update_sql = 'update t_arteva_extern_info set active = "{}" where id = {};'
        for row in rows:
            db.insert_args_sql(update_sql.format(status, row[0]))

def select_extern_info(db):
    desc, rows = db.select_sql(select_full_extern_sql, fetchall=True)
    display_select(desc, rows)

def add_broadcast_info(db, conf):
    user = conf["adminuser"]

    index_sql = 'select count(*) from t_arteva_broadcast_info;'
    desc, rows = db.select_sql(index_sql)

    if int(rows[0]) > 0:
        desc, rows = db.select_sql(select_full_broadcast_sql, fetchall=True)
        display_select(desc, rows)
        exit(1)

    print("Broadcast System Registration Start ")
    extern_id_sql = "select id, type from t_arteva_extern_info where type = 'BC';"
    desc, extern_id = db.select_sql(extern_id_sql)
    e_id = extern_id[0]
    print(e_id)
    for row in broadcast_sql_rows:

        '''
        alter table t_arteva_broadcast_info auto_increment =1;
        insert t_arteva_broadcast_info
        ( extern_id, ext_broadcast_id, broadcast_title, broadcast_text, 
        start_time, end_time, active, create_time, update_time, create_user, update_user)
        values
	    ( '{2}', %s, %s, %s, 
        case when '06:00' = '' then null else '06:00' end, 
        case when '12:00' = '' then null else '12:00' end, 
        %s, '{0}', '{0}', '{1}', '{1}' )

        '''
        print("Extern System Add : {}".format(row[0]))
        print()
        print(insert_broadcast_info_sql.format(now, user, e_id))
        print(row)
        db.insert_args_sql(insert_broadcast_info_sql.format(now, user, e_id), tuple(row))

    select_broadcast_info(db)

def delete_broadcast_info(db):
    '''
    '''
    desc, rows = db.select_sql(select_full_broadcast_sql, fetchall=True)

    for row in rows:
        delete_broadcast_info_sql = 'delete from t_arteva_broadcast_info where id = {};'
        print("Delete Broadcast Text: %s" % row[1])
        db.delete_sql(delete_broadcast_info_sql.format(row[0]))

    db.delete_sql('alter table t_arteva_broadcast_info auto_increment =1;')

    select_broadcast_info(db)

def update_broadcast_info(db, status):
    if status == 'A':
        srh = 'S'
    elif status == 'S':
        srh = 'A'

    status_broadcast = "select ID, ACTIVE from t_arteva_broadcast_info where ACTIVE = '{}';"
    desc, rows = db.select_sql(status_broadcast.format(srh), fetchall=True)
    if rows:
        update_sql = 'update t_arteva_broadcast_info set active = "{}" where id = {};'
        for row in rows:
            db.insert_args_sql(update_sql.format(status, row[0]))

def select_broadcast_info(db):
    desc, rows = db.select_sql(select_full_broadcast_sql, fetchall=True)
    display_select(desc, rows)

def display_select(desc, rows):
    header = []
    colsize = [] 
    rcolsize = [] 
    for des in desc:
        header.append(des[0].upper())
        colsize.append(len(des[0]))

    for row in rows:
        for i, r in enumerate(row):
            check_korean(str(r))
            sz = len(str(r))
            if colsize[i] < sz:
                colsize[i] = sz

    lines = []
    pstr = ""
    lows = ""
    for c in colsize:
        pstr += '+'
        for i in range(int(c+2)):
            pstr += "-"
        lows += "| %-" + str(c+1) + "s"
    pstr += "+"
    lows += "|"

    lines.append(pstr)
    lines.append(lows % tuple(header))
    lines.append(pstr)

    for r in rows:
        lines.append(lows % tuple(r))
    lines.append(pstr)
        
    for line in lines:
        print(line)

def check_korean(kstr):
    p = re.compile('[ㄱ-힣]')
    r = p.search(kstr)
    if r is None:
        return False
    else:
        return True

def main():
    try:
        filename = sys.argv[1]
        info = sys.argv[2]
        tags = sys.argv[3]
    except IndexError:
        print("Not read file")

    properties = configparser.ConfigParser()
    properties.read('cctv_config.ini')
    conf = properties["default"]

    db = connect_db(conf)
    if info == 'camera': 
        read_camera_csv(filename, conf)

        if tags == "add":
            add_camera_info(db, conf)

        if tags == "del":
            delete_camera_info(db)

        if tags == "sel":
            select_camera_info(db)

        if tags == "act":
            update_camera_info(db, 'A')

        if tags == "sby":
            update_camera_info(db, 'S')

    elif info == 'extern':
        read_extern_csv(filename, conf)

        if tags == "add" or tags == "add2":
            add_extern_info(db, conf, tags)

        if tags == "sel":
            select_extern_info(db, tags)

        if tags == "del":
            delete_extern_info(db)

        if tags == "act":
            update_extern_info(db, 'A')

        if tags == "sby":
            update_extern_info(db, 'S')

    elif info == 'broadcast':
        read_broadcast_csv(filename, conf)

        if tags == "sel":
            select_broadcast_info(db)

        if tags == "add":
            add_broadcast_info(db, conf)

        if tags == "del":
            delete_broadcast_info(db)

        if tags == "act":
            update_broadcast_info(db, 'A')

        if tags == "sby":
            update_broadcast_info(db, 'S')

    #select_db(db)

if __name__=='__main__':
    main()
