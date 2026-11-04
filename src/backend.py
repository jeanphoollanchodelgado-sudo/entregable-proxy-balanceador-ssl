#!/usr/bin/env python3
"""Backend de prueba identificable para la simulacion local."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os,json
NAME=os.getenv('BACKEND_NAME','backend')
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  body=json.dumps({'backend':NAME,'path':self.path,'status':'UP'}).encode()
  self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
 def log_message(self,fmt,*args): print('%s - %s'%(self.client_address[0],fmt%args),flush=True)
if __name__=='__main__':
 import sys
 port=int(sys.argv[1]); ThreadingHTTPServer(('127.0.0.1',port),H).serve_forever()
