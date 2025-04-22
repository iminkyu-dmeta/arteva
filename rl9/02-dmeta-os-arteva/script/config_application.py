#!/usr/bin/python

import os, sys, re
import json
import difflib
import pymysql
import platform
import socket
import hashlib
import time
import argparse
import subprocess
from pwd import getpwnam
from datetime import datetime
from datetime import date
from datetime import timedelta
import urllib.parse
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XMLParser 
from xml.etree.ElementTree import Element, SubElement
from xml.dom import minidom
import csv

try:
    import http.client as httplib
except:
    import httplib

XML='<?xml version="1.0" encoding="EUC-KR"?>\r\n'

class MysqlDBAcc:
    def __init__(self, config):
        self.conn = pymysql.connect(**config)
        self.curs = self.conn.cursor()

    def select_sql(self, sql=None, fetchall=False, size=None):
        self.curs.execute(sql)

        if fetchall:
            result = self.curs.fetchall()
        elif not fetchall and size:
            result = self.curs.fetchmany(size)
        else:
            result = self.curs.fetchone()

        return result

    def instart_sql(self, sql=None, many=None):
        if many:
            self.curs.executemany(sql, many)
        else:
            self.curs.execute(sql)

        self.conn.commit()

    def close_conn(self):
        self.conn.close()

class SetConfig:
    def __init__(self):
        self.max_depth = 0
        self.depth_tree = {}
        self.table_name = {}
        self.parent = ""
        self.child = ""
        self.set_bool = False

    def maxdepth(self, elem, level):
        ## element maxdepth, tag
        level += 1
        if level > self.max_depth:
            self.max_depth = level
        for x in elem:
            self.depth_tree[x.tag] = level
            self.maxdepth(x, level)

    def getparent(self, tree):
        ### get parent element
        parent_map = {}
        for parent in tree.iter():
            for child in parent:
                if child in parent_map:
                    parent_map[child.tag].append(parent.tag)
                else:
                    parent_map[child.tag] = parent.tag

        return parent_map

    def element_find(self, node, tag):
        for fst in node.findall(tag):
            if fst.tag:
                print(fst.tag)
                for sec in fst.findall(tag):
                    print(sec.tag , sec.get('name'))

    def delete_attribute(self, tree, attribute):
        del_param = []
        for child in tree.iter():
            for key, value in child.attrib.items():
                str_match = [ s for s in attribute if s.__contains__(key.rstrip())]
                if not str_match:
                    del_param.append(key)

            for att in del_param:
                if child.get(att):
                    del child.attrib[att]

        return tree

    def delete_element(self, tree, tags, level):
        keys = list(self.depth_tree.keys())
        values = list(self.depth_tree.values())
        level += 1

        for child in tree.findall(keys[level]):
            if  tags == child.tag:
                tree.remove(child)
            else:
                if values[level] == values[level+1]:
                    self.delete_element(tree, tags, level)
                else:
                    self.delete_element(child, tags, level)

        return tree

    def get_pkg_xml(self, xmldata, element=None, attribute=None, value=None):
        try:
            tree = ET.fromstring(xmldata)
        except ValueError :
            xmlp = ET.XMLParser(encoding="utf-8")
            tree = ET.fromstring(xmldata, parser=xmlp)

        self.maxdepth(tree, -1)

        for package in tree.findall(element):
            if attribute:
                if package.get(attribute) == value:
                    tree.remove(package)
            #else:
                #del package.attrib['type']
                #del package.attrib['activate']
                #package.set('vm', node)

        return tree, self.depth_tree

    def get_config_xml(self, xmldata, attribute=None, element=None):
        try:
            tree = ET.fromstring(xmldata)
        except ValueError :
            xmlp = ET.XMLParser(encoding="utf-8")
            tree = ET.fromstring(xmldata, parser=xmlp)

        self.maxdepth(tree, -1)

        if element:
            for tags in element:
                try:
                    depth = self.depth_tree[tags]
                    tree = self.delete_element(tree, tags, -1)
                    del self.depth_tree[tags]
                except KeyError as e:
                    depth = -1
                    continue

        depth_tree = self.depth_tree
        self.depth_tree = {}

        if attribute:
            tree = self.delete_attribute(tree, attribute)

        return tree , depth_tree

    def set_config_xml(self, ref_data, tree, depth, level, setbool=False):
        keys = list(depth.keys())
        values = list(depth.values())

        level +=1
        self.set_bool = setbool
        for child in tree.findall(keys[level]):
            if child.tag == 'param' :
                if ref_data[child.get('name')] != child.get('value') :
                    child.set('value', ref_data[child.get('name')])
                    self.set_bool = True

            if child.tag == 'table':
                self.table_name = child.get('name')

            if child.tag == 'field':
                table_name = [self.table_name, tree.get('index'), child.get('name')]
                table_key = '.'.join(table_name)
                if ref_data[table_key] != child.get('value') :
                    child.set('value', ref_data[table_key].strip())
                    self.set_bool = True

            if len(keys) > level+1:
                if values[level] == values[level+1]:
                    self.set_config_xml(ref_data, tree, depth, level, self.set_bool)
                else:
                    self.set_config_xml(ref_data, child, depth, level, self.set_bool)

        #print(ET.tostring(tree, encoding='utf-8', method='xml').decode('utf-8'))
        return ET.tostring(tree, encoding='utf-8', method='xml').decode('utf-8'), self.set_bool

    def element_delete(self, tree, depth, level):
        level += 1
        for child in tree.findall(depth[level]):
            if child.tag == 'record':
                tree.remove(child)
                
            if len(depth) > level+1:
                self.element_delete(child, depth, level)
        
        #print(ET.tostring(tree, encoding='utf-8', method='xml').decode('utf-8'))
            
    def create_config_xml(self, ref_data, tree, depth, level):
        keys = list(depth.keys())
        values = list(depth.values())

        self.set_bool = False
        xpath = ['.']    
        for key, value in depth.items():
            xpath.append(key)
            if value == 0: 
                continue

            elif key == 'param':
                for child in tree.findall('/'.join(xpath)):
                    try:
                        if ref_data[child.get('name')]:
                            if ref_data[child.get('name')] != child.get('value'):
                                child.set('value', ref_data[child.get('name')])
                                self.set_bool = True
                    except KeyError as e:
                        print("%s " % e)

            elif key == 'table':
                try:
                    if depth['param']:
                        del xpath[-2]
                except KeyError as e:
                    print("Nothing param ")

            elif key == 'record':
                del xpath[0]
                self.element_delete(tree, xpath, level)

                for tname, record in ref_data.items():
                    if isinstance(record, dict):
                        for index, field in record.items():
                            record_el = Element(key, {'index':index})
                            for name, value in field.items():
                                field_el = Element('field', {'name':name, 'value':value})

                                record_el.append(field_el)

                            for child in tree.findall('./section/table'):
                                if child.get('name') == tname:
                                    child.append(record_el)
                self.set_bool = True

        return ET.tostring(tree, encoding='utf-8', method='xml').decode('utf-8'), self.set_bool

def get_section_config(ip, port, name=None, section=None) :
    if section:
        params = urllib.parse.urlencode({'id': name, 'section': section})
    else:
        params = urllib.parse.urlencode({'id': name})

    headers = {"Host": ip + ":" + port,
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "User-Agent": "Gold-Config",
                "Accept": "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
                "Connection": "keep-alive"
    }
    try:
        conn = httplib.HTTPConnection(ip, port)
        conn.request("GET", "/get.xml?" + params, "" ,headers)
        response = conn.getresponse()
        body = response.read()
        return body
    except (httplib.HTTPException, socket.error) as ex :
        print("ERROR: %s" % ex)
        return 0

def set_section_config(ip, port, name, section, xmlbody):
    params = urllib.parse.urlencode({'id': name, 'section': section})
    headers = {"Host": ip + ":" + port,
                "Accept": "text/plain, application/json, application/*+json, */*",
                "Content-Type": "text/xml;charset=EUC-KR",
                "Accept-Charset": "big5, big5-hkscs, cesu-8, euc-kr, utf-16, utf-16be, utf-16le, utf-32, utf-32be, utf-32le, utf-8",
                "Connection": "keep-alive",
                "User-Agent": "Gold-Config",
                "Accept-Encoding": "gzip,deflate"
    }
    body = XML
    body += xmlbody
    #print(ip, body)

    try:
        conn = httplib.HTTPConnection(ip, port, timeout=5)
        conn.request("POST", "/set.xml?" + params, body, headers)
        response = conn.getresponse()
        #print(response.status, response.reason)
        return response
    except (httplib.HTTPException, socket.error) as ex :
        print("ERROR: %s" % ex)
        return 0

def read_nconfigure_file(filename):
    with open(filename, 'r') as nf:
        lines = nf.readlines()

    SET = {}
    SECTION = []
    KEYS = ['cmd', 'action', 'id', 'section', 'key', 'value']

    for line in lines:
        cmd = line.split(None, 5)
        key = [cmd[2], cmd[3]]
        try:
            if SET['_'.join(key)]:
                SET['_'.join(key)][cmd[4]] = cmd[5].strip()
        except KeyError as e:
            SET['_'.join(key)] = {}
            SET['_'.join(key)][cmd[4]] = cmd[5].strip()

        SECTION.append('_'.join(key))

    SECTION = sorted(list(set(SECTION)))

    return SET, SECTION

def display_xml(cd, depth_tree):
    for ne, data in cd.items():
        for lines in data.splitlines():
            for key, value in depth_tree[ne].items():
                if key in lines:
                    space = int(value) * 4 + len(lines)
                    print('{:>{}}'.format(lines, space))

        print()

def get_conf_xml(data):
    try:
        tree = ET.fromstring(data)
    except:
        xmlp = ET.XMLParser(encoding="utf-8")
        tree = ET.fromstring(data, parser=xmlp)

    return tree

def get_conf(filename, ip, port, attribute=None, element=None, data_bool=False):
    cd = {}
    depth_tree = {}
    setconf , section = read_nconfigure_file(filename)

    xml = SetConfig()
    for args in section:
        ID = args.split('_')[0]
        SE = args.split('_')[1]
        key = ID + '_' + SE
        data = get_section_config(ip, port, ID, SE)

        if data:
           xmldata, depth = xml.get_config_xml(data, attribute, element) 
           data = ET.tostring(xmldata, encoding='utf-8', method='xml').decode('utf-8')
           cd[key] = data
           depth_tree[key] = depth

    if data_bool:
        return cd, depth_tree, setconf
    else:
        display_xml(cd, depth_tree)

def set_conf(filename, ip, port, attribute=None, element=None):
    cd, depth_tree, setconf = get_conf(filename, ip, port, attribute, element, True)
    sconf = SetConfig()

    for gkey, gvalue in cd.items():
        get_key = gkey.split('_')
        set_data = {}
        tbset_data = {}

        print()
        print("==================================")
        print("get SECTION %s" % gkey)
        for skey, svalue in setconf[gkey].items():
            svalue = svalue.strip('"')
            slen = len(svalue.split(';;')[0].split(',,'))
            if slen > 1:
                set_data[skey] = {}
                table = svalue.split(';;')
                tb_table = {}
                for idx, record in enumerate(table):
                    set_data[skey][str(idx)] = {}
                    for field in record.split(',,'):
                        tb_table[field.split('=')[0]] = field.split('=')[1]

                    set_data[skey][str(idx)].update(tb_table)

            else:
                set_data[skey] = svalue.strip('"')
            
        depth = depth_tree[gkey]
        tree = ET.fromstring(gvalue)

        print()
        print("Get Config")
        print()
        print(gvalue)
        print()
        print(set_data)
        print()
        set_xml, setbool = sconf.create_config_xml(set_data, tree, depth, -1)
        #reparsed = minidom.parseString(set_xml)

        print()
        print("Set Config")
        #print(reparsed.toprettyxml(indent=" "))

        if setbool:
            response = set_section_config(ip, port, get_key[0], get_key[1], set_xml)
            if int(response.status) == 200:
                print()
                print("{} {} {}".format(get_key[0], get_key[1], ip))
                print(set_xml)
                print()
                print("{} set config success".format(response.status))
                print()
            else:
                print()
                print("{} {} {}".format(get_key[0], get_key[1], ip))
                print("{} {}".format(response.reason))
                print()
        else:
            print()
            print("{} {} : Config same !!!".format(get_key[0], get_key[1]))

        #time.sleep(1)

def main():
    try:
        ip = sys.argv[1]
        node = sys.argv[2]
        role = sys.argv[3]
    except:
        print("ipaddress")

    attribute = ['name', 'value', 'index']
    element = ['columns', 'column']
    name = ["config", node, role]
    filename = os.path.join("..", "roles", '-'.join(name[:-1]), "files", '-'.join(name))
    port = '8800'

    #get_conf(filename, ip, port, attribute, element, False)
    set_conf(filename, ip, port, attribute, element)


if __name__=='__main__':
    main()
