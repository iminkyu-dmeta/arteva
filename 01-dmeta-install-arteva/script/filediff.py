#!/usr/bin/python

import os,sys
import string
import difflib
import argparse
from difflib import Differ
from difflib import SequenceMatcher
from pprint import pprint
import urllib.parse

def write_files(filepath, result):
    if result:
        with open(filepath, 'w') as wf:
            wf.writelines(result)
    else:
        with open(filepath, 'w') as wf:
            pass

def read_file(filepath, opt=None):
    with open(filepath, 'r') as rf:
        result = rf.read()
        
    return result

def readlines_file(filepath, opt=None):
    with open(filepath, 'r') as rf:
        result = rf.readlines()

    return result

def diff_find(diff, opt):
    pre_list = []
    post_list = []
    diff_rpm_list = []

    for idx, line in enumerate(diff.split(',')):
        pos_m = line.find('- ')
        pos_p = line.find('+ ')
        pos_q = line.find('? ')
    
        if pos_q == 0:
            qusline = line.strip()
            diff_rpm_list.append(qusline)
            diff_rpm_list.append('\n')

        if pos_m == 0 :
            preline = line.strip()
            prename = line[2:].split('-')[:-2]
            prename = '-'.join(prename)
            if opt:
                pre_list.append(prename)
            else:
                pre_list.append(preline[2:])
            diff_rpm_list.append(preline)
            diff_rpm_list.append('\n')
    
        if pos_p == 0 :
            posline = line.strip()
            posname = line[2:].split('-')[:-2]
            posname = '-'.join(posname)
            if opt:
                post_list.append(posname)
            else:
                post_list.append(posline[2:])
            diff_rpm_list.append(posline)
            diff_rpm_list.append('\n')

    return pre_list, post_list, diff_rpm_list

def check_rpm(rpm_list, post_list, post_result, opt=None):
    updated_rpm = []
    not_updated_rpm = []
    deleted_rpm = []
    not_deleted_rpm = []

    for name in rpm_list:
        if ':' in name:
            name = name.split(':')
            name = name[0][:-1] + name[1]
        if 'rpm' in name:
            name = '.'.join(name.split('.')[:-1])

        str_match = [ s for s in post_list if s.__contains__(name.rstrip())]
        if str_match:
            if opt == 'delete':
                print('not deleted rpm : %s' % name)
                not_deleted_rpm.append(name)
            elif opt == 'update':
                updated_rpm.append(name)
                
        else:
            pstr_match = [ s for s in post_result if s.__contains__(name.rstrip())]
            if pstr_match:
                if opt == 'delete':
                    print('not deleted rpm : %s' % name)
                    not_deleted_rpm.append(name)
                elif opt == 'update':
                    continue

            else:
                if opt == 'update':
                    print('not updated rpm : %s' % name)
                    not_updated_rpm.append(name)
                elif opt == 'delete':
                    deleted_rpm.append(name)

    return updated_rpm, not_updated_rpm, deleted_rpm, not_deleted_rpm

def check_update_denpendance_rpm(dependance_rpm_list, add_updated_rpm):
    add_dep_rpm = []
    add_not_dep_rpm = []
    for idx, rpm in enumerate(add_updated_rpm):
        rpm_name = '-'.join(rpm.split('-')[:-2]).rstrip()
        rpm_fname = rpm.split('.')[-1:][0].rstrip()
        str_match = [ s for s in dependance_rpm_list if s.__contains__(rpm_name.rstrip()) and s.__contains__(rpm_fname.rstrip())]
        #str_match = set(str_match)
        #str_match = list(str_match)
        for sm in str_match:
            strname = '-'.join(sm.split('-')[:-2]).rstrip()
            if rpm_name != strname:
                str_match.remove(sm)
        if str_match:
            size = len(str_match)
            mat = False
            for st in str_match:
                if ':' in st:
                    stp = st.split(':')
                    stu = stp[0][:-1] + stp[1]
                if rpm in stu:
                    add_dep_rpm.append(st)
                    mat = True
                    break
                else:
                    vdep = '-'.join(rpm.split('-')[:-1])
                    vstu = '-'.join(stu.split('-')[:-1])
                    if vdep in vstu:
                        add_dep_rpm.append(st)
                        mat = True
                        #if opt == 'verdep':
                        #    print('cur : %s , dep : %s' % (rpm, stu))
                        break
            if not mat:
                print('not match dependence list : %s %s' % (rpm, str_match))
                add_not_dep_rpm.append(rpm)
        else:
            print('not dependence rpm : %s' % rpm)
            add_not_dep_rpm.append(rpm)
    
    return add_dep_rpm, add_not_dep_rpm

def check_delete_denpendance_rpm(dependance_rpm_list, deleted_rpm):
    del_dep_rpm = []
    del_not_dep_rpm = []
    for idx, rpm in enumerate(deleted_rpm):
        rpm_name = '-'.join(rpm.split('-')[:-2]).rstrip()
        rpm_fname = rpm.split('.')[-1:][0].rstrip()
        str_match = [ s for s in dependance_rpm_list if s.__contains__(rpm_name.rstrip())]
        #str_match = [ s for s in dependance_rpm_list if s.__contains__(rpm_name.rstrip()) and s.__contains__(rpm_fname.rstrip())]

        for idx, sm in enumerate(str_match):
            strc = sm[:3]
            strname = '-'.join(sm.split('-')[:-2]).rstrip()
            if 'dnf' == strc:
                str_match.pop(idx)
            if rpm_name != strname:
                str_match.pop(idx)

        if str_match:
            size = len(str_match)
            mat = False
            for st in str_match:
                if ':' in st:
                    stp = st.split(':')
                    stu = stp[0][:-1] + st[1]

                if rpm_name in stu:
                    del_dep_rpm.append(st)
                    mat = True
                    break
                else:
                    vdep = '-'.join(rpm.split('-')[:-1])
                    vstu = '-'.join(stu.split('-')[:-1])
                    if vdep in vstu:
                        del_dep_rpm.append(st)
                        mat = True
                        #if opt == 'verdep':
                        print('cur : %s , dep : %s' % (rpm, stu))
                        break
            if not mat:
                print('not match dependence list : %s %s' % (rpm, str_match))
                del_not_dep_rpm.append(rpm)
        else:
            print('not dependence rpm : %s' % rpm)
            del_not_dep_rpm.append(rpm)

    return del_dep_rpm, del_not_dep_rpm

def search_fname(rpm_list, sname):
    for name in rpm_list:
        if sname in name:
            return name
    
def diff_files(pre_file, post_file, host, input_file=None, opt=None):
    ## ref-pre-rpmall-[hostname].txt
    pre_filepath = os.path.join('..', 'file', 'RPM-LIST', pre_file)
    ## ref-post-rpmall-[hostname].txt
    post_filepath = os.path.join('..', 'file', 'RPM-LIST', post_file)

    pre_result = readlines_file(pre_filepath, None)
    post_result = readlines_file(post_filepath, None)
    prename_list = []
    postname_list = []
    pre_list = []
    post_list = []

    sm = SequenceMatcher(a=pre_result, b=post_result)
    if sm.ratio() == 1:
        if not input_file:
            print("Match!!!")

    else:
        d = Differ()
        difference = list(d.compare(pre_result, post_result))
        compare_result = os.path.join('../', 'file', 'RPM-LIST', host + '-result.txt') 
        diff_result = os.path.join('../', 'file', 'RPM-LIST', 'diff-rpm-list-' + host + '.txt') 
        diff = ','.join(difference)

        pre_list, post_list, diff_rpm_list = diff_find(diff, None)

        ## diff result diff-rpm-list-[hostname].txt
        write_files(compare_result, difference)
        write_files(diff_result, diff_rpm_list)

        if not input_file:
            if post_list:
                for pos in post_list:
                    print('not Match rpm: %s' % (pos))

            print("not Match!!!")
        
    if input_file:
        input_filepath = os.path.join('..', 'file', input_file)
        updated_rpmfile = os.path.join('../', 'file', 'RPM-LIST', 'updated-target-rpm-list-' + host + '.txt')
        depende_rpmfile = os.path.join('../', 'file', 'RPM-LIST', 'updated-dep-rpm-list-' + host + '.txt')
        deleted_rpmfile = os.path.join('../', 'file', 'RPM-LIST', 'deleted-target-rpm-list-' + host + '.txt')
        delwhol_rpmfile = os.path.join('../', 'file', 'RPM-LIST', 'deleted-whole-rpm-list-' + host + '.txt')
        deldepe_rpmfile = os.path.join('../', 'file', 'RPM-LIST', 'deleted-dep-rpm-list-' + host + '.txt')
        delnotd_rpmfile = os.path.join('../', 'file', 'RPM-LIST', 'deleted-not-dep-rpm-list-' + host + '.txt')
        updated_rpm = []
        deleted_rpm = []
        not_updated_rpm = []
        not_deleted_rpm = []

        ## Check if the input file has been updated
        update_rpm_lists = readlines_file(input_filepath, None)

        for name in pre_list:
            fname = name.split('-')
            fname = '-'.join(fname[:-2])
            prename_list.append(fname)

        for name in post_list:
            fname = name.split('-')
            fname = '-'.join(fname[:-2])
            postname_list.append(fname)

        updated_rpm, not_updated_rpm, deleted_rpm, not_deleted_rpm = check_rpm(update_rpm_lists, post_list, post_result, opt)

        if not not_updated_rpm and not not_deleted_rpm:
            print("%s %s" % (pre_filepath, post_filepath))

        if updated_rpm:
            write_files(updated_rpmfile, updated_rpm)
        if deleted_rpm:        
            write_files(deleted_rpmfile, deleted_rpm)

        ## Check if it has been updated with denpendancy
        dependance_file = 'ref-' + input_file.split('.')[0] + '-rpmdeplist.txt'
        dependance_rpm_file = os.path.join('..', 'file', 'RPM-LIST', dependance_file)
        dependance_rpm_list = readlines_file(dependance_rpm_file, None)

        #differ = list(d.compare(prename_list, postname_list))
        #differ = ','.join(differ)
        #prename_list, postname_list, diff_add_rpm_list = diff_find(differ, None)

        input_rpm_list = read_file(input_filepath, None)
        add_updated_rpm = []
        deleted_rpm = []
        if opt == 'update':
            for name in post_list:
                fname = name.split('-')
                fname = '-'.join(fname[:-2])
                if fname in input_rpm_list:
                    continue
                else:
                    add_updated_rpm.append(name)
        elif opt == 'delete':
            for name in pre_list:
                fname = name.split('-') 
                fname = '-'.join(fname[:-2])            
                if fname in input_rpm_list:                                    
                    continue                                                                
                else:                                                                                       
                    deleted_rpm.append(name)

        add_dep_rpm = []
        del_dep_rpm = []
        add_not_dep_rpm = []
        del_not_dep_rpm = []
        if add_updated_rpm:
            add_dep_rpm, add_not_dep_rpm = check_update_denpendance_rpm(dependance_rpm_list, add_updated_rpm)

        if deleted_rpm:
            del_dep_rpm, del_not_dep_rpm = check_delete_denpendance_rpm(dependance_rpm_list, deleted_rpm)
        
        if add_updated_rpm:
            add_updated_rpm = '\n'.join(add_updated_rpm)
            add_dep_rpm = '\n'.join(add_dep_rpm)
            add_not_dep_rpm = '\n'.join(add_not_dep_rpm)
            write_files(depende_rpmfile, add_updated_rpm)
        else:
            write_files(depende_rpmfile, None)

        if deleted_rpm:
            deleted_rpm = '\n'.join(deleted_rpm)
            del_dep_rpm = '\n'.join(del_dep_rpm)
            not_del_dep_rpm = '\n'.join(del_not_dep_rpm)
            write_files(delwhol_rpmfile, deleted_rpm)
            write_files(deldepe_rpmfile, del_dep_rpm)
            write_files(delnotd_rpmfile, del_not_dep_rpm)
        else:
            write_files(deldepe_rpmfile, None)

        if not not_updated_rpm and not add_not_dep_rpm and not not_deleted_rpm and not del_not_dep_rpm:
            print("Match!!!")
        else:
            print("Not Match!!!")

def main():
    parser = argparse.ArgumentParser(description='filediff')
    parser.add_argument('-r', dest='pre', help='before rpm list')
    parser.add_argument('-e', dest='post', help='after rpm list')
    parser.add_argument('-n', dest='host', help='hostname')
    parser.add_argument('-i', dest='input', help='input_file')
    parser.add_argument('-o', dest='options', help='options')
    
    args = parser.parse_args()
    pre_file = args.pre
    post_file = args.post
    host = args.host
    input_file = args.input
    opt = args.options
    diff_files(pre_file, post_file, host, input_file, opt)

if __name__=='__main__':
    main()

