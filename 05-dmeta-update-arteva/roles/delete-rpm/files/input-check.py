#!/usr/bin/env python

import string
import sys
import os

STR=sys.argv[1]

ARCH="x86_64"

if "rpm" in STR:
    STR=STR.split('.rpm')

STR=''.join(STR)

if ARCH in STR:
    arch=STR.split('.')[-1:][0]
    rpm=STR.split('.x86_64')[0]
    sep=rpm.split('-')
    size=len(sep)
    release=sep[size-1]
    version=sep[size-2]
    name='-'.join(sep[:-2])

    print(1)
else:
    print(0)
