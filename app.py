import os, socket, urllib.request, json, subprocess

def get(url, headers=None, timeout=4, method="GET", data=None):
        try:
                    req=urllib.request.Request(url, headers=headers or {}, method=method, data=data)
                    r=urllib.request.urlopen(req, timeout=timeout)
                    return {"status": r.status, "body": r.read().decode(errors="replace")[:2500]}
except Exception as e:
        return {"error": str(e)[:250]}

def run(cmd, timeout=15):
        try:
                    p=subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                    return (p.stdout or "")[:4000] or (p.stderr or "")[:800]
except Exception as e:
        return f"err: {e}"

def netprobe(host, port):
        out={"host":host,"port":port}
        try:
                    infos=socket.getaddrinfo(host,port)
                    out["resolve"]=[i[4][0] for i in infos]
except Exception as e:
        out["resolve_error"]=str(e); return out
    try:
                s=socket.create_connection((host,port),timeout=6)
                out["connect"]="ok"
                try:
                                s.settimeout(5)
                                if port in (6379,6380):
                                                    s.sendall(b"PING\r\n")
                                                    out["redis_ping"]=s.recv(200).decode(errors="replace")
                                                    s.sendall(b"INFO server\r\n")
                                                    out["redis_info"]=s.recv(800).decode(errors="replace")
                                                    s.sendall(b"CONFIG GET maxmemory\r\n")
                                                    out["redis_config"]=s.recv(300).decode(errors="replace")
                                                    s.sendall(b"SET bb_research_probe 1\r\n")
                                                    out["redis_set"]=s.recv(100).decode(errors="replace")
elif port==5432:
                s.sendall(b"\x00\x00\x00\x08\x04\xd2\x16\x2f")
                out["pg_resp"]=s.recv(100)
else:
                out["banner"]=s.recv(200).decode(errors="replace")
except Exception as e:
                out["post_connect"]=str(e)
            s.close()
except Exception as e:
        out["connect_error"]=str(e)
    return out

def collect():
        return {"note":"use /net?host=&port="}

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
class H(BaseHTTPRequestHandler):
        def do_GET(self):
                    u=urlparse(self.path)
                    if u.path=="/net":
                                    qs=parse_qs(u.query)
                                    host=qs.get("host",[""])[0]
                                    port=int(qs.get("port",["6379"])[0])
                                    if not host:
                                                        self.send_response(400); self.end_headers(); self.wfile.write(b"host required"); return
                                                    data=json.dumps(netprobe(host,port),default=str).encode()
                                    self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(data)
elif u.path=="/me":
            import socket as _s
            try: ip=_s.gethostbyname(_s.gethostname())
except Exception as e: ip=str(e)
                env={k:v for k,v in os.environ.items() if any(t in k for t in ("POD","IP","HOST"))}
            data=json.dumps({"hostname":_s.gethostname(),"ip":ip,"env":env}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(data)
elif u.path=="/scan":
            # scan own subnet for interesting ports
            ips=[f"10.12.0.{i}" for i in (1,10)]+[]
            res={ip:netprobe(ip,443) for ip in ips}
            data=json.dumps(res,default=str).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(data)
else:
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        def log_message(self,*a): pass
            port=int(os.environ.get("PORT","10000"))
HTTPServer(("0.0.0.0",port),H).serve_forever()
