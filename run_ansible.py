#!/usr/bin/python3

import os
import sys
import re
import pexpect
import getpass
from pathlib import Path
import time
import subprocess

def send_pexpect(cmd, passwd):
    child = pexpect.spawn(cmd, encoding='utf-8', timeout=None)
    if '-k ' in cmd:
        child.expect('SSH password:', timeout=120)
        child.sendline(passwd)
        
    #child.logfile = sys.stdout.buffer
    child.logfile = sys.stdout

    child.read()

def readlines_file(filepath, opt=None):
    with open(filepath, 'r') as rf:
        result = rf.readlines()

    return result

def CheckOutput(cmd, shell=False):
    ''' command [] '''
    ''' Return result '''
    #cmd = " ".join(cmd)
    try:
        output = subprocess.check_output(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        ERROR(e)
        return None

    return output.rstrip()

def main():
    ### ###
    try:
        rfile = sys.argv[1]
        site = sys.argv[2]
    except IndexError :
        print("./run_ansible.py arteva-install.txt")
        sys.exit(0)

    filepath = os.path.join('./', rfile)
    readlines = readlines_file(filepath)

    passwd = getpass.getpass("Password: ")
    if not passwd:
        sys.exit(0)
    gtacid= 'psadmin'
    for cmd in readlines:
        cmd = cmd.strip()

        if "${site-name}" in cmd:
            cmd = cmd.replace("${site-name}", site)
        if "${gtac-id}" in cmd:
            cmd = cmd.replace("${gtac-id}", gtacid)

        time.sleep(1)

        if 'cd ' in cmd:
            homedir = Path.home()
            cmd = cmd.replace("cd ~/", "")
            cmd = os.path.join(homedir, cmd + '/')
            print(cmd)
            os.chdir(cmd)
        elif 'cp ' in cmd:
            print(cmd)
            result = CheckOutput(cmd, shell=True)
            if result:
                print(result)
        elif 'ls ' in cmd:
            result = CheckOutput(cmd, shell=True)
            if result:
                print(result)

        elif 'sleep ' in cmd:
            stime = int(cmd.split(' ')[1])
            time.sleep(stime)

        elif 'ansible-playbook' in cmd:
            print(cmd)
            send_pexpect(cmd, passwd)

        else:
            continue

if __name__ == '__main__':
    main()
