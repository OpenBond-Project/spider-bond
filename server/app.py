# -*- coding: utf-8 -*-
"""Spider Bond 主服务（Python 标准库，零第三方依赖）。

- /                Vue 3 教学站（静态 SPA）
- /lab/*           服务端渲染靶场，HTML 源码即数据，供 XPath / BS4 练习
- /api/*           课程、靶站、关卡数据与判分接口
- /robots.txt      明确允许抓取 /lab/
"""
import html
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, parse_qsl, urlencode

from courses import COURSES, TRACKS
from cases import CASES, BY_SLUG
from labs import (BASE, SITES, LEVELS, TASKS, ANSWERS,
                  BOOKS, QUOTES, MOVIES, NEWS, API_ITEMS,
                  PRODUCTS, JOBS, FEED_ITEMS, STATS_ROWS,
                  BOOKS_PER_PAGE, QUOTES_PER_PAGE, API_PAGE_SIZE,
                  page_of_books, page_of_quotes,
                  VAULT_USER, VAULT_PASS, VAULT_SECRET, LAB_KEY,
                  GUARD_TOKEN, REPORT_SECRET, REQUIRED_UA, REQUIRED_REFERER)

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
ASSETS = os.path.join(ROOT, 'assets')

E = lambda s: html.escape(str(s), quote=True)

# ---------------------------------------------------------------- 图标（Lucide / ISC，零 emoji）
try:
    with open(os.path.join(ASSETS, 'lucide.svg'), encoding='utf-8') as _f:
        SPRITE = _f.read()
except OSError:
    SPRITE = ''


def icon(name, size=18):
    return ('<svg class="ico" width="%d" height="%d" aria-hidden="true">'
            '<use href="#i-%s"></use></svg>' % (size, size, name))


# ---------------------------------------------------------------- SEO
# 所有服务端渲染页的 head 都由 seo_head() 统一产出：标题模板、描述、canonical、
# Open Graph / Twitter 卡片、JSON-LD 结构化数据。页面只负责提供内容与路径，
# 避免每个页面各写一套标签导致遗漏（这正是之前 og:title 全站缺失的原因）。
SITE_NAME = 'Spider Bond'
SITE_URL = 'https://spider.skkk.uno'
SITE_DESC = ('部署在真实服务器上的 Python 爬虫实训平台：20 节系统课程、'
             '11 个可合法抓取的示例靶站、五级 30 关在线训练场。'
             '代码在浏览器沙箱内运行，提交即判分。')
OG_IMAGE = '/assets/og-cover.png'


def abs_url(path):
    return SITE_URL + path


def clip(text, limit=150):
    """描述截断：英文按字符、中文按字，尽量在标点处断开，不留半句。"""
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    if len(text) <= limit:
        return text
    head = text[:limit]
    for sep in ('。', '；', '！', '？', '，'):
        i = head.rfind(sep)
        if i >= int(limit * 0.55):
            return head[:i + 1]
    return head.rstrip() + '…'


def ld(obj):
    """输出一个 JSON-LD 块。"""
    return ('<script type="application/ld+json">%s</script>'
            % json.dumps(obj, ensure_ascii=False, separators=(',', ':')))


def ld_org():
    return {
        '@type': 'Organization',
        'name': SITE_NAME,
        'url': SITE_URL,
        'logo': abs_url('/assets/bond-logo.svg'),
        'parentOrganization': {'@type': 'Organization',
                               'name': 'OpenBond Project',
                               'url': 'https://bond.skkk.uno'},
    }


def ld_site():
    return ld({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        'name': SITE_NAME,
        'alternateName': 'SpiderBond',
        'url': SITE_URL,
        'description': SITE_DESC,
        'inLanguage': 'zh-CN',
        'publisher': ld_org(),
    })


def ld_crumbs(items):
    """items: [(名称, 路径), ...]，第一个通常是首页。"""
    return ld({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1,
             'name': name, 'item': abs_url(url)}
            for i, (name, url) in enumerate(items)
        ],
    })


def ld_learning(name, desc, path, level='', minutes=0, teaches=None):
    obj = {
        '@context': 'https://schema.org',
        '@type': 'LearningResource',
        'name': name,
        'description': clip(desc, 300),
        'url': abs_url(path),
        'inLanguage': 'zh-CN',
        'isAccessibleForFree': True,
        'learningResourceType': '课程',
        'provider': ld_org(),
    }
    if level:
        obj['educationalLevel'] = level
    if minutes:
        obj['timeRequired'] = 'PT%dM' % minutes
    if teaches:
        obj['teaches'] = [clip(t, 90) for t in teaches[:5]]
    return ld(obj)


def seo_head(title, desc, path, kind='website', extra_ld='', noindex=False,
             image=None):
    full = title if SITE_NAME in title else '%s | %s' % (title, SITE_NAME)
    desc = clip(desc or SITE_DESC)
    url = abs_url(path)
    img = abs_url(image or OG_IMAGE)
    robots = ('<meta name="robots" content="noindex,follow">' if noindex else
              '<meta name="robots" content="index,follow,max-image-preview:large">')
    parts = [
        '<title>%s</title>' % E(full),
        '<meta name="description" content="%s">' % E(desc),
        robots,
    ]
    # noindex 页不设 canonical：它本身不该被收录，指向别处会被当成重复页信号
    if not noindex:
        parts.append('<link rel="canonical" href="%s">' % E(url))
    parts += [
        '<meta property="og:type" content="%s">' % kind,
        '<meta property="og:site_name" content="%s">' % E(SITE_NAME),
        '<meta property="og:locale" content="zh_CN">',
        '<meta property="og:title" content="%s">' % E(full),
        '<meta property="og:description" content="%s">' % E(desc),
        '<meta property="og:url" content="%s">' % E(url),
        '<meta property="og:image" content="%s">' % E(img),
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Spider Bond · Python 爬虫实训平台">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % E(full),
        '<meta name="twitter:description" content="%s">' % E(desc),
        '<meta name="twitter:image" content="%s">' % E(img),
    ]
    if extra_ld:
        parts.append(extra_ld)
    return '\n'.join(parts)


# ---------------------------------------------------------------- 主题 / 高亮（SSR 页）
# 与 SPA 共用 /assets/theme.css；预置脚本在首帧前设置 data-theme，避免闪白。
#
# 这两个文件名是固定的，不能靠文件名 hash 失效缓存。用 mtime 当版本号拼到 URL 上：
# 部署新文件后 URL 变化，浏览器必然重新拉取，绕过旧的 max-age / immutable 缓存。
def _asset_ver(name):
    try:
        return int(os.path.getmtime(os.path.join(ROOT, 'dist', 'assets', name)))
    except OSError:
        return 0


# ---------------------------------------------------------------- 安全响应头
# CSP 用 nonce 而不是 'unsafe-inline'：站内所有动态内容都经过 E() 转义，
# 真正需要执行的内联脚本只有「主题预置」和「关卡提交答案」两处固定代码，
# 每次请求给一个随机 nonce 就够了，没必要对整站放开内联脚本执行权。
_nonce_local = threading.local()


def new_nonce():
    """每个请求生成一次性 nonce，供 HTML 内联脚本与 CSP 头配对。"""
    n = secrets.token_urlsafe(16)
    _nonce_local.value = n
    return n


def cur_nonce():
    return getattr(_nonce_local, 'value', '')


# 是否允许展示 Google AdSense 广告。
# 默认关闭：没有投放广告时不必把 Google 的一堆域放进 CSP，那是白白扩大攻击面。
# 要投广告时设环境变量 SPIDERLAB_ADS=1 再重启，CSP 会自动放开所需域名——
# 否则 AdSense 的脚本会被 script-src 拦住、广告 iframe 会被 child-src 拦住，
# 表现为"广告位一片空白，控制台一堆 Refused to load"。
ADS_ENABLED = os.environ.get('SPIDERLAB_ADS', '0') == '1'
ADS_SCRIPT = ('https://pagead2.googlesyndication.com '
              'https://googleads.g.doubleclick.net '
              'https://tpc.googlesyndication.com '
              'https://adservice.google.com '
              'https://www.googletagservices.com '
              'https://fundingchoicesmessages.google.com')
ADS_FRAME = ("'self' https://googleads.g.doubleclick.net "
             'https://tpc.googlesyndication.com https://www.google.com '
             'https://pagead2.googlesyndication.com '
             'https://fundingchoicesmessages.google.com')
ADS_IMG = ('https://pagead2.googlesyndication.com '
           'https://googleads.g.doubleclick.net https://www.google.com '
           'https://www.gstatic.com https://tpc.googlesyndication.com')
ADS_CONNECT = ('https://pagead2.googlesyndication.com '
               'https://googleads.g.doubleclick.net '
               'https://adservice.google.com '
               'https://fundingchoicesmessages.google.com')


def csp(nonce):
    """内容安全策略。

    以下三处放开是功能硬需求，不是图省事，改小会直接打死功能：
    - 'wasm-unsafe-eval'：Pyodide 要在浏览器内编译 WebAssembly，没有它沙箱起不来
    - blob:（script / worker）：Pyodide 内部用 blob URL 装载子模块
    - style-src 'unsafe-inline'：Element Plus 与 CodeMirror 运行时会动态插入 <style>
    """
    script = "script-src 'self' 'nonce-%s' 'wasm-unsafe-eval' blob:" % nonce
    img = "img-src 'self' data: https://avatars.githubusercontent.com"
    connect = "connect-src 'self'"
    extra = []
    if ADS_ENABLED:
        script += ' ' + ADS_SCRIPT
        img += ' ' + ADS_IMG
        connect += ' ' + ADS_CONNECT
        extra.append('frame-src ' + ADS_FRAME)
    return '; '.join([
        "default-src 'self'",
        script,
        "style-src 'self' 'unsafe-inline'",
        img,
        "font-src 'self' data:",
        connect,
        "worker-src 'self' blob:",
        "child-src 'self' blob:",
        "manifest-src 'self'",
        "media-src 'self'",
    ] + extra + [
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ] + ([] if os.environ.get('SPIDERLAB_CSP_PLAIN_HTTP') == '1'
         else ["upgrade-insecure-requests"]))


def theme_head():
    """主题预置脚本：在首帧前设置 data-theme，避免夜间模式闪白。

    这段是内联脚本，必须带 nonce 才不会被 CSP 拦掉；被拦掉的后果不是报错，
    而是深色模式闪白——所以 nonce 漏了会很难察觉，改这里要一起测。
    """
    return """<link rel="stylesheet" href="/assets/theme.css?v=%d">
<script nonce="%s">
(function(){
  function set(t){var h=document.documentElement;h.setAttribute('data-theme',t);h.classList.toggle('dark',t==='dark');}
  window.slToggleTheme=function(){
    var cur=document.documentElement.getAttribute('data-theme')==='dark'?'dark':'light';
    var t=cur==='dark'?'light':'dark'; set(t);
    try{localStorage.setItem('sl_theme',t)}catch(e){}
  };
  try{
    var t=localStorage.getItem('sl_theme')||
      (window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    set(t);
  }catch(e){set('light');}
  // CSP 会拦掉内联事件处理器（onclick 属性），所以统一用事件委托绑定。
  // 直接挂在 document 上，不必等 DOMContentLoaded。
  document.addEventListener('click', function(e){
    var t = e.target.closest && e.target.closest('[data-theme-toggle]');
    if (t) { e.preventDefault(); window.slToggleTheme(); }
  });
})();
</script>""" % (_asset_ver('theme.css'), cur_nonce())

THEME_BTN = """<button class="theme-toggle" data-theme-toggle title="切换日间/夜间模式">
<svg class="ico-moon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
<svg class="ico-sun" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
<span>主题</span></button>"""

HIGHLIGHT_SCRIPT = '<script src="/assets/highlight.js?v=%d" defer></script>' % _asset_ver('highlight.js')
TAIL = SPRITE + '\n' + HIGHLIGHT_SCRIPT

# 右上角 OpenBond 入口：Bond 标 + 文字，指向 OpenBond Project 主站
_BOND_MARK = ('<img class="brand-mark" src="/assets/bond-logo.svg" alt="OpenBond" '
              'width="21" height="21">')
ORG = ('<a class="org" href="https://bond.skkk.uno" target="_blank" rel="noopener" '
       'title="OpenBond Project · bond.skkk.uno">' + _BOND_MARK +
       '<span class="org-txt">OpenBond</span></a>')
# 靶场页没有「Python 爬虫实训平台」标语，需要自己把 OpenBond 推到最右
ORG_PUSH = ORG.replace('class="org"', 'class="org ms-auto"')


# ---------------------------------------------------------------- 通用样式
EXTRA_CSS = """
:root{--sl-blue:#12386e;--sl-accent:#1a67c2;--sl-orange:#c2542f;--sl-ink:#1f2d3d;
 --sl-line:#d5dee9;--sl-muted:#6b7a90;
 /* 等宽栈必须显式带中文字体，否则中文回退到宋体，代码块里的注释会发虚 */
 --sl-mono:"JetBrains Mono","Cascadia Code",Consolas,"DejaVu Sans Mono","Courier New",
   "Microsoft YaHei UI","Microsoft YaHei","PingFang SC","Noto Sans CJK SC",monospace;
 --bs-font-monospace:var(--sl-mono);
 --bs-border-radius:0;--bs-border-radius-sm:0;--bs-border-radius-lg:0}
pre,code,kbd,samp{font-family:var(--sl-mono)}
*,*::before,*::after{border-radius:0!important}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
 background:#f6f8fb;color:#3c4a5c;font-size:14.5px;line-height:1.7}
.ico{vertical-align:-3px;flex:none}
header.sl{background:#fff;border-bottom:2px solid var(--sl-blue)}
.nav{display:flex;align-items:center;gap:24px;min-height:58px;flex-wrap:wrap}
.brand{font-size:18px;font-weight:700;color:var(--sl-blue);letter-spacing:.2px;display:flex;align-items:center;gap:8px}
.brand:hover{text-decoration:none;color:var(--sl-blue)}
.brand i{font-style:normal;color:var(--sl-orange)}
/* 右上角 OpenBond 入口：纯文字链 + Bond 标 */
.org{display:inline-flex;align-items:center;gap:6px;padding:0;border:0;
 color:#6b7a90;font-size:12.5px;font-weight:600;white-space:nowrap}
.org:hover{text-decoration:none;color:var(--sl-accent)}
.org img.brand-mark{width:21px;height:21px;object-fit:contain;flex:none;display:block}
.nav a.lk{color:#4a5a70;font-weight:500;display:flex;align-items:center;gap:5px;padding:18px 0;border-bottom:3px solid transparent}
.nav a.lk:hover{color:var(--sl-accent);text-decoration:none}
.nav a.lk.on{color:var(--sl-accent);border-bottom-color:var(--sl-accent);background:#eef4fc}
.sl-main{padding:0 0 60px}
.sl-hero{background:var(--sl-blue);color:#fff;padding:30px 34px;margin-bottom:22px}
.sl-hero h1{color:#fff;font-size:28px;margin:0 0 12px}
.sl-hero p{color:#dce9fb;font-size:15px}
.sl-card{background:#fff;border:1px solid var(--sl-line);padding:20px 22px;margin:14px 0}
.sl-card h2,.sl-card h3{margin-top:0;color:var(--sl-blue)}
.sl-card h2{border-bottom:1px solid var(--sl-line);padding-bottom:10px;font-size:16px}
.lab-note{font-size:13px;color:var(--sl-muted);margin-top:20px;display:flex;align-items:center;gap:6px}
.breadcrumb{font-size:13px;color:var(--sl-muted);margin-bottom:14px;display:flex;gap:6px;align-items:center}
.breadcrumb a{color:var(--sl-muted)}
.badge-lv{display:inline-flex;align-items:center;gap:5px}
footer.sl{border-top:1px solid var(--sl-line);background:#fff;color:var(--sl-muted);font-size:12.5px;padding:18px 0;text-align:center}
table.lab-table{background:#fff}
pre.lab-code{background:#f7f9fc;border:1px solid var(--sl-line);
 padding:14px 16px;font:12.8px/1.7 Consolas,Monaco,"Courier New",monospace;
 color:#24344a;overflow-x:auto}
code{font:12.8px/1.6 Consolas,Monaco,monospace;background:#eef2f8;
 border:1px solid #dce5f1;padding:1px 5px;color:#1a4a86}
pre code{background:none;padding:0;border:0;color:inherit}
.book{border:1px solid var(--sl-line);padding:14px 16px;background:#fff;margin:10px 0}
.book h2{font-size:16px;margin:0 0 6px;color:var(--sl-blue)}
.book .meta{font-size:13px;color:#5b6b80;display:flex;gap:14px;flex-wrap:wrap}
.quote-card{border:1px solid var(--sl-line);background:#fff;padding:14px 18px;margin:10px 0}
.news-item{border-bottom:1px solid #e8edf4;padding:12px 0}
.trap{display:none}
.stat-box{background:#f0f4f9;border:1px solid var(--sl-line);padding:12px 18px;text-align:center}
.stat-box b{display:block;font-size:21px;color:var(--sl-blue)}
.pager{display:flex;gap:10px;align-items:center;margin-top:16px}
.callout{border:1px solid var(--sl-line);border-left:3px solid #c8901a;background:#fff8e8;padding:11px 15px;margin:14px 0}
.callout.ok{border-left-color:#1c7a4d;background:#edf8f2}
.callout.no{border-left-color:#b23b36;background:#fdf1f0}
@media (max-width:640px){
  .nav{gap:10px;min-height:0;padding:10px 0}
  .brand{font-size:16px;gap:6px}
  .org{padding:3px 7px;gap:0}
  .org img.brand-mark{width:19px;height:19px}
  .org-txt{display:none}
  .nav a.lk{font-size:13px}
  .sl-main{padding:18px 0 40px}
  .book{padding:12px}
  table.lab-table{display:block;overflow-x:auto;white-space:nowrap}
  pre.lab-code{font-size:12px;padding:11px 12px}
  .stat-box{padding:10px}
  .pager{flex-wrap:wrap}
  .breadcrumb{flex-wrap:wrap}
}
"""


# ---------------------------------------------------------------- 页面骨架
def shell(title, body, active='', desc='', inline_css='',
          path='/', kind='website', extra_ld='', noindex=False):
    navs = [('/', '首页', 'home'), ('/courses', '课程', 'courses'),
            ('/lab/', '示例靶站', 'lab'), ('/training', '训练场', 'training')]
    links = ''.join(
        '<a class="lk %s" href="%s">%s</a>' %
        ('on' if active == k else '', u, t) for u, t, k in navs)
    return ("""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#12386e">
%s
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="preload" as="style" href="/assets/lab.css">
<link rel="stylesheet" href="/assets/bootstrap.min.css">
<link rel="stylesheet" href="/assets/lab.css">
<style>%s</style>
%s</head>
<body><header class="sl"><div class="container nav">
<a class="brand" href="/">%s Spider <i>Bond</i></a>
%s<span class="ms-auto text-muted small d-none d-md-flex align-items-center gap-1">%s Python 爬虫实训平台</span>
%s</div></header>
<main class="sl-main"><div class="container">%s</div></main>
<footer class="sl"><div class="container">Spider Bond · 仅供教学演练 · /lab/ 靶场已在 robots.txt 中允许抓取 · 请遵守 Crawl-delay 与合规要求 · <a href="/about">关于</a> · <a href="/privacy">隐私政策</a></div></footer>
%s</body></html>""" % (seo_head(title, desc, path, kind, extra_ld, noindex),
                     EXTRA_CSS + inline_css, theme_head(), icon('bug', 22), links,
                     icon('shield-check', 15), THEME_BTN + ORG,
                     body, TAIL))


def lab_shell(title, body, crumb='示例靶站', index=False, desc='', path='/lab/'):
    """靶场专用骨架：语义清晰、无 JS 依赖，源码即教学素材。

    具体靶站页一律 noindex,follow：它们是给学员练解析用的素材，不是搜索目标，
    收录进去只会稀释站点主题。只有靶站「列表页」传 index=True 允许收录。
    """
    page_title = title if index else '%s | Spider Bond 靶场' % title
    page_desc = desc or ('Spider Bond 教学靶站页面「%s」，服务端渲染、结构稳定，'
                         '用于 XPath / CSS 选择器 / BeautifulSoup 解析练习。' % title)
    return ("""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
%s
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="stylesheet" href="/assets/bootstrap.min.css">
<link rel="stylesheet" href="/assets/lab.css">
<style>%s</style>
%s</head>
<body><header class="sl"><div class="container nav">
<a class="brand" href="/">%s Spider <i>Bond</i></a>
<a class="lk" href="/lab/">靶站列表</a>
<a class="lk" href="/training">训练场</a>
<a class="lk" href="/courses">课程</a>
%s</div></header>
<main class="sl-main"><div class="container">
<div class="breadcrumb"><a href="/lab/">%s</a> %s <span>%s</span></div>
<div id="main">%s</div>
<div class="lab-note">%s 本页为服务端渲染，结构稳定、字段语义清晰，专供解析练习。
<a href="/robots.txt">robots.txt</a> 已允许抓取本目录。</div>
</div></main>%s</body></html>""" % (
        seo_head(page_title, page_desc, path, noindex=not index),
        EXTRA_CSS, theme_head(),
        icon('bug', 22), THEME_BTN + ORG_PUSH,
        E(crumb), icon('chevron-right', 13), E(title),
        body, icon('info', 14), TAIL))


# ---------------------------------------------------------------- 靶场：书城
def lab_books(page):
    items = page_of_books(page)
    total_pages = (len(BOOKS) + BOOKS_PER_PAGE - 1) // BOOKS_PER_PAGE
    cards = ''
    for b in items:
        cards += ("""<div class="book" data-id="%d">
<h2>%s</h2>
<div class="meta">
<span class="author">%s</span>
<span class="price">%.2f</span>
<span class="rating">%.1f</span>
<span class="tag">%s</span>
</div>
<a class="detail" href="/lab/books/%d">详情</a>
</div>""" % (b['id'], E(b['title']), E(b['author']), b['price'],
             b['rating'], E(b['tag']), b['id']))
    pager = ''
    if page > 1:
        pager += '<a class="prev" href="/lab/books?page=%d">上一页</a>' % (page - 1)
    if page < total_pages:
        pager += '<a class="next" href="/lab/books?page=%d">下一页</a>' % (page + 1)
    body = ("""<h1>书城 - 第 %d 页</h1>
<p class="text-muted">共 %d 本书 / %d 页，每页 %d 本。本页全部书籍如下：</p>
<div id="book-list">%s</div>
<div class="pager">%s</div>""" %
            (page, len(BOOKS), total_pages, BOOKS_PER_PAGE, cards, pager))
    return lab_shell('书城 - 第 %d 页' % page, body, '示例靶站')


def lab_book_detail(bid):
    b = next((x for x in BOOKS if x['id'] == bid), None)
    if not b:
        return 404, lab_shell('书籍不存在', '<h1>404</h1><p>没有这本书。</p>')
    body = ("""<h1>%s</h1>
<div id="book-detail" class="book" data-id="%d">
<h2>%s</h2>
<p class="author">作者：%s</p>
<p class="price">价格：%.2f</p>
<p class="rating">评分：%.1f</p>
<p class="tag">分类：%s</p>
<div id="stock" data-stock="%d">库存：%d 本</div>
<a href="/lab/books?page=1">返回书城</a>
</div>""" % (E(b['title']), b['id'], E(b['title']), E(b['author']),
             b['price'], b['rating'], E(b['tag']), b['stock'], b['stock']))
    return 200, lab_shell('书籍详情 - %s' % b['title'], body, '书城')


# ---------------------------------------------------------------- 靶场：名言墙
def lab_quotes(page):
    items = page_of_quotes(page)
    total_pages = (len(QUOTES) + QUOTES_PER_PAGE - 1) // QUOTES_PER_PAGE
    blocks = ''
    for q in items:
        tags = ''.join('<span class="tag">%s</span>' % E(t) for t in q['tags'])
        blocks += ("""<blockquote class="quote" data-id="%d">
<p class="text">%s</p>
<span class="author">%s</span>
<div class="tags">%s</div>
</blockquote>""" % (q['id'], E(q['text']), E(q['author']), tags))
    pager = ''
    if page > 1:
        pager += '<a class="prev" href="/lab/quotes?page=%d">上一页</a>' % (page - 1)
    if page < total_pages:
        pager += '<a class="next" href="/lab/quotes?page=%d">下一页</a>' % (page + 1)
    body = ('<h1>名言墙 - 第 %d 页</h1><p class="text-muted">共 %d 条 / %d 页。</p>'
            '<div id="quote-list">%s</div><div class="pager">%s</div>' %
            (page, len(QUOTES), total_pages, blocks, pager))
    return lab_shell('名言墙 - 第 %d 页' % page, body, '示例靶站')


# ---------------------------------------------------------------- 靶场：电影榜
def lab_movies():
    rows = ''
    for m in MOVIES:
        rows += ("""<tr data-id="%d">
<td class="rank">%d</td><td class="title">%s</td><td class="year">%d</td>
<td class="rating">%.1f</td><td class="director">%s</td></tr>""" %
                 (m['id'], m['id'], E(m['title']), m['year'],
                  m['rating'], E(m['director'])))
    body = ("""<h1>电影排行榜</h1>
<p class="text-muted">标准表格结构，练习 tr / td 逐行解析与数值列比较。</p>
<table class="table table-bordered lab-table" id="movies">
<thead><tr><th>排名</th><th>片名</th><th>年份</th><th>评分</th><th>导演</th></tr></thead>
<tbody>%s</tbody></table>""" % rows)
    return lab_shell('电影排行榜', body, '示例靶站')


# ---------------------------------------------------------------- 靶场：商品库（参数筛选）
PRODUCTS_PER_PAGE = 6


def lab_products(page, lo, hi):
    items = PRODUCTS
    if lo is not None:
        items = [p for p in items if p['price'] >= lo]
    if hi is not None:
        items = [p for p in items if p['price'] <= hi]
    total_pages = max(1, (len(items) + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE)
    page = max(1, min(page, total_pages))
    chunk = items[(page - 1) * PRODUCTS_PER_PAGE: page * PRODUCTS_PER_PAGE]

    q = []
    if lo is not None:
        q.append('min=%g' % lo)
    if hi is not None:
        q.append('max=%g' % hi)
    qs_base = ('&' + '&'.join(q)) if q else ''

    cards = ''
    for p in chunk:
        state = ('<span class="stock out">缺货</span>' if p['stock'] == 0
                 else '<span class="stock in">库存 %d</span>' % p['stock'])
        cards += ("""<div class="product" data-id="%d" data-stock="%d" data-category="%s">
<h2>%s</h2>
<div class="meta"><span class="price">%.2f</span>%s<span class="cat">%s</span></div>
</div>""" % (p['id'], p['stock'], E(p['category']), E(p['name']),
             p['price'], state, E(p['category'])))

    pager = ''
    if page > 1:
        pager += '<a class="prev" href="/lab/products?page=%d%s">上一页</a>' % (page - 1, qs_base)
    if page < total_pages:
        pager += '<a class="next" href="/lab/products?page=%d%s">下一页</a>' % (page + 1, qs_base)

    cond = []
    if lo is not None:
        cond.append('最低价 %.0f' % lo)
    if hi is not None:
        cond.append('最高价 %.0f' % hi)
    cond_txt = ('，'.join(cond)) if cond else '无筛选'

    body = ("""<h1>商品库</h1>
<p class="text-muted">共 %d 件商品 / %d 页。当前筛选：%s。支持 <code>?min=</code> 与 <code>?max=</code> 价格区间。</p>
<div id="product-list">%s</div>
<div class="pager">%s</div>""" % (len(items), total_pages, cond_txt, cards, pager))
    return lab_shell('商品库', body, '示例靶站')


# ---------------------------------------------------------------- 靶场：招聘板（列表 + 详情）
JOBS_PER_PAGE = 4


def lab_jobs(page):
    total_pages = max(1, (len(JOBS) + JOBS_PER_PAGE - 1) // JOBS_PER_PAGE)
    page = max(1, min(page, total_pages))
    chunk = JOBS[(page - 1) * JOBS_PER_PAGE: page * JOBS_PER_PAGE]
    cards = ''
    for j in chunk:
        cards += ("""<article class="job" data-id="%d">
<h2><a href="/lab/jobs/%d">%s</a></h2>
<div class="meta"><span class="company">%s</span><span class="city">%s</span>
<span class="salary">%s</span><span class="exp">%s</span></div>
</article>""" % (j['id'], j['id'], E(j['title']), E(j['company']),
                 E(j['city']), E(j['salary']), E(j['exp'])))
    pager = ''
    if page > 1:
        pager += '<a class="prev" href="/lab/jobs?page=%d">上一页</a>' % (page - 1)
    if page < total_pages:
        pager += '<a class="next" href="/lab/jobs?page=%d">下一页</a>' % (page + 1)
    body = ("""<h1>招聘板</h1>
<p class="text-muted">共 %d 个职位 / %d 页。列表只给摘要，完整描述在详情页。</p>
<div id="job-list">%s</div><div class="pager">%s</div>""" %
            (len(JOBS), total_pages, cards, pager))
    return lab_shell('招聘板', body, '示例靶站')


def lab_job_detail(jid):
    j = next((x for x in JOBS if x['id'] == jid), None)
    if not j:
        return 404, lab_shell('职位不存在', '<h1>404</h1><p>没有这个职位。</p>')
    body = ("""<h1>%s</h1>
<div id="job-detail" class="job" data-id="%d">
<h2>%s</h2>
<p class="company">公司：%s</p>
<p class="city">城市：%s</p>
<p class="salary">薪资：%s</p>
<p class="exp">经验：%s</p>
<p class="desc">%s</p>
<a href="/lab/jobs?page=1">返回列表</a>
</div>""" % (E(j['title']), j['id'], E(j['title']), E(j['company']),
             E(j['city']), E(j['salary']), E(j['exp']), E(j['desc'])))
    return 200, lab_shell('职位详情 - %s' % j['title'], body, '招聘板')


# ---------------------------------------------------------------- 靶场：订阅源（XML / 命名空间）
def lab_feed():
    items = ''.join(
        """  <item>
    <title>%s</title>
    <link>%s%s</link>
    <guid isPermaLink="false">feed-%d</guid>
    <dc:date>%s</dc:date>
    <description>%s</description>
  </item>
""" % (E(i['title']), E(BASE), E(i['link']), i['id'], i['pub'], E(i['summary']))
        for i in FEED_ITEMS)
    return ("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>Spider Bond 教学订阅源</title>
  <link>%s/lab/feed</link>
  <description>用于练习 XML 解析与命名空间前缀</description>
  <language>zh-CN</language>
%s</channel>
</rss>
""" % (E(BASE), items))


# ---------------------------------------------------------------- 靶场：统计表（合计行陷阱）
def lab_stats():
    rows = ''
    total_count, total_amount = 0, 0.0
    for r in STATS_ROWS:
        total_count += r['count']
        total_amount += r['amount']
        rows += ("""<tr><td class="category">%s</td>
<td class="count">%d</td><td class="amount">%.2f</td></tr>""" %
                 (E(r['category']), r['count'], r['amount']))
    body = ("""<h1>分类统计表</h1>
<p class="text-muted">表格末尾有一行「合计」。直接对整列求和会把合计重复计入，解析时要排除它。</p>
<table class="table table-bordered lab-table" id="stats">
<thead><tr><th>分类</th><th>数量</th><th>金额</th></tr></thead>
<tbody>%s</tbody>
<tfoot><tr class="total"><td class="category">合计</td>
<td class="count">%d</td><td class="amount">%.2f</td></tr></tfoot>
</table>""" % (rows, total_count, total_amount))
    return lab_shell('分类统计表', body, '示例靶站')


# ---------------------------------------------------------------- 靶场：新闻中心（含蜜罐）
def lab_news():
    items = ''
    for n in NEWS:
        items += ("""<article class="news-item" data-id="%d" data-views="%d">
<h2><a href="/lab/news/%d">%s</a></h2>
<span class="cat">%s</span>
<time datetime="%s">%s</time>
<span class="views">%d 次浏览</span>
</article>""" % (n['id'], n['views'], n['id'], E(n['title']),
                 E(n['cat']), n['date'], n['date'], n['views']))
    body = ("""<h1>新闻中心</h1>
<p class="text-muted">列表使用 <code>data-id</code> / <code>data-views</code> 挂载结构化数据。</p>
<div class="callout">%s 合规提示：页面中存在隐藏的蜜罐链接。只跟随用户可见的链接，
不要盲目 follow 所有 <code>a[href]</code>。</div>
<section id="news-list">%s</section>
<div class="trap"><a href="/lab/trap/hidden">内部归档入口</a></div>""" %
            (icon('alert-triangle', 16), items))
    return lab_shell('新闻中心', body, '示例靶站')


def lab_trap():
    return 403, lab_shell('访问被拒绝',
        '<h1>403 Forbidden</h1><div class="callout no">%s 你跟随了一个隐藏链接（蜜罐）。'
        '真实站点会据此标记爬虫 IP。教学场景请只采集可见内容。</div>' % icon('shield-x', 18))


# ---------------------------------------------------------------- 靶场：API 说明
def lab_api_doc():
    body = ("""<h1>JSON 接口靶场</h1>
<p>本靶场模拟前后端分离站点。数据不在 HTML 里，而是由接口返回 JSON。
请先阅读下列接口契约，再用 <code>requests</code> 调用。</p>
<table class="table table-bordered lab-table" id="api-doc">
<thead><tr><th>项目</th><th>值</th></tr></thead><tbody>
<tr><td>列表接口</td><td><code>/lab/api/v1/items</code></td></tr>
<tr><td>必需请求头</td><td><code>X-Lab-Key: %s</code></td></tr>
<tr><td>分页参数</td><td><code>page</code>（从 1 开始）、<code>size</code>（每页条数）</td></tr>
<tr><td>响应字段</td><td><code>items</code>、<code>total</code>、<code>has_next</code>、<code>page</code></td></tr>
<tr><td>Token 接口</td><td><code>/lab/api/v1/token</code>（同样需要上述请求头）</td></tr>
<tr><td>未带头时</td><td>返回 <code>403</code> 与 JSON 错误说明</td></tr>
</tbody></table>
<h3>示例</h3>
<pre class="lab-code"><code>import requests
r = requests.get('%s/lab/api/v1/items',
    params={'page': 1, 'size': 5},
    headers={'X-Lab-Key': '%s'}, timeout=8)
print(r.json()['has_next'])</code></pre>""" %
                (E(LAB_KEY), E(BASE), E(LAB_KEY)))
    return lab_shell('JSON 接口靶场', body, '示例靶站')


def api_items(qs):
    page = max(1, int(qs.get('page', ['1'])[0]))
    size = max(1, min(20, int(qs.get('size', [str(API_PAGE_SIZE)])[0])))
    start = (page - 1) * size
    chunk = API_ITEMS[start:start + size]
    return 200, {
        'page': page, 'size': size, 'total': len(API_ITEMS),
        'has_next': start + size < len(API_ITEMS),
        'items': chunk,
    }


# ---------------------------------------------------------------- 靶场：登录保险库
def lab_vault(cookie_ok):
    if not cookie_ok:
        body = ("""<h1>登录保险库</h1>
<div class="callout no">%s 当前状态：未登录（HTTP 403）。请先 POST 登录并保持会话。</div>
<table class="table table-bordered lab-table" id="login-doc">
<thead><tr><th>项目</th><th>值</th></tr></thead><tbody>
<tr><td>登录地址</td><td><code>/lab/vault/login</code></td></tr>
<tr><td>方法</td><td><code>POST</code>（application/x-www-form-urlencoded）</td></tr>
<tr><td>用户名字段</td><td><code>username</code> = <code>%s</code></td></tr>
<tr><td>密码字段</td><td><code>password</code> = <code>%s</code></td></tr>
<tr><td>成功后</td><td>302 跳转回 <code>/lab/vault</code>，并通过 Set-Cookie 保持会话</td></tr>
</tbody></table>
<pre class="lab-code"><code>s = requests.Session()
s.post('%s/lab/vault/login',
       data={'username': '%s', 'password': '%s'})
r = s.get('%s/lab/vault')   # 必须复用同一个 Session</code></pre>""" %
                (icon('lock', 16), E(VAULT_USER), E(VAULT_PASS),
                 E(BASE), E(VAULT_USER), E(VAULT_PASS), E(BASE)))
        return 403, lab_shell('登录保险库', body, '示例靶站')
    body = ("""<h1>登录保险库</h1>
<div class="callout ok">%s 会话有效，欢迎回来。</div>
<div id="secret" class="book"><h2>Secret Code</h2><p>%s</p></div>
<a href="/lab/vault/logout">退出登录</a>""" % (icon('unlock', 16), E(VAULT_SECRET)))
    return 200, lab_shell('登录保险库', body, '示例靶站')


# ---------------------------------------------------------------- 靶场：请求头守卫 + 限流
_GUARD_HITS = {}


def guard_limited(ip):
    now = time.time()
    hits = [t for t in _GUARD_HITS.get(ip, []) if now - t < 10]
    hits.append(now)
    _GUARD_HITS[ip] = hits
    return len(hits) > 8


def lab_guard(headers, ip):
    if guard_limited(ip):
        return 429, lab_shell('请求过于频繁',
            '<h1>429 Too Many Requests</h1><div class="callout">%s 触发频率限制。'
            '请按 Retry-After 退避后重试。</div>' % icon('clock', 18)), {'Retry-After': '3'}
    ua = headers.get('User-Agent', '') or headers.get('X-Sl-Ua', '')
    ref = headers.get('Referer', '') or headers.get('X-Sl-Referer', '')
    # 允许通过域名或 IP 访问时构造的等价 Referer（只要求路径严格匹配）
    if REQUIRED_UA not in ua or not ref.endswith('/lab/guard/'):
        body = ("""<h1>请求头守卫</h1>
<div class="callout no">%s 请求头校验未通过（HTTP 403）。请按下列契约构造请求。</div>
<table class="table table-bordered lab-table" id="guard-doc">
<thead><tr><th>请求头</th><th>要求的值</th></tr></thead><tbody>
<tr><td>User-Agent</td><td>包含 <code>%s</code></td></tr>
<tr><td>Referer</td><td><code>%s</code></td></tr>
<tr><td>频率</td><td>10 秒内不超过 8 次，超限返回 429 并带 Retry-After</td></tr>
</tbody></table>
<pre class="lab-code"><code>headers = {
    'User-Agent': '%s',
    'Referer': '%s',
}
r = requests.get('%s/lab/guard', headers=headers)</code></pre>""" %
                (icon('shield-x', 16), E(REQUIRED_UA), E(REQUIRED_REFERER),
                 E(REQUIRED_UA), E(REQUIRED_REFERER), E(BASE)))
        return 403, lab_shell('请求头守卫', body, '示例靶站'), {}
    body = ("""<h1>请求头守卫</h1>
<div class="callout ok">%s 校验通过。你已遵守身份标识与限速约定。</div>
<div id="guard-code" class="book"><h2>Guard Code</h2><p>%s</p></div>""" %
            (icon('shield-check', 16), E(REPORT_SECRET)))
    return 200, lab_shell('请求头守卫', body, '示例靶站'), {}


# ---------------------------------------------------------------- 靶站索引
def lab_index():
    cards = ''
    for s in SITES:
        cards += ("""<div class="col-md-6 col-lg-4 mb-3"><div class="sl-card h-100">
<div class="d-flex justify-content-between align-items-start">
<h3 class="h6 mb-1">%s</h3><span class="badge bg-secondary">%s</span></div>
<p class="text-muted small mb-2">%s</p>
<p class="small mb-2">%s %s</p>
<a class="btn btn-sm btn-outline-primary" href="%s">进入靶站 %s</a>
</div></div>""" % (E(s['name']), E(s['level']), E(s['desc']),
                   icon('code', 14), E(s['tech']), E(s['path']), icon('arrow-right', 13)))
    body = ("""<h1>示例靶站</h1>
<p class="text-muted">以下站点全部为服务端渲染、结构稳定，且已在 robots.txt 中明确允许抓取。
请放心用作解析练习，但依然要遵守 Crawl-delay 并保持低频率。</p>
<div class="row">%s</div>
<div class="callout">%s 教学用途声明：本目录下的数据均为虚构演示数据，不含任何真实个人信息。</div>""" %
            (cards, icon('info', 16)))
    return lab_shell(
        'Spider Bond 示例靶站：%d 个可合法抓取的爬虫练习站' % len(SITES),
        body, '示例靶站', index=True, path='/lab/',
        desc='%d 个服务端渲染、结构稳定的爬虫练习靶站：书城、名言墙、电影榜、商品库、'
             '招聘板、统计表、RSS 订阅源、JSON 接口、需登录的保险库、校验请求头的守卫页。'
             '全部虚构演示数据，robots.txt 明确允许抓取，可放心用于 XPath、CSS 选择器、'
             'BeautifulSoup 与 requests 的解析练习。' % len(SITES),
    )


# ---------------------------------------------------------------- 教学站：课程（SSR 兜底）
def page_courses():
    rows = ''
    for c in COURSES:
        rows += ("""<tr><td>%d</td><td><a href="/courses/%s">%s</a></td>
<td>%s</td><td>%s</td><td>%d 分钟</td></tr>""" %
                 (c['no'], E(c['slug']), E(c['title']), E(c['track']),
                  E(c['level']), c['minutes']))
    body = ("""<h1>Python 爬虫课程目录</h1>
<p class="text-muted">共 %d 课，四个篇章覆盖 Python 爬虫全链路：合规底线、HTTP 协议、
解析三件套（XPath / lxml / BeautifulSoup）、CSS 选择器与正则、JSON 接口与分页、
Session 登录与请求头，最后落到限速、重试与数据落库的工程化收尾。</p>
<table class="table table-bordered lab-table"><thead><tr>
<th>#</th><th>课程</th><th>篇章</th><th>难度</th><th>时长</th>
</tr></thead><tbody>%s</tbody></table>""" % (len(COURSES), rows))
    return shell(
        'Python 爬虫课程目录：%d 课从合规底线到工程实战' % len(COURSES),
        body, 'courses',
        'Spider Bond 的 %d 节 Python 爬虫系统课程，按基础篇、解析篇、进阶篇、工程篇'
        '四个篇章组织：从 robots.txt 合规底线与 HTTP 协议起步，掌握 XPath、lxml、'
        'BeautifulSoup、CSS 选择器与正则解析，再到 JSON 接口、分页、Session 登录、'
        '请求头校验，最后完成限速、重试与结构化输出的工程收尾。每课配可运行代码与靶站练习。'
        % len(COURSES),
        path='/courses',
        extra_ld=ld_crumbs([('首页', '/'), ('课程目录', '/courses')]),
    )


def page_course(slug):
    c = next((x for x in COURSES if x['slug'] == slug), None)
    if not c:
        return shell('课程不存在', '<h1>404</h1><p>课程不存在，请回到'
                     '<a href="/courses">课程目录</a>。</p>', 'courses',
                     path='/courses', noindex=True)
    points = ''.join('<li>%s</li>' % E(p) for p in c['points'])
    pits = ''.join('<li>%s</li>' % E(p) for p in c['pitfalls'])
    body = ("""<div class="breadcrumb"><a href="/courses">课程目录</a> %s <span>%s</span></div>
<h1>%s</h1><p class="text-muted">%s · %s · 约 %d 分钟</p>
<p>%s</p><div class="sl-card"><h2>%s 核心知识点</h2><ul>%s</ul></div>
<div class="sl-card"><h2>%s 示例代码</h2>
<pre class="lab-code"><code>%s</code></pre></div>
<div class="sl-card"><h2>%s 常见坑</h2><ul>%s</ul></div>
<div class="callout">%s <b>练习：</b>%s
<a href="%s">%s %s</a></div>
<div class="callout">%s <b>在线运行：</b>这一课配有可在浏览器里直接跑的沙箱与自测题。
<a href="/#/courses/%s">打开交互版 →</a></div>""" %
            (icon('chevron-right', 13), E(c['title']), E(c['title']),
             E(c['track']), E(c['level']), c['minutes'], E(c['summary']),
             icon('list', 19), points, icon('code', 19), E(c['code']),
             icon('alert-triangle', 19), pits, icon('target', 16),
             E(c['exercise']), E(c['lab']), E(c['lab_text']), icon('arrow-right', 13),
             icon('terminal', 16), E(c['slug'])))
    # 上一课 / 下一课：既方便连续阅读，也让爬虫顺着内链走完全部课程
    idx = COURSES.index(c)
    nav = '<a class="btn btn-sm btn-outline-secondary" href="/courses">全部课程</a>'
    if idx > 0:
        pc = COURSES[idx - 1]
        nav = ('<a class="btn btn-sm btn-outline-primary" href="/courses/%s">← 第 %d 课 %s</a> '
               % (E(pc['slug']), pc['no'], E(pc['title']))) + nav
    if idx + 1 < len(COURSES):
        nc = COURSES[idx + 1]
        nav += (' <a class="btn btn-sm btn-outline-primary" href="/courses/%s">第 %d 课 %s →</a>'
                % (E(nc['slug']), nc['no'], E(nc['title'])))
    body += '<div class="mt-3 d-flex gap-2 flex-wrap align-items-center">%s</div>' % nav

    return shell(
        '%s · 第 %d 课' % (c['title'], c['no']),
        body, 'courses', c['summary'],
        path='/courses/%s' % c['slug'],
        kind='article',
        extra_ld=ld_crumbs([('首页', '/'), ('课程目录', '/courses'),
                            ('第 %d 课 %s' % (c['no'], c['title']),
                             '/courses/%s' % c['slug'])])
        + ld_learning(c['title'], c['summary'],
                      '/courses/%s' % c['slug'],
                      level=c['level'], minutes=c['minutes'],
                      teaches=c['points']),
    )


# ---------------------------------------------------------------- 训练场（SSR 兜底）
def page_training():
    cards = ''
    for lv in LEVELS:
        tasks = ''.join(
            '<li><a href="/training/%s">%s %s</a> <span class="badge bg-light text-dark">%d 分</span></li>' %
            (tid, E(tid), E(TASKS[tid]['title']), TASKS[tid]['points'])
            for tid in lv['tasks'])
        cards += ("""<div class="col-md-6 col-lg-4 mb-3"><div class="sl-card h-100">
<div class="d-flex justify-content-between align-items-center mb-2">
<h3 class="h6 mb-0">%s %s</h3><span class="badge bg-%s">%s</span></div>
<p class="text-muted small">%s</p><p class="small">%s</p>
<ul class="small">%s</ul></div></div>""" %
                  (icon('layers', 17), E(lv['name']), E(lv['color']),
                   E(lv['badge']), E(lv['desc']),
                   E(' / '.join(lv['skills'])), tasks))
    body = ('<h1>Python 爬虫分级训练场</h1><p class="text-muted">五级 %d 关，从静态解析到综合工程任务，'
            '在浏览器沙箱里写代码直接打真实靶站，结果自动判分。</p><div class="row">%s</div>' %
            (len(TASKS), cards))
    return shell(
        'Python 爬虫分级训练场：%d 关在线实战' % len(TASKS),
        body, 'training',
        '五级 %d 关爬虫实战训练：单页字段提取、列表翻页、JSON 接口、会话登录、'
        '请求头校验、限速重试与结构化输出。每关配可运行起始代码，在浏览器沙箱内'
        '直接请求本站靶站，提交答案即时判分，不进服务器进程。' % len(TASKS),
        path='/training',
        extra_ld=ld_crumbs([('首页', '/'), ('分级训练场', '/training')]),
    )


def page_task(tid):
    t = TASKS.get(tid)
    if not t:
        return shell('关卡不存在', '<h1>404</h1><p>关卡不存在，请回到'
                     '<a href="/training">训练场</a>。</p>', 'training',
                     path='/training', noindex=True)
    spec = ('<p><b>输出规范：</b><code>%s</code></p><p class="text-muted small">示例：%s</p>'
            % (E(t['spec']), E(t['example']))) if 'spec' in t else ''
    body = ("""<div class="breadcrumb"><a href="/training">训练场</a> %s <span>%s</span></div>
<h1>%s %s</h1><p class="text-muted">%s · %d 分 · %s</p>
<div class="callout">%s <b>在线实战：</b><a href="/#/training/%s">在训练场里写代码直接运行 →</a>
（本页的输入框提交的是纯文本答案，交互版可以写完整代码并看到运行输出）</div>
<div class="sl-card"><h2>%s 任务目标</h2><p>%s</p>
<p><b>目标靶站：</b><a href="%s">%s</a></p>
<p><b>提交格式：</b>%s</p>%s</div>
<div class="sl-card"><h2>%s 提交答案</h2>
<textarea id="answer" class="form-control" placeholder="在此粘贴你的答案"></textarea>
<div class="mt-2"><button class="btn btn-primary" id="btn-submit">%s 提交判分</button>
<button class="btn btn-outline-secondary" id="btn-hint">%s 查看提示</button></div>
<div id="result" class="callout mt-3" style="display:none"></div>
<div id="hintbox" class="callout mt-3" style="display:none">%s</div></div>
<script nonce="%s">
function showHint(){document.getElementById('hintbox').style.display='block';}
async function submitAnswer(){
 const a=document.getElementById('answer').value;
 const r=await fetch('/api/check',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({task_id:'%s',answer:a})});
 const d=await r.json();const el=document.getElementById('result');
 el.style.display='block';el.className='callout mt-3 '+(d.ok?'ok':'no');
 el.textContent=(d.ok?'通过：':'未通过：')+d.message+(d.ok?'':' 提示：'+d.hint);
}
// CSP 禁止内联事件处理器，按钮改用 JS 绑定。脚本在按钮之后，此时节点已存在。
document.getElementById('btn-submit').addEventListener('click', submitAnswer);
document.getElementById('btn-hint').addEventListener('click', showHint);
</script>""" %
            (icon('chevron-right', 13), E(tid), icon('target', 26), E(t['title']),
             E(t['level']), t['points'], E(' / '.join(t['skills'])),
             icon('terminal', 16), E(tid),
             icon('flag', 19), E(t['goal']), E(t['target']),
             E(t['target_text']), E(t['format']), spec,
             icon('send', 19), icon('check-circle', 15), icon('lightbulb', 15),
             E(t['hint']), cur_nonce(), E(tid)))
    # 同级别上一关 / 下一关：让 30 个关卡页之间形成可爬取的内链
    order = next((lv['tasks'] for lv in LEVELS if tid in lv['tasks']), [])
    nav = '<a class="btn btn-sm btn-outline-secondary" href="/training">训练场</a>'
    if tid in order:
        i = order.index(tid)
        if i > 0:
            pp = order[i - 1]
            nav = ('<a class="btn btn-sm btn-outline-primary" href="/training/%s">← %s %s</a> '
                   % (E(pp), E(pp), E(TASKS[pp]['title']))) + nav
        if i + 1 < len(order):
            nn = order[i + 1]
            nav += (' <a class="btn btn-sm btn-outline-primary" href="/training/%s">%s %s →</a>'
                    % (E(nn), E(nn), E(TASKS[nn]['title'])))
    body += '<div class="mt-3 d-flex gap-2 flex-wrap align-items-center">%s</div>' % nav

    return shell(
        '%s %s · 实战关卡' % (tid, t['title']),
        body, 'training',
        '%s 任务目标：%s 目标靶站 %s，%d 分。' %
        (tid, t['goal'], t['target_text'], t['points']),
        path='/training/%s' % tid,
        kind='article',
        extra_ld=ld_crumbs([('首页', '/'), ('分级训练场', '/training'),
                            ('%s %s' % (tid, t['title']),
                             '/training/%s' % tid)])
        + ld_learning('%s %s' % (tid, t['title']), t['goal'],
                      '/training/%s' % tid,
                      level=t['level'], teaches=t['skills']),
    )


# ---------------------------------------------------------------- 静态内容页（SSR）
def page_static(path):
    """关于 / 合规说明的 SSR 版本。

    和 SPA 的 #/about、#/compliance 是同一份内容的不同呈现：这里给搜索引擎,
    那边给交互体验。之所以要有 SSR 版，是因为 hash 路由对检索不可见。
    """
    if path == '/about':
        body = """<h1>关于 Spider Bond</h1>
<p>Spider Bond 是一个部署在真实服务器上的 Python 爬虫实训平台。它不讲空泛概念，
每一课都配可运行代码，每一关都对着真实靶站提交、真实判分。</p>

<div class="sl-card"><h2>为什么做这个</h2>
<p>市面上的爬虫教程有个通病：看懂之后会觉得「我会了」，但一动手写不出来。
原因不在讲解，在于缺少一个「允许你随便抓」的练习对象——拿真实网站练手容易踩法律红线，
也容易被封 IP。</p>
<p>所以这里把练习对象自己造出来：11 个服务端渲染的靶站，结构稳定、字段语义清晰、
robots.txt 明确允许抓取，数据全部虚构。你可以放心练 XPath、CSS 选择器、
BeautifulSoup、requests 会话与请求头，不用担心越界。</p></div>

<div class="sl-card"><h2>项目构成</h2>
<ul>
<li><b>20 节系统课程</b>：基础篇、解析篇、进阶篇、工程篇，从 robots.txt 合规底线到限速重试的工程收尾</li>
<li><b>11 个示例靶站</b>：书城、名言墙、电影榜、商品库、招聘板、统计表、RSS、JSON 接口、登录保险库、请求头守卫</li>
<li><b>30 关分级训练场</b>：五级难度，在线写代码直接打真实靶站，提交即判分</li>
<li><b>浏览器内沙箱</b>：Python 运行时跑在 Web Worker 里，学员代码不进服务器进程</li>
</ul></div>

<div class="sl-card"><h2>技术说明</h2>
<p>服务端是 Python 标准库实现的 HTTP 服务，零第三方运行时依赖；前端是 Vue 3 单页应用；
在线沙箱用 Pyodide 在浏览器里跑 CPython。全站支持夜间模式与移动端布局。</p></div>

<div class="sl-card"><h2>开源许可</h2>
<p>本项目以 <b>MIT License</b> 开源，Copyright 2026 OpenBond Project。
第三方组件（Vue、Element Plus、Bootstrap、Lucide、CodeMirror、Pyodide、
highlight.js、lxml、BeautifulSoup）各自保留其原始许可证。</p></div>

<div class="sl-card"><h2>相关链接</h2>
<ul>
<li><a href="https://skkk.uno" rel="noopener">博客 skkk.uno</a></li>
<li><a href="https://bond.skkk.uno" rel="noopener">Bond Project</a></li>
<li><a href="https://github.com/OpenBond-Project" rel="noopener">GitHub · OpenBond Project</a></li>
</ul></div>"""
        return shell(
            '关于 Spider Bond：可合法抓取的 Python 爬虫实战教学站',
            body, '', 
            'Spider Bond 是部署在真实服务器上的 Python 爬虫实训平台：20 节系统课程、'
            '11 个可合法抓取的示例靶站、30 关在线实战训练场。服务端零第三方依赖，'
            '沙箱在浏览器内运行学员代码，以 MIT 许可证开源。',
            path='/about',
            extra_ld=ld_crumbs([('首页', '/'), ('关于', '/about')]),
        )

    if path == '/privacy':
        # 广告段落按实际开关渲染：没投广告却说"本站使用 AdSense"是不准确的，
        # 而 AdSense 审核又需要看到完整的 Cookie 说明，所以两种状态各写一版。
        if ADS_ENABLED:
            ads_block = """<p>本站使用 <b>Google AdSense</b> 展示广告。Google 及其合作伙伴可能
使用 Cookie（包括 DoubleClick Cookie）根据你访问本站及其他网站的历史投放个性化广告。</p>
<p>如果你不想接受个性化广告，可以：</p>
<ul>
<li>访问 <a href="https://www.google.com/settings/ads" rel="noopener">Google 广告设置</a> 关闭个性化广告</li>
<li>访问 <a href="https://www.aboutads.info" rel="noopener">aboutads.info</a> 了解如何关闭第三方广告 Cookie</li>
<li>在浏览器中禁用第三方 Cookie（可能影响部分功能）</li>
</ul>
<p>关闭个性化广告后你仍会看到广告，只是不再基于你的浏览历史定向。</p>"""
        else:
            ads_block = """<p>本站<b>目前未启用任何广告</b>，页面中不加载 Google AdSense 或其他广告网络的代码，
也不存在广告相关的 Cookie。</p>
<p>如果将来启用广告，本节会更新，并明确说明所用平台与 Cookie 用途。</p>"""

        body = ("""<h1>隐私政策</h1>
<p class="text-muted">最后更新：2026 年 11 月 13 日</p>

<div class="sl-card"><h2>一句话概括</h2>
<p>本站不接入第三方统计工具，不售卖、不共享你的学习数据。不登录时，
你的所有记录只存在你自己的浏览器里。</p></div>

<div class="sl-card"><h2>一、未登录时</h2>
<p>不需要提供任何信息就能使用全部课程与训练场。你的数据存在浏览器的
localStorage 里，<b>不会上传到服务器</b>：</p>
<table class="table table-bordered lab-table"><thead><tr>
<th>键名</th><th>内容</th></tr></thead><tbody>
<tr><td><code>sl_done</code></td><td>已通关的关卡编号</td></tr>
<tr><td><code>sl_code_*</code></td><td>每道题各自的代码草稿</td></tr>
<tr><td><code>sl_study</code></td><td>每天的学习时长（秒）</td></tr>
<tr><td><code>sl_events</code></td><td>通关事件流水，用于画学习日历</td></tr>
<tr><td><code>sl_theme</code></td><td>日间 / 夜间模式偏好</td></tr>
</tbody></table>
<p>清除浏览器数据即可彻底删除，本站没有任何副本。</p></div>

<div class="sl-card"><h2>二、使用 GitHub 登录时</h2>
<p>登录是可选的。只有你主动点击登录，本站才会通过 GitHub OAuth 获取以下信息
（权限范围仅为 <code>read:user</code>）：</p>
<ul>
<li>GitHub 用户 ID（作为账号唯一标识）</li>
<li>用户名、昵称</li>
<li>头像地址</li>
</ul>
<p><b>不获取</b>邮箱、仓库、组织成员关系，也没有任何写入权限。</p>
<p>这些信息与你的学习记录一起存放在本站服务器的 SQLite 数据库中，
用于跨设备同步进度。同步内容包括：通关记录、代码草稿、每日学习时长、通关时间流水。</p></div>

<div class="sl-card"><h2>三、Cookie 清单</h2>
<table class="table table-bordered lab-table"><thead><tr>
<th>名称</th><th>用途</th><th>时效</th><th>来源</th></tr></thead><tbody>
<tr><td><code>sl_sid</code></td><td>登录会话标识（HttpOnly，脚本不可读）</td><td>30 天</td><td>本站</td></tr>
<tr><td><code>sl_oauth_state</code></td><td>GitHub 登录的 CSRF 防护</td><td>10 分钟</td><td>本站</td></tr>
<tr><td><code>__cf_bm</code> 等</td><td>CDN 的机器人识别与安全防护</td><td>短期</td><td>Cloudflare</td></tr>
</tbody></table>
<p>本站自身不使用任何广告或统计类 Cookie；第三方 Cookie 见下一节。</p></div>

<div class="sl-card"><h2>四、广告</h2>
%s</div>

<div class="sl-card"><h2>五、服务器日志</h2>
<p>为了排查故障和防御攻击，服务器会记录访问日志，包含 IP 地址、浏览器标识
（User-Agent）、请求路径与时间。日志不用于用户画像，也从不与账号关联分析，
按系统的日志轮转策略定期清除（通常保留两周左右）。</p></div>

<div class="sl-card"><h2>六、第三方服务</h2>
<table class="table table-bordered lab-table"><thead><tr>
<th>服务</th><th>用途</th><th>涉及数据</th></tr></thead><tbody>
<tr><td>Cloudflare</td><td>CDN 与安全防护</td><td>IP、访问日志</td></tr>
<tr><td>GitHub</td><td>可选登录</td><td>用户 ID、用户名、头像</td></tr>
<tr><td>Google AdSense</td><td>广告（%s）</td><td>Cookie、浏览行为</td></tr>
</tbody></table></div>

<div class="sl-card"><h2>七、数据删除</h2>
<ul>
<li><b>清空浏览器数据</b>：删除本地全部记录，服务器上若有同步数据则需另行处理</li>
<li><b>退出登录</b>：只清除会话 Cookie，服务器上的学习记录仍保留（便于下次登录恢复）</li>
<li><b>彻底删除账号与全部云端数据</b>：发邮件到
<a href="mailto:skkk_lovelove@outlook.com">skkk_lovelove@outlook.com</a>，
说明你的 GitHub 用户名，我会在 7 个工作日内删除并回复确认</li>
</ul></div>

<div class="sl-card"><h2>八、儿童</h2>
<p>本站面向具备基础编程能力的学习者，不针对 14 岁以下儿童设计，
也不会主动收集儿童的个人信息。</p></div>

<div class="sl-card"><h2>九、政策变更</h2>
<p>本政策如有变更，会直接更新本页并修改上方的「最后更新」日期。
涉及数据使用方式的重大变更，会在站内显著位置提示。</p></div>

<div class="sl-card"><h2>十、联系方式</h2>
<p>与本政策或数据处理有关的任何问题，请联系
<a href="mailto:skkk_lovelove@outlook.com">skkk_lovelove@outlook.com</a>。</p></div>""" %
                (ads_block, '已启用' if ADS_ENABLED else '当前未启用'))
        return shell(
            '隐私政策：数据收集、Cookie 与广告说明',
            body, '',
            'Spider Bond 的隐私政策：未登录时数据只存在本地浏览器；使用 GitHub 登录时'
            '仅获取用户 ID、用户名与头像用于进度同步；Cookie 清单、服务器日志保留时间、'
            '广告与第三方服务说明，以及数据删除方式。',
            path='/privacy',
            extra_ld=ld_crumbs([('首页', '/'), ('隐私政策', '/privacy')]),
        )

    body = """<h1>爬虫合规说明</h1>
<p>技术能做到，不等于可以去做。爬虫的边界主要由四件事决定：目标站点的公开声明、
你的请求对服务器的影响、你抓的数据是否涉及个人信息、以及你是否遵守目标站点的服务条款。</p>

<div class="row">
<div class="col-md-6 mb-3"><div class="sl-card h-100"><h2>只抓公开数据</h2>
<p>不登录、不绕过任何访问控制就能看到的内容，才是公开数据。需要登录才能看的、
被 robots.txt 禁止的、藏在接口鉴权后面的，都不属于「公开」。</p></div></div>
<div class="col-md-6 mb-3"><div class="sl-card h-100"><h2>标明身份</h2>
<p>在 User-Agent 里写清你是谁、怎么联系。伪装成浏览器来规避识别，
在很多场景会被认定为不正当竞争的证据。</p></div></div>
<div class="col-md-6 mb-3"><div class="sl-card h-100"><h2>优雅退让</h2>
<p>并发数、请求间隔、指数退避重试。遵守 Crawl-delay，被返回 429 就退让，
别把对方服务器打挂——这可能构成破坏计算机信息系统。</p></div></div>
<div class="col-md-6 mb-3"><div class="sl-card h-100"><h2>遵守条款</h2>
<p>robots.txt 是约定不是技术封锁，但绕过它风险很高。同时要看服务条款、
数据授权范围，以及《个人信息保护法》《反不正当竞争法》的相关要求。</p></div></div>
</div>

<div class="sl-card"><h2>本站的边界</h2>
<p>本站所有 <code>/lab/</code> 靶站都在 <a href="/robots.txt">robots.txt</a> 中明确允许抓取，
数据全部虚构，不含任何真实个人信息。你可以放心练习，但依然请遵守 Crawl-delay 0.5 秒
的要求，保持低频率请求。</p>
<p>练习的目的是掌握方法，不是把某个站点抓空。离开本站之后，
这个判断力比任何解析技巧都重要。</p></div>"""
    return shell(
        '爬虫合规说明：robots.txt、限速、身份标识与数据边界',
        body, '',
        '写爬虫之前先搞清楚边界：哪些是公开数据、如何在 User-Agent 标明身份、'
        '为什么要遵守 Crawl-delay 与指数退避、robots.txt 的法律属性，'
        '以及《个人信息保护法》《反不正当竞争法》的相关要求。',
        path='/compliance',
        extra_ld=ld_crumbs([('首页', '/'), ('合规说明', '/compliance')]),
    )


# ---------------------------------------------------------------- 判分
def normalize(value, typ):
    """归一化答案。

    浏览器沙箱提交的是 JSON 序列化后的字符串（如 '"书名"'）
    或 '["甲","乙"]'；手填文本框提交的是纯文本。
    两种都要能吃下去，否则沙箱来的答案永远判错。
    """
    if isinstance(value, str):
        parsed, ok = None, False
        try:
            parsed, ok = json.loads(value.strip()), True
        except (ValueError, TypeError):
            ok = False
        if ok:
            if typ == 'number' and isinstance(parsed, (int, float)) and not isinstance(parsed, bool):
                value = float(parsed)
            elif typ in ('olist', 'ulist') and isinstance(parsed, list):
                value = parsed
            elif typ in ('text', 'json') and isinstance(parsed, str):
                value = parsed
            elif typ == 'json':
                value = parsed

    if typ == 'number':
        return float(str(value).strip())
    if typ in ('olist', 'ulist'):
        if isinstance(value, list):
            return [str(x).strip() for x in value]
        return [x.strip() for x in str(value).replace('，', ',').split(',') if x.strip()]
    if typ == 'json':
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)
    return str(value).strip()


def _norm_url(x):
    """URL 类答案只比较路径：学员用域名或 IP 访问都能判对。"""
    s = str(x).strip()
    if '://' in s:
        try:
            return urlparse(s).path or s
        except ValueError:
            return s
    return s


def judge(tid, raw):
    t = TASKS.get(tid)
    if not t:
        return {'ok': False, 'message': '关卡不存在', 'hint': ''}
    typ = t['type']
    expected = ANSWERS[tid]
    try:
        got = normalize(raw, typ)
    except Exception as ex:
        return {'ok': False, 'message': '答案格式不正确（%s）' % type(ex).__name__,
                'hint': t['hint']}
    if typ == 'number':
        ok = abs(got - float(expected)) < 1e-6
    elif typ == 'ulist':
        ok = {_norm_url(x) for x in got} == {_norm_url(x) for x in expected}
    elif typ == 'olist':
        ok = [_norm_url(x) for x in got] == [_norm_url(x) for x in expected]
    else:
        ok = got == expected
    if ok:
        return {'ok': True,
                'message': '正确，%s「%s」通过，获得 %d 分。' % (tid, t['title'], t['points']),
                'hint': ''}
    return {'ok': False, 'message': '答案还不对，再检查一下。', 'hint': t['hint']}


def normalize_case(value, typ):
    """归一化浏览器沙箱提交的答案（前端统一 JSON 序列化）。"""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            pass
    if typ == 'number':
        return float(str(value).strip())
    if typ in ('olist', 'ulist'):
        if isinstance(value, (list, tuple)):
            return [str(x).strip() for x in value]
        return [x.strip() for x in str(value).replace('，', ',').split(',') if x.strip()]
    if typ == 'json':
        return value
    return str(value).strip()


def judge_case(slug, raw):
    """在线实练判分：只接收学员代码运行得到的 answer，不下发标准答案。"""
    c = BY_SLUG.get(slug)
    if not c:
        return {'ok': False, 'message': '案例不存在', 'hint': ''}
    typ, expected = c['type'], c['answer']
    try:
        got = normalize_case(raw, typ)
        if typ == 'number':
            ok = abs(got - float(expected)) < 1e-6
        elif typ == 'ulist':
            ok = {_norm_url(x) for x in got} == {_norm_url(x) for x in expected}
        elif typ == 'olist':
            ok = [_norm_url(x) for x in got] == [_norm_url(x) for x in expected]
        else:
            ok = got == expected
    except Exception:
        return {'ok': False, 'message': '答案格式不正确，请检查类型。', 'hint': c['hint']}
    if ok:
        return {'ok': True,
                'message': '通过，「%s」实练完成，获得 %d 分。' % (c['title'], c['points']),
                'hint': ''}
    return {'ok': False, 'message': '运行结果还不对，再检查一下代码。', 'hint': c['hint']}


def case_public(c):
    """下发到浏览器的案例数据：绝不包含 answer。"""
    return {k: v for k, v in c.items() if k != 'answer'}


# ---------------------------------------------------------------- robots / sitemap
ROBOTS = """# Spider Bond 教学靶场 robots.txt
# 本文件是第 1 课「合规底线」的实练素材。
User-agent: *
Allow: /
Disallow: /api/check
Disallow: /api/check_case
Disallow: /lab/trap/
Disallow: /admin/
Disallow: /auth/
Crawl-delay: 0.5

User-agent: SpiderBond-Student
Allow: /lab/
Crawl-delay: 0.5

Sitemap: %s/sitemap.xml
""" % BASE

# AdSense 授权文件（/ads.txt）。Google 会定期抓取它，核对本站是否授权 google.com
# 售卖广告位。格式是固定的四段式，必须以换行结尾、不能有 BOM 或注释，
# 否则会被判为无效条目（表现为 AdSense 后台一直显示"未找到 ads.txt"）。
ADS_TXT = 'google.com, pub-1319247814064058, DIRECT, f08c47fec0942fa0\n'

def _content_date():
    """内容更新时间：取课程数据的 mtime。内容改了就变，不改就稳定。"""
    try:
        return time.strftime('%Y-%m-%d', time.localtime(
            os.path.getmtime(os.path.join(ROOT, 'server', 'courses.py'))))
    except OSError:
        return time.strftime('%Y-%m-%d')


# IndexNow：Bing / Yandex / Naver / Seznam 共用的即时收录接口。
# 验证方式是在站点根暴露一个 {key}.txt（内容即 key 本身），然后 POST 待收录 URL。
# 不需要注册账号，也不需要像 Search Console 那样做域名验证。
# 注意 Google 不参与 IndexNow，它在 Google 一边必须走 Search Console 或自然发现。
INDEXNOW_KEY = '05a9b8d38a0f0b7cb167bb8095d8b2c7'


def _content_date_rfc822():
    """RSS 2.0 要求 RFC 822 时间格式，不能只给日期。"""
    try:
        ts = os.path.getmtime(os.path.join(ROOT, 'server', 'courses.py'))
    except OSError:
        ts = time.time()
    return time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime(ts))


def sitemap_xml():
    """站点地图：只收可索引页。

    靶站详情页全部 noindex，放进来只会互相矛盾，所以排除；
    课程与关卡才是真正有检索价值的页面，优先级按内容厚度分级。
    """
    lastmod = _content_date()
    urls = [('/', 'daily', '1.0'), ('/courses', 'weekly', '0.9')]
    urls += [('/courses/%s' % c['slug'], 'monthly', '0.8') for c in COURSES]
    urls += [('/training', 'weekly', '0.8')]
    urls += [('/training/%s' % tid, 'monthly', '0.4') for tid in TASKS]
    urls += [('/lab/', 'weekly', '0.6'),
             ('/compliance', 'monthly', '0.5'),
             ('/privacy', 'yearly', '0.3'),
             ('/about', 'yearly', '0.3')]
    rows = ''.join(
        '  <url><loc>%s</loc><lastmod>%s</lastmod>'
        '<changefreq>%s</changefreq><priority>%s</priority></url>\n'
        % (html.escape(abs_url(u)), lastmod, cf, pr)
        for u, cf, pr in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '%s</urlset>\n' % rows)


def rss_feed():
    """课程更新 feed。给订阅器和聚合站一个稳定的抓取入口。"""
    stamp = _content_date_rfc822()
    items = ''
    for c in COURSES:
        link = abs_url('/courses/%s' % c['slug'])
        items += (
            '  <item>\n'
            '    <title>%s</title>\n'
            '    <link>%s</link>\n'
            '    <guid isPermaLink="true">%s</guid>\n'
            '    <pubDate>%s</pubDate>\n'
            '    <description>%s</description>\n'
            '    <category>%s</category>\n'
            '  </item>\n'
            % (html.escape('第 %d 课 %s' % (c['no'], c['title'])),
               html.escape(link), html.escape(link), stamp,
               html.escape(clip(c['summary'], 200)),
               html.escape(c['track'])))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        '<channel>\n'
        '  <title>Spider Bond · Python 爬虫课程</title>\n'
        '  <link>%s</link>\n'
        '  <description>%s</description>\n'
        '  <language>zh-CN</language>\n'
        '  <lastBuildDate>%s</lastBuildDate>\n'
        '  <atom:link href="%s" rel="self" type="application/rss+xml"/>\n'
        '%s</channel>\n</rss>\n'
        % (html.escape(SITE_URL), html.escape(SITE_DESC), stamp,
           html.escape(abs_url('/feed.xml')), items))


# ---------------------------------------------------------------- HTTP Handler
# ---------------------------------------------------------------- 账号与进度同步（可选）
# 未登录：进度和代码草稿只存在浏览器 localStorage。
# 已登录：GitHub OAuth 换本站 session，进度同步到 SQLite。
# 配置写在 /opt/spiderlab.env —— 部署目录之外，重新部署不会被覆盖：
#   GITHUB_CLIENT_ID=xxx
#   GITHUB_CLIENT_SECRET=xxx
#   GITHUB_REDIRECT=https://spider.skkk.uno/auth/github/callback
def _load_env():
    for path in ('/opt/spiderlab.env', os.path.join(ROOT, '.env')):
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except OSError:
            continue


_load_env()

GH_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GH_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
GH_ENABLED = bool(GH_CLIENT_ID and GH_CLIENT_SECRET)
GH_REDIRECT = os.environ.get('GITHUB_REDIRECT',
                             'https://spider.skkk.uno/auth/github/callback')

_DB = {'path': os.environ.get('SPIDERLAB_DB', '')}


def db_path():
    if _DB['path']:
        return _DB['path']
    for cand in ('/opt/spiderlab.db', os.path.join(ROOT, 'spiderlab.db')):
        try:
            if os.access(os.path.dirname(cand) or '.', os.W_OK):
                _DB['path'] = cand
                return cand
        except Exception:
            pass
    _DB['path'] = os.path.join(ROOT, 'spiderlab.db')
    return _DB['path']


def db():
    conn = sqlite3.connect(db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def init_db():
    try:
        with db() as c:
            c.executescript("""
CREATE TABLE IF NOT EXISTS users(
  gid TEXT PRIMARY KEY, login TEXT, name TEXT, avatar TEXT,
  created_at TEXT, seen_at TEXT);
CREATE TABLE IF NOT EXISTS progress(
  gid TEXT NOT NULL, item TEXT NOT NULL, done INTEGER DEFAULT 0,
  draft TEXT, updated_at TEXT, PRIMARY KEY(gid, item));
CREATE TABLE IF NOT EXISTS sessions(
  sid TEXT PRIMARY KEY, gid TEXT NOT NULL, created_at TEXT);
CREATE TABLE IF NOT EXISTS events(
  gid TEXT NOT NULL, item TEXT NOT NULL, kind TEXT, ts TEXT);
CREATE INDEX IF NOT EXISTS idx_events_gid ON events(gid, ts);
CREATE TABLE IF NOT EXISTS study(
  gid TEXT NOT NULL, day TEXT NOT NULL, seconds INTEGER DEFAULT 0,
  PRIMARY KEY(gid, day));
""")
    except Exception as ex:
        print('数据库初始化失败：%s' % ex, flush=True)


def gh_authorize_url(state):
    return 'https://github.com/login/oauth/authorize?' + urlencode({
        'client_id': GH_CLIENT_ID,
        'redirect_uri': GH_REDIRECT,
        'scope': 'read:user',
        'state': state,
    })


def gh_exchange_code(code):
    body = urlencode({
        'client_id': GH_CLIENT_ID,
        'client_secret': GH_CLIENT_SECRET,
        'code': code,
        'redirect_uri': GH_REDIRECT,
    }).encode()
    req = urllib.request.Request(
        'https://github.com/login/oauth/access_token', data=body,
        headers={'Accept': 'application/json', 'User-Agent': 'SpiderBond'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8')).get('access_token')


def gh_fetch_user(token):
    req = urllib.request.Request(
        'https://api.github.com/user',
        headers={'Authorization': 'Bearer %s' % token,
                 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'SpiderBond'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def create_session(gid):
    sid = secrets.token_urlsafe(32)
    with db() as c:
        c.execute('INSERT INTO sessions(sid, gid, created_at) VALUES(?,?,?)',
                  (sid, gid, now_iso()))
    return sid


def session_user(sid):
    if not sid:
        return None
    try:
        with db() as c:
            row = c.execute(
                'SELECT u.gid, u.login, u.name, u.avatar FROM sessions s '
                'JOIN users u ON u.gid = s.gid WHERE s.sid = ?', (sid,)).fetchone()
        return dict(row) if row else None
    except Exception:
        return None


init_db()


class Handler(BaseHTTPRequestHandler):
    server_version = 'SpiderBond/1.0'
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt % args), flush=True)

    # ---------- 底层发送 ----------
    def _send(self, code, body, ctype='text/html; charset=utf-8', extra=None):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        # 三项基础防护：Referrer 只发源不发路径（别把查询串里的东西带给外站）；
        # XFO 禁止被 iframe 嵌入（与 CSP 的 frame-ancestors 双保险，兼容老浏览器）；
        # COOP 把本窗口与其他文档隔离，防止被恶意页面通过 window.opener 反向操作。
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Permissions-Policy',
                         'geolocation=(), microphone=(), camera=(), payment=()')
        # 动态 HTML 一律不缓存。SPA 首页引用的是带 hash 的 JS bundle，
        # 若 HTML 被浏览器启发式缓存，发布新版本后用户会一直加载旧 bundle。
        # CSP 只对 HTML 下发：JSON 接口不需要，接口的 CSP 头没有意义。
        headers = {}
        if 'text/html' in ctype:
            headers['Cache-Control'] = 'no-cache'
            headers['Content-Security-Policy'] = csp(cur_nonce())
        headers.update(extra or {})
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # ---- 账号相关小工具 ----
    def _cookie(self, name):
        m = re.search(r'(?:^|;\s*)' + re.escape(name) + r'=([^;]+)',
                      self.headers.get('Cookie') or '')
        return m.group(1) if m else ''

    def _cookie_secure(self):
        host = self.headers.get('Host') or ''
        return '' if host.startswith(('127.0.0.1', 'localhost', '192.168.')) else '; Secure'

    def _me(self):
        return session_user(self._cookie('sl_sid'))

    def _json(self, code, obj, extra=None):
        self._send(code, json.dumps(obj, ensure_ascii=False),
                   'application/json; charset=utf-8', extra)

    def _redirect(self, location, extra=None):
        self.send_response(302)
        self.send_header('Location', location)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _static(self, path):
        name = os.path.basename(path)
        if not re.match(r'^[\w.\-]+$', name):
            return False
        candidates = [os.path.join(DIST, 'assets', name),
                      os.path.join(ASSETS, name),
                      os.path.join(DIST, name),
                      # Pyodide 运行时。线上由 Nginx 的 /pyodide/ 直接服务，
                      # 这里兜底是为了本地跑起来不依赖 Nginx（否则沙箱 404）。
                      os.path.join(DIST, 'pyodide', name)]
        for fp in candidates:
            if os.path.isfile(fp):
                ctype = mimetypes.guess_type(fp)[0] or 'application/octet-stream'
                # 下面几个类型必须显式指定：.mjs 若被当成 octet-stream，
                # 浏览器会拒绝执行 dynamic import；.wasm 若不是 application/wasm，
                # 会退化成非流式编译甚至直接失败。
                if fp.endswith('.js') or fp.endswith('.mjs'):
                    ctype = 'text/javascript; charset=utf-8'
                elif fp.endswith('.css'):
                    ctype = 'text/css; charset=utf-8'
                elif fp.endswith('.svg'):
                    ctype = 'image/svg+xml'
                elif fp.endswith('.wasm'):
                    ctype = 'application/wasm'
                elif fp.endswith('.whl') or fp.endswith('.zip'):
                    ctype = 'application/zip'
                elif fp.endswith('.json'):
                    ctype = 'application/json; charset=utf-8'
                with open(fp, 'rb') as f:
                    self._send(200, f.read(), ctype)
                return True
        return False

    def _spa(self):
        fp = os.path.join(DIST, 'index.html')
        if os.path.isfile(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                html = f.read()
            # 静态 index.html 里的内联脚本用占位符，请求时换成一次性 nonce。
            # 换掉之后浏览器才会执行它，否则深色模式会闪白。
            n = cur_nonce()
            if n:
                html = html.replace('__CSP_NONCE__', n)
            self._send(200, html, 'text/html; charset=utf-8')
        else:
            self._send(200, shell('Spider Bond',
                '<h1>Spider Bond</h1><p>教学站正在构建中，请先访问 '
                '<a href="/courses">课程目录</a> 与 <a href="/lab/">示例靶站</a>。</p>'))

    # ---------- GET ----------
    def do_GET(self):
        # 先备好本次请求的 nonce，页面渲染时取用，_send 再把它写进 CSP 头
        new_nonce()
        u = urlparse(self.path)
        p, qs = u.path, parse_qs(u.query)
        h = self.headers
        ip = self.client_address[0]

        try:
            if p == '/%s.txt' % INDEXNOW_KEY:
                # IndexNow 的归属验证文件：内容必须与文件名里的 key 完全一致
                return self._send(200, INDEXNOW_KEY,
                                  'text/plain; charset=utf-8',
                                  {'Cache-Control': 'public, max-age=86400'})
            if p == '/ads.txt':
                # 不能长缓存：AdSense 审核期间改动要尽快生效；文件本身不到 100 字节
                return self._send(200, ADS_TXT, 'text/plain; charset=utf-8',
                                  {'Cache-Control': 'no-cache'})
            if p == '/robots.txt':
                # 教学用 robots：禁止中间层缓存，确保新增规则立即生效
                return self._send(200, ROBOTS, 'text/plain; charset=utf-8',
                                  {'Cache-Control': 'no-cache, no-store, must-revalidate'})
            if p == '/sitemap.xml':
                return self._send(200, sitemap_xml(),
                                  'application/xml; charset=utf-8')
            if p in ('/feed.xml', '/rss.xml'):
                return self._send(200, rss_feed(),
                                  'application/rss+xml; charset=utf-8')

            if (p.startswith('/assets/') or p.startswith('/pyodide/')
                    or p in ('/favicon.svg', '/favicon.ico')):
                if self._static(p):
                    return
                return self._send(404, 'Not Found', 'text/plain; charset=utf-8')

            # ---- 教学站 / SSR 兜底页 ----
            if p == '/':
                return self._spa()
            if p == '/courses':
                return self._send(200, page_courses())
            if p.startswith('/courses/'):
                # 不存在的课程必须返回真 404：之前一律 200 会让搜索引擎把
                # 一堆空壳页当有效内容收录（软 404）。
                slug = p.split('/')[-1]
                ok = any(c['slug'] == slug for c in COURSES)
                return self._send(200 if ok else 404, page_course(slug))
            if p == '/training':
                return self._send(200, page_training())
            if p.startswith('/training/'):
                tid = p.split('/')[-1]
                return self._send(200 if tid in TASKS else 404, page_task(tid))
            if p in ('/about', '/compliance', '/privacy'):
                return self._send(200, page_static(p))

            # ---- JSON API（内容类） ----
            if p == '/api/courses':
                return self._json(200, [
                    {k: c[k] for k in ('slug', 'no', 'title', 'track', 'level',
                                       'minutes', 'summary')} for c in COURSES])
            if p.startswith('/api/courses/'):
                slug = p.split('/')[-1]
                c = next((x for x in COURSES if x['slug'] == slug), None)
                return self._json(200, c) if c else self._json(404, {'error': 'not found'})
            if p == '/api/tracks':
                return self._json(200, TRACKS)
            if p == '/api/me':
                u = self._me()
                return self._json(200, {
                    'enabled': GH_ENABLED,
                    'user': ({'login': u['login'], 'name': u['name'], 'avatar': u['avatar']}
                             if u else None),
                })

            if p == '/auth/github':
                if not GH_ENABLED:
                    return self._send(503, 'GitHub 登录未配置', 'text/plain; charset=utf-8')
                state = secrets.token_urlsafe(20)
                return self._redirect(gh_authorize_url(state), {
                    'Set-Cookie': 'sl_oauth_state=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=600%s'
                                  % (state, self._cookie_secure())})

            if p == '/auth/github/callback':
                code = (qs.get('code') or [''])[0]
                state = (qs.get('state') or [''])[0]
                if not (GH_ENABLED and code and self._cookie('sl_oauth_state') == state):
                    return self._redirect('/?auth=state')
                try:
                    token = gh_exchange_code(code)
                    gu = gh_fetch_user(token) if token else None
                except Exception:
                    gu = None
                if not gu or not gu.get('id'):
                    return self._redirect('/?auth=failed')
                gid = str(gu['id'])
                with db() as c:
                    c.execute(
                        'INSERT INTO users(gid, login, name, avatar, created_at, seen_at) '
                        'VALUES(?,?,?,?,?,?) ON CONFLICT(gid) DO UPDATE SET '
                        'login=excluded.login, name=excluded.name, '
                        'avatar=excluded.avatar, seen_at=excluded.seen_at',
                        (gid, gu.get('login') or '', gu.get('name') or '',
                         gu.get('avatar_url') or '', now_iso(), now_iso()))
                sid = create_session(gid)
                return self._redirect('/?auth=ok', {
                    'Set-Cookie': 'sl_sid=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000%s'
                                  % (sid, self._cookie_secure())})

            if p == '/api/progress':
                u = self._me()
                if not u:
                    return self._json(401, {'error': 'not_logged_in'})
                with db() as c:
                    rows = c.execute(
                        'SELECT item, done, draft FROM progress WHERE gid = ?',
                        (u['gid'],)).fetchall()
                return self._json(200, {
                    'done': [r['item'] for r in rows if r['done']],
                    'drafts': {r['item']: r['draft'] for r in rows if r['draft']},
                })

            if p == '/api/profile':
                u = self._me()
                if not u:
                    return self._json(401, {'error': 'not_logged_in'})
                with db() as c:
                    evs = c.execute(
                        'SELECT item, kind, ts FROM events WHERE gid = ? '
                        'ORDER BY ts DESC LIMIT 800', (u['gid'],)).fetchall()
                    done_rows = c.execute(
                        'SELECT item FROM progress WHERE gid = ? AND done = 1',
                        (u['gid'],)).fetchall()
                    st_rows = c.execute(
                        'SELECT day, seconds FROM study WHERE gid = ?',
                        (u['gid'],)).fetchall()
                days = {}
                for r in evs:
                    d = (r['ts'] or '')[:10]
                    if d:
                        days[d] = days.get(d, 0) + 1
                return self._json(200, {
                    'user': {'login': u['login'], 'name': u['name'], 'avatar': u['avatar']},
                    'done': [r['item'] for r in done_rows],
                    'days': days,
                    'study': {r['day']: r['seconds'] for r in st_rows},
                    'events': [{'item': r['item'], 'ts': r['ts']} for r in evs],
                })

            if p == '/api/labs':
                return self._json(200, SITES)
            if p == '/api/levels':
                safe = copy_tasks_without_answers()
                return self._json(200, {'levels': LEVELS, 'tasks': safe})
            if p == '/api/cases':
                return self._json(200, [case_public(c) for c in CASES])
            if p.startswith('/api/cases/'):
                slug = p.split('/')[-1]
                c = BY_SLUG.get(slug)
                return self._json(200, case_public(c)) if c else self._json(404, {'error': 'not found'})

            # ---- 靶场：书城 ----
            if p == '/lab' or p == '/lab/':
                return self._send(200, lab_index())
            if p == '/lab/robots.txt':
                # 教学版 robots.txt：不受 CDN 托管 robots 规则干扰
                return self._send(200, ROBOTS, 'text/plain; charset=utf-8',
                                  {'Cache-Control': 'no-cache'})
            if p == '/lab/books':
                page = max(1, int(qs.get('page', ['1'])[0]))
                return self._send(200, lab_books(page))
            m = re.match(r'^/lab/books/(\d+)$', p)
            if m:
                code, body = lab_book_detail(int(m.group(1)))
                return self._send(code, body)
            if p == '/lab/quotes':
                page = max(1, int(qs.get('page', ['1'])[0]))
                return self._send(200, lab_quotes(page))
            if p == '/lab/movies':
                return self._send(200, lab_movies())
            if p == '/lab/products':
                page = max(1, int(qs.get('page', ['1'])[0]))
                def _num(k):
                    v = qs.get(k, [None])[0]
                    try:
                        return float(v) if v not in (None, '') else None
                    except ValueError:
                        return None
                return self._send(200, lab_products(page, _num('min'), _num('max')))
            if p == '/lab/jobs':
                page = max(1, int(qs.get('page', ['1'])[0]))
                return self._send(200, lab_jobs(page))
            _jm = re.match(r'^/lab/jobs/(\d+)$', p)
            if _jm:
                code, body = lab_job_detail(int(_jm.group(1)))
                return self._send(code, body)
            if p == '/lab/feed':
                return self._send(200, lab_feed(), 'application/rss+xml; charset=utf-8')
            if p == '/lab/stats':
                return self._send(200, lab_stats())
            if p == '/lab/news':
                return self._send(200, lab_news())
            if p.startswith('/lab/news/'):
                return self._send(200, lab_shell('新闻详情',
                    '<h1>新闻详情</h1><p>该靶场仅提供列表页用于解析练习。</p>'))
            if p.startswith('/lab/trap'):
                code, body = lab_trap()
                return self._send(code, body)

            # ---- 靶场：JSON 接口 ----
            if p == '/lab/api':
                return self._send(200, lab_api_doc())
            if p in ('/lab/api/v1/items', '/lab/api/v1/token'):
                labkey = h.get('X-Lab-Key') or h.get('X-Sl-Lab-Key')
                if labkey != LAB_KEY:
                    return self._json(403, {'error': 'missing or invalid X-Lab-Key',
                                            'hint': '见 /lab/api 说明页'})
                if p.endswith('/token'):
                    return self._json(200, {'token': GUARD_TOKEN})
                code, obj = api_items(qs)
                return self._json(code, obj)

            # ---- 靶场：登录保险库 ----
            if p == '/lab/vault':
                cookie = h.get('Cookie', '') or h.get('X-Sl-Cookie', '')
                ok = 'lab_session=ok' in cookie
                code, body = lab_vault(ok)
                return self._send(code, body)
            if p == '/lab/vault/logout':
                return self._redirect('/lab/vault',
                    {'Set-Cookie': 'lab_session=; Path=/; Max-Age=0'})

            # ---- 靶场：请求头守卫 ----
            if p == '/lab/guard' or p == '/lab/guard/':
                code, body, extra = lab_guard(h, ip)
                return self._send(code, body, extra=extra)

            return self._send(404, shell('404',
                '<h1>404</h1><p>页面不存在。<a href="/">返回首页</a></p>'))
        except (ValueError, IndexError):
            return self._send(400, shell('400', '<h1>400</h1><p>请求参数不合法。</p>'))
        except Exception as ex:
            print('ERROR:', repr(ex), flush=True)
            return self._send(500, shell('500', '<h1>500</h1><p>服务内部错误。</p>'))

    # ---------- POST ----------
    def do_POST(self):
        u = urlparse(self.path)
        p = u.path
        length = int(self.headers.get('Content-Length', 0) or 0)
        raw = self.rfile.read(length).decode('utf-8', 'ignore') if length else ''
        try:
            ctype = self.headers.get('Content-Type', '')
            data = (json.loads(raw or '{}') if 'application/json' in ctype
                    else dict(parse_qsl(raw))) if raw else {}
            if p == '/api/progress':
                u = self._me()
                if not u:
                    return self._json(401, {'error': 'not_logged_in'})
                ts = now_iso()
                done = data.get('done') or []
                drafts = data.get('drafts') or {}
                with db() as c:
                    for item in done:
                        key = str(item)[:80]
                        # 只有「从未完成 → 完成」这一刻才写事件。
                        # 不能用「events 里没有就补」——那会把功能上线前的历史
                        # 通关全部补记到当天，日历出现假的集中记录。
                        row = c.execute(
                            'SELECT done FROM progress WHERE gid = ? AND item = ?',
                            (u['gid'], key)).fetchone()
                        was_done = bool(row and row['done'])
                        c.execute(
                            'INSERT INTO progress(gid, item, done, updated_at) VALUES(?,?,1,?) '
                            'ON CONFLICT(gid, item) DO UPDATE SET '
                            'done=1, updated_at=excluded.updated_at',
                            (u['gid'], key, ts))
                        if not was_done:
                            c.execute(
                                'INSERT INTO events(gid, item, kind, ts) VALUES(?,?,?,?)',
                                (u['gid'], key, 'pass', ts))
                    for item, code in drafts.items():
                        c.execute(
                            'INSERT INTO progress(gid, item, done, draft, updated_at) '
                            'VALUES(?,?,0,?,?) ON CONFLICT(gid, item) DO UPDATE SET '
                            'draft=excluded.draft, updated_at=excluded.updated_at',
                            (u['gid'], str(item)[:80], str(code)[:20000], ts))
                    # 学习时长：客户端传的是「当天累计秒数」，用 MAX 避免多端互相覆盖回退
                    for day, secs in (data.get('study') or {}).items():
                        try:
                            secs = int(secs)
                        except (TypeError, ValueError):
                            continue
                        if secs <= 0:
                            continue
                        c.execute(
                            'INSERT INTO study(gid, day, seconds) VALUES(?,?,?) '
                            'ON CONFLICT(gid, day) DO UPDATE SET '
                            'seconds = MAX(study.seconds, excluded.seconds)',
                            (u['gid'], str(day)[:10], min(secs, 86400)))
                return self._json(200, {'ok': True})

            if p == '/auth/logout':
                sid = self._cookie('sl_sid')
                if sid:
                    try:
                        with db() as c:
                            c.execute('DELETE FROM sessions WHERE sid = ?', (sid,))
                    except Exception:
                        pass
                return self._json(200, {'ok': True}, {
                    'Set-Cookie': 'sl_sid=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax'})

            if p == '/api/check':
                return self._json(200, judge(data.get('task_id', ''),
                                             data.get('answer', '')))

            if p == '/api/check_case':
                return self._json(200, judge_case(data.get('slug', ''),
                                                 data.get('answer', '')))

            if p == '/lab/vault/login':
                form = dict(parse_qsl(raw))
                if form.get('username') == VAULT_USER and form.get('password') == VAULT_PASS:
                    ck = {'Set-Cookie': 'lab_session=ok; Path=/; HttpOnly; SameSite=Lax'}
                    # 浏览器沙箱无法读取 Set-Cookie / 禁止手动设置 Cookie，
                    # 用可读别名回传会话，沙箱再通过 X-Sl-Cookie 带回来。
                    if self.headers.get('X-Sl-Shim') == '1':
                        ck['X-Sl-Set-Cookie'] = 'lab_session=ok; Path=/'
                        return self._send(200, '{"ok":true}',
                                          'application/json; charset=utf-8', ck)
                    return self._redirect('/lab/vault', ck)
                body = lab_shell('登录失败',
                    '<h1>登录失败</h1><div class="callout no">用户名或密码不正确，'
                    '请对照说明页的字段与取值。</div><a href="/lab/vault">返回说明页</a>')
                return self._send(401, body)

            return self._send(404, shell('404', '<h1>404</h1><p>接口不存在。</p>'))
        except Exception as ex:
            print('POST ERROR:', repr(ex), flush=True)
            return self._json(500, {'error': 'internal error'})

    def do_HEAD(self):
        self.do_GET()


def copy_tasks_without_answers():
    """只下发关卡描述，绝不下发 ANSWERS。"""
    return {tid: {k: v for k, v in t.items()} for tid, t in TASKS.items()}


if __name__ == '__main__':
    os.chdir(ROOT)
    port = int(os.environ.get('SPIDERLAB_PORT', '8080'))
    srv = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    srv.daemon_threads = True
    print('Spider Bond listening on 0.0.0.0:%d' % port, flush=True)
    srv.serve_forever()
