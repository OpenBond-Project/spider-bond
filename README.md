# Spider Bond

部署在真实服务器上的 Python 爬虫实训平台。**20 节系统课程 · 15 个可合法抓取的示例靶站 · 36 关在线实战**。

在线体验：<https://spider.skkk.uno>

## 它解决什么问题

学爬虫最大的障碍不是听不懂，是**没有能合法练手的对象**——拿真实网站练容易踩法律红线，也容易封 IP。

所以这个项目把练习对象自己造出来：15 个服务端渲染的靶站，结构稳定、字段语义清晰、`robots.txt` 明确允许抓取，数据全部虚构。你可以放心练 XPath、CSS 选择器、BeautifulSoup、requests 会话与请求头。

课程按「要写多少代码」分级，而不是按名词听起来高不高级——传一个请求头只是多一个字典，它就属于入门之后的第一层。

## 特性

- **在线沙箱**：Python 运行时跑在浏览器 Web Worker 里（Pyodide），学员代码不进入服务器进程，网络只允许访问本站靶站
- **提交即判分**：答案只在后端，代码运行结果提交比对，前端拿不到标准答案
- **媒体与文件实训**：图库练 `srcset` / `data-src` / CSS 背景图；视频页练 `<source>` 与 Range 请求；文件页练 Content-Type 判断与二进制落盘
- **综合实训站**：`/lab/portal` 把分页、详情、登录、接口、图片、附件、限速串成一条完整抓取链路，是毕业级任务
- **流量分析后台**：自建统计，能区分搜索引擎、AI 爬虫、SEO 工具、脚本抓取与普通访客——这类数据在 umami 一类工具里默认被过滤掉
- **学习记录**：类 GitHub 的贡献日历、分级进度、连续天数；可选 GitHub 登录跨设备同步
- **全站响应式**：日间 / 夜间双主题，移动端可用
- **SEO 完备**：真实路径的 SSR 落地页、结构化数据、sitemap、RSS、IndexNow 推送

## 技术栈

| 层 | 选型 |
|---|---|
| 服务端 | Python 标准库（`http.server`），**零第三方运行时依赖** |
| 前端 | Vue 3 + Vite + Element Plus + CodeMirror 6 |
| 浏览器内 Python | Pyodide（WASM） |
| 靶场页 | 服务端渲染，HTML 源码即数据 |

完整依赖与许可证见站内「关于」页。

## 本地运行

```bash
python build.py            # 打包前端、准备 Pyodide、生成资源
python server/app.py       # 默认 8080
python selftest.py         # 路由 / 判分 / 靶场 / 安全头自测
```

首次构建会下载约 19 MB 的 Pyodide 运行时，之后走本地缓存。

## 部署

### 方式一：Docker（推荐给新环境）

```bash
docker compose up -d --build      # 打开 http://localhost:8080
```

镜像多阶段构建：node 阶段打前端，Python 阶段准备资源，最终镜像只保留 `server/`，以非 root 用户运行。数据库挂在 `spiderbond-data` 卷里，容器重建不丢记录。

要接 Nginx / Caddy 做证书时，去掉 `ports` 映射，让反代连 `spiderbond:8080`。

### 方式二：裸机 + systemd（低配服务器）

容器有基础开销，1 GB 内存的机器更适合直跑。

```bash
cp .env.example .env.local     # 填服务器地址
./sl.sh boot                   # 首次：输入一次密码装公钥，之后免密
./sl.sh deploy                 # 构建 + 上传 + 重启 + 健康检查
./sl.sh status                 # 服务 / 端口 / 证书 / 磁盘
./sl.sh test                   # 站点接口自检（在服务器本机跑）
./sl.sh logs 100               # 跟踪后端日志
```

`deploy` 采用「先传新版本、再切换、失败自动回滚」的方式，Nginx 全程不停机。服务器端需要 Nginx + systemd + Let's Encrypt 证书，配置模板在 `server/deploy/`。

## 目录结构

```
server/
  app.py            HTTP 服务、路由、SSR 页面、判分、账号、访问统计
  courses.py        20 节课程的正文与代码
  labs.py           15 个靶站的数据、36 个关卡与答案
  cases.py          课程内嵌的可运行案例
  enrich.py         课程内容的补充章节
  assets/           图标 sprite、站点 logo、社交分享图
  media/            靶站用的图片 / 视频 / PDF / CSV（由 prepare_media.py 生成）
  deploy/           Nginx 配置模板、证书脚本、systemd unit
web/
  src/App.vue       主应用与各视图
  src/CodeLab.vue   在线代码沙箱
  src/Profile.vue   学习记录页
  src/theme.css     主题变量与暗色覆盖
tests/              浏览器端与沙箱验证脚本（需要 playwright）
build.py            构建脚本
prepare_media.py    生成靶站媒体资源
prepare_pyodide.py  下载并整理 Pyodide 运行时
audit.py            提交前的敏感信息审计
sl.sh               服务器运维
Dockerfile          容器镜像
```

## 配置

私密配置放 `.env.local`（已被 `.gitignore` 排除）：

| 变量 | 用途 |
|---|---|
| `SL_HOST` / `SL_DOMAIN` | 服务器地址与域名（`sl.sh` 使用） |
| `SPIDERLAB_PORT` | 监听端口，默认 8080 |
| `SPIDERLAB_DB` | 数据库路径，容器里指向 `/data/spiderlab.db` |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | 可选的 GitHub 登录 |
| `SPIDERLAB_ADMIN_GIDS` | 后台管理员 GitHub 用户 ID，逗号分隔 |
| `SPIDERLAB_ADS` | 设为 `1` 时放开 AdSense 所需的 CSP 域名 |

## 流量后台

访问 `/admin`，需先用 GitHub 登录且账号在白名单内。统计写入 SQLite 的 `hits` 表，
内存缓冲 + 后台线程批量落库，保留 90 天；静态资源与 Pyodide 请求不计入。

## 安全说明

- 学员代码只在浏览器内运行，服务器不执行用户代码
- 内容安全策略使用 **nonce** 而不是 `unsafe-inline`；`script-src` 不含 `unsafe-eval`
- 唯一放宽的是 `wasm-unsafe-eval`——Pyodide 编译 WebAssembly 所必需
- 登录仅申请 GitHub `read:user`，不获取邮箱与仓库权限
- 提交前跑 `python audit.py`，它同时检查工作区与 Git 历史对象
- 不接入第三方统计，不售卖数据；详见 `/privacy`

## 许可证

[MIT](LICENSE) © 2026 OpenBond Project

第三方组件各自遵循其原始许可证，站内「关于」页有完整清单与链接。
