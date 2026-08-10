#!/usr/bin/env python

import csv
import sys
import yaml
import os, sys
import glob

FIELDS_VAR = ["HOSTNAME","VMHost","NOTES","VMIP","VMPREFIX","VMGW","IPC_IP","IPC_PREFIX","IPC_GATEWAY","SIGNAL_IP","SIGNAL_GW","SIGNAL_PREFIX","VIP","DISK2ND"]
NE_NAME = ["PresenceEMS1","PresenceEMS2","Presence1","Presence2","XDMS1","XDMS2","PresenceDB1","PresenceDB2","XDMSDB1","XDMSDB2"]
NE_SIZE = len(NE_NAME)

SETUP=sys.argv[1]
fname=sys.argv[2]
csv_data = []

def data_string(field, value):
    data = '%s %s\n' % (field, value)
    return data

def list_string(pd):
    data = ""
    for key, value in pd.items():
        data = data + '%s: %s\n' % (key, value)

    return data

fpath = os.path.join('..', '..', '01-mcptx-vmdeploy-presence', 'input')
fullpath = os.path.join(fpath, fname)
location = glob.glob(fullpath)
print(location)
SIZE = len(location)

if SIZE == 1:
    filename = " ".join(location)
    basename = os.path.basename(filename)
    print(filename)
    print(basename)
    with open(filename, "r") as csvfile:
        reader = csv.reader(csvfile)
        if SETUP == 'online':
            for row in reader:
                if row[0] == 'Name':
                    with open(fpath + '/ACTIVE-' + basename, 'w') as active:
                        wr = csv.writer(active)
                        wr.writerow(row)
                    with open(fpath + '/STANDBY-' + basename, 'w') as standby:
                        wr = csv.writer(standby)
                        wr.writerow(row)
                if row[5][-1:] == '1':
                    with open(fpath + '/ACTIVE-' + basename, 'a') as active:
                        wr = csv.writer(active)
                        wr.writerow(row)
                elif row[5][-1:] == '2':
                    with open(fpath + '/STANDBY-' + basename, 'a') as active:
                        wr = csv.writer(active)
                        wr.writerow(row)
            #os.rename(filename, fpath + '/.' + basename)
        elif SETUP == 'online-ne':
            for row in reader:
                if row[0] == 'Name':
                    for ne in NE_NAME:
                        ne = ne[:-1]
                        with open(fpath + '/ACTIVE-' + ne + '-' + basename, 'w') as active:
                            wr = csv.writer(active)
                            wr.writerow(row)
                        with open(fpath + '/STANDBY-' + ne + '-' + basename, 'w') as standby:
                            wr = csv.writer(standby)
                            wr.writerow(row)
                else:
                    ne = row[5][:-1]
                    if row[5][-1:] == '1':
                        with open(fpath + '/ACTIVE-' + ne + '-' + basename, 'a') as active:
                            wr = csv.writer(active)
                            wr.writerow(row)
                    elif row[5][-1:] == '2':
                        with open(fpath + '/STANDBY-' + ne + '-' + basename, 'a') as active:
                            wr = csv.writer(active)
                            wr.writerow(row)
            #os.rename(filename, fpath + '/.' + basename)

else:
    print("Many file or Not search file")

GVAPATH = os.path.join('..', 'inventory', 'group_vars', 'all.yml')
with open(GVAPATH, 'a') as outfile:
    outfile.write("\n")
    outfile.write('  ONLINE: True\n')
