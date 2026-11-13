#!/usr/bin/env bash
# 为 spider.skkk.uno 申请 Let's Encrypt 证书并启用 HTTPS
# 前置条件：Cloudflare 中 spider 的 A 记录指向本服务器的公网 IPv4，且设为 DNS only（灰云）
set -euo pipefail

DOMAIN=spider.skkk.uno
WWW=/var/www/certbot
D=/opt/spiderlab
# 本机公网 IPv4：优先用环境变量，否则自动探测，避免把具体地址写进仓库
SERVER_IP="${SL_HOST:-$(curl -s -m 5 https://api.ipify.org 2>/dev/null || true)}"
[ -n "$SERVER_IP" ] || SERVER_IP="<本机公网 IP>"

echo "== DNS 现状 =="
getent ahostsv4 "$DOMAIN" | head -2 || true
echo "  提示：若上面不是 $SERVER_IP，请在 Cloudflare 把 A 记录改为 DNS only 指向 $SERVER_IP"
echo

echo "== 申请证书（HTTP-01 / webroot） =="
certbot certonly \
  --webroot -w "$WWW" \
  -d "$DOMAIN" \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  --keep-until-expiring

echo "== 启用 HTTPS 配置 =="
cp "$D/deploy/nginx-ssl.conf" /etc/nginx/conf.d/spiderlab.conf
nginx -t
systemctl reload nginx

echo "== 开启自动续期 =="
if systemctl list-unit-files | grep -q 'certbot.timer'; then
  systemctl enable certbot.timer >/dev/null 2>&1 || true
  systemctl start certbot.timer 2>/dev/null || true
else
  # 兜底：每天两次尝试续期，成功后重载 Nginx
  (crontab -l 2>/dev/null; echo "12 3,15 * * * certbot renew -q --deploy-hook 'systemctl reload nginx'") \
    | sort -u | crontab -
fi

echo "CERT OK -> https://$DOMAIN"
