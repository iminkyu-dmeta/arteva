#!/usr/bin/python3

import os, sys, re
import json
import difflib
import pymysql
import platform
import socket
import hashlib
import time
import argparse
import subprocess
import shutil
from pwd import getpwnam
from datetime import datetime
from datetime import date
from datetime import timedelta
from dateutil import parser
import urllib.parse
import xml.etree.ElementTree as ET
import csv
import itertools
import glob

from pysnmp.hlapi import *
from pysnmp import debug

try:
            import http.client as httplib
except:
            import httplib

## Write File Path
#BDIR=os.path.join('/', 'apps', 'RCS', 'util', 'proactive')
BDIR=os.path.join('/', 'logs')

DIR=os.path.join(BDIR, 'DC')
RDIR=os.path.join(DIR, 'report')
GOLDDIR=os.path.join('/', 'logs', 'CM')

#NDATE=date.today()
DATE=datetime.now()

PERIOD = 30

CURHOUR = DATE.strftime("%H")
FDATE = DATE - timedelta(days=1)
FHOUR = DATE - timedelta(hours=1)

NW = "############################################################################"
NW2 = "\n############################################################################"
LINES = []

###  NEMS DB SQL ##
PROCESS_STATUS_SQL= "SELECT A.name AS 'NE Name', B.group AS 'Process Group', B.name AS 'Process Type', B.version AS 'Version', CASE WHEN B.start_time = 0 THEN '-' ELSE B.start_time END AS 'Start Time', CASE WHEN B.status = 1 THEN 'Active' ELSE 'Inactive' END AS 'Status', CASE WHEN B.ha_status = 1 THEN 'Active' WHEN B.ha_status = 0 THEN 'Standby' ELSE '-' END AS 'VRRP Status' FROM nemsdb.ne A, nemsdb.process B WHERE A.id = B.ne_id ORDER BY A.name, B.group, B.name;"

SELECT_ALARM_COLUMN = "C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status', B.name AS 'Node Name' , B.ip AS 'IP', C.entity AS 'Entity ', C.category AS 'Category', C.event_time AS 'Start Time', C.clear_time AS 'Clear Time', C.message AS 'Description'"

SELECT_ALARM_SQL = "SELECT CASE WHEN " + SELECT_ALARM_COLUMN + " FROM nemsdb.fault AS C LEFT JOIN nemsdb.ne AS B ON C.ne_id = B.id  WHERE C.event_time >= '{}' AND C.event_time < '{}' ORDER BY C.event_time;"
NOT_CLEAR_ALARM_SQL = "SELECT CASE WHEN " + SELECT_ALARM_COLUMN + " FROM nemsdb.fault C INNER JOIN nemsdb.ne B ON B.id = C.ne_id INNER JOIN nemsdb.ne_group A ON B.group_id = A.id WHERE C.clear_time is null AND C.event_time >= '{}' ORDER BY C.event_time;"

DEFAULT_RESPONSE_CODE = ['200', '201', '204', '400', '401', '403', '404', '406', '408', '409', '412', '415', '421', '423', '480', '481', '500', '503', '506', 'etc'] 
COLMN_RESPONSE = "sum(if (STATUS_ITEM = 'req' , count , 0)) AS 'req', sum(if(STATUS_ITEM = 'res_success' , count , 0)) AS 'res success', sum(if (STATUS_ITEM = 'res_fail' , count , 0)) AS 'res fail'"

SELECT_DTIME = "SELECT DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) AS 'DTIME', "
SELECT_DISTINCT = "SELECT DISTINCT HOST "
GROUPBY = " GROUP BY DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) ORDER BY DTIME;"

NE_NAME_SQL = "select name from ne order by id asc;"
NE_SELECT_HOSTNAME_SQL = "SELECT hostname FROM nemsdb.ne WHERE name = '{}'"

## Active Process IP, Hostname SELECT 
PROCESS_SELECT_SQL="select name, ip, hostname from ne where id IN (select ne_id from process where name = '{}' and start_time is not null and ha_status = 1);"


PROCESS_STAT_SQL_FSTR = '(AS )\'([A-Za-z]+)[ ]([A-Za-z0-9]+)|(AS )\'([A-Za-z0-9]+)'

## Resouce "2024-01-19 01"
RESOURCE_DICT = {'CPU': ['CPU', 'CPU'], 'MEM': ['Memory', 'MEMORY'], 'DISK': ['Disk', 'DISK']}

RESOURCE_FIELD1 = "DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) AS 'DTIME'"
RESOURCE_FIELD2 = "PART AS 'PART'"
SELECT_RESOURCE = "SELECT {}, USAGE_SUM/COUNT AS 'AVERAGE(%)', USAGE_MAX AS 'PEAK(%)' FROM "

### nstat DB SQL
RESOURCE_FIVE_STAT_SQL = SELECT_RESOURCE + "nstatdb.STAT_{}_USAGE_FIVE WHERE DTIME >= '{}' AND DTIME < '{}' AND NTSID = '{}' ORDER BY DTIME;"
RESOURCE_STAT_SQL = SELECT_RESOURCE + "nstatdb.STAT_{}_USAGE_{} WHERE DTIME = '{}' AND NTSID = '{}' ORDER BY DTIME;"

RESOURCE_PROCESS_FIVE_STAT_SQL = SELECT_RESOURCE + "nstatdb.STAT_PROCESS_{}_USAGE_FIVE WHERE DTIME >= '{}' AND DTIME < '{}' AND NENAME = '{}' AND PROCESS = '{}' ORDER BY DTIME;"
RESOURCE_PROCESS_STAT_SQL = SELECT_RESOURCE + "nstatdb.STAT_PROCESS_{}_USAGE_{} WHERE DTIME = '{}' AND NENAME = '{}' AND PROCESS = '{}' ORDER BY DTIME;"
RESOURCE_PROCESS_FIVE_DISTINCT_SQL = "SELECT DISTINCT PROCESS FROM nstatdb.STAT_PROCESS_{}_USAGE_FIVE WHERE NENAME = '{}' ORDER BY DTIME;"
RESOURCE_PROCESS_DISTINCT_SQL = "SELECT DISTINCT PROCESS FROM nstatdb.STAT_PROCESS_{}_USAGE_{} WHERE NENAME = '{}' ORDER BY DTIME;"

RSS_COLUMN = " sum({4}_REQ_COUNT) AS 'req', sum({4}_RES_SUCC_COUNT) AS 'res success', sum({4}_RES_FAIL_COUNT) AS 'res fail'"

###################################################################
## global vars 
NE = []
## clay 2.6.2-nr
CLAY_COMMAND_PATH = os.path.join('common', 'usr', 'sbin')

def golobal_vars(vnf):
    global COMMAND_ACTION
    global STAT_METHOD 
    global PROCESS_FIVE_STAT_SQL
    global PROCESS_FIVE_STAT_HOSTNAME_SQL
    global PROCESS_STAT_SQL
    global COLMN_RESPONSE

    if vnf == "presence":
        COMMAND_ACTION = {
            'rcs_ps.exe': ["DIS-REGI-COUNT", "CHECK-SYSTEMS", "DIS-DB-REPLICATION-STATUS"],
            'rcs_xdms.exe': ["COUNT-USER", "CHECK-SYSTEMS", "DIS-DB-REPLICATION-STATUS"]
        }
        for code in DEFAULT_RESPONSE_CODE:
            COLMN_RESPONSE += ", sum(if (STATUS_ITEM = 'res_" + code + "' , count , 0)) AS 'res " + code + "'"

        PROCESS_FIVE_STAT_SQL = SELECT_DTIME + COLMN_RESPONSE + " FROM nstatdb.TRAFFIC_RCS_{}_FIVE WHERE DTIME >= '{}' AND DTIME < '{}' AND REMOTE_TYPE = '{}' AND PROT_METHOD = '{}' " + GROUPBY
        PROCESS_FIVE_STAT_HOSTNAME_SQL = SELECT_DISTINCT + " FROM nstatdb.TRAFFIC_RCS_{}_FIVE WHERE DTIME >= '{}' AND DTIME < '{}' AND REMOTE_TYPE = '{}' AND PROT_METHOD = '{}' LIMIT 1;"
        PROCESS_STAT_SQL = SELECT_DTIME + COLMN_RESPONSE + " FROM nstatdb.TRAFFIC_RCS_{}_{} WHERE DTIME = '{}' AND REMOTE_TYPE = '{}' AND PROT_METHOD = '{}'" + GROUPBY

        STAT_METHOD = {
                'PS': {
                    'CSCF': ['REGISTER', 'PUBLISH', 'SUBSCRIBE', 'NOTIFY', 'RLS-SUBSCRIBE', 'RLS-NOTIFY']
                },
                'XDMS': {
                    'CSCF': ['DIFF-SUBSCRIBE', 'DIFF-NOTIFY'],
                    'admin': ['XCAP-PUT', 'XCAP-GET', 'XCAP-DEL'],
                    'UE': ['XCAP-PUT', 'XCAP-GET', 'XCAP-DEL']
                }
        }


    elif vnf == "recording":
        COMMAND_ACTION = {
                'rss.exe': ["DIS-NECHK-INFO"],
                'rms.exe': ["DIS-DB-REPLICATION-STATUS"]
        }

        PROCESS_FIVE_STAT_SQL = SELECT_DTIME + RSS_COLUMN + " FROM nstatdb.STAT_{0}_PROTOCOL_FIVE WHERE DTIME >= '{1}' AND DTIME < '{2}' " + GROUPBY
        PROCESS_FIVE_STAT_HOSTNAME_SQL = SELECT_DISTINCT + " FROM nstatdb.STAT_{0}_PROTOCOL_FIVE WHERE DTIME >= '{1}' AND DTIME < '{2}' LIMIT 1;"
        PROCESS_STAT_SQL = SELECT_DTIME + RSS_COLUMN + " FROM nstatdb.STAT_{0}_PROTOCOL_{1} WHERE DTIME = '{2}' " + GROUPBY

        STAT_METHOD = {
                'RSS': {
                    'MCPTT_MCVIDEO': ['SIP_INVITE'],
                    'MCDATA': ['SIP_MESSAGE'],
                    'GMS': ['SIP_SUBSCRIBE', 'SIP_NOTIFY', 'XCAP_GET'],
                    'PV': ['XCAP_PUT'],
                    'CS_GMS': ['HTTP_GET'],
                    'KMS': ['HTTP_POST']
                }
       }

###################################################################

class proactive:
    def __init__(self, opt_data, db, cycle):
        self.od = opt_data
        self.db = db
        self.cycle = cycle
        self.rdate= opt_data['cycle'][cycle]
        self.vnf = opt_data["vnf_info"]["vnf"]
        self.line = []
        self.var_name = {}

    def get_vars(self):
        return self.var_name

    def set_vars(self, unit):
        date_format = "%Y-%m-%d"
        if len(self.rdate) == 10:
            unit = [0, 1]
            hour_format = " %H"
            date_format += hour_format
        dformat = ''.join(re.split(r'-|\ ', date_format))

        START_DTIME = datetime.strptime(self.rdate, dformat)
        END_DTIME = datetime.strptime(self.rdate, dformat) + timedelta(days=unit[0], hours=unit[1])
        if len(self.rdate) == 10:
            ALARM_DATE = START_DTIME - timedelta(hours=1)
        else:
            ALARM_DATE = START_DTIME - timedelta(days=PERIOD)
	
        print("{} {} ".format(START_DTIME, END_DTIME))

        self.var_name['RS_FIELD_CPU'] = RESOURCE_FIELD1 
        self.var_name['RS_FIELD_MEM'] = RESOURCE_FIELD1
        self.var_name['RS_FIELD_DISK'] = RESOURCE_FIELD2
        self.var_name['START_DTIME'] = START_DTIME
        self.var_name['END_DTIME'] = END_DTIME 
        self.var_name['ALARM_DATE'] = ALARM_DATE

        ## colection Proactive monitoring 
        self.append_title(datetime.strptime(self.rdate, dformat).strftime(date_format), NW, NW)

    def command_action(self):
        '''
        # dict COMMAND_ACTION
        #{'process name': ['command1', ...]}
        '''
        for process, cmdact in COMMAND_ACTION.items():
            self.line.append(process)
            SQL = PROCESS_SELECT_SQL.format(process)
            result = self.db.select_sql(SQL, False)
            if result:
                nename = result[0]
                hostip = result[1]
                hostname = result[2]

                for cmd in cmdact:
                    self.line.append(cmd)
                    result = get_command_action(hostip, '8800', process, cmd)
                    if xml_to_text(result):
                        self.line.append(urllib.parse.unquote_plus(xml_to_text(result)))
                    else:
                        self.line.append("Check the %s Process " % key)

            else:
                self.line.append("Check the %s Process " % process)
                self.line.append("\n")

        self.append_lines()

    def process_status(self):
        self.append_title('- Process Status\n1. Presence Process status check & Redundancy status check', NW)
        self.extend_lines(PROCESS_STATUS_SQL, True) 

    def alarm_check(self):
        self.append_title('- Alarm History\n1. System alarm check', NW2)
        self.append_lines()

        SQL = SELECT_ALARM_SQL.format(self.var_name['START_DTIME'], self.var_name['END_DTIME'])
        self.extend_lines(SQL, True)

        report_file_name = [self.vnf, platform.node(), 'kpi', 'stat', 'alarm', self.rdate]
        self.write_report(report_file_name, SQL, True)

        self.append_title('2. System alarm check(Not Clear Alarm)', NW2)

        self.extend_lines(NOT_CLEAR_ALARM_SQL.format(self.var_name['ALARM_DATE']), True)
        self.append_lines()

    def resource_statistics(self):
        self.append_title('- Resource Statistics', NW2)
        self.append_lines()

        idx=1
        for tab in self.od["stat_vm_resource"]:
            RS = tab.split('_')[-2]

            if RS == "NETINTERFACE":
                continue
            self.line.append("{}. {} statistics".format(str(idx), RESOURCE_DICT[RS][0]))

            idx += 1
            self.append_lines()
            for name in NE:
                self.line.append("{} : {}".format(name, RESOURCE_DICT[RS][1]))

                ## report file name list
                ## vnf-hostname-stat-resource-data.csv
                report_file_name = [self.vnf, select_ne_hostname(self.db, name), 'stat', RS.lower(), self.rdate]

                if RS != 'DISK':
                    # (select column , resource, start, end, ne name)
                    SQL=RESOURCE_FIVE_STAT_SQL.format(self.var_name['RS_FIELD_' + RS], RS, self.var_name['START_DTIME'], self.var_name['END_DTIME'], name)
                    self.extend_lines(SQL, True)

                    self.write_report(report_file_name, SQL, True)

                # (select column , resource, cycle, start, ne name)
                DSQL=RESOURCE_STAT_SQL.format(self.var_name['RS_FIELD_' + RS], RS, self.cycle, self.var_name['START_DTIME'], name)
                self.extend_lines(DSQL, True)
                if RS == 'DISK':

                    self.write_report(report_file_name, DSQL, True)

                self.line.append("")
            self.line.append("")
        self.append_lines()

        ## process resource cpu, memory (add monitoring)
        if self.od["process_resource"]:
            for tab in self.od["stat_process_resource"]:
                RS = tab.split('_')[-2]
                self.line.append("{}. Process {} statistics".format(str(idx), RS))
                idx += 1
                self.append_lines()

                for name in NE:
                    # select vnfc process name
                    pname_list = self.select_ne_pname(RS, name)
                    for pname in pname_list:
                        self.line.append("{} : {}({})".format(name, RS, pname))

                        # (vnf, hostname , stat, resource, process name, date)
                        report_file_name = [self.vnf, select_ne_hostname(self.db, name), 'stat', RS.lower(), pname, self.rdate]

                        # (select column, resource, start, end, vnfc name, process name)
                        SQL=RESOURCE_PROCESS_FIVE_STAT_SQL.format(self.var_name['RS_FIELD_' + RS], RS, self.var_name['START_DTIME'], self.var_name['END_DTIME'], name, pname)
                        self.extend_lines(SQL, True)

                        self.write_report(report_file_name, SQL, True)

                        # (select column, resource, cycle, start, vnfc name, process name)
                        DSQL=RESOURCE_PROCESS_STAT_SQL.format(self.var_name['RS_FIELD_' + RS], RS, self.cycle, self.var_name['START_DTIME'], name, pname)
                        self.extend_lines(DSQL, True)

                    self.line.append("")

                self.line.append("")
            self.append_lines()

    def process_statistics(self):
        self.append_title('- Call Processing Statistics', NW2)
        self.append_lines()
        '''
        # dict STAT_METHOD
        ## {'PS': {remote}: ['method1', ...]
        '''
        idx=1
        for application, remote in STAT_METHOD.items():
            for remote_type, prot_method in remote.items():
                for method in prot_method:
                    self.line.append("{}. {} by {}".format(str(idx), method, remote_type))
                    idx += 1

                    # (application name, start, end, remote type, method)
                    STAT_FIVE_SQL= PROCESS_FIVE_STAT_SQL.format(application, self.var_name['START_DTIME'], self.var_name['END_DTIME'], remote_type, method)
                    self.extend_lines(STAT_FIVE_SQL, True)

                    # select hostname
                    # (application name, start, end, remote type, method)
                    DISTINCT_SQL = PROCESS_FIVE_STAT_HOSTNAME_SQL.format(application, self.var_name['START_DTIME'], self.var_name['END_DTIME'], remote_type, method)

                    hostname = select_vm_hostname(self.db, DISTINCT_SQL)
                    if hostname:
                        if 'admin' == remote_type or 'UE' == remote_type:
                            report_file_name = [self.vnf, select_vm_hostname(self.db, DISTINCT_SQL), 'kpi', remote_type, method, self.rdate]
                        else:
                            report_file_name = [self.vnf, select_vm_hostname(self.db, DISTINCT_SQL), 'kpi', method, self.rdate]
                        self.write_report(report_file_name, STAT_FIVE_SQL, True)

                    SQL=PROCESS_STAT_SQL.format(application, self.cycle, self.var_name['START_DTIME'], remote_type, method)
                    self.extend_lines(SQL, True)
                    self.line.append("")

                    self.append_lines()

    def gold_config(self):
        self.append_title('Presence Gold Parameter', NW)

        find_file = find_latest_file(GOLDDIR, 'GoldConfig-*')
        lines = read(find_file)

        self.line.append(lines)

        self.append_lines()

    def naming_rule(self, bdir, file_name, file_type):
        #{VNF}-{HOSTNAME}-[hourly|]-monitoring-YYYYMMDDHH.txt
        if self.cycle == "HOUR":
            file_name.insert(2, 'hourly')

        if self.od["option"]:
            file_name.append('ondemand')

        file_name = os.path.join(bdir, '-'.join(file_name) + '.' + file_type)

        return file_name

    def write_monitoring_file(self):
        monitoring_file_name = [self.vnf, platform.node(), 'monitoring', self.rdate]
        file_name = self.naming_rule(DIR, monitoring_file_name, 'txt')

        with open(file_name, 'w') as wf:
            wf.writelines('\n'.join(LINES))

        LINES.clear() 

    def select_rows(self, SQL, fetchall=None):
        result = self.db.select_sql(SQL, fetchall)
        fieldlist, fieldsize  = sql_field(PROCESS_STAT_SQL_FSTR, SQL, result)


        return result, fieldlist, fieldsize

    def append_title(self, title, openline=None, closeline=None):
        if openline:
            self.line.append(openline)
        self.line.append(title)
        if closeline:
            self.line.append(closeline)

    def append_lines(self):
        LINES.extend(self.line)
        self.line.clear()

    def extend_lines(self, SQL, fetchall=None):
        result, fieldlist, fieldsize = self.select_rows(SQL, fetchall)

        self.line.extend(display_select(result, fieldlist, fieldsize))

    def extend_stat_lines(self, SQL, fetchall=None):
        result, fieldlist, fieldsize = self.select_rows(SQL, fetchall)

        if result:
            self.line.extend(display_select(result, fieldlist, fieldsize))
        else:
            self.line.append("Empty rows \n" + SQL)

    def write_report(self, file_name, SQL, fetchall=None):
        fname = self.naming_rule(os.path.join(RDIR, self.rdate), file_name, 'csv')
        result, fieldlist, fieldsize = self.select_rows(SQL, fetchall)

        for cycle, fdate in self.od['cycle'].items():
            if not os.path.isdir(os.path.join(RDIR, fdate)):
                os.mkdir(os.path.join(RDIR, fdate))

        write_to_csvfile(fname, result, fieldlist)

    def select_ne_pname(self, rs, name):
        SQL = RESOURCE_PROCESS_FIVE_DISTINCT_SQL.format(rs, name)
        result = self.db.select_sql(SQL, True)

        pname_list = []
        for pname in list(result):
            pname_list.append(pname[0])

        return pname_list

class mysqlDBAcc:
    def __init__(self, config):
        self.conn = pymysql.connect(**config)
        self.curs = self.conn.cursor()

    def select_sql(self, sql=None, fetchall=False, size=None):
        self.curs.execute(sql)

        if fetchall:
            result = self.curs.fetchall()
        elif not fetchall and size:
            result = self.curs.fetchmany(size)
        else:
            result = self.curs.fetchone()

        return result 

    def instart_sql(self, sql=None, many=None):
        if many:
            self.curs.executemany(sql, many)
        else:
            self.curs.execute(sql)


        self.conn.commit()

    def close_conn(self):
        self.conn.close()

def get_command_action(remoteip, port, name=None, command=None) :
    if command:
        params = urllib.parse.urlencode({'id': name, 'command': command})

    headers = {"Host": remoteip + ":" + port,
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "User-Agent": "proactive-mornitoring",
                "Accept": "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
                "Connection": "keep-alive"
    }
    try:
        conn = httplib.HTTPConnection(remoteip, port)
        conn.request("GET", "/polling.xml?" + params, "" ,headers)
        response = conn.getresponse()
        body = response.read()
        return body
    except (httplib.HTTPException, socket.error) as ex :
        print("ERROR: %s" % ex)
        return 0

def delete_old_files(keepday):
    delete_dir(RDIR, keepday)
    delete_file(DIR, keepday)
    sys.exit(0)    

def select_ne_hostname(db, ne):
    SQL = NE_SELECT_HOSTNAME_SQL.format(ne)
    HOSTNAME = db.select_sql(SQL, False)
    return HOSTNAME[0]

def select_vm_hostname(db, SQL):
    hostname = db.select_sql(SQL, False)

    if hostname:
        return hostname[0]
    else:
        return None

def delete_file(path, keepday):
    today = datetime.today()
    for root, directories, files in os.walk(path, topdown=False):
        for name in files:
            t = os.stat(os.path.join(root, name))[8]
            filetime = datetime.fromtimestamp(t) - today
            if filetime.days <= -keepday:
                print(os.path.join(root, name), filetime.days)
                os.remove(os.path.join(root, name))

def delete_dir(path, keepday):
    today = datetime.today()
    for root, directories, files in os.walk(path, topdown=False):
        for name in directories:
            t = os.stat(os.path.join(root, name))[8]
            filetime = datetime.fromtimestamp(t) - today
            if filetime.days <= -keepday:
                print(os.path.join(root, name), filetime.days)
                try:
                    #os.rmdir(os.path.join(root, name))
                    shutil.rmtree(os.path.join(root, name), ignore_errors=True)
                except OSError as ex:
                    print(ex)

def create_dir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print('Error: creating directory %s' % path)

def check_output(cmd, shell=False):
    ''' command [] '''
    ''' Return result '''
    cmd = " ".join(cmd)

    try:
        output = subprocess.check_output(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        ERROR(e)
        return None

    return output.rstrip()

def system_output(cmd, shell=False):
    ''' command [] '''
    ''' Return result '''
    #cmd = " ".join(cmd)

    try:
        output = subprocess.check_output(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        ERROR(e)
        return None

    return output.rstrip()

def command_path(command, clayhome):
    path = os.path.join(clayhome, CLAY_COMMAND_PATH)
    cpath = os.path.join(path, command)
    if os.path.isfile(cpath):
        return cpath

    else:
        return command

def read_clay_conf():
    filename = 'clay.conf'
    path = '~/etc/clay'
    cpath = os.path.join(path, filename)

    if not os.path.isfile(cpath):
        cpath = '/etc/clay/clay.conf'

    with open(cpath, 'r') as cf:
        reader = cf.readlines()
        for line in reader:
            if 'CLAYHOME' in line:
                CLAYHOME = line.split('=')[1].rstrip('\n')
            if 'CLAYLOG' in line:
                CLAYLOG = line.split('=')[1].rstrip('\n')
            if 'export SOCKET_FILE_OWN_GROUP' in line:
                USER = line.split('=')[1].rstrip('\n')

    print("%s %s %s" % (CLAYHOME, CLAYLOG, USER))
    if not CLAYHOME:
        CLAYHOME = "/apps/RCS"
    if not CLAYLOG:
        CLAYLOG= "/logs/RCS"
    if not USER:
        USER = "attps"

    return CLAYHOME, CLAYLOG, USER

def xml_to_text(xmldata, url=None, node=None):
    try:
        tree = ET.fromstring(xmldata)
    except ValueError :
        xmlp = ET.XMLParser(encoding="utf-8")
        tree = ET.fromstring(xmldata, parser=xmlp)

    return tree.text

def read_xml(fname, element, attribute=None):
    tree = ET.parse(fname)
    root = tree.getroot()

    ele = tree.iter(tag=element)
    atb = []
    if attribute:
        for att in ele:
            atb.append(att.get(attribute))
    else :
        for att in ele:
            atb.append(att.text)
        
    return atb

def sql_field(fstr, sql, result):
    findstr = re.findall(fstr, sql)

    collist = []
    for col in findstr:
        if col[0]:
            name = col[1] + " " + col[2]
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

def display_select(data, field, size):
    pstr = ""
    lows = ""
    fids = ""
    fsz = len(field)
    lines = []

    for idx, sz in enumerate(size):
        pstr += '+'
        for i in range(int(sz+2)):
            pstr += '-'
        lows += "| %-" + str(sz+1) + "s"
    pstr += '+'
    lows += "|"

    lines.append(pstr)
    lines.append(lows % tuple(field))
    lines.append(pstr)

    if data:
        for row in data:
            lines.append(lows % tuple(row))

    lines.append(pstr)

    return lines

def read(fname):
    with open(fname, 'r') as f:
        readline = f.read()
        
    return readline

def read_line(fname):
    with open(fname, 'r') as f:
        readline = f.readline()

    return readline

def read_lines(fname):
    with open(fname, 'r') as f:
        readline = f.readlines()

    return readline

def find_latest_file(fdir, pattern):
    fpath = os.path.join(fdir, pattern)
    files = glob.glob(fpath)
    latest = max(files, key=os.path.getctime)

    return latest

def write_to_csvfile(fname, output, field, option=None):
    rows = list(output)
    for a in range(len(rows)):
        rows[a] = list(rows[a])

    with open(fname, 'w') as f:
        wtc = csv.writer(f)
        wtc.writerow(field)
        for r in range(len(rows)):
            wtc.writerow(rows[r])

        f.close()

def check_option(args):
    option_data = {}
    cycle_data = {}
    option_data['clock'] = args.clock.zfill(2)
    option_data['option'] = args.opt

    if args.fdate:
        finddate = args.fdate
        size = len(args.fdate)
        dstr = ""
        if size == 8: 
            dstr = datetime.strptime(args.fdate, "%Y%m%d")
            cycle_data['DAY'] = args.fdate
            option_data['cycle'] = cycle_data
        elif size == 10:
            dstr = datetime.strptime(args.fdate, "%Y%m%d%H")
            cycle_data['HOUR'] = args.fdate
            option_data['cycle'] = cycle_data

        try:
            Format = bool(parser.parse(str(dstr)))
        except ValueError:
            print("Incorrect data format")
            sys.exit(0)
        
    else :
        finddate = str(FDATE.strftime("%Y%m%d"))
        findhour = str(FHOUR.strftime("%Y%m%d%H"))
        if args.cycle == 'all': 
            if args.clock.zfill(2) == CURHOUR:
                cycle_data['DAY'] = finddate
                cycle_data['HOUR'] = findhour 

            elif args.clock.zfill(2) != CURHOUR:
                cycle_data['HOUR'] = findhour

        elif args.cycle == 'daily':
            cycle_data['DAY'] = finddate

        elif args.cycle == 'hourly':
            cycle_data['HOUR'] = findhour 

    if args.keep != 30:
        keepday=args.keep
    else:
        keepday=40

    option_data['keepday'] = keepday
    option_data['cycle'] = cycle_data

    if args.delete:
        delete_old_files(int(keepday)+1)

    option_data['clayhome'], option_data['claylog'], option_data['user'] = read_clay_conf()
    option_data['nconfigurepath'] = command_path('nconfigure', option_data['clayhome'])

    vnf = get_vnf(option_data['nconfigurepath'])
    option_data['vnf_info'] = vnf
    golobal_vars(vnf['vnf'])

    fname = os.path.join(option_data['clayhome'], "nstat", "current", "res", option_data['vnf_info']['res_project'], "table.info")
    option_data['stat_vm_resource'], option_data['stat_process_resource'], option_data['stat_process_traffic'] = get_stat_table(fname, 'table')

    option_data['process_resource'] = args.pro
    option_data['log'] = args.log

    create_dir(RDIR)

    return option_data

def get_nemsdb(npath):
    ## get nemsdb config
    ## config = {'host':host, 'user':user, 'passwd':passwd, 'database':db, 'port':3306, 'charset':'utf8'}
    parameters = ['host', 'user', 'passwd', 'database', 'port']
    emsparas = ['db.ip', 'db.user', 'db.password', 'db.name', 'db.port']
    config = {}

    for para, epara in zip(parameters, emsparas):
        ncmd = [npath, 'get', 'nems', 'database']
        ncmd.append(epara)
        result = str(check_output(ncmd, shell=True), 'utf-8')
        if epara == 'db.port':
            config[para] = int(result)
        elif epara == 'db.ip':
            if result == 'localhost':
                config[para] = '127.0.0.1'
        else:
            config[para] = str(check_output(ncmd, shell=True), 'utf-8')

    config['charset'] = 'utf8'

    return mysqlDBAcc(config)

def get_vnf(npath):
    vnf = {}
    vendor_type_cmd = [npath, 'get', 'nems', 'system', 'system.vendor.type']
    vnf['verdor_type'] = str(check_output(vendor_type_cmd, shell=True), 'utf-8')

    server_type_cmd = [npath, 'get', 'nems', 'system', 'system.server.type']
    vnf['server_type'] = str(check_output(server_type_cmd, shell=True), 'utf-8')

    res_project_cmd = [npath, 'get', 'nstat', 'servers', 'Project']
    vnf['res_project'] = str(check_output(res_project_cmd, shell=True), 'utf-8')

    if vnf['server_type'] == "RCSBB":
        vnf['vnf'] = "presence"
    elif vnf['server_type'] == "RS":
        vnf['vnf'] = "recording"

    return vnf

def get_stat_table(fname, element):
    table_list = read_xml(fname, element)

    stat_vm_resource = []
    stat_process_resource = []
    stat_process_traffic = []
    for tab in table_list:
        if "STAT_PROCESS_" in tab and  "_USAGE" in tab:
            stat_process_resource.append(tab)
        elif "STAT_" in tab and  "_USAGE" in tab: 
            stat_vm_resource.append(tab)
        else:
            stat_process_traffic.append(tab)

    return stat_vm_resource, stat_process_resource, stat_process_traffic

def collection(opt_data, db):
    ## colection Proactive monitoring 
    # print argument 
    print("option data")
    for key, value in opt_data.items():
        print("key : %s , value : %s" % (key, value))

    print()
    # Read nstat table.info
    result = db.select_sql(NE_NAME_SQL, True)
    for name in list(result):
        NE.append(name[0])

    unit = [1, 0]
    for cycle in opt_data['cycle'].keys():
        pa = proactive(opt_data, db, cycle)
        pa.set_vars(unit)

        pa.command_action()
        pa.process_status()
        pa.alarm_check()
        pa.resource_statistics()
        pa.process_statistics()
        pa.gold_config()

        if opt_data['log']:
            print()
            for line in LINES:
                print(line)

        pa.write_monitoring_file()

    delete_old_files(int(opt_data['keepday'])+1)

def arg_parse():
    parser = argparse.ArgumentParser(description='Proactive monitoring')
    #parser.add_argument('-v', dest='vnf', help='vnf name')
    parser.add_argument('-d', dest='fdate', help='search date')
    parser.add_argument('-o', dest='opt', help='ondemand')
    parser.add_argument('-c', dest='cycle', help='Cycle', default='all')
    parser.add_argument('-t', dest='clock', help='run time daily', default='03')
    parser.add_argument('-r', dest='delete', help='file delete', default=False)
    parser.add_argument('-k', dest='keep', help='file keepday', default=30)
    parser.add_argument('-l', dest='log', help='display result', default=False)
    parser.add_argument('-p', dest='pro', help='process resource', default=True)

    args = parser.parse_args()
    return args

def main():
    args = arg_parse()
    ## options
    opt_data = check_option(args)

    ## connect database
    db = get_nemsdb(opt_data['nconfigurepath'])
    
    collection(opt_data, db)

if __name__=='__main__':
    main()
