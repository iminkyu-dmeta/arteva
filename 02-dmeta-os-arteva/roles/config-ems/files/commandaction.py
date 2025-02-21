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
import itertools

try:
            import http.client as httplib
except:
            import httplib

###  SQL ##
ProcessStatus = "SELECT A.name AS 'NE Name', CASE WHEN A.status = 1 THEN 'Active' ELSE 'Inactive' END AS 'NE Status', B.name AS 'Process Name', B.version AS 'Version', CASE WHEN B.start_time = 0 THEN '-' ELSE B.start_time END AS 'Start Time', CASE WHEN B.status = 1 THEN 'Active' ELSE 'Inactive' END AS 'Status', CASE WHEN B.ha_status = 1 THEN 'Active' WHEN B.ha_status = 0 THEN 'Standby' ELSE '-' END AS 'VRRP Status' FROM nemsdb.ne A, nemsdb.process B WHERE A.id = B.ne_id ORDER BY A.name, B.group, B.name;"
NEIP = "SELECT A.name AS 'NE Name', B.name AS 'Process Type', A.ip AS 'NE IP' FROM nemsdb.ne A, nemsdb.process B WHERE A.id = B.ne_id and B.name = '"
SQL="select id, name, ip, hostName from ne where name = '"

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

def pollingHttpGet(remoteip, port, name=None, command=None, param=None) :
    if command and not param:
        params = urllib.parse.urlencode({'id': name, 'command': command})
    elif command and param:
        params = urllib.parse.urlencode({'id': name, 'command': command, 'params': param})

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

def pollingListHttpGet(remoteip, port, name) :
    params = urllib.parse.urlencode({'id': name})

    headers = {"Host": remoteip + ":" + port,
                "Accept": "text/plain, application/json, application/*+json, */*",
                "User-Agent": "command-action",
                "Connection": "keep-alive",
                "Accept-Encoding": "gzip/deflate"
    }
    try:
        conn = httplib.HTTPConnection(remoteip, port)
        conn.request("GET", "/polling_list.xml?" + params, "" ,headers)
        response = conn.getresponse()
        body = response.read()
        return body
    except (httplib.HTTPException, socket.error) as ex :
        print("ERROR: %s" % ex)
        return 0

def commandListxml(xmldata, element, attribute):
    commandlist = []
    try:
        tree = ET.fromstring(xmldata)
    except ValueError :
        xmlp = ET.XMLParser(encoding="utf-8")
        tree = ET.fromstring(xmldata, parser=xmlp)

    elements= tree.iter(tag=element) 
    if elements:
        for ele in elements:
            commandlist.append(ele.get(attribute))

    else:
        print("%s is nothing" % element)

    return commandlist

def getpollingxml(xmldata, url=None, node=None):
    try:
        tree = ET.fromstring(xmldata)
    except ValueError :
        xmlp = ET.XMLParser(encoding="utf-8")
        tree = ET.fromstring(xmldata, parser=xmlp)

    return tree.text

def findfieldas(sql, result):
    fstr = '(AS )\'([A-Za-z]+ )([A-Za-z]+)|(AS )\'([A-Za-z]+)'
    findstr = re.findall(fstr, sql)

    collist = []
    for col in findstr:
        if col[0]:
            name = col[1] + col[2]
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

def findfield(sql, result):
    findstr = sql.split(' ')

    collist = []
    if findstr[1]:
        name = findstr[1].split(',')
        for field in name:
            collist.append(field)

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

def rowtable(data, field, size):
    lines = []
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
    lines.append(lows % tuple(field))
    lines.append(pstr)

    for row in data:
        lines.append(lows % tuple(row))
        if LogLevel == 'debug':
            print(lows % tuple(row))

    lines.append(pstr)

    return lines

def display(lines):
    for line in lines:
        print(line)

def processStatus(db):
    result = db.selectDB(ProcessStatus, True)
    fieldlist, fieldsize  = findfieldas(ProcessStatus, result)
    lines = rowtable(result, fieldlist, fieldsize)

    print()
    print('Presence Process status')
    display(lines)
    print()

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

def commandpath(command):
    clayhome, claylog, user = readclayconf()
    path = os.path.join(clayhome, COMMONPATH)
    cpath = os.path.join(path, command)
    if os.path.isfile(cpath):
        return cpath

    else:
        return command

def dbapi():
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

    return db

def getRemoteip(db, pname):
    SELECT_SQL = NEIP + pname + "'"
    result = db.selectDB(SELECT_SQL, True)

    nename = result[0][0]
    hostip = result[0][2]

    return hostip

def commandList(hostip, pname, command=None):
    result = pollingListHttpGet(hostip, '8800', pname)
    commandlist = commandListxml(result, "polling", "name")

    if command:
        if command in commandlist:
            return True
        else:
            return False
    else:
        commandlist.remove('DELETE-USER')
        if pname == 'rcs_xdms.exe':
            commandlist.remove('DELETE-PROFILE')
            commandlist.remove('CHG-CONTACT-SYNC')
        if commandlist:
            return commandlist

        else:
            return 

def main():
    ''' Presence Command Action '''
    if len(sys.argv) < 2:
        print()
        print('Usage:')
        print(' %s [PS/XDMS/pstatus]' % sys.argv[0])
        print()
        print('Presence Process status and run Command Action')
        print()
        exit()

    ## Connect mysql
    db = dbapi() 

    if sys.argv[1].lower() == 'pstatus' or sys.argv[1].lower() == 'process':
        processStatus(db)

    elif sys.argv[1].lower() == 'xdms' or sys.argv[1].lower() == 'ps':
        pname = 'rcs_' + sys.argv[1].lower() + '.exe'
        hostip = getRemoteip(db, pname)
        if len(sys.argv) < 3:
            commandlist = commandList(hostip, pname)
            print()
            print('USAGE: ')
            print('\t%s %s %s' % (sys.argv[0], sys.argv[1].upper(), '[ ' + ' | '.join(commandlist) + ' ]'))
            #print('USAGE: %s %s' % (sys.argv[0].split('/')[-1:][0], commandlist))
            print()
            exit()

        exist = commandList(hostip, pname, sys.argv[2])
        if exist:
            if sys.argv[2] == 'GET-USER' or sys.argv[2] == 'DIS-PROFILE' or sys.argv[2] == 'DIS-PIDF-INF':
                if len(sys.argv) < 4:
                    print()
                    print('USAGE:  %s %s %s [ MCPTTID ]' % (sys.argv[0], sys.argv[1], sys.argv[2]))
                    print()
                    exit()

                result = pollingHttpGet(hostip, '8800', pname, sys.argv[2], sys.argv[3])
                string = urllib.parse.unquote_plus(getpollingxml(result))
                print(string)

            else:
                result = pollingHttpGet(hostip, '8800', pname, sys.argv[2])
                print(result)
                string = urllib.parse.unquote_plus(getpollingxml(result))
                print(string)

        else:
            print()
            print("%s %s is a command that does not exist." % (sys.argv[1].upper(), sys.argv[2]))
            print()
            exit()

    else:
        print("not supported!!!")

if __name__=='__main__':
    main()
