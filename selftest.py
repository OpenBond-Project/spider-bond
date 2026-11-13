# -*- coding: utf-8 -*-
"""Spider Bond 本地自测：启动服务并逐项验证路由、判分、靶场语义。"""
import json
import os
import re
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'server'))
os.chdir(ROOT / 'server')

from app import Handler, SPRITE, ROBOTS  # noqa: E402
from labs import ANSWERS, BASE, TASKS    # noqa: E402

Handler.log_message = lambda self, *a: None
srv = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

PASSED, FAILED = [], []


def req(path, method='GET', data=None, headers=None):
    url = 'http://127.0.0.1:%d%s' % (PORT, path)
    body = None
    h = headers or {}
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode()
            h.setdefault('Content-Type', 'application/json')
        else:
            body = data.encode() if isinstance(data, str) else data
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode('utf-8', 'ignore'), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore'), dict(e.headers)


def check(name, cond, detail=''):
    (PASSED if cond else FAILED).append(name)
    print(('  OK   ' if cond else '  FAIL ') + name + ((' -> ' + detail) if detail and not cond else ''))


print('\n=== 1. 教学站与静态资源 ===')
c, b, _ = req('/')
check('SPA 首页返回 200 且挂载点存在', c == 200 and 'id="app"' in b, 'code=%d' % c)
m = re.search(r'/assets/(index-[\w-]+\.(?:js|css))', b)
check('index.html 引用了构建产物', bool(m))
if m:
    c2, b2, h2 = req('/assets/' + m.group(1))
    check('构建产物可访问', c2 == 200 and len(b2) > 1000 and
          ('javascript' in h2.get('Content-Type', '') or 'text/css' in h2.get('Content-Type', '')),
          'code=%d ctype=%s' % (c2, h2.get('Content-Type')))
for f in ('bootstrap.min.css', 'lab.css', 'lucide.svg', 'favicon.svg'):
    c2, b2, _ = req('/assets/' + f)
    check('静态资源 ' + f, c2 == 200 and len(b2) > 20, 'code=%d len=%d' % (c2, len(b2)))
check('Lucide sprite 含 symbol', 'i-bug' in SPRITE and 'i-unlock' in SPRITE)

print('\n=== 2. SSR 兜底页 ===')
for path, kw in [('/courses', '课程目录'), ('/courses/xpath', 'XPath'),
                 ('/training', '分级训练场'), ('/training/L1-1', '提交答案')]:
    c2, b2, _ = req(path)
    check(path, c2 == 200 and kw in b2, 'code=%d' % c2)

print('\n=== 3. JSON 接口 ===')
c, b, _ = req('/api/courses')
check('/api/courses 返回 20 课', c == 200 and len(json.loads(b)) == 20)
c, b, _ = req('/api/levels')
d = json.loads(b)
check('/api/levels 返回 5 级 30 关', len(d['levels']) == 5 and len(d['tasks']) == 30)
_leak = [k for k, v in ANSWERS.items()
         if len(str(v)) > 8 and not str(v).startswith('/') and str(v) in b]
check('关卡数据未泄露答案', not _leak, str(_leak[:3]))
c, b, _ = req('/api/labs')
check('/api/labs 返回 11 个靶站', len(json.loads(b)) == 11)
c, b, _ = req('/api/courses/xpath')
check('课程详情含示例代码', 'lxml' in b or 'etree' in b)

print('\n=== 4. robots / sitemap ===')
c, b, _ = req('/robots.txt')
check('robots.txt 允许 /lab/ 且含 Crawl-delay', c == 200 and 'Allow: /' in b and 'Crawl-delay' in b)
c, b, _ = req('/sitemap.xml')
# 靶站页是 noindex 的教学素材，不应出现在 sitemap；有检索价值的是课程与关卡
check('sitemap.xml 列出课程与关卡',
      c == 200 and '/courses/intro-and-law' in b and '/training/L1-1' in b)
check('sitemap.xml 不含 noindex 的靶站页', '/lab/books' not in b)

print('\n=== 4b. SEO 标签 ===')
c, b, _ = req('/courses')
check('课程目录页有 canonical',
      'rel="canonical" href="https://spider.skkk.uno/courses"' in b)
check('课程目录页有 og:image',
      'property="og:image" content="https://spider.skkk.uno/assets/og-cover.png"' in b)
c, b, _ = req('/courses/intro-and-law')
check('课程详情有 LearningResource 结构化数据',
      'application/ld+json' in b and 'LearningResource' in b)
check('课程详情有面包屑结构化数据', 'BreadcrumbList' in b)
c, b, _ = req('/lab/books?page=1')
check('靶站页为 noindex', 'noindex' in b and 'rel="canonical"' not in b)
c, b, _ = req('/courses/not-a-real-course')
check('不存在的课程返回真 404', c == 404)
c, b, _ = req('/privacy')
check('隐私政策页可访问', c == 200 and '<h1>' in b)
check('隐私政策含 Cookie 清单',
      'sl_sid' in b and 'sl_oauth_state' in b and '__cf_bm' in b)
check('隐私政策说明广告现状（未启用时须如实写明）', '未启用任何广告' in b)
check('隐私政策含数据删除方式', 'skkk_lovelove@outlook.com' in b)
check('隐私政策有 canonical',
      'rel="canonical" href="https://spider.skkk.uno/privacy"' in b)
c, b, _ = req('/sitemap.xml')
check('sitemap 含隐私政策', '/privacy' in b)
c, b, _ = req('/feed.xml')
check('RSS feed 可用', c == 200 and '<rss' in b and b.count('<item>') == 20)

print('\n=== 4c. 安全响应头（CSP / HSTS / COOP / XFO）===')
c, b, hd = req('/')
csp_v = hd.get('Content-Security-Policy', '')
check('HTML 下发 CSP', c == 200 and 'default-src' in csp_v)
check('CSP 含 frame-ancestors none（防点击劫持）', "frame-ancestors 'none'" in csp_v)
check('CSP 含 object-src none', "object-src 'none'" in csp_v)
check('CSP 含 base-uri self', "base-uri 'self'" in csp_v)
check('CSP 保留 wasm-unsafe-eval（沙箱必需）', "'wasm-unsafe-eval'" in csp_v)
# 关键：script-src 里不能有 'unsafe-inline'，否则 XSS 防护形同虚设
_script_src = csp_v.split('script-src')[1].split(';')[0] if 'script-src' in csp_v else ''
check("script-src 不含 'unsafe-inline'", "'unsafe-inline'" not in _script_src)
check("script-src 不含 'unsafe-eval'", "'unsafe-eval'" not in _script_src)
# nonce 必须与 HTML 内联脚本一致，否则主题脚本被拦、深色模式闪白
_m = re.search(r"'nonce-([^']+)'", csp_v)
_h = re.search(r'nonce="([^"]+)"', b)
check('CSP nonce 与 HTML 内联脚本一致',
      bool(_m and _h and _m.group(1) == _h.group(1)))
check('X-Frame-Options 为 DENY', hd.get('X-Frame-Options') == 'DENY')
check('COOP 为 same-origin', hd.get('Cross-Origin-Opener-Policy') == 'same-origin')
check('Referrer-Policy 已设置', 'strict-origin' in hd.get('Referrer-Policy', ''))
check('默认不放开广告域（未投放时不该扩大攻击面）',
      'googlesyndication' not in csp_v and 'frame-src' not in csp_v)
c, b, hd = req('/api/levels')
check('JSON 接口不下发 CSP（无意义且浪费字节）',
      'Content-Security-Policy' not in hd)
c, b, hd = req('/lab/books?page=1')
check('靶场页同样下发 CSP', 'Content-Security-Policy' in hd)
check('靶场页无内联 onclick 残留（CSP 会拦）', 'onclick="' not in b)

print('\n=== 4d. ads.txt（AdSense 授权）===')
c, b, hd = req('/ads.txt')
check('ads.txt 返回 200', c == 200)
check('ads.txt 为纯文本', 'text/plain' in hd.get('Content-Type', ''))
check('ads.txt 内容与 AdSense 后台一致',
      b.strip() == 'google.com, pub-1319247814064058, DIRECT, f08c47fec0942fa0')
check('ads.txt 无 BOM', not b.startswith('\ufeff'))
check('ads.txt 以换行结尾', b.endswith('\n'))
check('ads.txt 短缓存（改动尽快生效）',
      'no-cache' in hd.get('Cache-Control', ''))

print('\n=== 5. 靶场页面（服务端渲染，源码即数据） ===')
c, b, _ = req('/lab/')
check('靶站索引', c == 200 and '书城' in b)
c, b, _ = req('/lab/books?page=1')
check('书城title与L1-1答案一致', '<title>%s</title>' % ANSWERS['L1-1'] in b, b[:200])
check('书城含 4 个 div.book', b.count('class="book"') == 4, str(b.count('class="book"')))
check('书城含 h2/price/author/detail', all(x in b for x in
      ('<h2>', 'class="price"', 'class="author"', 'class="detail"')))
c, b, _ = req('/lab/books/2')
check('书籍详情含 data-stock', 'data-stock="7"' in b)
c, b, _ = req('/lab/quotes?page=1')
check('名言墙含 span.author', 'class="author"' in b)
c, b, _ = req('/lab/movies')
check('电影榜为 table 结构', '<table' in b and 'class="rating"' in b)
c, b, _ = req('/lab/news')
check('新闻中心含 data-id/data-views 与蜜罐', 'data-id="101"' in b and 'class="trap"' in b)
c, b, _ = req('/lab/trap/hidden')
check('蜜罐链接返回 403', c == 403, 'code=%d' % c)

print('\n=== 6. 鉴权 / 会话 / 守卫 ===')
c, b, _ = req('/lab/api/v1/items?page=1&size=5')
check('接口未带 X-Lab-Key 返回 403', c == 403, 'code=%d' % c)
H = {'X-Lab-Key': 'spiderlab'}
c, b, _ = req('/lab/api/v1/items?page=1&size=5', headers=H)
d = json.loads(b)
check('接口返回分页 JSON 且 has_next=True', c == 200 and len(d['items']) == 5 and d['has_next'])
c, b, _ = req('/lab/api/v1/token', headers=H)
check('Token 接口返回正确答案', json.loads(b)['token'] == ANSWERS['L3-1'])
c, b, _ = req('/lab/vault')
check('未登录访问保险库返回 403', c == 403, 'code=%d' % c)
check('403 页面含用户名字段说明', 'username' in b)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_no_redirect_opener = urllib.request.build_opener(NoRedirect)
login = 'username=student&password=spiderlab'.encode()
_r = urllib.request.Request('http://127.0.0.1:%d/lab/vault/login' % PORT,
                            data=login, method='POST',
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
try:
    _resp = _no_redirect_opener.open(_r, timeout=10)
    c, h = _resp.status, dict(_resp.headers)
except urllib.error.HTTPError as e:
    c, h = e.code, dict(e.headers)
cookie = h.get('Set-Cookie', '').split(';')[0]
check('登录成功返回 302 并设置 Cookie', c == 302 and 'lab_session=ok' in cookie,
      'code=%d cookie=%s' % (c, cookie))
check('登录 302 指向 /lab/vault', h.get('Location') == '/lab/vault', str(h.get('Location')))
c, b, _ = req('/lab/vault', headers={'Cookie': cookie})
check('带 Cookie 可读取 secret', c == 200 and ANSWERS['L3-2'] in b, 'code=%d' % c)
c, b, _ = req('/lab/guard')
check('守卫页无请求头返回 403', c == 403, 'code=%d' % c)
GH = {'User-Agent': 'SpiderBond-Student/1.0', 'Referer': BASE + '/lab/guard/'}
c, b, _ = req('/lab/guard', headers=GH)
check('合规请求头取得 guard-code', c == 200 and ANSWERS['L5-1'] in b, 'code=%d' % c)

print('\n=== 7. 判分接口（全部 30 关正确答案 + 错误答案） ===')
ok_all = True
for tid, ans in ANSWERS.items():
    payload = ans if isinstance(ans, (int, float, list)) else ans
    if isinstance(payload, list):
        payload = json.dumps(payload, ensure_ascii=False) if TASKS[tid]['type'] == 'json' \
            else ','.join(str(x) for x in payload)
    c, b, _ = req('/api/check', method='POST',
                  data={'task_id': tid, 'answer': str(payload)})
    d = json.loads(b)
    if not d.get('ok'):
        ok_all = False
        print('       %s 判分失败: %s' % (tid, d.get('message')))
check('30 关标准答案全部判为通过', ok_all)
c, b, _ = req('/api/check', method='POST', data={'task_id': 'L1-3', 'answer': '999'})
check('错误答案被拒绝并返回提示', not json.loads(b)['ok'] and bool(json.loads(b)['hint']))
c, b, _ = req('/api/check', method='POST', data={'task_id': 'NOPE', 'answer': 'x'})
check('不存在的关卡被拒绝', not json.loads(b)['ok'])

print('\n=== 8. 零 emoji 校验（渲染输出） ===')
pat = re.compile('[\U0001F300-\U0001FAFF\u2600-\u27BF]')
pages = ['/', '/courses', '/courses/xpath', '/training', '/lab/', '/lab/books?page=1',
         '/lab/movies', '/lab/news', '/lab/api', '/lab/vault', '/lab/guard']
bad = [p for p in pages if pat.search(req(p)[1])]
check('所有渲染页面无 emoji', not bad, str(bad))

srv.shutdown()
print('\n' + '=' * 54)
print('PASS: %d   FAIL: %d' % (len(PASSED), len(FAILED)))
if FAILED:
    print('FAILED ITEMS:')
    for f in FAILED:
        print('  -', f)
    sys.exit(1)
print('SELFTEST OK')
