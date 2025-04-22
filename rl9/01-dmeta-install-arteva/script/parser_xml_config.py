#!/usr/bin/python

import os, sys
import xml.etree.ElementTree as ET


def parser_child_classloader(section):
    section_name = section.attrib.get('section')
    section_tag = section.tag
    table_dict = {}
    field_list = []

    for param in section:
        if param.tag and param.tag == 'field':
            field_list.append(param.attrib.get('name'))

    table_dict[section_name] =  field_list

    return table_dict

def parser_child_group(section):
    section_name = section.attrib.get('section')
    section_tag = section.tag
    table_dict = {}

    param_list = []

    group_param_list = []

    table_field_list = []
    class_field_list = []

    group_group_param_list = []
    group_group_table_list = []
    group_table_field_list = []

    group_param_name = ""
    table_field_name = ""
    class_field_name = ""
    group_table_field_name = ""
    group_group_table_name = ""
    ## Section 1st
    for param in section:
        group_param_name = section_name

        ## Section 2nd <group section="" <param /> </group>
        if param.tag == 'param':
            param_list.append(param.attrib.get('name'))

        ## Section 2nd <group />
        if param.tag == 'group':
            group_param_name = param.attrib.get('name')
            for group_param in param:
                ## Section 3rd <param /> 
                if group_param.tag == 'param':
                    group_param_name = param.attrib.get('name')
                    group_param_list.append(group_param.attrib.get('name'))

                if group_param.tag == 'group':
                    group_param_name = group_param.attrib.get('name')
                    for gg_param in group_param:
                        if gg_param.tag == 'param':
                            param_list.append(gg_param.attrib.get('name'))

                        if gg_param.tag == 'table':
                            group_group_table_name = gg_param.attrib.get('name')
                            for gt_param in gg_param:
                                group_group_table_list.append(gt_param.attrib.get('name'))

                if group_param.tag == 'table':
                    group_table_field_name = group_param.attrib.get('name')
                    for group_table_param in group_param:
                        group_table_field_list.append(group_table_param.attrib.get('name'))


            table_dict[group_param_name + "_param"] = group_param_list
            table_dict[group_group_table_name] = group_group_table_list
            table_dict[group_table_field_name] = group_table_field_list 
            group_param_list = []

        ## Section 2nd <table />
        if param.tag == 'table':
            table_field_name = param.attrib.get('name')
            ## Section 3rd <table />
            for table_param in param:
                table_field_list.append(table_param.attrib.get('name'))

            #print(table_field_name)
            table_dict[table_field_name] = table_field_list 
            table_field_list = []
                
        ## Section 2nd <classloader />
        if param.tag == 'classloader':
            class_field_name = param.attrib.get('name')
            class_field_list = []
            ## Section 3rd <table />
            for class_param in param:
                class_field_list.append(class_param.attrib.get('name'))

            if class_field_list:
                table_dict[class_field_name] = class_field_list 

    table_dict['param'] =  param_list
    table_dict[group_param_name] = group_param_list
    #table_dict[table_field_name] = table_field_list 

    return table_dict

def read_xml(filename):
    tree = ET.parse(filename)
    conf = tree.getroot()

    nconfiure = {} 
    ### root tag [conf]
    sections = {}
    if conf.tag == 'conf':
        conf_id = conf.attrib.get('id')    
        ### child group tag [ group, section ]
        ### <group section="Users" name="Users" description="go to level Users" >
        for section in conf:
            ### second tag name
            ### second classloader tag name 'section'
            section_tag = section.tag
            section_name = section.attrib.get('section')
            
            classloader_dict = []
            if section_tag == 'classloader' and section_name and section_name != 'ACL':
                if section_name:
                    classloader_dict = parser_child_classloader(section)

                sections[section_name] = classloader_dict

            elif section_tag == 'group':
                group_dict = parser_child_group(section)

                sections[section_name] = group_dict

    #print("cliconf.xml ")
    #print()
    #for key, value in sections.items():
    #    print("%-15s " % (key))
    #    for fkey, fvalue in value.items():
    #        print("%15s : %s " % (fkey, fvalue))
    
    return conf_id, sections 

def get_nconfigure(action, pname, sections):
    nconfigure = []
    vars_string = "{{ setup_cfg[NE_Group][" + pname + "]"
    for key, value in sections.items():
        for fkey, fvalue in value.items():
            if fvalue:
                if fkey == 'param':
                    for param in fvalue:
                        string = 'nconfigure'
                        string += ' ' + action + ' ' + pname + ' ' + key + ' ' + param# + ' ' + vars_string + "['" + param + "'] }}"
                        nconfigure.append(string)
                elif '_param' in fkey:
                    skey = fkey[:-6]
                    for param in fvalue:
                        string = 'nconfigure'
                        string += ' ' + action + ' ' + pname + ' ' + skey + ' ' + param# + ' ' + vars_string + "['" + param + "'] }}"
                        nconfigure.append(string)
                else:
                    tbset_string = ""
                    for i, param in enumerate(fvalue):
                        if i == len(fvalue)-1:
                            tbset_string += param + '=' + vars_string + "['" + param + "'] }}"
                        else:
                            tbset_string += param + '=' + vars_string + "['" + param + "'] }},,"
                    string = 'nconfigure tbget ' + pname + ' ' + key + ' ' + fkey# + ' "' + tbset_string + '"'
                    nconfigure.append(string)

    for line in nconfigure:
        print(line)

def set_nconfigure(action, pname, sections):
    jinja_nconfigure = []
    nconfigure = []
    open_vars = "\"{{ "
    close_vars = " }}\""
    close_if =  "{% endif %}"
    vars_string = "setup_cfg[NE_Group]['" + pname + "']" 

    space_str = " "
    for key, value in sections.items():
        for fkey, fvalue in value.items():
            if fvalue:
                if fkey == 'param':
                    for param in fvalue:
                        key_string = "['" + key + "." + param + "']"
                        set_vars_string = vars_string + key_string
                        jinja_string = "{% if " + set_vars_string + " is defined %}"
                        string = "nconfigure "
                        string += action + space_str + pname + space_str + key + space_str + param + space_str + open_vars + set_vars_string + close_vars
                        nconfigure.append(string)

                        jinja_nconfigure.append(jinja_string)
                        jinja_nconfigure.append(string)
                        jinja_nconfigure.append(close_if)

                elif '_param' in fkey:
                    skey = fkey[:-6]
                    for param in fvalue:
                        key_string = "['" + skey + "." + param + "']"
                        set_vars_string = vars_string + key_string
                        jinja_string = "{% if " + set_vars_string + " is defined %}"
                        string = 'nconfigure '
                        string += action + space_str + pname + space_str + skey + space_str + param + space_str + open_vars + set_vars_string + close_vars
                        nconfigure.append(string)

                        jinja_nconfigure.append(jinja_string)
                        jinja_nconfigure.append(string)
                        jinja_nconfigure.append(close_if)
                else:
                    tbset_string = ""
                    key_string = "['" + key + "." + fkey + "']"
                    fkey_string = "['" + key + "." + fkey + ".index']"
                    tbset_vars_string = vars_string + key_string 
                    vars_param = "["
                    for i, param in enumerate(fvalue):
                        if i == len(fvalue)-1:
                            vars_param += "'" + param + "'"
                        else:
                            vars_param += "'" + param + "', "

                    vars_param += "]"

                    #string = 'nconfigure tbset ' + pname + ' ' + key + ' ' + fkey + ' "' + tbset_string
                    #nconfigure.append(string)

                    #jinja_nconfigure.append(jinja_string)

                    ### Create jinja2 file 
                    #jinja_string = "{% if " + tbset_vars_string + " is defined %}"
                    jinja_nconfigure.append("{% if " + tbset_vars_string + " is defined %}")
                    jinja_nconfigure.append("{%   set fields = " + vars_param + " %}")
                    jinja_nconfigure.append("{%   set idx = " + vars_string + fkey_string + "|int %}")
                    jinja_nconfigure.append("{%   set var_string = [] %}")
                    jinja_nconfigure.append("{%   for i in range(idx) %}")
                    jinja_nconfigure.append("{%     for name in fields %}")
                    jinja_nconfigure.append("{%       set field = name + '.' + i|string %}")
                    jinja_nconfigure.append("{%       if loop.last %}")
                    jinja_nconfigure.append("{%         if idx-1 == i %}")
                    jinja_nconfigure.append("{%           set var_string = var_string.append(name + '=' + " + vars_string + key_string + "[field]) %}")
                    jinja_nconfigure.append("{%         else %}")
                    jinja_nconfigure.append("{%           set var_string = var_string.append(name + '=' + " + vars_string + key_string + "[field] + ';;') %}")
                    jinja_nconfigure.append("{%         endif %}")
                    jinja_nconfigure.append("{%       else %}")
                    jinja_nconfigure.append("{%         set var_string = var_string.append(name + '=' + " + vars_string + key_string + "[field] + ',,') %}")
                    jinja_nconfigure.append("{%       endif %}")
                    jinja_nconfigure.append("{%     endfor %}")
                    jinja_nconfigure.append("{%   endfor %}")
                    jinja_nconfigure.append("nconfigure tbset " + pname + " " + key + " " + fkey + " " + "\"{{ var_string|join('') }}\"")
                    jinja_nconfigure.append("{% endif %}")

    #for line in nconfigure:
    #    print(line)

    for line in jinja_nconfigure:
        print(line)

def get_read_xml(filename, tags):
    tree = ET.parse(filename)
    root = tree.getroot()

    pkg = tree.iter(tag=tags)
    process_list = []
    for ele in pkg:
        process_list.append(ele.get("id"))

    return process_list

def read_sction_config(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    if root.tag == 'ncliconf':
        child = root.find('section')

    if child:
        return child

    #print(ET.tostring(child, encoding='utf-8', method='xml').decode('utf-8'))

def readclayconf():
    filename = 'clay.conf'
    path = '~/etc/clay'
    cpath = os.path.join(path, filename)

    if not os.path.isfile(cpath):
        cpath = '/etc/clay/clay.conf'

    with open(cpath, 'r') as cf:
        reader = cf.readline()
        for line in reader:
            if 'CLAYHOME' in line:
                CLAYHOME = line.split('=')[1]
            else:
                CLAYHOME = "/apps/RCS"

            if 'CLAYLOG' in line:
                CLAYLOG = line.split('=')[1]
            else:
                CLAYLOG= "/logs/RCS"
            if 'export SOCKET_FILE_OWN_GROUP' in line:
                USER = line.split('=')[1]
            else:
                USER = "attps"

    return CLAYHOME, CLAYLOG, USER

def read_nconfigure_file(filename):
    with open(filename, 'r') as nf:
        lines = nf.readlines()
    
    SET = {} ## process name
    SECTION = []

    keys = ['cmd', 'action', 'id', 'section', 'key', 'value']

    for line in lines:
        ncmd = line.split(None,5)
        try:
            key = SET[ncmd[1]]
        except KeyError as e:
            SET[ncmd[1]] = {}

    for line in lines:
        ncmd = line.split(None,5)
        arg = [ncmd[2], ncmd[3], ncmd[4]]
        SET[ncmd[1]]['-'.join(arg)] = {}
        SET[ncmd[1]]['-'.join(arg)] = ncmd[5].strip()
        arg.insert(0, ncmd[1])
        del arg[-1]
        SECTION.append('-'.join(arg))

    SECTION = list(set(SECTION))
    
    return SET, SECTION

def main():
    try:
        node = sys.argv[1]
        role = sys.argv[2]
    except IndexError:
        print("argv[1]: node name, arvg[2]: role(act, sby)")

    name = ["config", node, role] 
    nfilename = os.path.join("..", "roles", "config-ems", "files", '-'.join(name))
    read_nconfigure_file(nfilename)

    #filename = os.path.join("..", "file", '_'.join(name ) + ".txt")
    #section_xml = read_sction_config(filename)

    #print(section_xml)
    #print(ET.tostring(child, encoding='utf-8', method='xml').decode('utf-8'))
    #print(ET.tostring(section_xml, encoding='utf-8', method='xml').decode('utf-8'))

    #for child in section_xml.findall('param'):
    #    print("name: %s, value: %s" % (child.get('name'), child.get('value')))

    print()


    sys.exit(1)
    if pname:
        process_list = get_read_xml(filename, tags)
        str_match = [ s for s in process_list if s.__contains__(pname.rstrip())]
        process_list = []
        if str_match:
            process_list.append(pname)
        else:
            print("%s is not exist" % (pname))
    else:
        process_list = ection_xmlet_read_xml(filename, tags)

    if process_list:
        for pname in process_list:
            fname = os.path.join(CLAYHOME, pname, 'current', 'conf', 'cliconf.xml')
            pname, sections = read_xml(fname)

            if job == 'get':
                get_nconfigure('get', pname, sections)
            elif job == 'set':
                set_nconfigure('set', pname, sections)

if __name__=='__main__':
    main()
