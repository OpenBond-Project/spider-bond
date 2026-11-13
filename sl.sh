#!/usr/bin/env bash
# =============================================================================
# SpiderLab 服务器运维脚本  —— 本地直接运行，不需要助手介入
#
#   ./sl.sh boot           首次：输入一次密码，装上本机公钥，之后永久免密
#   ./sl.sh ssh            登录服务器（交互 shell）
#   ./sl.sh deploy         一键上线：构建 + 上传 + 重启 + 健康检查（失败自动回滚）
#   ./sl.sh deploy -n      跳过构建，直接上传现有 spiderlab.tar.gz
#   ./sl.sh status         服务 / 端口 / 证书 / 磁盘 一览
#   ./sl.sh test           站点接口自检（在服务器本机执行，绕开本地网络问题）
#   ./sl.sh logs [行数]    实时跟踪后端日志（默认 60 行）
#   ./sl.sh restart        只重启后端并重载 Nginx
#   ./sl.sh push <本地> <远端>   单文件上传（改一个 py 文件时用，比整包快）
#   ./sl.sh indexnow             把 sitemap 里的 URL 推给 Bing/Yandex（即时收录）
#
#   服务器地址等基础设施信息不在仓库里：复制 .env.example 为 .env.local 后填写。
#   站点域名默认 https://spider.skkk.uno，可用 SL_DOMAIN 覆盖。
# =============================================================================
set -uo pipefail

LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# 本地私密配置（含服务器 IP）。.env.local 已在 .gitignore 中，不会进仓库。
if [ -f "$LOCAL_DIR/.env.local" ]; then
  # shellcheck disable=SC1091
  . "$LOCAL_DIR/.env.local"
fi

HOST="${SL_HOST:-}"
SSH_USER="${SL_USER:-root}"
DOMAIN="${SL_DOMAIN:-spider.skkk.uno}"
APP_DIR="${SL_APP_DIR:-/opt/spiderlab}"
SVC="${SL_SVC:-spiderlab}"
KEY="${SL_KEY:-$HOME/.ssh/id_ed25519}"

PKG="$LOCAL_DIR/spiderlab.tar.gz"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -o ServerAliveInterval=30)

if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_ERR=$'\033[31m'; C_WARN=$'\033[33m'
  C_DIM=$'\033[2m';  C_B=$'\033[1m';    C_0=$'\033[0m'
else
  C_OK=; C_ERR=; C_WARN=; C_DIM=; C_B=; C_0=
fi

ok()   { printf '%s[OK]%s %s\n'  "$C_OK"   "$C_0" "$*"; }
err()  { printf '%s[!]%s %s\n'   "$C_ERR"  "$C_0" "$*" >&2; }
warn() { printf '%s[-]%s %s\n'   "$C_WARN" "$C_0" "$*"; }
step() { printf '\n%s==> %s%s\n' "$C_B"    "$*" "$C_0"; }
dim()  { printf '%s%s%s\n'       "$C_DIM"  "$*" "$C_0"; }
die()  { err "$*"; exit 1; }

rsh() { ssh "${SSH_OPTS[@]}" "$SSH_USER@$HOST" "$@"; }

has_auth() {
  ssh "${SSH_OPTS[@]}" -o BatchMode=yes "$SSH_USER@$HOST" 'exit 0' >/dev/null 2>&1
}

need_auth() {
  if ! has_auth; then
    err "还不能免密登录 ${SSH_USER}@${HOST}"
    echo "  先运行一次:  ./sl.sh boot"
    echo "  （只需输入一次服务器密码，之后永久免密）"
    exit 2
  fi
}

add_ssh_alias() {
  local cfg="$HOME/.ssh/config"
  mkdir -p "$HOME/.ssh"
  [ -f "$cfg" ] || : > "$cfg"
  chmod 600 "$cfg" 2>/dev/null || true
  if grep -qE "^[[:space:]]*Host[[:space:]]+spiderlab([[:space:]]|$)" "$cfg" 2>/dev/null; then
    ok "ssh 别名 spiderlab 已存在"
    return 0
  fi
  cat >> "$cfg" <<EOF

Host spiderlab
    HostName $HOST
    User $SSH_USER
    IdentityFile $KEY
    ServerAliveInterval 30
    StrictHostKeyChecking accept-new
EOF
  ok "已写入 ssh 别名，以后可直接: ssh spiderlab"
}

# ---------------------------------------------------------------- boot
cmd_boot() {
  [ -f "$KEY" ] || die "找不到私钥 $KEY（可先 ssh-keygen -t ed25519 生成）"

  if has_auth; then
    ok "已经能免密登录 ${SSH_USER}@${HOST}，无需重复配置"
    add_ssh_alias
    return 0
  fi

  command -v sshpass >/dev/null 2>&1 || \
    die "本机缺少 sshpass，无法自动安装公钥。请改用: ssh-copy-id ${SSH_USER}@${HOST}"

  echo "首次配置免密登录"
  dim "  从本地上传公钥: ${KEY}.pub"
  dim "  密码仅用于这一次安装公钥，不写入任何文件、不留在历史记录"
  printf "  请输入 %s@%s 的密码: " "$SSH_USER" "$HOST"
  local pw=""
  read -rs pw; echo
  [ -n "$pw" ] || die "密码为空，已取消"

  local b64
  b64=$(base64 -w0 < "${KEY}.pub" 2>/dev/null || base64 < "${KEY}.pub" | tr -d '\n')
  [ -n "$b64" ] || die "读取公钥失败"

  step "安装公钥"
  if SSHPASS="$pw" sshpass -e ssh "${SSH_OPTS[@]}" "$SSH_USER@$HOST" \
      "umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; echo $b64 | base64 -d > /tmp/.slk; grep -qxF -f /tmp/.slk ~/.ssh/authorized_keys || cat /tmp/.slk >> ~/.ssh/authorized_keys; rm -f /tmp/.slk; chmod 700 ~/.ssh; chmod 600 ~/.ssh/authorized_keys; echo PUBKEY_INSTALLED"
  then
    unset pw
    ok "公钥已写入服务器"
  else
    unset pw
    die "sshpass 方式安装失败。
  如果密码确认无误，多半是 sshpass 在 Git Bash 下无法正确传递含 + = 等字符的密码。
  可以手动装公钥：
    1) 复制本机公钥内容:  cat ~/.ssh/id_ed25519.pub
    2) 登录服务器，粘贴到 ~/.ssh/authorized_keys 末尾
    3) 回来重跑:  ./sl.sh status"
  fi

  sleep 1
  if has_auth; then
    ok "免密登录已生效"
    add_ssh_alias
    echo
    dim "  试一下:  ./sl.sh status"
  else
    die "公钥写入成功但仍无法免密登录，请检查 /etc/ssh/sshd_config"
  fi
}

# ---------------------------------------------------------------- deploy
cmd_deploy() {
  local do_build=1
  for a in "$@"; do
    case "$a" in
      --no-build|-n) do_build=0 ;;
      -h|--help) usage; exit 0 ;;
      *) die "未知参数: $a（可用 -n 跳过构建）" ;;
    esac
  done

  need_auth

  if [ "$do_build" = 1 ]; then
    step "本地构建"
    command -v python >/dev/null 2>&1 || die "本机找不到 python，无法构建。可用 ./sl.sh deploy -n 直接上传现有包"
    ( cd "$LOCAL_DIR" && python build.py ) || die "构建失败，已中止（线上未受影响）"
  else
    step "跳过构建，使用现有部署包"
  fi

  [ -f "$PKG" ] || die "找不到部署包 $PKG"

  local sum size
  sum=$(md5sum "$PKG" | awk '{print $1}')
  size=$(du -h "$PKG" | awk '{print $1}')
  ok "部署包 ${size}  MD5 ${sum}"

  step "上传到服务器"
  scp -q -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
      "$PKG" "$SSH_USER@$HOST:/tmp/spiderlab.tgz" || die "上传失败"
  ok "上传完成"

  step "安装并重启（任何一步失败自动回滚）"
  rsh "EXPECT=$sum SVC=$SVC bash -s" <<'REMOTE'
set -u
say(){ printf '  %s\n' "$*"; }
fail(){ printf 'FAIL:%s\n' "$*"; exit 20; }

ACT=$(md5sum /tmp/spiderlab.tgz | awk '{print $1}')
[ "$ACT" = "$EXPECT" ] || fail "MD5 不一致 remote=$ACT"
say "MD5 校验通过"

cd /opt || fail "无法进入 /opt"
rm -rf /opt/spiderlab.prev
if [ -d /opt/spiderlab ]; then mv /opt/spiderlab /opt/spiderlab.prev; fi

tar -xzf /tmp/spiderlab.tgz -C /opt || fail "解压失败"
[ -f /opt/spiderlab/app.py ] || fail "解压后缺少 app.py"
[ -f /opt/spiderlab/dist/index.html ] || fail "解压后缺少 dist/index.html"
say "解压完成"

if [ -f /etc/letsencrypt/live/spider.skkk.uno/fullchain.pem ]; then
  cp /opt/spiderlab/deploy/nginx-ssl.conf /etc/nginx/conf.d/spiderlab.conf
else
  cp /opt/spiderlab/deploy/nginx-http.conf /etc/nginx/conf.d/spiderlab.conf
fi
cp /opt/spiderlab/deploy/00-gzip.conf /etc/nginx/conf.d/00-gzip.conf
chmod +x /opt/spiderlab/deploy/*.sh 2>/dev/null || true

rollback(){
  say "健康检查未通过，回滚到上一版本"
  rm -rf /opt/spiderlab
  if [ -d /opt/spiderlab.prev ]; then mv /opt/spiderlab.prev /opt/spiderlab; fi
  systemctl restart "$SVC" >/dev/null 2>&1 || true
  systemctl reload nginx >/dev/null 2>&1 || true
  printf 'ROLLED_BACK\n'
  exit 21
}

nginx -t >/dev/null 2>&1 || rollback
say "Nginx 配置检查通过"

systemctl restart "$SVC" || rollback
systemctl reload nginx || rollback
sleep 2

CODE=$(curl -s -o /dev/null -w '%{http_code}' -m 8 http://127.0.0.1/ 2>/dev/null || echo 000)
[ "$CODE" = "200" ] || { say "首页返回 $CODE"; rollback; }
say "首页 HTTP 200"

ACTIVE=$(systemctl is-active "$SVC" 2>/dev/null || echo unknown)
[ "$ACTIVE" = "active" ] || rollback
say "后端服务 active"

echo "$EXPECT $(date '+%F %T')" > /opt/spiderlab/.build
rm -rf /opt/spiderlab.prev
rm -f /tmp/spiderlab.tgz
printf 'DEPLOY_OK\n'
REMOTE

  local rc=$?
  if [ $rc -ne 0 ]; then
    err "部署失败（返回码 $rc），线上已回滚到上一版本"
    exit $rc
  fi
  ok "部署成功"

  step "线上状态"
  cmd_status
}

# ---------------------------------------------------------------- status
cmd_status() {
  need_auth
  rsh 'bash -s' <<'REMOTE'
act(){ systemctl is-active "$1" 2>/dev/null || echo unknown; }
printf '  后端 %-10s %s\n' "spiderlab" "$(act spiderlab)"
printf '  代理 %-10s %s\n' "nginx" "$(act nginx)"
if [ -f /etc/letsencrypt/live/spider.skkk.uno/fullchain.pem ]; then
  printf '  证书 %-10s %s\n' "到期" "$(openssl x509 -in /etc/letsencrypt/live/spider.skkk.uno/fullchain.pem -noout -enddate 2>/dev/null | cut -d= -f2)"
else
  printf '  证书 %-10s %s\n' "状态" "未配置"
fi
printf '  版本 %-10s %s\n' "部署" "$(cat /opt/spiderlab/.build 2>/dev/null || echo 未知)"
echo
echo "  端口监听:"
ss -tln 2>/dev/null | awk 'NR>1 && /:(80|443|8080)[ \t]/{printf "    %-22s %s\n", $4, $1}' | sort -u | sed 's/^/  /'
echo "  可达性:"
printf '    %-12s %s\n' "本机 HTTP"  "$(curl -s -o /dev/null -w '%{http_code}' -m 6 http://127.0.0.1/ 2>/dev/null)"
printf '    %-12s %s\n' "本机 HTTPS" "$(curl -sk -o /dev/null -w '%{http_code}' -m 6 https://127.0.0.1/ 2>/dev/null)"
printf '    %-12s %s\n' "域名 HTTPS" "$(curl -s -o /dev/null -w '%{http_code}' -m 15 https://spider.skkk.uno/ 2>/dev/null)"
echo "  资源:"
df -h / 2>/dev/null | awk 'NR==2{printf "    磁盘 总量 %s / 已用 %s (%s)\n", $2, $3, $5}'
free -m 2>/dev/null | awk 'NR==2{printf "    内存 总量 %sMB / 已用 %sMB\n", $2, $3}'
REMOTE
}

# ---------------------------------------------------------------- test
cmd_test() {
  need_auth
  rsh 'bash -s' <<'REMOTE'
c(){ curl -s -o /dev/null -w '%{http_code}' -m 10 "$1" 2>/dev/null || echo 000; }
B=http://127.0.0.1
printf '  %-18s %s\n' "首页"          "$(c $B/)"
printf '  %-18s %s\n' "robots.txt"    "$(c $B/robots.txt)"
printf '  %-18s %s\n' "教学 robots"   "$(c $B/lab/robots.txt)"
printf '  %-18s %s\n' "课程列表"      "$(c $B/api/courses)"
printf '  %-18s %s\n' "靶站列表"      "$(c $B/api/labs)"
printf '  %-18s %s\n' "靶场页"        "$(c "$B/lab/books?page=1")"
printf '  %-18s %s\n' "Pyodide WASM"  "$(c $B/pyodide/pyodide.asm.wasm)"
printf '  %-18s %s\n' "域名 HTTPS"    "$(curl -s -o /dev/null -w '%{http_code}' -m 15 https://spider.skkk.uno/ 2>/dev/null)"
echo
printf '  课程数 %s | 靶站数 %s | 案例数 %s\n' \
  "$(curl -s -m 8 $B/api/courses  | grep -o '"slug"' | wc -l)" \
  "$(curl -s -m 8 $B/api/labs     | grep -o '"path"' | wc -l)" \
  "$(curl -s -m 8 $B/api/cases    | grep -o '"slug"' | wc -l)"
REMOTE
}

# ---------------------------------------------------------------- logs
cmd_logs() {
  local n="${1:-60}"
  case "$n" in ''|*[!0-9]*) die "行数必须是数字" ;; esac
  need_auth
  step "最近 $n 行日志（Ctrl+C 退出）"
  ssh "${SSH_OPTS[@]}" -t "$SSH_USER@$HOST" "tail -n $n -f /var/log/spiderlab.log"
}

# ---------------------------------------------------------------- restart
cmd_restart() {
  need_auth
  step "重启后端"
  rsh "systemctl restart $SVC && systemctl reload nginx && sleep 2 && echo \"  后端: \$(systemctl is-active $SVC) / Nginx: \$(systemctl is-active nginx)\""
}

# ---------------------------------------------------------------- push
cmd_push() {
  local src="${1:-}" dst="${2:-}"
  if [ -z "$src" ] || [ -z "$dst" ]; then
    die "用法: ./sl.sh push <本地文件> <服务器绝对路径>"
  fi
  [ -f "$src" ] || die "本地文件不存在: $src"
  need_auth
  scp -q "$src" "$SSH_USER@$HOST:$dst" || die "上传失败"
  ok "已上传 -> $dst"
  dim "  改 Python 代码需执行 ./sl.sh restart 才生效"
}

# ---------------------------------------------------------------- ssh
cmd_ssh() {
  need_auth
  exec ssh "${SSH_OPTS[@]}" -t "$SSH_USER@$HOST"
}

# ---------------------------------------------------------------- help
usage() {
  cat <<EOF
SpiderLab 服务器运维脚本

  服务器  ${SSH_USER}@${HOST}
  站点    https://${DOMAIN}
  目录    ${APP_DIR}

命令
  boot            首次配置：输入一次密码，装上本机公钥，之后永久免密
  ssh             登录服务器
  deploy          一键上线：构建 + 上传 + 重启 + 健康检查（失败自动回滚）
  deploy -n       跳过构建，直接上传现有部署包
  status          服务 / 端口 / 证书 / 磁盘 一览
  test            站点接口自检（在服务器本机执行）
  logs [行数]     实时跟踪后端日志，默认 60 行
  restart         只重启后端并重载 Nginx
  push <本地> <远端>   单文件上传

首次使用
  ./sl.sh boot
  ./sl.sh status

日常改完代码
  ./sl.sh deploy
EOF
}

# ---------------------------------------------------------------- main
cmd_indexnow() {
  command -v python >/dev/null 2>&1 || die "本机找不到 python，无法推送"
  ( cd "$LOCAL_DIR" && python indexnow.py "$@" )
}

# 除 help 外的命令都要知道服务器地址。未配置时给明确指引，
# 而不是拿空字符串去 ssh（那样报错信息会非常难懂）。
case "${1:-help}" in
  help|-h|--help) ;;
  *) [ -n "$HOST" ] || {
       err "未配置服务器地址（SL_HOST）"
       echo "  cp .env.example .env.local"
       echo "  然后编辑 .env.local，填入 SL_HOST=<服务器 IP 或域名>，重试"
       exit 1
     } ;;
esac

case "${1:-help}" in
  boot|bootstrap)   shift; cmd_boot "$@" ;;
  deploy)           shift; cmd_deploy "$@" ;;
  status|st)        shift; cmd_status "$@" ;;
  test|check)       shift; cmd_test "$@" ;;
  logs|log)         shift; cmd_logs "$@" ;;
  restart)          shift; cmd_restart "$@" ;;
  push)             shift; cmd_push "$@" ;;
  indexnow|seo)     shift; cmd_indexnow "$@" ;;
  ssh|shell)        shift; cmd_ssh "$@" ;;
  help|-h|--help)   usage ;;
  *)                err "未知命令: $1"; echo; usage; exit 1 ;;
esac
