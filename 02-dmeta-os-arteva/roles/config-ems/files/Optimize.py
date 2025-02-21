#!/usr/bin/python

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
from pwd import getpwnam
from datetime import datetime
from datetime import date
from datetime import timedelta
import urllib.parse
import xml.etree.ElementTree as ET
import csv
import itertools

from pysnmp.hlapi import *
from pysnmp import debug

try:
            import http.client as httplib
except:
            import httplib

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

    def selectDB(self, sql=None, fetchall=False, desc=False):
        self.curs.execute(sql)

        if desc:
            desc = self.curs.description

        if fetchall:
            result = self.curs.fetchall()
        else:
            result = self.curs.fetchone()

        if desc:
            return result, desc
        else:
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

    try :
        host = sys.argv[1]
    except IndexError :
        host = ""

    nconfigurepath = commandpath('nconfigure')
    cmduser = [nconfigurepath, 'get', 'nems', 'database', 'db.user']
    user = str(CheckOutput(cmduser, shell=True), 'utf-8')
    cmdpasswd = [nconfigurepath, 'get', 'nems', 'database', 'db.password']
    passwd = str(CheckOutput(cmdpasswd, shell=True), 'utf-8')
    cmdhost = [nconfigurepath, 'get', 'nems', 'database', 'db.host']
    hostip = str(CheckOutput(cmdhost, shell=True), 'utf-8')
    if host:
        hostip = host
    else:
        hostip = '127.0.0.1'

    #cmdname = [nconfigurepath, 'get', 'nems', 'database', 'db.name']
    cmdname = [nconfigurepath, 'get', 'nstat', 'database', 'DBName']
    dbname = str(CheckOutput(cmdname, shell=True), 'utf-8')

    db = DBAcc(user, passwd, host, dbname)

    NDATE=date.today()
    DATE = (NDATE - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")

    NSATTAB = ['STAT_CPU_USAGE', 'STAT_DISK_USAGE', 'STAT_MEM_USAGE', 'TRAFFIC_RCS_PS', 'TRAFFIC_RCS_XDMS']
    SQL = "DELETE FROM %s WHERE DTIME < '" + DATE + "';"

    for t in NSATTAB:
        SQL = "DELETE FROM " + t + " WHERE DTIME < '" + DATE + "';"
        print(SQL)
        db.insertDB(SQL)

    Period = ['FIVE', 'HOUR', 'DAY', 'MONTH']

    OPT = "optimize table "
    for tt in NSATTAB:
        SQL = OPT + tt + ";"
        print(SQL)
        db.insertDB(SQL)
        for period in Period:
            SQL = OPT + tt + "_" + period + ";"
            print(SQL)
            db.insertDB(SQL)
            

if __name__=='__main__':
    main()
