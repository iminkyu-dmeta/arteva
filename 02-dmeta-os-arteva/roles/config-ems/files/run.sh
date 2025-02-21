#!/bin/bash

if [ -z ${CLAYLOG} ]; then
        CLAYLOG=/log/RCS
fi

if [ -z ${CLAYHOME} ]; then
        CLAYHOME=/apps/RCS
fi

PNAME=pm_stat.exe
GROUPNAME=pm
GROUPID=1200

NPATH="${CLAYHOME}/PM"
LOGDIR="${CLAYHOME}/PM/log"
CONF="${NPATH}/conf/${PNAME}.conf"
BINPATH=${NPATH}/bin
LIBPATH=${NPATH}/lib
ROLE="unittest"
NOW=`date '+%Y%m%d-%H%M%S'`

if [ ! -d  "${LOGDIR}" ] ; then
        MKDIR_COMMAND="su - attps -c 'mkdir -p ${LOGDIR}'"
        eval ${MKDIR_COMMAND}
fi

if [ ! -d  "${CLAYLOG}/PM" ] ; then
        MKDIR_COMMAND="su - attps -c 'mkdir -p ${CLAYLOG}/PM'"
        eval ${MKDIR_COMMAND}
fi

COMMAND="su - attps -c 'cd ${BINPATH}; ./${PNAME} -s 1 -c ${CONF} -r ${ROLE} -l ${LOGDIR} >> ${LOGDIR}/${PNAME}_backtrace_${NOW}.log 2>&1 &'"

PID=$(pgrep -f "${PNAME} -s" | grep -v grep)
if [ -z ${PID} ]; then

   cd ${NPATH}/bin

   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./lib:./usr/lib64:/usr/lib64/mysql:/apps/RCS/PM/lib

   eval ${COMMAND}
   echo ${COMMAND}

   PID=$(pgrep -f "${PNAME} -s" | grep -v grep)
   printf ""
   if [ -z ${PID} ]; then
       printf "\nStart Failed - Please check "${PNAME}" log.\n\n"
       exit -1
   else
       printf "Successfully started pid ${PID}"
   fi
   printf "\n"
else
   printf "\n"${PNAME}" already running. pid ${PID}\n\n"
fi

## DELETE LOG
HOUR=`date '+%H'`
MINUTE=`date '+%M'`
if [ ${HOUR} == 00 ]; then
	/usr/bin/sh /apps/RCS/PM/delete.sh
fi

chown -R attps:pmoss /logs/PM/
