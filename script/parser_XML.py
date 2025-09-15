# XML files
# Read and Write

import sys
import csv 
import requests
import xml.etree.ElementTree as ET


def parseXML(xmlfile):
    # create element tree
    tree = ET.parse(xmlfile)

    # get root element
    root = tree.getroot()

    print(root.tag, root.attrib)

    for child in root:
        print(child.tag, child.attrib)

    tags = {}
    for Connector in root.iter('Connector'):
        #print(Connector.tag, Connector.attrib)
        tags[Connector.tag] = Connector.attrib

    print(tags)

def main():
    try:
        xmlfile = sys.argv[1]
    except IndexError:
        print("index Error xml file")


    # load xml
    read = parseXML(xmlfile)


if __name__=="__main__":
    main()


