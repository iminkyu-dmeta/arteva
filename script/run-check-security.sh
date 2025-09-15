#!/bin/sh

EXE=$1
if [[ ${EXE} == "ALL" ]] | [[ ${EXE} == "1" ]] ; then
echo "4.1.2 패스워드 복잡성 설정"
echo "# 숫자 최소 사용 수 설정 (dcredit = -1)"
echo "cat /etc/security/pwquality.conf | grep dcredit"
cat /etc/security/pwquality.conf | grep dcredit
echo
echo "# 이전에 사용하던 패스워드에서 사용한 문자 허용 금지 수 설정(difok = 4)"
echo "cat /etc/security/pwquality.conf | grep difok"
cat /etc/security/pwquality.conf | grep difok
echo 
echo "# 소문자 최소 사용 수 설정(lcredit = -1)"
echo "cat /etc/security/pwquality.conf | grep lcredit"
cat /etc/security/pwquality.conf | grep lcredit
echo 
echo "# 동일한 타입(대소문자, 숫자, 특수문자)의 최대 허용 연속 문자 수 설정(maxclassrepeat = 4)"
echo "cat /etc/security/pwquality.conf | grep maxclassrepeat"
cat /etc/security/pwquality.conf | grep maxclassrepeat
echo 
echo "# 동일 문자 사용 최대 허용 문자 수 설정(maxrepeat = 3)"
echo "cat /etc/security/pwquality.conf | grep maxrepeat"
cat /etc/security/pwquality.conf | grep maxrepeat
echo 
echo "# 패스워드 최소 길이 설정(minlen = 12)"
echo "cat /etc/security/pwquality.conf | grep minlen"
cat /etc/security/pwquality.conf | grep minlen
echo 
echo "# 특수문자 최소 사용 수 설정(ocredit = -1)"
echo "cat /etc/security/pwquality.conf | grep ocredit"
cat /etc/security/pwquality.conf | grep ocredit
echo 
echo "# 대문자 최소 사용 수 설정(ucredit = -1)"
echo "cat /etc/security/pwquality.conf | grep ucredit"
cat /etc/security/pwquality.conf | grep ucredit
echo
echo
echo "4.1.3 계정 잠금 임계값 설정"
echo "# 패스워드 입력 실패시 잠금 (deny =3)"
echo "$ cat /etc/security/faillock.conf | grep '^deny'"
cat /etc/security/faillock.conf | grep '^deny'
echo
echo "# 900 초 동안 연속 인증 실패시 계정 잠김(fail_interval = 900)"
echo "$ cat /etc/security/faillock.conf | grep '^fail_interval'"
cat /etc/security/faillock.conf | grep '^fail_interval'
echo
echo "# 600 초 후 계정 해제 (unlock_time = 600)"
echo "$ cat /etc/security/faillock.conf | grep '^unlock_time'"
cat /etc/security/faillock.conf | grep '^unlock_time'
echo
echo
echo "4.1.4 패스워드 파일 보호"
echo "# shadow 파일이 존재 확인"
echo "ll /etc/shadow"
ls -ltr /etc/shadow
echo 
echo "# passwd 파일 password를 x로 표시"
echo "cat /etc/passwd | grep dmeta"
cat /etc/passwd | grep dmeta
echo 
echo 
echo "4.1.5 root 이외의 UID가 ‘0’금지"
echo "# UID 확인한다. "
echo "$ cat /etc/passwd | grep 'x:0:'"
cat /etc/passwd | grep 'x:0:'
echo
echo
echo "4.1.6  root 계정 su 제한"
echo "# su 로 root 접속 되는지 확인한다."
echo "$ su – root"
/usr/bin/su - root << EOF
dmeta!@34
EOF
echo
echo
echo "4.1.7 패스워드 최대 사용기간 설정,패스워드 최소 사용기간 설정"
echo "# 패스워드 최소 길이, 패스워드 최대 사용기간 설정, 패스워드 최소 사용기간 설정"
echo "- PASS_MIN_LEN    12"
echo "- PASS_MAX_DAYS   90"
echo "- PASS_MIN_DAYS   1"
echo
echo "$ cat /etc/login.defs | grep '^PASS_M'"
cat /etc/login.defs | grep '^PASS_M'
echo
echo
echo "4.1.8 root 계정 원격 접속 제한"
echo "# bash 사용 계정 확인"
echo "$ cat /etc/passwd | grep bash"
cat /etc/passwd | grep bash
echo
echo
echo "4.1.9 관리자 그룹에 최소한의 계정 포함"
echo "# root 그룹에 최소한의 계정 포함"
echo "$ sudo cat /etc/gshadow | grep root"
sudo cat /etc/gshadow | grep root
echo
echo
echo "4.1.10 동일한 UID 금지"
echo "# uid 가 같은 것이 있는지 확인"
echo "$ cat /etc/passwd | awk -F: '{print $3,$1}' | sort -n"
cat /etc/passwd | awk -F: '{print $3,$1}' | sort -n
echo
echo
echo "4.1.11 사용자 shell 점검"
echo "# 사용자 shell 확인"
echo "$ cat /etc/passwd | awk -F: '{print $1, $7}' | egrep 'bin/bash|bin/ksh'"
cat /etc/passwd | awk -F: '{print $1, $7}' | egrep 'bin/bash|bin/ksh'
echo
echo
echo "4.1.12 Session Timeout 설정"
echo "# ssh session timeout 설정값이 300 설정 확인"
echo "$ sudo cat /etc/ssh/sshd_config | grep ClientAliveInterval"
sudo cat /etc/ssh/sshd_config | grep ClientAliveInterval
echo
echo
echo "4.1.13 root 홈, 패스 디렉터리 권한 및 패스 설정"
echo "# path 환경변수"
echo "$ echo $PATH | grep "\.:" | wc -l"
echo $PATH | grep "\.:" | wc -l
echo
echo
echo "4.1.14 파일 및 디렉터리 소유자 설정"
echo "$ sudo find / -nouser -print"
echo "$ sudo find / -nogroup -print"
sudo find / -nouser -print
sudo find / -nogroup -print
echo
echo
echo "4.1.15 파일 및 디렉터리 소유자 설정"
echo "/etc/passwd 파일 소유자  및  권한 설정(644)"
ls -l /etc/passwd
echo
echo "/etc/shadow 파일 소유자 및 권한 설정(400)"
ls -l /etc/shadow
echo
echo "/etc/hosts 파일 소유자 및 권한 설정(644)"
ls -l /etc/hosts
echo
echo "/etc/(x)inetd.conf 파일 소유자 및 권한 설정 (미사용)"
ls -al /etc/xinetd.d/
echo
echo "/etc/syslog.conf 파일 소유자  및 권한 설정 (미사용)"
ls /etc/syslog.conf
echo
echo "/etc/services 파일 소유자 및 권한 설정(644)"
ls -al /etc/services
echo
echo
echo "4.1.16 SUID, SGID, Sticky bit 설정 파일 점검"
echo "User 사용 파일 중 SUID, SGID, Sticky bit 설정 파일 있는지 확인한다."
echo "$ sudo find / -xdev -user root -type f \( -perm -04000 -o -perm -02000 \) -exec ls -al {} \;"
sudo find / -xdev -user root -type f \( -perm -04000 -o -perm -02000 \) -exec ls -al {} \;
echo
echo
echo "4.1.17 사용자, 시스템 시작파일 및 환경파일 소유자 및 권한 설정"
echo "user : dmeta "
echo "ls -al /home/dmeta/ | grep bash"
ls -al /home/dmeta/ | grep bash
echo
echo "user : tomcat"
echo "sudo ls -al /home/tomcat/ | grep bash"
sudo ls -al /home/tomcat/ | grep bash
echo
echo "profile "
echo "ls -al /etc/profile"
ls -al /etc/profile
echo
echo
echo "4.1.18 world writable 파일 점검"
echo "$ sudo find /apps -type f -perm -2 -exec ls -l {} \;"
sudo find /apps -type f -perm -2 -exec ls -l {} \;
echo
echo
echo "4.1.19 /dev에 존재하지 않는 device 파일 점검"
echo "$ sudo find /dev -type f -exec ls -l {} \;"
sudo find /dev -type f -exec ls -l {} \;
echo
echo
echo "4.1.20 $HOME/.rhosts, hosts.equiv 사용 금지"
echo "ls –al /home/dmeta/.rhosts"
ls –al /home/dmeta/.rhosts
echo 
echo "ls -al /etc/hosts.equiv"
ls -al /etc/hosts.equiv
echo
echo
echo "4.1.21 접속 IP 및 포트 제한"
echo "- mysql :3306"
echo "- Admin Web: http 8000, Https 8443"
echo "- RabbiMQ :5672, 15672"
echo
echo "$ sudo firewall-cmd --list-all"
sudo firewall-cmd --list-all
echo
echo
echo "4.1.22 hosts.lpd 파일 소유자 및 권한 설정"
echo "ls -al /etc/hosts.lpd"
ls -al /etc/hosts.lpd
echo
echo
echo "4.1.23 UMASK 설정 관리(022)"
echo "cat /etc/profile | grep umask"
cat /etc/profile | grep umask
echo 
echo "cat /etc/bashrc | grep umask"
cat /etc/bashrc | grep umask
echo
echo
echo "4.1.24 홈디렉토리 소유자 및 권한 설정"
echo "ls -al /home/"
ls -al /home/ 
echo
echo "cat /etc/passwd | grep bash"
cat /etc/passwd | grep bash
echo
echo
echo "4.1.25 숨겨진 파일 및 디렉토리 검색 및 제거"
echo "$ sudo find /apps -type f -name '.*'"
sudo find /apps -type f -name ".*"
echo
echo "$ sudo find /apps -type d -name '.*'"
sudo find /apps -type d -name ".*"
echo
echo
echo "4.1.26 finger 서비스 비활성화"
echo "sudo systemctl status finger"
sudo systemctl status finger
echo
echo "cat /etc/passwd | grep ftp"
cat /etc/passwd | grep ftp
echo
echo "ls -alL /etc/xinetd.d/* | egrep 'rsh|rlogin|rexec' | egrep –v 'grep|klogin|kshell|kexec'"
ls -alL /etc/xinetd.d/* | egrep "rsh|rlogin|rexec" | egrep –v "grep|klogin|kshell|kexec"
echo 
echo "ls –al /etc/cron.deny"
ls –al /etc/cron.deny
echo
echo "sudo ls -alL /etc/xinetd.d/* | egrep '(echo|discard|daytime|charge)'"
sudo ls -alL /etc/xinetd.d/* | egrep '(echo|discard|daytime|charge)'
echo
echo "ps -ef | egrep 'nfsd|statd|mountd'"
ps -ef | egrep "nfsd|statd|mountd"
echo
echo
echo "4.1.27 finger 서비스 비활성화"
echo "ps -ef | grep autofs"
ps -ef | grep autofs
echo 
echo "sudo systemctl status rpcbind"
sudo systemctl status rpcbind
echo
echo "sudo systemctl status ypserv ypbind ypxfrd rpc.yppasswdd rpc.ypupdated"
sudo systemctl status ypserv ypbind ypxfrd rpc.yppasswdd rpc.ypupdated
echo
echo "sudo systemctl status tftp.service"
sudo systemctl status tftp.service
echo
echo "sudo systemctl status talkd.service"
sudo systemctl status talkd.service
echo
echo "rpm -q sendmail"
rpm -q sendmail
echo
echo
echo "4.1.28 finger 서비스 비활성화"
echo "rpm -q bind"
rpm -q bind
echo
echo "sudo systemctl status httpd"
sudo systemctl status httpd
echo
echo
echo "4.1.29 ssh 원격접속 허용"
echo "sudo systemctl status sshd"
sudo systemctl status sshd | head
echo
echo "sudo netstat -anp | egrep -E '22.*sshd'"
sudo netstat -anp | egrep -E "22.*sshd"
echo
echo
echo "4.1.30 ftp 서비스 확인"
echo "netstat -an | grep LISTEN | grep  21"
netstat -an | grep LISTEN | grep  21
echo
echo "cat /etc/passwd | grep ftp"
cat /etc/passwd | grep ftp
echo
echo "ls -al /etc/ftpusers"
ls -al /etc/ftpusers
echo
echo "ls -al /etc/ftpf/ftpusers"
ls -al /etc/ftpf/ftpusers
echo
echo
echo "4.1.31 at 파일 소유자 및 권한 설정"
echo "ls -l /etc/at.allow"
ls -l /etc/at.allow
echo
echo
echo "4.1.32 SNMP 서비스 구동 점검"
echo "rpm -q net-snmp"
rpm -q net-snmp
echo 
echo 
echo "4.1.33 로그온 시 경고 메시지 제공"
echo "cat /etc/issue"
cat /etc/issue
echo "$ ssh dmeta@192.168.132.183"
ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no dmeta@192.168.132.183 

echo
echo
echo "4.1.34 서비스 관리"
echo "  - NFS 설정파일 접근 제한"
echo "ps -ef | egrep 'nfsd|statd|mountd'"
ps -ef | egrep "nfsd|statd|mountd"
echo
echo "  - expn, vrfy 명령어 제한"
echo "expn"
echo
echo "vrfy"
vrfy
echo
echo "  - Apache 웹 서비스 정보 숨김(미설치) "
echo "sudo systemctl status httpd"
sudo systemctl status httpd | head
echo
echo
fi

if [[ ${EXE} == "ALL" ]] | [[ ${EXE} == "2" ]] ; then
echo "4.2.1 정책에 따른 시스템 로깅 설정"
echo "sudo systemctl status syslog.service"
sudo systemctl status syslog.service | head
echo
echo "sudo systemctl status auditd.service"
sudo systemctl status auditd.service | head
echo 
echo
echo "4.2.2 기본 계정의 패스워드, 권한 등을 변경하여 사용"
echo "$ sudo mariadb -u root -p mysql -e \"select User, Password from user where User = 'root';\""
sudo mariadb -u root -p'dmeta!@34' mysql -e "select User, Password from user where User = 'root';"
echo 
echo
echo "4.2.3 데이터베이스의 불필요 계정을 제거하거나, 잠금설정 후 사용"
echo "$ sudo mariadb -u root -p mysql -e \"select Host, User, password_expired from user where Host = 'localhost';\""
sudo mariadb -u root -p'dmeta!@34' mysql -e "select Host, User, password_expired from user where Host = 'localhost';"
echo
echo
echo "4.2.4 패스워드의 사용기간 및 복잡도를 기관 정책에 맞도록 설정"
echo "$ sudo mariadb -u root -p mysql -e \"select Host, User, password_expired, plugin from user where Host = 'localhost';\“"
sudo mariadb -u root -p'dmeta!@34' mysql -e "select Host, User, password_expired, plugin from user where Host = 'localhost';"
echo "$ sudo mariadb -u root -p mysql -e \"show variables like 'strict_password_validation';\""
sudo mariadb -u root -p'dmeta!@34' mysql -e "show variables like 'strict_password_validation';"
echo
echo
echo "4.2.5 데이터베이스 관리자 권한"
echo "$ sudo mariadb -u root -p mysql -e \"select Host, User, Select_priv, Insert_priv, Update_priv, Delete_priv, Create_priv, Drop_priv, Reload_priv, Shutdown_priv, Grant_priv from user;\""
sudo mariadb -u root -p'dmeta!@34' mysql -e "select Host, User, Select_priv, Insert_priv, Update_priv, Delete_priv, Create_priv, Drop_priv, Reload_priv, Shutdown_priv, Grant_priv from user;"
echo
echo
echo "4.2.6 DB 사용자 계정을 개별적으로 부여하여 사용"
echo "$ sudo mariadb -u root -p mysql -e \"select Host, User from user;\""
sudo mariadb -u root -p'dmeta!@34' mysql -e "select Host, User from user;"
echo
echo
echo "4.2.7 원격에서 DB 서버로의 접속 제한"
echo "$ sudo mariadb -u dmeta -p mysql -e \"select Host, User from user;\""
sudo mariadb -u dmeta -p'dmeta!@34' mysql -e "select Host, User from user;"
echo
echo
echo "4.2.8 데이터베이스의 주요 파일 보호"
echo "$ cat /etc/profile | grep umask"
cat /etc/profile | grep umask
echo
echo
echo "4.2.9 데이터베이스의 주요 설정"
echo "$ ls -al /etc/my.cnf"
ls -al /etc/my.cnf
echo
echo
echo "4.2.10 인가되지 않은 GRANT OPTION 사용 제한"
echo "$ sudo mariadb -u root -p mysql -e \"select Host, User, Grant_priv from user;\""
sudo mariadb -u root -p'dmeta!@34' mysql -e "select Host, User, Grant_priv from user;"
echo
echo
echo "4.2.11 데이터베이스에 대해 최신 보안패치"
echo "$ mariadb --version"
mariadb --version
fi
