#!/usr/bin/env bash
# SpiderLab 服务器端初始化：Nginx 反代 + gzip + 静态缓存 + Python 退到内网 8080
set -euo pipefail

D=/opt/spiderlab
CONF=/etc/nginx/conf.d
WWW=/var/www/certbot
mkdir -p "$WWW" "$CONF"

echo "[1/5] 安装 Nginx 与 Certbot"
if ! command -v nginx >/dev/null 2>&1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nginx certbot
fi
nginx -v
certbot --version || true

echo "[2/5] 将 SpiderLab 切换到内网 8080"
cp "$D/spiderlab.service" /etc/systemd/system/spiderlab.service
systemctl daemon-reload
systemctl restart spiderlab
sleep 2
systemctl is-active spiderlab
ss -tlnp | grep ':8080 ' || { echo "8080 未监听"; exit 1; }

echo "[3/5] 写入 Nginx 配置"
# 移除默认站点，避免 default_server 冲突
if [ -e /etc/nginx/sites-enabled/default ]; then
  unlink /etc/nginx/sites-enabled/default
fi
cp "$D/deploy/00-gzip.conf"   "$CONF/00-gzip.conf"
cp "$D/deploy/nginx-http.conf" "$CONF/spiderlab.conf"
nginx -t

echo "[4/5] 启动 Nginx"
systemctl enable nginx >/dev/null 2>&1 || true
systemctl restart nginx
sleep 1
systemctl is-active nginx

echo "[5/5] 验证"
curl -s -o /dev/null -w '  home   HTTP %{http_code}\n' http://127.0.0.1/
curl -s -o /dev/null -w '  robots HTTP %{http_code}\n' http://127.0.0.1/robots.txt
curl -s -o /dev/null -w '  css    HTTP %{http_code}\n' http://127.0.0.1/assets/bootstrap.min.css
echo "SETUP OK - 80 端口已由 Nginx 接管，应用在内网 8080"
