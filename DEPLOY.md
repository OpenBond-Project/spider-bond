# 待部署版本说明

**状态：已构建、自测通过，尚未上传到服务器。**

- 包：`C:\Users\SKKK\WorkBuddy\Oasis\spiderlab\spiderlab.tar.gz`
- 大小：9.2 MB
- MD5：`18cd9ea55fd9046b9cdab5879256aa70`
- 原因：`lighthouse-ops` 的 MCP 工具在 2026-11-13 14:13 后从会话中消失，
  无法再调用 `execute_command` / 防火墙接口。

## 本次改动（均已在本地验证）

| 问题 | 修复 |
|------|------|
| 沙箱报 `Classic web workers are not supported` | Pyodide 314.x 只支持 module worker；Worker 改为 `{type:'module'}`，入口改用 `import('/pyodide/pyodide.mjs')` |
| 示例代码暴露源站 IP | 课程/案例/robots/sitemap 里的源站 IP 全部改为 `https://spider.skkk.uno` |
| robots 未及时更新 | `/robots.txt` 与 `/lab/robots.txt` 增加 `Cache-Control: no-cache`；新增 `/api/check_case` 的 Disallow |
| URL 类答案与访问方式绑定 | 判分对 URL 只比较 path，学员用域名或 IP 都能过 |
| 夜间模式不完整 | 补 SSR 页选择器（`header.sl`/`.nav`/`.brand`/`.lk`/`.news-item`）、Element Plus 暗色变量、滚动条/选中/占位符、Bootstrap badge；CodeMirror 语法高亮改为语义类名 + 主题变量 |
| 字体不适宜阅读 | 字体栈改为 `ui-sans-serif` + `Microsoft YaHei UI` + `PingFang SC`；正文 15.5px / 行高 1.85~1.95 / 字距 .012em；关闭 antialiased |
| 靶站过少 | 7 → 11：新增商品库（参数筛选）、招聘板（列表+详情）、订阅源（XML/命名空间）、统计表（合计行陷阱） |
| 等级不够直白 | 等级改为「单页提取 / 列表翻页 / 身份与会话 / 接口与结构 / 综合工程」，每级标注*需要会什么*与*建议先学的课程编号* |
| 请求头被错标为 L4-L5 | 修正为 L3（构造请求头只是多传一个字典）；`/lab/guard` 标注为「L3（头）+ L5（退避）」 |

## 部署方式（任选其一）

### A. 本地一键部署（推荐，不需要助手）

```bash
cd /c/Users/SKKK/WorkBuddy/Oasis/spiderlab
bash sl.sh boot      # 首次：输入一次密码装公钥，之后永久免密
bash sl.sh deploy    # 构建 + 上传 + 重启 + 健康检查，失败自动回滚
```

详见 `SERVER.md`。也支持 `sl.sh status / test / logs / restart / push`。

### B. 通过 Lighthouse 控制台上传后执行

1. 在 Lighthouse 控制台的「文件管理 / OrcaTerm」把 `spiderlab.tar.gz` 上传到 `/opt/`。
2. 在「远程命令」执行：

```bash
cd /opt && md5sum spiderlab.tar.gz && tar -xzf spiderlab.tar.gz \
  && systemctl restart spiderlab && systemctl reload nginx \
  && systemctl is-active spiderlab nginx
```

### C. 有临时上传通道时（助手常用）

```bash
# 1) 服务器：启动一次性接收器（8081，需先放行防火墙）
# 2) 本地：
# 3) 服务器：解压并重启
cd /opt && tar -xzf spiderlab.tar.gz && systemctl restart spiderlab && systemctl reload nginx
# 4) 删除临时防火墙规则
```

## 部署后验证清单

```bash
curl -s http://127.0.0.1/api/labs | python3 -c "import sys,json;print(len(json.load(sys.stdin)))"   # 11
curl -s http://127.0.0.1/lab/products?page=1'&'min=300'&'max=1000 | grep -c 'class="product"'          # 5
curl -s http://127.0.0.1/lab/feed | head -3                                                          # RSS
curl -s http://127.0.0.1/robots.txt | grep check_case                                                # 有 Disallow
curl -sI http://127.0.0.1/assets/highlight.js | head -1                                              # 200
curl -sI http://127.0.0.1/pyodide/pyodide.mjs | head -1                                              # 200
```

浏览器侧重点检查：

1. 课程详情页 → 滚动到「在线实练」→ 点「运行代码」，应显示「正在加载 Python 运行时…」后出结果（首次约 3-5 秒）。
2. 顶栏右侧主题按钮切换亮/暗，刷新后保持。
3. 暗色下靶场页（`/lab/books`）导航、表格、代码块均为深色。
4. 代码块有语法高亮，字体为等宽。
