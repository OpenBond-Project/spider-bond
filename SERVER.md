# 连接与部署服务器（本地自助，不需要助手）

服务器信息（已固化进脚本，无需手动输入）：

| 项 | 值 |
|---|---|
| 主机 | `root@<你的服务器 IP>`（见 `.env.local`） |
| 站点 | https://spider.skkk.uno |
| 应用目录 | `/opt/spiderlab` |
| 服务名 | `spiderlab`（systemd） |
| 反向代理 | Nginx（80/443），后端 Python 在 8080 |
| 证书 | Let's Encrypt，certbot.timer 自动续期 |

---

## 一、首次配置（只做一次，约 30 秒）

在项目目录打开 Git Bash，执行：

```bash
cd /c/Users/SKKK/WorkBuddy/Oasis/spiderlab
bash sl.sh boot
```

它会提示你输入**一次**服务器 root 密码。随后：

1. 把本机公钥 `~/.ssh/id_ed25519.pub` 装到服务器 `authorized_keys`
2. 在 `~/.ssh/config` 写入别名 `spiderlab`
3. 以后**永久免密**

> 密码只用于这一次安装公钥：不写入任何文件、不进入 shell 历史、不留在脚本里。
> 装好公钥后，服务器上密码登录对你来说就不再有用了（想彻底关闭可另说）。

### 如果 `sl.sh boot` 报 Permission denied，但密码确认没错

`sshpass` 在 Git Bash 下对含 `+` `=` 等字符的密码存在传递问题（密码包发出去了但内容不对，表现为"密码错误"）。换 paramiko 通道：

```bash
cd /c/Users/SKKK/WorkBuddy/Oasis/spiderlab
python bootstrap_ssh.py
```

它会用同样的密码、走标准 SSH 协议登录并安装公钥，不依赖 pty。这个方式在本机实测可用。

配置完成后，最省事的连接方式就是：

```bash
ssh spiderlab
```

---

## 二、日常命令

所有命令都在项目目录下执行：

```bash
bash sl.sh <命令>
```

Windows 上也可以直接用 `sl.cmd`（cmd / PowerShell 里都行）：

```
sl status
```

| 命令 | 作用 |
|---|---|
| `sl.sh deploy` | **一键上线**：本地构建 → 上传 → 解压 → 换 Nginx 配置 → 重启 → 健康检查 |
| `sl.sh deploy -n` | 跳过构建，直接上传现有的 `spiderlab.tar.gz` |
| `sl.sh status` | 服务状态、监听端口、证书到期、HTTP/HTTPS 可达性、磁盘内存 |
| `sl.sh test` | 接口自检：首页 / robots / 课程 / 靶站 / 靶场页 / Pyodide / 域名 |
| `sl.sh logs` | 实时跟踪 `/var/log/spiderlab.log`，`sl.sh logs 200` 看最近 200 行 |
| `sl.sh restart` | 只重启后端并重载 Nginx（改了 `.py` 后想快速生效） |
| `sl.sh push <本地> <远端>` | 单文件上传，例如 `sl.sh push server/courses.py /opt/spiderlab/courses.py` |
| `sl.sh ssh` | 等价于 `ssh spiderlab` |
| `sl.sh boot` | 重新配置免密（换电脑、换密钥时用） |

### 最常用的两条

```bash
# 改完代码上线
bash sl.sh deploy

# 上线后确认一切正常
bash sl.sh status && bash sl.sh test
```

---

## 三、deploy 做了什么（以及为什么安全）

```
本地 python build.py            → 生成 spiderlab.tar.gz
        |
        v
scp 上传到 /tmp/spiderlab.tgz    → 比对 MD5，不一致直接中止
        |
        v
旧版目录改名 spiderlab.prev      → 新版解压到 /opt/spiderlab
        |
        v
nginx -t 配置检查                → 失败则回滚
        |
        v
重启 spiderlab + reload nginx    → Nginx 不中断，不会出现 522
        |
        v
本机 curl 首页必须 200           → 不是 200 就自动回滚到上一版
```

**任何一步失败都会自动回滚**，线上不会停在半坏状态。整个过程 Nginx 不停机，浏览器不会看到报错。

---

## 四、让命令在任何目录都能用（可选）

把项目目录加进用户 PATH，之后在任意位置敲 `sl`：

```powershell
[Environment]::SetEnvironmentVariable(
  "Path",
  [Environment]::GetEnvironmentVariable("Path","User") + ";C:\Users\SKKK\WorkBuddy\Oasis\spiderlab",
  "User")
```

重开终端后：

```
sl status
sl deploy
```

（Windows 会优先调用同名的 `sl.cmd`，它内部再转给 Git Bash 执行 `sl.sh`。）

---

## 五、常见问题

**我不知道 root 密码 / 从来没有过密码**

正常。这个实例平时是靠腾讯云「自动化助手（TAT）」远程执行命令的，TAT 以 root 身份运行、不走 SSH，所以从来不需要密码。

要拿回 SSH 登录能力，任选一条：

1. **控制台在线重置密码（推荐，不关机、不中断业务）**
   控制台 → 轻量应用服务器 → 找到实例 → 实例详情页右上角「重置密码」（或列表里 更多 → 重置密码）
   → 选 **在线重置**（不要选离线，离线会强制关机）→ 用户名 `root` → 设新密码 → 确定。
   在线重置要求实例和自动化助手都是"运行中"；完成后立即生效，无需重启。
   然后本地跑 `sl.sh boot`，输入这个新密码即可装公钥。

2. **让助手通过 TAT 装公钥**（最省事，不碰密码）
   在对话框的连接器入口重新授权 `lighthouse-ops`，助手执行一条命令把公钥写进
   `/root/.ssh/authorized_keys`，之后直接 `ssh spiderlab`。

3. **已经能进控制台网页终端时**
   在终端里粘贴（把公钥换成你自己的）：

   ```bash
   mkdir -p /root/.ssh && chmod 700 /root/.ssh && \
   printf '%s\n' 'ssh-ed25519 AAAA...你的公钥... user@host' >> /root/.ssh/authorized_keys && \
   sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys && \
   chmod 600 /root/.ssh/authorized_keys && echo PUBKEY_OK
   ```

> 密码只在本地提示符里输入，不要发给任何人（包括助手）。

**`boot` 失败：Permission denied**
密码错，或服务器禁用了密码登录（`PasswordAuthentication no`）。这种情况用上面第 3 条，通过控制台网页终端把公钥粘进 `/root/.ssh/authorized_keys`。

**`deploy` 报「构建失败」**
本地 `python` 不在 PATH。脚本会直接中止，**线上不受影响**。可以先用 `sl deploy -n` 上传上一次构建好的包，或把 Python 加进 PATH。

**线上 522 / 522 又出现了**
522 是 Cloudflare 连不到源站 443。先跑 `sl status` 看 `nginx` 是否 active、443 是否在监听；再确认腾讯云防火墙对 443 有 `0.0.0.0/0` 的 IPv4 放行（IPv6 那条规则单独存在，不能替代）。

**改了 `.py` 但线上没变**
`push` 只传文件，需要 `sl restart`；用 `sl deploy` 则会自动重启。

**证书到期**
`certbot.timer` 已自动续期，`sl status` 里能看到当前到期时间。

**前端改动没生效**
浏览器强刷（Ctrl+F5）。静态资源带 30 天 `immutable` 缓存，构建后文件名带 hash，正常刷新会拿到新文件。

---

## 六、脚本本身

- `sl.sh` —— 全部逻辑（Bash）
- `sl.cmd` —— Windows 入口，用 Git Bash 调 `sl.sh`

需要改主机、域名、服务名时，改文件顶部这几个变量即可，或用环境变量覆盖：

```bash
SL_HOST=1.2.3.4 SL_DOMAIN=example.com bash sl.sh status
```
