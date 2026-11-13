# Spider Bond

部署在腾讯云 Lighthouse 上的 Python 爬虫实训平台。

## 访问

- 域名：`https://spider.skkk.uno`（Let's Encrypt 证书，自动续期）
- IP 直连：`http://<你的服务器 IP>`（始终保留，便于证书未就绪时排障）

## 架构

```
公网 80/443 -> Nginx（gzip / 静态长缓存 / TLS / ACME）
                 |  /assets/*    前端构建产物
                 |  /pyodide/*   Pyodide WASM 运行时（15MB，365 天缓存）
                 |  /*           反代 127.0.0.1:8080
                 v
              Python 3 标准库服务（systemd: spiderlab，监听 8080）
                 |  /            Vue 3 教学站 SPA
                 |  /lab/*       服务端渲染靶场（HTML 源码即数据）
                 |  /api/*       课程 / 靶站 / 关卡 / 实练判分
                 v
              浏览器 Web Worker 内的 Pyodide 沙箱（在线实练）
```

## 教学体系

### 20 门课程（真正的课程结构）

每课包含：开场导入、生活化类比、学习目标、前置知识、分节精讲（共 63 节，
每节带小例子）、跟我做逐步演练（共 60 步）、完整示例代码、知识点速查、
常见坑、**在线实练**、课后作业、自测题（共 40 题，即时判分）、本课小结、延伸阅读。

四个篇章：基础篇（5）、解析篇（6）、进阶篇（5）、工程篇（4）。
覆盖 HTTP/HTML、requests、编码、XPath、lxml、BeautifulSoup、CSS 选择器、
正则、JSON 接口、分页、Session、请求头、动态页面、Selenium、并发、Scrapy、存储、反爬合规。

### 11 个示例靶站

书城、名言墙、电影榜、商品库、招聘板、统计表、新闻中心、订阅源（XML）、JSON 接口、登录保险库、请求头守卫。
全部虚构数据、服务端渲染、robots.txt 明确允许，HTML 源码里就有数据。

### 5 级 20 关训练场

L1 入门 → L2 基础 → L3 进阶 → L4 高阶 → L5 综合挑战，提交答案即时判分，
进度存浏览器 localStorage。

### 每课一个在线实练案例（20 个）

CodeMirror 6 编辑器 + 浏览器内 Python 运行时，学员在线编写真实爬虫代码、
真实请求本站靶场、提交 `answer` 变量由后端判分。

## 在线实练沙箱的安全模型

学员代码**只在浏览器 Web Worker 的 Pyodide/WASM 内运行**，服务器不执行任何学员代码。

| 风险 | 防护 |
|------|------|
| 恶意代码碰服务器 | 浏览器 WASM 沙箱，无服务器进程 / 文件系统访问 |
| 请求外域 / 云元数据 | Worker 内 URL 白名单，仅允许同站 `/lab/`、`/robots.txt`、`/sitemap.xml`；外域直接抛错 |
| 死循环 | 主线程看门狗 12 秒硬超时，`worker.terminate()` 整个 Worker，下次自动重建 |
| 输出爆炸 | stdout 截断 8KB，每次运行使用全新 globals dict |
| 浏览器禁设请求头 | Referer/Cookie/User-Agent 改写为 `X-Sl-*` 别名，服务端兼容读取 |
| 答案泄露 | 标准答案只存在后端，案例接口不下发 `answer` |

运行时与 wheel 全部本地化在 `/pyodide/`，不依赖任何外部 CDN。

## 开源组件与设计规范

Vue 3、Vite、Element Plus（按需自动引入）、CodeMirror 6、Bootstrap 5（MIT）、
Lucide Icons（ISC）、highlight.js（BSD-3-Clause）、Pyodide、lxml、BeautifulSoup、
Python 标准库。

- **全站不使用 emoji 作为图标**，统一使用 Lucide SVG；CodeMirror 补全项自带的
  emoji 图标也已通过 CSS 隐藏。
- **禁用圆角**：`border-radius: 0` 全局生效，细边框 + 左侧色条 + 分区标题的文档式排版。
- **代码统一等宽字体**：`--sl-mono` 字体栈覆盖所有 `pre` / `code` / 编辑器 /
  输出区 / 输入框，并关闭连字、`tab-size: 4`。
- **代码语法高亮**：课程示例代码、分节小例子、演练步骤、靶场说明页一律走
  highlight.js；在线编辑器本身用 CodeMirror 的 Python 语言包实时高亮。
- **护眼配色 + 夜间模式**：`web/src/theme.css` 是 SPA 与 SSR 页共用的主题层，
  亮色为暖白低对比（无纯黑纯白），夜间为低亮度低蓝光。首帧前从 localStorage
  读取 `sl_theme`（未设置时跟随系统偏好），顶部按钮切换并记忆。
- 首屏不加载 Pyodide（按需懒加载）；Nginx gzip + 30 天静态缓存应对 4Mbps 带宽。

## 主题与高亮资源

| 文件 | 作用 |
|------|------|
| `dist/assets/theme.css` | 共享主题层：亮/暗变量、hljs token 配色、CodeMirror 与 Element Plus 暗色覆盖 |
| `dist/assets/highlight.js` | 由 `hljs-standalone.js` 打包的 IIFE，供无框架的 SSR 页高亮代码块 |
| `web/src/theme.css` | 主题源码（构建时复制到上述位置，同时打包进 SPA 主 CSS） |

## 运维

```bash
systemctl status nginx spiderlab
systemctl restart spiderlab      # 应用后端（8080）
systemctl reload nginx           # 重载 Nginx
nginx -t
tail -100 /var/log/spiderlab.log
```

部署脚本（`deploy/`）：

| 脚本 | 作用 |
|------|------|
| `setup.sh` | 安装 Nginx/Certbot、应用切到 8080、启用 gzip 与静态缓存 |
| `issue-cert.sh` | 申请 Let's Encrypt 证书、启用 HTTPS、配置自动续期 |
| `nginx-http.conf` / `nginx-ssl.conf` | 80 / 443 配置（含 `/pyodide/` 静态映射） |
| `00-gzip.conf` | gzip 参数（Ubuntu 已内置 `gzip on`，不要重复声明） |

## 域名与证书

`skkk.uno` 的 NS 在 Cloudflare，`spider` 为橙云代理记录，源站已指向本机。
Cloudflare 会在 `/robots.txt` 前插入托管的 Content-Signal 段落，因此教学实练
改用 `/lab/robots.txt`（纯教学版，不受代理影响）。

证书：`certbot certonly --webroot`，由 `certbot.timer` 自动续期。
腾讯云防火墙已放行 IPv4/IPv6 的 80 与 443（**443 的 IPv4 规则是 522 的常见根因**）。

## 本地构建与自测

```bash
python build.py             # 构建前端 + 本地化 Pyodide + 打包
python selftest.py          # 服务端 42 项回归
python selftest_cases.py    # 真实运行 20 个实练案例并判分
python selftest_shim.py     # 验证浏览器沙箱 Python shim 逻辑
python verify_remote.py     # 线上 41 项回归
```
