#!/usr/bin/env python

import string
import os

# Private Enterprise numbers
Decimal=236
# IPv4 Flag
IPv4='01'

# Convert IP to hex
def ip2hex(ip) :
    ip1 = ''.join([hex(int(x)+256)[3:] for x in ip.split('.')])
    return ip1.upper()

# Convert private to Enterprise numbers 
def num2hex(num) :
    number = ''.join(["0x8" + hex(int(num)+256)[3:].zfill(7)])
    return number

    VIP = raw_input('INPUT EMS VIP : ')

    enterprise_number = num2hex(Decimal)
    hexip = ip2hex(VIP)
    engineID = enterprise_number + IPv4 + hexip

    print "=> " + engineID
