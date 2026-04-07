#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
import ssl

class httpHandler(BaseHTTPRequestHandler):
    def DO_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Communication Established\n')

httpd = HTTPServer(('localhost', 49083), BaseHTTPRequestHandler)

httpd.socket = ssl.wrap_socket (httpd.socket, 
        keyfile="your_selfsigned.key",
        certfile='your_selfsigned.crt', server_side=True)

httpd.serve_forever()
