#!/usr/bin/env python3
"""Reverse proxy HTTP de demostracion con balanceo round-robin y health checks."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from itertools import cycle
from threading import Lock
import json, os, time, ssl

BACKENDS = [x.strip().rstrip('/') for x in os.getenv('BACKENDS','http://127.0.0.1:9001,http://127.0.0.1:9002').split(',') if x.strip()]
if not BACKENDS: raise RuntimeError('Configure al menos un backend en BACKENDS')
_alive = {b: True for b in BACKENDS}
_lock = Lock(); _rr = cycle(BACKENDS)

def choose_backend():
    with _lock:
        for _ in range(len(BACKENDS)):
            b=next(_rr)
            if _alive.get(b,False): return b
    return None

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self, fmt, *args): print('%s - %s' % (self.client_address[0], fmt%args), flush=True)
    def send_json(self, code, obj):
        body=json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/health': return self.send_json(200,{'status':'UP','backends':_alive})
        backend=choose_backend()
        if backend is None: return self.send_json(503,{'error':'sin backends disponibles'})
        try:
            headers={k:v for k,v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
            headers['X-Forwarded-For']=self.client_address[0]
            req=Request(backend+self.path,headers=headers,method='GET')
            with urlopen(req,timeout=3) as response:
                body=response.read(); self.send_response(response.status)
                for k,v in response.headers.items():
                    if k.lower() not in ('transfer-encoding','connection','content-length'): self.send_header(k,v)
                self.send_header('Content-Length',str(len(body))); self.send_header('X-Backend',backend); self.end_headers(); self.wfile.write(body)
        except (URLError,HTTPError,TimeoutError,OSError) as exc:
            _alive[backend]=False
            return self.send_json(502,{'error':'backend no disponible','backend':backend,'detail':str(exc)})

def health_loop():
    while True:
        for b in BACKENDS:
            try:
                with urlopen(b+'/health',timeout=1) as r: _alive[b]=r.status==200
            except Exception: _alive[b]=False
        time.sleep(2)

if __name__=='__main__':
    from threading import Thread
    Thread(target=health_loop,daemon=True).start()
    port=int(os.getenv('PORT','8080'))
    http_server=ThreadingHTTPServer(('0.0.0.0',port),Handler)
    tls_port=os.getenv('TLS_PORT')
    if tls_port:
        cert=os.getenv('TLS_CERT','cert/server.crt')
        key=os.getenv('TLS_KEY','cert/server.key')
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version=ssl.TLSVersion.TLSv1_3
        context.maximum_version=ssl.TLSVersion.TLSv1_3
        context.load_cert_chain(certfile=cert,keyfile=key)
        https_server=ThreadingHTTPServer(('0.0.0.0',int(tls_port)),Handler)
        https_server.socket=context.wrap_socket(https_server.socket,server_side=True)
        Thread(target=https_server.serve_forever,daemon=True).start()
        print(f'HTTPS TLS 1.3 activo en 0.0.0.0:{tls_port} usando {cert}',flush=True)
    print(f'Proxy HTTP activo en 0.0.0.0:{port}; upstreams={BACKENDS}',flush=True)
    http_server.serve_forever()
