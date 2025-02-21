#!/usr/bin/python

import os, sys, re
import json
import pymysql
import platform
import socket
import hashlib
import time
import argparse
import subprocess
from pwd import getpwnam
from datetime import datetime
from datetime import date
from datetime import timedelta
import urllib.parse
import xml.etree.ElementTree as ET
import csv

try:
            import http.client as httplib
except:
            import httplib

THRESHOLD=["CPU", "Memory", "/"]

NE="select id, group_id, name from ne;"

THRESHOLDINSERT="insert into threshold (id, comparison_type, critical_value, major_value, minor_value, warning_value, message) values (id, 0, 90, 80, 70, 0, 'NULL');"
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

    def insertDB(self, sql=None, many=None):
        if many:
            var=many
            self.curs.executemany(sql, var)
        else:
            self.curs.execute(sql)

        self.conn.commit()

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

    cmdserver=[nconfigurepath, 'get', 'nems', 'system', 'system.server.type']
    servername = str(CheckOutput(cmdserver, shell=True), 'utf-8')

    db = DBAcc(user, passwd, '127.0.0.1', dbname)
    result = db.selectDB(NE, True)

    CPUID = []
    MEMID = []
    DISID = []
    for idx, row in enumerate(result):
        #print(row)
        PERFCPUID = "select id  from performance where ne_id = " + str(row[0]) + " and entity = 'CPU';"
        idcs = db.selectDB(PERFCPUID, False)
        CPUID.append(idcs[0])

        PERFMEMID = "select id  from performance where ne_id = " + str(row[0]) + " and entity = 'Memory';"
        idms = db.selectDB(PERFMEMID, False)
        MEMID.append(idms[0])

        PERFDISID = "select id  from performance where ne_id = " + str(row[0]) + " and entity like '/%';"
        idds = db.selectDB(PERFDISID, True)
        for idx in idds:
            DISID.append(idx[0])

    Threshold = "truncate threshold;"
    db.insertDB(Threshold)

    ## Insert CPU Threshold 
    CPUINSERT="insert into threshold (id, comparison_type, critical_value, major_value, minor_value, warning_value) values (%s, 0, 90, 80, 70, 0);"
    MEMINSERT="insert into threshold (id, comparison_type, critical_value, major_value, minor_value, warning_value) values (%s, 0, 90, 80, 70, 0);"
    DISINSERT="insert into threshold (id, comparison_type, critical_value, major_value, minor_value, warning_value) values (%s, 0, 90, 80, 70, 0);"
    db.insertDB(CPUINSERT, CPUID)

    db.insertDB(CPUINSERT, MEMID)

    db.insertDB(CPUINSERT, DISID)

    if servername == 'MPGW':
        PERFQRY1="update performance set is_service = '0' where code = 'T0009002' or code = 'T0009003' or code = 'T0009004' or code = 'T0009006' or code = 'T0009008' or code = 'T0009009' or code = 'T0009010' or code = 'T0009011';"
        PERFQRY2="update performance set is_service = '1' where code = 'T0009001' or code = 'T0009005';"

        db.insertDB(PERFQRY1)
        db.insertDB(PERFQRY2)

if __name__=='__main__':
    main()
