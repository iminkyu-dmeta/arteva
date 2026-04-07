# -*- coding: utf-8 -*
#import socket module 
from socket import * 
import sys
import re
import ssl
import traceback
import json

##########################################################
#global params
##########################################################
HOST = "127.0.0.1"
PORT = 49083
FILE = "index.html"
ssl_version = None
certfile = "certificate.pem"
keyfile = "key.pem"
ciphers = None
option_test_switch = 0 # to test, change to 1

version_dict = {
    "tlsv1.0" : ssl.PROTOCOL_TLSv1,
    "tlsv1.1" : ssl.PROTOCOL_TLSv1_1,
    "tlsv1.2" : ssl.PROTOCOL_TLSv1_2,
    "sslv23"  : ssl.PROTOCOL_SSLv23,
}


##########################################################
# Param Hander: get sslContext options through user input
##########################################################
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if re.match("[-]{,2}(tlsv|sslv)[0-9.]{,3}", arg, re.I):
        ssl_version = re.sub("-", "", arg)
    if re.match("[-]{,2}ciphers", arg, re.I):
        ciphers = sys.argv[i + 1]
    if re.match("[-]{,2}cacert", arg, re.I):
        certfile = sys.argv[i + 1]
    if re.match("^[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}\.[0-9]{,3}|localhost$", arg, re.I):
        HOST = arg
    if re.match("^[0-9]{,5}$", arg):
        PORT = arg
    if re.match("^[0-9a-zA-Z_/]+\.[0-9a-zA-Z-_/]+$", arg, re.I):
        FILE = arg

if option_test_switch == 1:
    print("ver=", ssl_version, "ciphers=",ciphers, "certfile=", certfile, 
            "keyfile=", keyfile, "HOST=", HOST, "PORT=", PORT, "FILE=", FILE)

##########################################################
# Init and configure SSLContext, then Wrap socket
# Params: socket sock
#         str ssl_version
#         str keyfile
#         str certificate
#         str ciphers
# Exception: SSLError
##########################################################
def ssl_wrap_socket(sock, ssl_version=None, keyfile=None, certfile=None, ciphers=None):

    #1. init a context with given version(if any)
    if ssl_version is not None and ssl_version in version_dict:
        #create a new SSL context with specified TLS version
        sslContext = ssl.SSLContext(version_dict[ssl_version])
        if option_test_switch == 1:
            print("ssl_version loaded!! =", ssl_version)
    else:
        #if not specified, default
        sslContext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
    if ciphers is not None:
        #if specified, set certain ciphersuite
        sslContext.set_ciphers(ciphers)
        if option_test_switch == 1:
            print("ciphers loaded!! =", ciphers)
    
    #server-side must load certfile and keyfile, so no if-else
    sslContext.load_cert_chain(certfile, keyfile)
    print("ssl loaded!! certfile=", certfile, "keyfile=", keyfile)
    
    try:
        return sslContext.wrap_socket(sock, server_side = True)
    except ssl.SSLError as e:
        print("wrap socket failed!")
        print(traceback.format_exc())


#4. Prepare a sever socket 
serverSocket = socket(AF_INET, SOCK_STREAM) 
serverSocket.bind((HOST, PORT))
serverSocket.listen(3)


#######################################################
# Init socket and start connection (from hw1)
#######################################################
while True:
    #Establish the connection
    print('Ready to serve...')
    newSocket, addr = serverSocket.accept()
    connectionSocket = ssl_wrap_socket(newSocket, ssl_version, keyfile, certfile, ciphers)
    if not connectionSocket:
        continue
    
    try:
      message = connectionSocket.recv(1024).decode("utf-8")
      print("message=", message)
      url = message.split()[2] 
      recvbody = json.loads(message.split()[3])
      print("recvbody=", recvbody)
      #f = open(filename[1:])  
      #outputdate = f.read() 
      #f.close()

      #Send one HTTP header line into socket
      #refrence website: https://goo.gl/UGTC9Q 
      header = "HTTP/1.1 200 OK\n\n"
      #header += "Content-Type: application/json;utf-8"
      header += "\n\n"
      body = '{"status":1}'

      connectionSocket.send(header.encode())
      #connectionSocket.send(header.encode() + body.encode())

      print("SEND: 200 OK : %s" % header.encode())

      #outputdata = str(filename, 'utf-8') 
      if "statusss" in url:
        for k, v in recvbody.items(): 
          print("%s : %s" % (k, v))
          if k == "status" and v == 0:
            print("POST status 1 send ")
            reqheader = "POST /ai/server/arteva_183/status HTTP/1.1\r\n\r\n"
            reqheader += "Content-Type: application/json;utf-8"
            reqheader += "\n\n"

            body = '{"status":1}'
            
            connectionSocket.send(reqheader.encode() + body.encode())
            print("%s : %s" % (reqheader.encode(), body.encode()))

            print("POST status 1 sended ")

      elif "evt" in url:
        for k, v in recvbody.items():
          print("%s : %s" % (k, v))

      #Send the content of the requested file to the client 
      #connectionSocket.send(outputdata)
      
      #close socket after sending
      #connectionSocket.shutdown(SHUT_RDWR)
      #connectionSocket.close()

    except IOError:
        #Send response message for file not found 
        connectionSocket.send("404 Not Found")

        #Close client socket
        connectionSocket.shutdown(SHUT_RDWR)
        connectionSocket.close()
    
serverSocket.close()
sys.exit(0)
