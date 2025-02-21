#!/usr/bin/env python

import csv
import sys
import yaml
import os, sys
import re
import subprocess
from collections import OrderedDict

COMMAND=""
COMMONPATH = os.path.join('common', 'usr', 'sbin')
NCONFIG="nconfigure tbset clay ScheduleV2 CommandList '"
COMMIT="nconfigure set clay ScheduleV2 CommandList Commit"
COMM="command="
ARGU="arguments="
HOUR="executeHour="
MIN="executeMin="
CYCLE="cycle="
MID=",,"
DIVI=";;"
field=["command", "arguments", "executeHour", "executeMin", "cycle"]

class clayScheduleTool:

    def get_Schedule():
        cmd=['nconfigure', 'tbget', 'clay', 'ScheduleV2', 'CommandList']
        result = str(CheckOutput(cmd, shell=True), 'utf-8')

        #dic, name = clayScheduleTool.list_schedule(result)
        return result

    def add_Schedule(arglist):
        dic = clayScheduleTool.get_Schedule()
        result, name = clayScheduleTool.list_schedule(dic)
        bname = os.path.basename(arglist[0])
        
        nconfig = ""
        klen = len(result)
        exist = False
        for tlist in result.values():
            ext = [x for x in tlist if re.search(bname, x)]
            if ext:
                exist = True

        if exist:
            nconfig = clayScheduleTool.chg_Schedule(arglist)

            return nconfig
            
        result[str(klen)] = arglist
                
        nconfig = clayScheduleTool.setnconfig(result, name)

    def chg_Schedule(arglist):
        dic = clayScheduleTool.get_Schedule()
        result, name = clayScheduleTool.list_schedule(dic)
        bname = os.path.basename(arglist[0])

        nconfig = ""
        key = ""
        chglist = []
        exist = False
        for item in result.items():
            ext = [x for x in item[1] if re.search(bname, x)]
            if ext:
                exist = True
                key = item[0]

        if exist:
            for org, new, row in zip(result[key], arglist, field):
                if row == "arguments" and new is None:
                    chglist.append(org)
                else:
                    chglist.append(new)

        else:
            nconfig = clayScheduleTool.add_Schedule(arglist)

            return nconfig

        result[key] = chglist

        nconfig = clayScheduleTool.setnconfig(result, name)

    def del_Schedule(arglist):
        dic = clayScheduleTool.get_Schedule()
        result, name = clayScheduleTool.list_schedule(dic)
        bname = os.path.basename(arglist[0])

        nconfig = ""
        delkey = ""
        for item in result.items():
            exist = [x for x in item[1] if re.search(bname, x)]
            if exist:
                delkey = item[0]

        if delkey:
            result.pop(delkey)
            nconfig = clayScheduleTool.setnconfig(result, name)

    def list_schedule(result):
        dic = {}
        cname = []
        ## read revered
        result = result.split('\n')
        revresult = list(reversed(result))

        for f in revresult:
            if f and f.find("CommandList.records=") > -1 :
                record = f.split("=")[1]

            else:
                key = f.split("=")[0]
                ckey = key.split('.')[1]
                val = f.split("=")[1]
                cname.append(key.split('.')[2])

                try:
                    if not dic[ckey]:
                        dic[ckey] = [val]
                    else:
                        dic[ckey].append(val)
                except KeyError:
                    dic[ckey] = [val]

        return dic, cname

    def setnconfig(result, name):
        nconfig = ""
        for index, tlist in enumerate(result.values()):
            for i, pair in enumerate(zip(tlist, name)):
                if i != len(tlist) -1:
                    nconfig += pair[1] + "=" + pair[0] + MID
                else:
                    nconfig += pair[1] + "=" + pair[0] + DIVI

        nconfig = NCONFIG + nconfig[:-2] + "\'"
        print(" ")
        print(nconfig)
        os.system(nconfig)

        print(" ")
        print(clayScheduleTool.get_Schedule())

def check_arg(EXEHOUR, EXEMIN):
    if int(EXEHOUR) < 0 or int(EXEHOUR) > 23 :
        print("INPUT VALUE(hour): " + EXEHOUR + " range : hour ( 0 ~ 23 ) ")

        return False

    if int(EXEMIN) < 0 or int(EXEMIN) > 59 :
        print("INPUT VALUE(min): " + EXEMIN + " range : hour ( 0 ~ 59 ) ")

        return False

    return True

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

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

def printList(plist, clist=None):
    print()
    if clist:
        for row in zip(plist, clist):
            print("%s  : %s" % (row[1], row[0]))

    else:
        for row in plist:
            print(row)

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
    try:
        # ADD, CHG, DEL
        ACTION=sys.argv[1].upper()
        COMMAND=sys.argv[2]
        ARGU=sys.argv[3]
        EXEHOUR=sys.argv[4]
        EXEMIN=sys.argv[5]
        EXECYCLE=sys.argv[6]
    except IndexError :
        ARGU = ''
        EXEHOUR='7'
        EXEMIN='10'
        EXECYCLE = 'daily'

    arglist = [COMMAND, ARGU, EXEHOUR, EXEMIN, EXECYCLE]
    
    if not check_arg(EXEHOUR, EXEMIN):
        sys.exit(1)

    tool = clayScheduleTool

    if ACTION == 'ADD':
        print("Add schedule : ")
        printList(arglist, field)
        tool.add_Schedule(arglist)

    elif ACTION == 'CHG':
        print("Update : ") 
        printList(arglist, field)
        tool.chg_Schedule(arglist)

    elif ACTION == 'DEL':
        print("Delete : ")
        printList(arglist, field)
        tool.del_Schedule(arglist)

    elif ACTION == 'GET':
        print("Schedule : ")
        print(tool.get_Schedule())

if __name__ == '__main__':
    main()
