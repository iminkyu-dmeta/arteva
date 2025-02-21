#!/usr/bin/bash

DATE=$1
if [ "${DATE}" == "" ] ; then
  DATE=10
fi

RESULTDIR=/logs/RCS/result

find ${RESULTDIR} -name '*' -mtime +${DATE} -delete

rm -rf /tmp/nems_gc.log
rm -rf /tmp/ThreadDump.txt
