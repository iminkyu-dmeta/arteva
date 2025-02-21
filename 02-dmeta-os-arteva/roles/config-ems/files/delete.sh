#!/usr/bin/bash 
# PM stat-date delete script
echo "Delete stat-data for one month from today!"
PMDIR="/logs/PM"
BKDIR="${PMDIR}/Backup"

STATDATE=20
LOGDATE=10

#===========================
echo "Delete static log file"
find /logs/PM/ -name '*' -mtime +${STATDATE} -delete
find /logs/PM/Backup/ -name '*' -mtime +${LOGDATE} -delete

#===========================
#LOG
echo "Delete log-data for 10 days from today!"
TODAY=`date '+%Y%m%d' -d '1 day ago'`

export CURRENT_DIR=/apps/RCS/PM
/bin/mv /apps/RCS/PM/log/pm_stat.exe_0001.log  /apps/RCS/PM/log/pm_stat.exe_0001.log.$TODAY

find ${CURRENT_DIR}/log/ -name 'backtrace_pmstat_*' -mtime +${LOGDATE} -delete
find ${CURRENT_DIR}/log/ -name 'pm_stat.exe_*' -mtime +${LOGDATE} -delete
