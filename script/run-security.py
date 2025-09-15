#!/usr/bin/python3

import os
import sys
import re
import pexpect
import getpass
from pathlib import Path
import time
import subprocess
import platform

COMMANDS = ['cat', 'sudo', 'echo', 'ls', 'ps', 'rpm', 'netstat', 'expn', 'vrfy', 'mariadb']

class check_secrity:
    def __init__(self, arg, password):
        self.filename = arg[1]
        self.ipaddress = arg[2]
        if len(arg) > 3:
            self.num = arg[3]
        else:
            self.num = None

        self.password = password
        self.prompt = get_prompt()

    def read_file(self):
        filepath = os.path.join('./', self.filename)
        readlines = readlines_file(filepath)

        return readlines

    def checkout(self, cmd, shell):
        result = CheckOutput(cmd, shell=shell)

        if result:
            print(result.decode('utf-8'))

    def run_cmd(self, cmd, scmd):
        fstr = scmd[0]
        print()
        if fstr == "su" :
            print(self.prompt + cmd.rstrip())
            send_cmd_pexpect(cmd, self.password, 'Password:')

        elif fstr == "ssh" :
            ncmd = []
            ncmd.append(fstr)
            domain = scmd[1].rstrip()
            if 'ipaddress' in domain:
                domain = domain.replace('ipaddress', self.ipaddress)
                ncmd.append(domain)
                ncmd.append("-o StrictHostKeyChecking=no")

            ncmd = " ".join(ncmd)
            expect_cmd = domain + "'s password:"

            print(self.prompt + ncmd.rstrip())
            send_cmd_pexpect(ncmd, self.password, expect_cmd)

        elif fstr == "sudo" :
            if scmd[1] == "mariadb" :
                print(self.prompt + cmd.rstrip())
                # print(cmd.rstrip())
                send_cmd_pexpect(cmd, self.password, 'Enter password: ')

            else :
                print(self.prompt + cmd.rstrip())
                self.checkout(cmd, True)

        else:
            print(self.prompt + cmd.rstrip())
            self.checkout(cmd, True)


    def read_cmd(self):
        readlines = self.read_file() 
        print()
        for cmd in readlines:
            scmd = cmd.split()

            if scmd and scmd[0].isalpha():
                ## print(cmd.rstrip())
                self.run_cmd(cmd, scmd)

            else :
                if scmd and scmd[0].replace('.', '').isdigit():
                    time.sleep(0.5)
                print(cmd.rstrip())

    def pre_work(self):
        flag = False
        if self.num:
            readlines = self.read_file() 
            for cmd in readlines:
                scmd = cmd.split()
                if scmd and scmd[0].replace('.', '').isdigit():
                    l = len(self.num)
                    if scmd and scmd[0][:l] == self.num:
                        time.sleep(0.5)
                        flag = True
                        print()
                        print(cmd.rstrip())

                    elif scmd and scmd[0][:l] != self.num:
                        if flag:
                            exit(0)

                else:
                    if flag:
                        ## time.sleep(0.5)
                        if scmd and scmd[0].isalpha():
                            self.run_cmd(cmd, scmd)
                        else:
                            print(cmd.rstrip())
                

        else:
            self.read_cmd()

def send_pexpect(cmd, passwd):
    child = pexpect.spawn(cmd, encoding='utf-8', timeout=None)
    if 'ssh' in cmd:
        child.expect('SSH password:', timeout=120)
        child.sendline(passwd)

    #child.logfile = sys.stdout.buffer
    child.logfile = sys.stdout

    child.read()
    
def send_cmd_pexpect(cmd, passwd, word):
    child = pexpect.spawn(cmd, encoding='utf-8', timeout=None)
    if 'root@' in cmd:
        child.expect(word, timeout=10)
        child.sendline(passwd)

        child.expect(word, timeout=10)
        child.sendline(passwd)

        child.expect(word, timeout=120)
        child.sendline(passwd)

    elif 'mariadb' in cmd:
        print()
        child.expect(word, timeout=10)
        child.sendline(passwd)

    elif 'ssh' in cmd:
        print()
        print(passwd)
        child.expect(word, timeout=10)
        print(child.before)
        child.sendline(passwd)
        # We expect any of these three patterns 
        i = child.expect (['Permission denied', 'Terminal type', '[#\$] '])
        print(child.after)
        time.sleep(2)
        if i==1 or i==2:
            child.sendline('exit')

    else:
        print()
        child.expect(word, timeout=10)
        child.sendline(passwd)

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
        #ERROR(e)
        return None

    return output.rstrip()

def input_password():
    passwd = getpass.getpass("Password: ")
    #print(passwd)

    if not passwd:
        sys.exit(0)

    return passwd

def get_prompt():
    #cmd = "echo ${PS1}"
    prompt = "[/u@/h /W]$ "
    p = {}

    u = os.getlogin()
    h = platform.node()
    if os.environ['HOME'] == os.getcwd():
        W = '~'
    elif os.environ['HOME'] in os.getcwd():
        W = os.getcwd()[len(os.environ['HOME']):]

    for c in prompt:
        if c.isalpha():
            p[c] = eval(c)
            prompt = prompt.replace('/' + c, eval(c))

    return prompt

def run_expect(password):
    filename = sys.argv[1]
    ipaddress = sys.argv[2]
    if len(sys.argv) > 3:
        num = sys.argv[3]
    else:
        num = None

    prompt = get_prompt()

    prompt = get_prompt()
    filepath = os.path.join('.', filename)

    lines = readlines_file(filepath, opt=None)
    for line in lines:
        scmd = line.split()
        
        if scmd and scmd[0].isalpha():
            print(line.rstrip())
            #self.run_cmd(cmd, scmd)
        
        else :
            if scmd and scmd[0].replace('.', '').isdigit():
                time.sleep(0.5)
            print(prompt + line.rstrip())

def main():
    ### ###
    #try:
    #    arg.append( sys.argv[1]
    #    ipaddress = sys.argv[2]
    #except IndexError :
    #    print("./run-security.py check-security.txt")
    #    sys.exit(0)

    passwd = input_password()
    gtacid= 'dmeta'

    #if remote:
    # run_expect(passwd)

    run = check_secrity(sys.argv, passwd)
    run.pre_work()

    print()


if __name__ == '__main__':
    main()
