#!/usr/bin/env python

import csv
import sys
import yaml
import os, sys
import ipaddress
import json
import shutil

try:
    import configparser as ConfigParser
except:
    import ConfigParser

def loadconfig(conf_file):
    if os.path.exists(conf_file)==False:
        raise Exception("%s file does not exist.\n" % conf_file)

    config=ConfigParser.ConfigParser()
    config.read(conf_file)

    section = config.sections()

    return config, section

def removeAllFile(filePath):
    if os.path.exists(filePath):
        filelist = [ f for f in os.listdir(filePath) ]
        for f in filelist:
            if os.path.isfile(filePath + '/' + f):
                #print(f)
                os.remove(filePath + '/' + f)

def keyvars(field, value):
    data = '%s %s\n' % (field, value)
    return data

def vars_str(pd):
    data = ""
    for key, value in pd.items():
        data = data + '%s: %s\n' % (key, value)

    return data

def disk_calc(partition, size):
    pd = {}
    if int(size) < 0:
        size = 0

    disk = []
    for key, value in partition.items():
        disk.append(key.lower())
        if size >= 0:
            pd[key] = int(float(value[0]) + (size * float(value[1])))
    
    pd['EXTEND'] = disk

    return vars_str(pd)

PWD=os.getcwd()
HOSTPWD=os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

# remove old host vars file
HAPATH = os.path.join(HOSTPWD, 'inventory', 'host_vars')
removeAllFile(HAPATH)

HOST_VARS_PATH = os.path.join('..', 'inventory', 'host_vars', '')
GROUP_VARS_PATH = os.path.join('..', 'inventory', 'group_vars', 'all.yml')
GEO_CONFIG_PATH = os.path.join('../','roles', 'config-db-table-create', 'vars', 'main.yml')
if os.path.isfile(GEO_CONFIG_PATH):
    os.remove(GEO_CONFIG_PATH)

def read_Variables(json_data, csv_file):
    csv_data = {}
    add_route = []

    with open(csv_file, "r") as cf:
        reader = csv.DictReader(cf)

        for row in reader:
            disk_size = {}
            host_data = []
            with open(HOST_VARS_PATH + row['Name'] + '.yml', 'w') as host_vars:
                for field in reader.fieldnames:
                    if row[field] and not row[field].isspace():
                        host_data.append('%s: %s\n' % (field, row[field]))
                        if field == 'Target':
                            if row[field].split('/')[0] == row['SIGNAL2GW'][:-1] or row[field].split('/')[0] == row['SIGNALGW'][:-1]:
                                print("Same prefix " + row[field])
                            else:
                                str_match = [ s for s in add_route if s.__contains__(row[field].rstrip())]
                                if str_match:
                                    print(str_match)
                                else:
                                    add_route.append(row[field])

                    if field == 'Disk2nd': 
                        group = row['Notes'][:-1]
                        partition = json_data[group]['Partition']
                        if not row[field] or row[field].isspace() or int(row[field]) < 0:
                            host_data.append('%s: %s\n' % (field, "0"))
                            disk_size = disk_calc(partition, 0)
                        else:
                            disk_size = disk_calc(partition, int(row['Disk2nd']))
    
                host_vars.write(''.join(host_data))
                host_vars.write(''.join(disk_size))
                #if add_route:
                #    host_vars.write(keyvars("ADD_TARGET: ", add_route))

                host_vars.close()

                csv_data[row['Notes']] = dict(row)

            headers = reader.fieldnames

    return csv_data, headers, add_route

def update_Variables(json_data, csv_data, headers, add_route, online=None):
    VNF = json_data['VNF']
    NE = json_data['NE']
    NEGROUP = json_data['NEGroup']

    print(headers)
    print(NE)

    ## group_vars all.yml 
    EMS = VNF + "EMS"
    group_data = []
    group_data.append("---\n\n")
    group_data.append(keyvars('  EMSVIP:', csv_data[EMS + '1']['SIGNALVIP']))
    group_data.append("\n")
    group_data.append("  EMS_SERVER_LIST:\n")
    group_data.append(keyvars('    - server', csv_data[EMS + '1']['IPCIP']))
    group_data.append(keyvars('    - server', csv_data[EMS + '1']['IPCIP']))
    group_data.append("\n")
    group_data.append(keyvars('  VNF:', VNF.lower()))
    group_data.append(keyvars('  NE:', NE))
    group_data.append(keyvars('  NEGroup:', NEGROUP))

    for key, value in json_data['group_vars'].items():
        group_data.append(keyvars('  %s:' % key, value))
    
    if online == 'ONLINE':
        group_data.append('\n  ONLINE: True\n')
    
    with open(GROUP_VARS_PATH, 'w') as gv:
        gv.write(''.join(group_data))
        gv.close()

    for notes in NE:
        print("%s %s" % (notes, csv_data[notes]['Name']))

        host_data = []
        nic_list = []
        bnic_list = []
        ne_group = notes[:-1]

        with open(HOST_VARS_PATH + csv_data[notes]['Name'] + '.yml', 'a') as hf:
            for nic in json_data['NICLIST']:
                try:
                    if csv_data[notes][nic+'IP'] and not csv_data[notes][nic+'IP'].isspace() : 
                        nic_list.append(nic)
                except KeyError as e:
                    print(nic)
                    #continue

            print(nic_list)
            host_data.append(keyvars('NICLIST:', nic_list))
                
            if json_data['BONDINGLIST']:
                for key, value in json_data['BONDINGLIST'].items():
                    try:
                        if csv_data[notes][key+'IP'] and not csv_data[notes][key+'IP'].isspace() : 
                            bnic_list.append(key)

                            host_data.append(keyvars(key.upper() + 'ifname:', json_data['BONDINGLIST'][key].split(',')))
                    except KeyError as e:
                        print(key)
                     
                if bnic_list:
                    host_data.append(keyvars('BONDINGLIST:', bnic_list))

            vardict = {}
            num = notes[-1:]
            vardict['num'] = num
            site = csv_data[notes]['Name'][:3]
            if site == 'akr' or site == 'all':
                vardict['site'] = 'COMM'
            else:
                vardict['site'] = 'LAB'
            if add_route:
                vardict['add_route'] = add_route
            if int(num)% 2 == 1:
                vardict['peer'] = '2'
                vardict['master'] = 'repl' + '2'
                vardict['slave'] = 'repl' + '1'
                vardict['priority'] = '10' 
            elif int(num)% 2 == 0:
                vardict['peer'] = '1'
                vardict['priority'] = '5' 
                vardict['master'] = 'repl' + '1'
                vardict['slave'] = 'repl' + '2'

            ## common vars
            host_data.append(keyvars('NE_Group:', notes[:-1]))
            peer = notes[:-1] + vardict['peer']
            host_data.append(keyvars('PEER_IPCIP:', csv_data[peer]['IPCIP']))
            host_data.append(keyvars('PEER_SIGNALIP:', csv_data[peer]['SIGNALIP']))

            try:
                for key, value in json_data[ne_group]['Host_vars'].items():
                    if len(value.split(',')) == 1:
                        host_data.append(keyvars(key + ":", vardict[value]))
                    elif len(value.split(',')) == 2:
                        host_data.append(keyvars(key + ":", csv_data[value.split(',')[0]][value.split(',')[1]]))
            except KeyError as e:
                print("Not keys")
                #continue

            print(host_data)
            print()
            hf.write(''.join(host_data))

def read_Json(filename):
    with open(filename, 'r') as js:
        json_data = json.load(js)

    return json_data

def main():
    ## read json file 
    json_file=os.path.join('..', 'script', 'create_vars.json')
    json_data = read_Json(json_file)

    csv_file = sys.argv[1]
    online = sys.argv[2]
    #read_Variables(json_data, csv_file, online)
    csvdata, headers, add_route = read_Variables(json_data, csv_file)

    update_Variables(json_data, csvdata, headers, add_route, online)

if __name__=='__main__':
    main()
