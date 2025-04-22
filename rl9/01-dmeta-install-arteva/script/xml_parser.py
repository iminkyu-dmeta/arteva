#!/usr/bin/python

import os, sys
import xml.etree.ElementTree as ET

def read_xml(filename, tags):
    tree = ET.parse(filename)
    root = tree.getroot()

    pkg = tree.iter(tag=tags)
    for ele in pkg:
        print(ele.get("id"))

def main():
    try:
        fname = sys.argv[1]
        tags = sys.argv[2]
    except IndexError:
        print("Not read file")

    read_xml(fname, tags)

if __name__=='__main__':
    main()
