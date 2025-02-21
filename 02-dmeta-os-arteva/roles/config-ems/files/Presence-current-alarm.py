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
import glob
import shutil
from pwd import getpwnam
from datetime import datetime
from datetime import date
from datetime import timedelta
import urllib.parse
import xml.etree.ElementTree as ET
import csv

from pysnmp.hlapi import *
from pysnmp import debug

try:
        import http.client as httplib
except:
        import httplib

## 
DIR=os.path.join('/', 'logs', 'DC')
RDIR=os.path.join('/', 'logs', 'DC', 'report')
ADIR=os.path.join('/', 'logs', 'DC', 'alarm')
NDATE=date.today()
DATE=datetime.now()
YDATE=NDATE - timedelta(days=1)
SDATE=NDATE - timedelta(days=90)
HOSTNAME=platform.node()

FINDDATE = DATE - timedelta(days=1)
FINDDATE = FINDDATE.strftime("%Y-%m-%d")
FINDHOUR = DATE - timedelta(hours=1)
FINDMIN = FINDHOUR.strftime("%H%m")

STARHDTIME=(DATE - timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
EENDHDTIME=(DATE - timedelta(hours=1)).strftime("%Y-%m-%d %H:59:59")

FINDDATE = str(FINDDATE)
FINDHOUR = str(FINDHOUR)
SDATE = str(SDATE)

NE=["PresenceEMS1", "PresenceEMS2", "Presence1", "Presence2", "XDMS1", "XDMS2", "PresenceDB1", "PresenceDB2", "XDMSDB1", "XDMSDB2"]
PSCOMMAND=["DIS-REGI-COUNT", "CHECK-SYSTEMS", "DIS-DB-REPLICATION-STATUS"]
XDMSCOMMAND=["COUNT-USER", "CHECK-SYSTEMS", "DIS-DB-REPLICATION-STATUS"]

NW = "############################################################################"
NW2 = "\n############################################################################"
lines = []

###  SQL ##
YESTALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status', B.name AS 'Node Name' , B.ip AS 'IP', C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time', C.clear_time AS 'Clear Time' FROM nemsdb.fault AS C LEFT JOIN nemsdb.ne AS B ON C.ne_id = B.id  WHERE C.event_time >= '" + FINDDATE + " 00:00:00' AND C.event_time <= '" + FINDDATE + " 23:59:59'  ORDER BY C.event_time;"

HOURALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status', B.name AS 'Node Name' , B.ip AS 'IP', C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time', C.clear_time AS 'Clear Time' FROM nemsdb.fault AS C LEFT JOIN nemsdb.ne AS B ON C.ne_id = B.id  WHERE C.event_time >= '" + STARHDTIME + "' AND C.event_time <= '" + EENDHDTIME + "'  ORDER BY C.event_time;"

NOTHCALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status' , B.name AS 'Node Name' , B.ip AS 'IP' , C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time' , C.message AS 'Description' FROM nemsdb.fault C INNER JOIN nemsdb.ne B ON B.id = C.ne_id INNER JOIN nemsdb.ne_group A ON B.group_id = A.id WHERE C.clear_time is null AND C.event_time >= '" + STARHDTIME+ "' AND C.event_time <= '" + EENDHDTIME + "' ORDER BY C.event_time;"

NOTCLEARALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status' , B.name AS 'Node Name' , B.ip AS 'IP' , C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time' , C.message AS 'Description' FROM nemsdb.fault C INNER JOIN nemsdb.ne B ON B.id = C.ne_id INNER JOIN nemsdb.ne_group A ON B.group_id = A.id WHERE (C.clear_time is null AND C.severity != 4 AND C.severity != 5 AND C.event_time >= '" + SDATE + " 23:59:59' ) or (C.event_time >= '" + STARHDTIME+ "' AND C.event_time <= '" + EENDHDTIME + "') ORDER BY C.event_time;"

SELDTIME = "SELECT DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) AS 'DTIME', "
GROUPBY = "' GROUP BY DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) ORDER BY DTIME;"
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

def systemOutput(cmd, shell=False):
    ''' command [] '''
    ''' Return result '''
    #cmd = " ".join(cmd)

    try:
        output = subprocess.check_output(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        ERROR(e)
        return None

    return output.rstrip()


def createdir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print('Error: creating directory %s' % path)

def pollingHttpGet(remoteip, port, name=None, command=None) :
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

def getpollingxml(xmldata, url=None, node=None):
    try:
        tree = ET.fromstring(xmldata)
    except ValueError :
        xmlp = ET.XMLParser(encoding="utf-8")
        tree = ET.fromstring(xmldata, parser=xmlp)

    return tree.text

def findfield(sql, result):
    fstr = '(AS )\'([A-Za-z]+)[ ]([A-Za-z0-9]+)|(AS )\'([A-Za-z0-9]+)'
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

def display(data, field, size):
    LogLevel = 'info'
    pstr = ""
    lows = ""
    fids = ""
    fsz = len(field)

    for idx, sz in enumerate(size):
        pstr += '+'
        for i in range(int(sz+2)):
            pstr += '-'
        lows += "| %-" + str(sz+1) + "s"
    pstr += '+'
    lows += "|"
        
    lines.append(pstr)
    if LogLevel == 'debug':
        print(lows)
    if field:
        lines.append(lows % tuple(field))
    lines.append(pstr)

    for row in data:
        lines.append(lows % tuple(row))
        if LogLevel == 'debug':
            print(lows % tuple(row))

    lines.append(pstr)
    lines.append('\n')

def minuteSql(cycle):
    STARHDTIME=(DATE - timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
    EENDHDTIME=(DATE - timedelta(hours=1)).strftime("%Y-%m-%d %H:59:59")

    STARMDTIME=(DATE - timedelta(minutes=cycle)).strftime("%Y-%m-%d %H:%M:00")
    EENDMDTIME=(DATE.strftime("%Y-%m-%d %H:%M:00"))
    
    HOURALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status', B.name AS 'Node Name' , B.ip AS 'IP', C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time', C.clear_time AS 'Clear Time' FROM nemsdb.fault AS C LEFT JOIN nemsdb.ne AS B ON C.ne_id = B.id  WHERE C.event_time >= '" + STARHDTIME + "' AND C.event_time <= '" + EENDHDTIME + "'  ORDER BY C.event_time;"
    
    MINUALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status', B.name AS 'Node Name' , B.ip AS 'IP', C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time', C.clear_time AS 'Clear Time' FROM nemsdb.fault AS C LEFT JOIN nemsdb.ne AS B ON C.ne_id = B.id  WHERE C.event_time >= '" + STARMDTIME + "' AND C.event_time <= '" + EENDMDTIME + "'  ORDER BY C.event_time;"
    
    NOTHCALARM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status' , B.name AS 'Node Name' , B.ip AS 'IP' , C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time' , C.message AS 'Description' FROM nemsdb.fault C INNER JOIN nemsdb.ne B ON B.id = C.ne_id INNER JOIN nemsdb.ne_group A ON B.group_id = A.id WHERE C.clear_time is null AND C.event_time >= '" + STARMDTIME+ "' AND C.event_time <= '" + EENDMDTIME + "' ORDER BY C.event_time;"

    NOTCLEARALRM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status' , B.name AS 'Node Name' , B.ip AS 'IP' , C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time' , C.message AS 'Description' FROM nemsdb.fault C INNER JOIN nemsdb.ne B ON B.id = C.ne_id INNER JOIN nemsdb.ne_group A ON B.group_id = A.id WHERE C.clear_time is null AND C.severity != 4 AND C.severity != 5 ORDER BY C.event_time;"

    CURRENTARALRM = "SELECT CASE WHEN C.severity = 1 THEN 'Critical' WHEN C.severity = 2 THEN 'Major' WHEN C.severity = 3 THEN 'Minor' WHEN C.severity = 4 THEN 'Warning' WHEN C.severity = 5 THEN 'Clear' WHEN C.severity = 6 THEN 'Info' ELSE '' END AS 'Status' , B.name AS 'Node Name' , B.ip AS 'IP' , C.entity AS 'Entity', C.category AS 'Category', C.event_time AS 'Start Time' , C.message AS 'Description' FROM nemsdb.fault C INNER JOIN nemsdb.ne B ON B.id = C.ne_id INNER JOIN nemsdb.ne_group A ON B.group_id = A.id WHERE (C.clear_time is null AND C.severity != 4 AND C.severity != 5 AND C.event_time >= '" + SDATE + " 23:59:59' ) or (C.event_time >= '" + STARHDTIME+ "' AND C.event_time <= '" + EENDHDTIME + "') ORDER BY C.event_time;"
    
    SELDTIME = "SELECT DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) AS 'DTIME', "
    GROUPBY = "' GROUP BY DATE_FORMAT( DTIME, '%Y-%m-%d %H:%i' ) ORDER BY DTIME;"

    return HOURALARM, MINUALARM, NOTCLEARALRM, CURRENTARALRM

def alarmCheck(cycle, db, opt=None):
    hoursql, minutesql, notsql, cursql = minuteSql(int(cycle))
    result = db.selectDB(cursql, True)
    fieldlist, fieldsize  = findfield(cursql, result)
    display(result, fieldlist, fieldsize)

    if opt:
        result = db.selectDB(notsql, True)
        display(result, fieldlist, fieldsize)


def deleteFile(path, keepday):
    today = datetime.today()
    for root, directories, files in os.walk(path, topdown=False):
        for name in files:
            t = os.stat(os.path.join(root, name))[8]
            filetime = datetime.fromtimestamp(t) - today
            if filetime.days <= -keepday:
                print(os.path.join(root, name), filetime.days)
                os.remove(os.path.join(root, name))

def deleteDir(path, keepday):
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

def writeFile(cycle, opt=None):
    CDTIME=DATE.strftime("%Y%m%d%H%M")    
    LOGFILE = 'presence-' + HOSTNAME + '-current-monitoring-' + CDTIME + '.txt'

    fpath = os.path.join(ADIR, LOGFILE)

    with open(fpath, 'w') as lf:
        lf.writelines('\n'.join(lines))
    

    lf.close()

def fiveminute(db, cycle, opt=None):
    ## Proactive monitoring 

    ## 5 minute Alarm check
    alarmCheck(cycle, db, opt)

    ## write current alarm file
    writeFile(cycle, opt)

    lines.clear()

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

def main():
    parser = argparse.ArgumentParser(description='Proactive monitoring curretn alarm')
    parser.add_argument('-d', dest='fdate', help='search date')
    parser.add_argument('-c', dest='cycle', help='cycle', default='5')

    args = parser.parse_args()
    cycle = args.cycle

    keepday=5

    if int(cycle) < 0 or int(cycle) > 60:
        print("wrong is %s" % (cycle))
        sys.exit(0)

    MINUTE = DATE.strftime("%M")
    dmod = int(MINUTE)%5
    if dmod != 0:
        sys.exit(0)

    ## Create /logs/DC
    createdir(ADIR)

    nconfigurepath = commandpath('nconfigure')
    ## get nemsdb config
    cmduser = [nconfigurepath, 'get', 'nems', 'database', 'db.user']
    user = str(CheckOutput(cmduser, shell=True), 'utf-8')
    cmdpasswd = [nconfigurepath, 'get', 'nems', 'database', 'db.password']
    passwd = str(CheckOutput(cmdpasswd, shell=True), 'utf-8')
    cmdhost = [nconfigurepath, 'get', 'nems', 'database', 'db.ip']
    hostip = str(CheckOutput(cmdhost, shell=True), 'utf-8')
    if hostip == 'localhost':
        hostip = '127.0.0.1'
    cmdname = [nconfigurepath, 'get', 'nems', 'database', 'db.name']
    dbname = str(CheckOutput(cmdname, shell=True), 'utf-8')

    ## mysql connect
    db = DBAcc(user, passwd, '127.0.0.1', dbname)
    
    fiveminute(db, cycle, opt=None)

    deleteFile(ADIR, keepday+1)

if __name__=='__main__':
    main()
