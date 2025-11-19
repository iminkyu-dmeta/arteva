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

## dmeta_arteva sql 
import arsql

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

        num = 1
        for row in reader:
            if row[11]: 
                sql_row = [
                        'CCTV' + str(num).zfill(3),         # CCTV name
                        row[8],                             # URL
                        conf["ACTIVE"],                     # Active
                        conf["RESOLUTION"],                 # Resolution(FHD)
                        row[2] + " 역사, \n카메라 이름: " + row[3] + ", \n용도: " + row[12],    # comment
                        now,                                # create_time 
                        now,                                # update_time
                        conf["adminuser"],                  # create_user
                        conf["adminuser"],                  # update_user
                        row[11]                             # event_type
                    ]
                camera_sql_rows.append(sql_row)

                num+=1

    for l in camera_sql_rows:
        print(l)

    sys.exit(0)

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

def select_db(db):
    desc, rows = db.select_sql(arsql.LAST_INSERT_SQL)

    return rows 

def add_camera_info(db, conf):
    ## Check CCTV INFO
    desc, rows = db.select_sql(arsql.COUNT_CAMERA_INFO_SQL)
    user = conf["adminuser"]

    if int(rows[0]) > 0:
        des, res = db.select_sql(arsql.SELECT_FULL_CAMERA_INFO_SQL, fetchall=True)
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
        db.insert_args_sql(arsql.INSERT_CAMERA_INFO_SQL, tuple(row))

        '''
        CAMERA_ID
        EVENT TYPE 
        DATETIME
        USER
        '''
        ### Insert t_arteva_camera_info
        cctv_id = int(re.sub(r'[^0-9]', '', row[0]))
        print("CCTV ID: %s" % cctv_id)
        SQL = arsql.INSERT_CAMERA_EVENT_SQL + arsql.SELECT_EVENT_CONF_SQL.format(cctv_id, event_type, now, now, user, user)
        print(SQL)
        db.insert_args_sql(SQL)

        time.sleep(2)
        
    select_camera_info(db)

def delete_camera_info(db):
    '''
    '''
    desc, rows = db.select_sql(arsql.SELECT_CAMERA_INFO_SQL, fetchall=True)

    for row in rows:
        print("Delete CCTV : %s" % row[0])
        db.delete_sql(arsql.DEL_CAMERA_INFO_SQL.format(row[0]))
        db.delete_sql(arsql.DEL_CAMERA_EVENT_CONF.format(row[0]))

    db.delete_sql(arsql.ALTER_CAMERA_INFO_AUTO_INCREMENT_INIT)

    select_camera_info(db)
    
def update_camera_info(db, status):
    if status == 'A':
        srh = 'S'
    elif status == 'S':
        srh = 'A'

    desc, rows = db.select_sql(arsql.SELECT_CAMERA_STATUS.format(srh), fetchall=True)
    if rows:
        for row in rows:
            db.insert_args_sql(arsql.UPDATE_CAMERA_ACTIVE.format(status, row[0]))

def update_broadcast_camera_info(db):
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

def select_camera_info(db):
    info_desc, info_rows = db.select_sql(arsql.SELECT_FULL_CAMERA_INFO_SQL, fetchall=True)
    conf_desc, conf_rows = db.select_sql(arsql.SELECT_FULL_CAMERA_EVENT_CONF_SQL, fetchall=True)
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

    desc, rows = db.select_sql(arsql.COUNT_EXTERN_INFO_SQL)

    if int(rows[0]) > 0:
        desc, rows = db.select_sql(arsql.SELECT_FULL_EXTERN_SQL, fetchall=True)
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
            db.insert_args_sql(arsql.INSERT_EXTERN_INFO_SQL.format(now, user), tuple(row))
    
    print()
    select_extern_info(db)

def delete_extern_info(db):
    '''
    '''
    desc, rows = db.select_sql(arsql.SELECT_FULL_EXTERN_SQL, fetchall=True)

    for row in rows:
        print("Delete Extern System: %s" % row[1])
        db.delete_sql(arsql.DEL_EXTERN_INFO_SQL.format(row[0]))

    db.delete_sql(arsql.ALTER_EXTERN_INFO_AUTO_INCREMENT_INIT)

    select_extern_info(db)

def update_extern_info(db, status):
    if status == 'A':
        srh = 'S'
    elif status == 'S':
        srh = 'A'

    desc, rows = db.select_sql(arsql.SELECT_EXTERN_STATUS.format(srh), fetchall=True)
    if rows:
        for row in rows:
            db.insert_args_sql(arsql.UPDATE_EXTERN_ACTIVE.format(status, row[0]))

def select_extern_info(db):
    desc, rows = db.select_sql(arsql.SELECT_FULL_EXTERN_SQL, fetchall=True)
    display_select(desc, rows)

def add_broadcast_info(db, conf):
    user = conf["adminuser"]

    desc, rows = db.select_sql(arsql.COUNT_BROADCAST_INFO_SQL)

    if int(rows[0]) > 0:
        desc, rows = db.select_sql(arsql.SELECT_FULL_BROADCAST_SQL, fetchall=True)
        display_select(desc, rows)
        exit(1)

    desc, extern_id = db.select_sql(arsql.SELECT_EXTERN_INFO_BC)
    if extern_id:
        print("Broadcast System Registration Start ")
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
            print(arsql.INSERT_BROADCAST_INFO_SQL.format(now, user, e_id))
            print(row)
            db.insert_args_sql(arsql.INSERT_BROADCAST_INFO_SQL.format(now, user, e_id), tuple(row))
    else:
        print("register broadcast server(extern)")
        sys.exit(0)

    select_broadcast_info(db)

def delete_broadcast_info(db):
    '''
    '''
    desc, rows = db.select_sql(arsql.SELECT_FULL_BROADCAST_SQL, fetchall=True)

    for row in rows:
        print("Delete Broadcast Text: %s" % row[1])
        db.delete_sql(arsql.DEL_BROADCAST_INFO_SQL.format(row[0]))

    db.delete_sql(arsql.ALTER_BROADCAST_INFO_AUTO_INCREMENT)

    select_broadcast_info(db)

def update_broadcast_info(db, status):
    if status == 'A':
        srh = 'S'
    elif status == 'S':
        srh = 'A'

    desc, rows = db.select_sql(arsql.SELECT_BROADCAST_STATUS.format(srh), fetchall=True)
    if rows:
        for row in rows:
            db.insert_args_sql(arsql.UPDATE_BROADCAST_ACTIVE.format(status, row[0]))

def select_broadcast_info(db):
    desc, rows = db.select_sql(arsql.SELECT_FULL_BROADCAST_SQL, fetchall=True)
    display_select(desc, rows)

def display_select(desc, rows):
    ## read description and print Field name, size
    kv = {}
    lines = []
    pstr = []
    lows = ""

    for dc in desc:
        print(dc)
        kv[dc[0].upper()] = len(dc[0])

    for rw in rows:
        for i, k in enumerate(kv.keys()) :
            if len(str(rw[i])) > kv[k] :
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

def check_korean(kstr):
    p = re.compile('[ㄱ-힣]')
    r = p.search(kstr)
    if r is None:
        return False
    else:
        return True

def main():
    if len(sys.argv) < 4 :
        print("./register_cctv.py filename [camera|extern|broadcast] [sel|add|del|act|sby]")
        sys.exit(1)

    try:
        filename = sys.argv[1]
        info = sys.argv[2]
        tags = sys.argv[3]
    except IndexError:
        print("Not read file")

    properties = configparser.ConfigParser()
    properties.read('cctv_config.ini')
    conf = properties["default"]

    read_camera_csv(filename, conf)

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

        if tags == "add" :
            add_extern_info(db, conf, tags)

        if tags == "sel":
            select_extern_info(db)

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
