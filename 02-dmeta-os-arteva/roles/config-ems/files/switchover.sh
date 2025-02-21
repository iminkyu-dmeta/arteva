#!/bin/bash

VRRP_NAME="vrrpd"
VRRP_PID=$(ps -eo pid,args | grep -E "${VRRP_NAME}" |  grep -v grep | awk '{ printf( "%s\n",$1); }')

kill -USR2 ${VRRP_PID}

