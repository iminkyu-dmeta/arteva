#!/usr/bin/env python

import string
import sys
import os

STR=sys.argv[1]
ck=0

if "rpm" in STR:
    STR=STR.split('.rpm')

if ('x86_64' in STR) or ('i686' in STR) or ('noarch' in STR):
    ck=1
    arch=STR.split('.')[-1:][0]    
    STR=STR.split('.' + arch)[0]    
    
split=STR.split('-')
if '.el' in split[-1:][0] :
    ck=1
    release=split[-1:][0]
    version=split[-2:-1][0]
    name='-'.join(split[:-2])
    
print(ck)
