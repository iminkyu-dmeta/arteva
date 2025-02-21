#!/usr/bin/env python

import os, sys, datetime
import re
import csv
import pymysql
import subprocess
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, dump, ElementTree
#import pymysql

# Argument DATE
DATETIME=sys.argv[1]
dsize = len(DATETIME)
DATE=""
HOUR=""
if dsize == 8: 
    DATE = DATETIME
elif dsize == 10:
    HOUR = DATETIME[-2:]
    DATE = DATETIME[:-2]

SDATE = str(datetime.datetime.strptime(DATE, '%Y%m%d').date())

CDATE= datetime.datetime.now()
CHOUR = CDATE.strftime("%Y%m%d%H")

print('sdate: %s' % SDATE)

if HOUR:
    SHOUR = SDATE + ' ' + HOUR 
    EHOUR = SDATE + ' ' + HOUR 
else:
    SHOUR = SDATE + ' 00'
    EHOUR = SDATE + ' 23'

DIR="/logs/DC/report/"
EMSDBNAME="nemsdb"

# Presence NE list
NE=["PresenceEMS1", "PresenceEMS2", "Presence1", "Presence2", "XDMS1", "XDMS2", "PresenceDB1", "PresenceDB2", "XDMSDB1", "XDMSDB2"]

# NSTATDB SQL 
STAT_CPU_USAGE_FIVE="SELECT DATE_FORMAT(DTIME,'%Y-%m-%d-%H:%i') AS 'DATE', USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM nstatdb.STAT_CPU_USAGE_FIVE WHERE "
STAT_CPU_USAGE_HOUR="SELECT DATE_FORMAT(DTIME,'%Y-%m-%d-%H:00') AS 'DATE', USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM nstatdb.STAT_CPU_USAGE_HOUR WHERE "
STAT_MEM_USAGE_FIVE="SELECT DATE_FORMAT(DTIME,'%Y-%m-%d-%H:%i') AS 'DATE', USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM nstatdb.STAT_MEM_USAGE_FIVE WHERE "
STAT_MEM_USAGE_HOUR="SELECT DATE_FORMAT(DTIME,'%Y-%m-%d-%H:00') AS 'DATE', USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM nstatdb.STAT_MEM_USAGE_HOUR WHERE "
STAT_DISK_USAGE_HOUR="SELECT PART AS 'PART', USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM nstatdb.STAT_DISK_USAGE_HOUR WHERE "
STAT_DISK_USAGE_DAY="SELECT PART AS 'PART', USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM nstatdb.STAT_DISK_USAGE_DAY WHERE "

# ems release 3 database name(nemsdb)
DATE_SECTION="DTIME >= '" + SDATE + " 00:00:00.000' AND DTIME <= '" + SDATE + " 23:59:00.000'"
NE_SELECT_IP = "SELECT ip FROM nemsdb.ne WHERE name = '"
NE_SELECT_HOSTNAME = "SELECT hostname FROM nemsdb.ne WHERE name = '"
GROUP_BY="GROUP BY DATE_FORMAT(DTIME,'%Y-%m-%d %H:%i') ORDER BY DATE;"

CSCF_REMOTE_TYPE="CSCF"
ADMIN_REMOTE_TYPE="ADMIN"
UE_REMOTE_TYPE="UE"
PS_SIP_MESSAGE=["REGISTER", "PUBLISH", "SUBSCRIBE", "NOTIFY", "RLS-SUBSCRIBE", "RLS-NOTIFY"]
PS_XCAP_MESSAGE=["XCAP-PUT", "XCAP-DEL"]
XDMS_SIP_MESSAGE=["DIFF-SUBSCRIBE", "DIFF-NOTIFY"]
XDMS_XCAP_MESSAGE=["XCAP-PUT", "XCAP-GET", "XCAP-DEL", "SYNC-PUT"]

# EMS release 3 database name(nemsdb)
NE_SELECT_IP = "SELECT ip FROM nemsdb.ne WHERE name = '"
FAULT = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status', B.name AS 'Node Name' , B.ip AS 'IP', C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time', C.clear_time AS 'Clear Time' FROM nemsdb.fault AS C LEFT JOIN nemsdb.ne AS B ON C.ne_id = B.id "
FAULT_DATE = " WHERE C.event_time >= '" + SDATE + " 00:00:00' AND C.event_time <= '" + SDATE + " 23:59:59'  ORDER BY C.event_time;"
COMMONPATH = os.path.join('common', 'usr', 'sbin')

class DBAcc:
    def __init__(self, user, passwd, host, db):
        config = {
                'host':host,
                'user':user,
                'passwd':passwd,
                'database':db,
                'port':3306,
                'charset':'utf8'
        }

        self.conn = pymysql.connect(**config)
        self.curs = self.conn.cursor()

    def selectDB(self, sql=None, fetchall=False):
        self.curs.execute(sql)
        if fetchall:
            result = self.curs.fetchall()
        else:
            result = self.curs.fetchone()

        return result

    def insertDB(self, sql=None):
        print("ToBe")

    def closeDB(self):
        self.conn.close()

def CheckOutput(cmd, shell=False):
    ''' command [] '''
    ''' Return result '''
    cmd = " ".join(cmd)

    try:
        output = subprocess.check_output(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        ERROR(e)
        return None

    return output.rstrip()

def findfield(sql, result):
    fstr = '(AS )\'([A-Za-z]+)[_]([A-Za-z0-9]+)|(AS )\'([A-Za-z0-9]+)'
    findstr = re.findall(fstr, sql)

    collist = []
    for col in findstr:
        if col[0]:
            name = col[1] + "_" + col[2]
            collist.append(name)
        else:
            name = col[4]
            collist.append(name)

    lsize = len(collist)
    colsize = []
    for idx, cl in enumerate(collist):
        sz = len(cl)
        colsize.append(sz)
    for rows in result:
        for idx, row in enumerate(rows):
            sz = len(str(row))
            if colsize[idx] < sz:
                colsize[idx] = sz

    return collist, colsize

def display(data, field, size):
    LogLevel = 'info'
    pstr = ""
    lows = ""
    fids = ""
    fsz = len(field)
    lines = []

    for idx, sz in enumerate(size):
        lows += " %-" + str(sz+1) + "s"

    for row in data:
        lines.append(lows % tuple(row))
        if LogLevel == 'debug':
            print(lows % tuple(row))

def create_response(TABLE, db, distinct=False):
    res_status = ['req', 'res_success', 'res_fail', 'res_etc']
    response = ['res_200', 'res_400', 'res_401', 'res_403', 'res_404', 'res_406', 'res_408', 'res_409', 'res_412', 'res_415', 'res_421', 'res_423', 'res_480', 'res_481', 'res_500', 'res_503', 'res_506']

    # response
    RESPONSE_ITEM = "SELECT DISTINCT STATUS_ITEM FROM nstatdb." + TABLE + " ORDER BY STATUS_ITEM ASC;"
    STATUS_ITEM = db.selectDB(RESPONSE_ITEM, True)

    ITEM = []
    for i in STATUS_ITEM:
        ITEM.append(i[0])

    #ITEM = STATUS_ITEM.split('\n')
    for item in res_status:
        if item in ITEM:
            ITEM.remove(item)
        else:
            continue

    if distinct == True:
        ALIASSTART = "sum(if (STATUS_ITEM = 'req' , count , 0)) AS 'req', \
                sum(if(STATUS_ITEM = 'res_success' , count , 0)) AS 'res_success', \
                sum(if (STATUS_ITEM = 'res_fail' , count , 0)) AS 'res_fail', "
        ALIASEND = "sum(if (STATUS_ITEM = 'res_etc' , count , 0)) AS 'res_etc'"
        RESPONSE = ALIASSTART
        
        ITEM_SIZE=len(ITEM)
        if ITEM_SIZE > 0:
            for idx,item in enumerate(ITEM):
                if item.startswith('res_') and item[4].isdigit():
                    RESPONSE += "sum(if (STATUS_ITEM = '" + item + "' , count , 0)) AS '" + item + "', "
        RESPONSE += ALIASEND

        return RESPONSE

    else:
        for item in response:
            if item in ITEM:
                ITEM.remove(item)
            else:
                continue
        SIZE = len(ITEM)
        if SIZE > 1:
            for add in ITEM:
                if 'STATUS_ITEM' in add:
                    continue
                else:
                    response.append(add)

            response.sort()

        RESPONSE = "sum(if (STATUS_ITEM = 'req' , count , 0)) AS 'req', \
                sum(if (STATUS_ITEM = 'res_success' , count , 0)) AS 'res_success', \
                sum(if (STATUS_ITEM = 'res_fail' , count , 0)) AS 'res_fail',"

        for res in response:
            RESPONSE = RESPONSE + " sum(if (STATUS_ITEM = '" + res + "' , count , 0)) AS '" + res + "',"

        RESPONSE = RESPONSE + "sum(if (STATUS_ITEM = 'res_etc' , count , 0)) AS 'res_etc'"
        
        return RESPONSE

#####################################################################################
# CSV FILE Write
#####################################################################################
def writecsvfile(name, output, field, datedir=None, opt=None):

    if opt == 'ondemand':
        name = '-ondemand.'.join(name.split('.'))

    if datedir:
        fpath = os.path.join(DIR, datedir, name)
    else:
        fpath = os.path.join(DIR, name)

    print(fpath)
    rows = list(output)

    for a in range(len(rows)):
        rows[a] = list(rows[a])

    with open(fpath, "w") as f :
        wr = csv.writer(f)
        wr.writerow(field)
        for i in range(len(rows)):
            wr.writerow(rows[i])
        f.close()

#####################################################################################
# Get HOSTNAME 
#####################################################################################
def get_hostname_snmp(ne):
    ## Selct NE IP
    HOST_QUERY = MYSQL + NE_SELECT_IP + ne + "';\""
    HOST_IP = os.popen(HOST_QUERY).read().replace("ip", "").strip()
    HOSTNAME = os.popen("snmpwalk -v 2c " + HOST_IP + ":2161 -c public SNMPv2-MIB::sysName | awk '{print $4}'").read().rstrip()
    return HOSTNAME

def get_hostname_ne(ne, db):
    HOST_QUERY = NE_SELECT_HOSTNAME + ne + "';"
    HOSTNAME = db.selectDB(HOST_QUERY, False)
    return HOSTNAME[0]

def check_ems_version():
    version = ""
    filename = os.path.join('/', 'apps', 'RCS', 'clay', 'claycommon', 'service.xml')
    doc = ET.parse(filename)
    root = doc.getroot()

    for child in root:
        if child.get('id') == 'nems':
            version = child.get('path').split('/')[4][4:5]
            print(version)

    return version

#####################################################################################
# Get VM HOSTNAME 
#####################################################################################
def get_hostname_vm(table, remote, message, db) :
    HOST = table + DATE_SECTION + " AND REMOTE_TYPE = '" + remote + "' AND PROT_METHOD = '" + message + "' LIMIT 1;"
    HOSTNAME = db.selectDB(HOST, False)
    return HOSTNAME
 
def resource_stat(cycle, db=None, opt=None):
    global DATE_SECTION

    STAT_DISK_USAGE=""
    if cycle == 'hourly':
        DATE_SECTION = "DTIME >= '" + SHOUR + ":00:00.000' AND DTIME <= '" + EHOUR + ":59:00.000'"

    # 1. CPU
    for ne in NE :
        CPU_SQL=STAT_CPU_USAGE_FIVE + DATE_SECTION + " AND NTSID = '" + ne + "' ORDER BY DTIME;"
        output = db.selectDB(CPU_SQL, True)
        flist, fsize  = findfield(CPU_SQL, output)
        if cycle == 'hourly':
            writecsvfile("presence-" + get_hostname_ne(ne, db) + "-hourly-stat-cpu-" + DATETIME + ".csv", output, flist, DATETIME, opt)
        else:
            writecsvfile("presence-" + get_hostname_ne(ne, db) + "-stat-cpu-" + DATETIME + ".csv", output, flist, DATETIME, opt)

    # 2. MEMORY
    for ne in NE :
        MEM_SQL=STAT_MEM_USAGE_FIVE + DATE_SECTION + " AND NTSID = '" + ne + "' ORDER BY DTIME;"
        output = db.selectDB(MEM_SQL, True)
        flist, fsize  = findfield(MEM_SQL, output)
        if cycle == 'hourly':
            writecsvfile("presence-" + get_hostname_ne(ne, db) + "-hourly-stat-mem-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
        else:
            writecsvfile("presence-" + get_hostname_ne(ne, db) + "-stat-mem-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

    # 3. DISK
    if cycle == 'hourly':
        STAT_DISK_USAGE = STAT_DISK_USAGE_HOUR
        DATE_DAY = "DTIME = '" + EHOUR + ":00:00'"
        for ne in NE :
            DISK_SQL=STAT_DISK_USAGE + DATE_DAY + " AND NTSID = '" + ne + "' ORDER BY DTIME;"
            output = db.selectDB(DISK_SQL, True)
            flist, fsize  = findfield(DISK_SQL, output)
            writecsvfile("presence-" + get_hostname_ne(ne, db) + "-hourly-stat-disk-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
    else:
        STAT_DISK_USAGE = STAT_DISK_USAGE_DAY
        DATE_DAY = " DTIME = '" + SDATE + " 00:00:00'"
        for ne in NE :
            DISK_SQL=STAT_DISK_USAGE + DATE_DAY + " AND NTSID = '" + ne + "' ORDER BY DTIME;"
            output = db.selectDB(DISK_SQL, True)
            flist, fsize  = findfield(DISK_SQL, output)
            writecsvfile("presence-" + get_hostname_ne(ne, db) + "-stat-disk-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

#####################################################################################
# 4. STAT
## - Presence KPI
def presence_kpi_stat(TABLE, cycle, db, distinct=False, opt=None):
    RESPONSE = create_response(TABLE, db, distinct)
    TRAFFIC_RCS_PS_FIVE="SELECT DATE_FORMAT(DTIME,'%Y-%m-%d-%H:%i') AS 'DATE', " + RESPONSE + " FROM nstatdb.TRAFFIC_RCS_PS_FIVE WHERE "
    HOST_RCS_PS_FIVE="SELECT DISTINCT HOST FROM nstatdb.TRAFFIC_RCS_PS_FIVE WHERE "

    global DATE_SECTION

    if cycle == 'hourly':
        DATE_SECTION = "DTIME >= '" + SHOUR + ":00:00.000' AND DTIME <= '" + EHOUR + ":59:00.000'"

    for ps in PS_SIP_MESSAGE :
        PS_SQL=TRAFFIC_RCS_PS_FIVE + DATE_SECTION + "AND REMOTE_TYPE = '" + CSCF_REMOTE_TYPE + "' AND PROT_METHOD = '" + ps + "' " + GROUP_BY
        output = db.selectDB(PS_SQL, True)
        flist, fsize  = findfield(PS_SQL, output)
        host = get_hostname_vm(HOST_RCS_PS_FIVE, CSCF_REMOTE_TYPE, ps, db)
        if cycle == 'hourly':
            writecsvfile("presence-" + host[0] + "-hourly-kpi-" + ps + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
        else:
            writecsvfile("presence-" + host[0] + "-kpi-" + ps + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

    for xcap in PS_XCAP_MESSAGE :
        PS_SQL=TRAFFIC_RCS_PS_FIVE + DATE_SECTION + "AND REMOTE_TYPE = '" + ADMIN_REMOTE_TYPE + "' AND PROT_METHOD = '" + xcap + "' " + GROUP_BY
        output = db.selectDB(PS_SQL, True)
        flist, fsize  = findfield(PS_SQL, output)
        host = get_hostname_vm(HOST_RCS_PS_FIVE, ADMIN_REMOTE_TYPE, xcap, db)
        if cycle == 'hourly':
            writecsvfile("presence-" + host[0] + "-hourly-kpi-" + xcap + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
        else:
            writecsvfile("presence-" + host[0] + "-kpi-" + xcap + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

## - XDMS KPI
def xdms_kpi_stat(TABLE, cycle, db, distinct=False, opt=None):
    RESPONSE = create_response(TABLE, db, distinct)
    TRAFFIC_RCS_XDMS_FIVE="SELECT DATE_FORMAT(DTIME,'%Y-%m-%d-%H:%i') AS 'DATE', " + RESPONSE + " FROM nstatdb.TRAFFIC_RCS_XDMS_FIVE WHERE "
    HOST_RCS_XDMS_FIVE="SELECT DISTINCT HOST FROM nstatdb.TRAFFIC_RCS_XDMS_FIVE WHERE "
    PROCESS_SELECT = "SELECT version FROM nemsdb.process where name = 'rcs_xdms.exe' and ha_status = 1;"
    CKVERSION = PROCESS_SELECT
    REMOTE_TYPE = "CSCF"

    global DATE_SECTION

    if cycle == 'hourly':
        DATE_SECTION = "DTIME >= '" + SHOUR + ":00:00.000' AND DTIME <= '" + EHOUR + ":59:00.000'"

    for xdms in XDMS_SIP_MESSAGE :
        XDMS_SQL=TRAFFIC_RCS_XDMS_FIVE + DATE_SECTION + "AND REMOTE_TYPE = '" + REMOTE_TYPE + "' AND PROT_METHOD = '" + xdms + "' " + GROUP_BY
        output = db.selectDB(XDMS_SQL, True)
        flist, fsize  = findfield(XDMS_SQL, output)
        host = get_hostname_vm(HOST_RCS_XDMS_FIVE, CSCF_REMOTE_TYPE, xdms, db)
        if cycle == 'hourly':
            writecsvfile("presence-" + host[0] + "-hourly-kpi-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
        else:
            writecsvfile("presence-" + host[0] + "-kpi-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

    for xdms in XDMS_XCAP_MESSAGE :
        if xdms == 'XCAP-PUT' or xdms == 'XCAP-GET' or xdms == 'XCAP-DEL' :
            # ADMIN PUT
            XDMS_SQL=TRAFFIC_RCS_XDMS_FIVE + DATE_SECTION + "AND REMOTE_TYPE = '" + ADMIN_REMOTE_TYPE + "' AND PROT_METHOD = '" + xdms + "' " + GROUP_BY
            output = db.selectDB(XDMS_SQL, True)
            flist, fsize  = findfield(XDMS_SQL, output)
            host = get_hostname_vm(HOST_RCS_XDMS_FIVE, ADMIN_REMOTE_TYPE, xdms, db)
            if cycle == 'hourly':
                writecsvfile("presence-" + host[0] + "-hourly-kpi-" + ADMIN_REMOTE_TYPE + "-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
            else:
                writecsvfile("presence-" + host[0] + "-kpi-" + ADMIN_REMOTE_TYPE + "-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
            # UE PUT
            XDMS_SQL=TRAFFIC_RCS_XDMS_FIVE + DATE_SECTION + "AND REMOTE_TYPE = '" + UE_REMOTE_TYPE + "' AND PROT_METHOD = '" + xdms + "' " + GROUP_BY
            output = db.selectDB(XDMS_SQL, True)
            flist, fsize  = findfield(XDMS_SQL, output)
            host = get_hostname_vm(HOST_RCS_XDMS_FIVE, UE_REMOTE_TYPE, xdms, db)
            if cycle == 'hourly':
                writecsvfile("presence-" + host[0] + "-hourly-kpi-" + UE_REMOTE_TYPE + "-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
            else:
                writecsvfile("presence-" + host[0] + "-kpi-" + UE_REMOTE_TYPE + "-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

        elif xdms == 'SYNC-PUT' :
            # SYNC PUT
            XDMS_SQL=TRAFFIC_RCS_XDMS_FIVE + DATE_SECTION + "AND REMOTE_TYPE = '" + ADMIN_REMOTE_TYPE + "' AND PROT_METHOD = '" + xdms + "' " + GROUP_BY
            output = db.selectDB(XDMS_SQL, True)
            flist, fsize  = findfield(XDMS_SQL, output)
            host = get_hostname_vm(HOST_RCS_XDMS_FIVE, ADMIN_REMOTE_TYPE, xdms, db)
            if cycle == 'hourly':
                writecsvfile("presence-" + host[0] + "-hourly-kpi-" + ADMIN_REMOTE_TYPE + "-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
            else:
                writecsvfile("presence-" + host[0] + "-kpi-" + ADMIN_REMOTE_TYPE + "-" + xdms + "-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

#####################################################################################
# 5. Alarm History
def alarm_stat_nemsdb(cycle, db, opt=None):
    FAULT_DATE = " WHERE C.event_time >= '" + SHOUR + ":00:00' AND C.event_time <= '" + EHOUR + ":59:59'  ORDER BY C.event_time;"
    ALAR_SQL=FAULT + FAULT_DATE
    output = db.selectDB(ALAR_SQL, True)
    flist, fsize  = findfield(ALAR_SQL, output)
    HOST_SQL = "select hostname from nemsdb.ne where name = 'PresenceEMS1';"
    host = db.selectDB(HOST_SQL, False)
    if cycle == 'hourly':
        writecsvfile("presence-" + host[0] + "-hourly-kpi-stat-alarm-"+ DATETIME + ".csv", output, flist, DATETIME, opt)
    else:
        writecsvfile("presence-" + host[0] + "-kpi-stat-alarm-"+ DATETIME + ".csv", output, flist, DATETIME, opt)

# clay non root
def commandpath(command):
    clayhome, claylog, user = readclayconf()
    path = os.path.join(clayhome, COMMONPATH)
    cpath = os.path.join(path, command)
    if os.path.isfile(cpath):
        return cpath

    else:
        return command

def readclayconf():
    filename = 'clay.conf'
    path = '~/etc/clay'
    cpath = os.path.join(path, filename)

    if not os.path.isfile(cpath):
        cpath = '/etc/clay/clay.conf'

    with open(cpath, 'r') as cf:
        reader = cf.readline()
        for line in reader:
            if 'CLAYHOME' in line:
                CLAYHOME = line.split('=')[1]
            else:
                CLAYHOME = "/apps/RCS"

            if 'CLAYLOG' in line:
                CLAYLOG = line.split('=')[1]
            else:
                CLAYLOG= "/logs/RCS"
            if 'export SOCKET_FILE_OWN_GROUP' in line:
                USER = line.split('=')[1]
            else:
                USER = "attps"

    return CLAYHOME, CLAYLOG, USER

#####################################################################################
# RUN MAIN 
#####################################################################################
def main():
    distinct = True
    cycle = 'daily'
    opt = ""
    try :
        cycle = sys.argv[2]
        opt = sys.argv[3]
        distinct = sys.argv[4]
    except IndexError :
        print(cycle)
        print(opt)
        print(distinct)

    reportdir = os.path.join(DIR, DATETIME)
    if not os.path.isdir(reportdir) :
        os.mkdir(reportdir)

    nconfigurepath = commandpath('nconfigure')
    cmduser = [nconfigurepath, 'get', 'nems', 'database', 'db.user']
    user = str(CheckOutput(cmduser, shell=True), 'utf-8')
    cmdpasswd = [nconfigurepath, 'get', 'nems', 'database', 'db.password']
    passwd = str(CheckOutput(cmdpasswd, shell=True), 'utf-8')
    cmdhost = [nconfigurepath, 'get', 'nems', 'database', 'db.host']
    hostip = str(CheckOutput(cmdhost, shell=True), 'utf-8')
    if hostip == 'localhost':
        hostip = '127.0.0.1'
    cmdname = [nconfigurepath, 'get', 'nems', 'database', 'db.name']
    dbname = str(CheckOutput(cmdname, shell=True), 'utf-8')

    db = DBAcc(user, passwd, '127.0.0.1', dbname)

    version = check_ems_version()
        
    resource_stat(cycle, db, opt)

    presence_kpi_stat('TRAFFIC_RCS_PS_FIVE', cycle, db, distinct, opt)
    
    xdms_kpi_stat('TRAFFIC_RCS_XDMS_FIVE', cycle, db, distinct, opt)

    alarm_stat_nemsdb(cycle, db, opt)

    #os.system("chown -R attps:attps " + DIR)

if __name__=='__main__':
    main()
