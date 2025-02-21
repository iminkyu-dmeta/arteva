
import os, sys, re
import pipes
import subprocess
import socket
import glob
from datetime import datetime
from datetime import date
from datetime import timedelta
import tarfile
import shutil

DATE=datetime.now()
CDATE=DATE.strftime("%Y%m%d")
keepday=3

def db_dump(host, user, password, db_name, target, all_databases, port): 
    cmd = ['mysqldump']
    if user is not None:
        #cmd += " --user=%s" % pipes.quote(user)
        cmd.append(" --user=%s" % pipes.quote(user))
    if password is not None:
        cmd.append(" --password=%s" % pipes.quote(password))
    if host is not None:
        cmd.append(" --host=%s --port=%i" % (pipes.quote(host), port))
    if all_databases:
        cmd.append(" --all-databases")
    else:
        cmd.append(" %s" % pipes.quote(db_name))

    if target is not None:
        cmd.append(" > %s" % pipes.quote(target))

    print(cmd)

    CheckOutput(cmd, shell=True)

def db_import(host,user, password, db_name, target, all_databases, port):
    if not os.path.exists(target):
        print("target %s does not exist on the host" % target)
        return None
    if user: 
        cmd.append(" --user=%s" % pipes.quote(user))
    if password:
        cmd.append(" --password=%s" % pipes.quote(password))
    if host is not None:
        cmd.append(" --host=%s --port=%i" % (pipes.quote(host), port))
    if not all_databases:
        cmd.append("-D")
        cmd.append(pipes.quote(db_name))

    if target:
        cmd.apppend(" < %s" % pipes.quote(target))

    print(cmd)
    CheckOutput(cmd, shell=True)

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

def createdir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print('Error: creating directory %s' % path)

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

def compress_tarfile(target, remove=False):
    dest_path = os.path.dirname(target)
    dest_name = os.path.basename(target) + ".tar.gz"
    os.chdir(dest_path)
    with tarfile.open(dest_name, "w:gz") as tar:
        tar.add(os.path.basename(target))

    tar.close()

    if remove:
        if os.path.isfile(target):
            os.remove(target)

def main():
    try :
        state = sys.argv[1]
        db_name = sys.argv[2]
        path = sys.argv[3]
        host = sys.argv[4]
    except IndexError :
        target = None
        path = None
        host = None

    if not path:
        path = os.path.join('/', 'data', 'drbackup', CDATE)

    createdir(path)
    hostname = socket.gethostname()
    target = os.path.join(path, hostname + "_" + db_name + ".sql")

    cmduser = ['nconfigure', 'get', 'nems', 'database', 'db.user']
    user = str(CheckOutput(cmduser, shell=True), 'utf-8')
    cmdpasswd = ['nconfigure', 'get', 'nems', 'database', 'db.password']
    passwd = str(CheckOutput(cmdpasswd, shell=True), 'utf-8')
    cmdhost = ['nconfigure', 'get', 'nems', 'database', 'db.host']
    hostip = str(CheckOutput(cmdhost, shell=True), 'utf-8')
    if host:
        hostip = host
    else:
        hostip = '127.0.0.1'

    if state == "dump":
        db_dump(hostip, user, passwd, db_name, target, None, 3306)
        compress_tarfile(target, True)
        os.system("chown -R attps:attps " + os.path.join('/', 'data', 'drbackup'))
    elif state == "backup":
        emsdb = ['nemsdb', 'nstatdb']
        for db_name in emsdb:
            target = os.path.join(path, hostname + "_" + db_name + ".sql")
            db_dump(hostip, user, passwd, db_name, target, None, 3306)
            compress_tarfile(target, True)

        os.system("chown -R attps:attps " + os.path.join('/', 'data', 'drbackup'))

    elif state == "import":
        db_import(hostip, user, passwd, db_name, target, None, 3306)

    deleteDir(os.path.join('/', 'data', 'drbackup'), keepday)
    deleteFile(os.path.join('/', 'data', 'drbackup'), keepday)

if __name__=='__main__':
    main()
