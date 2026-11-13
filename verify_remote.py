# -*- coding: utf-8 -*-
"""Spider Bond 公网端到端验证（针对已部署的站点）。

默认验证 https://spider.skkk.uno；要验证其他地址，设环境变量：
    SL_HOST_URL=http://<你的服务器 IP> python verify_remote.py
"""
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'server'))
from labs import ANSWERS, TASKS, BASE  # noqa: E402

HOST = os.environ.get('SL_HOST_URL', 'https://spider.skkk.uno').rstrip('/')
PASS, FAIL = [], []


def req(path, method='GET', data=None, headers=None, opener=None):
    h = dict(headers or {})
    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode()
            h.setdefault('Content-Type', 'application/json')
        else:
            body = str(data).encode()
            h.setdefault('Content-Type', 'application/x-www-form-urlencoded')
    op = opener or urllib.request.build_opener()
    last = None
    for attempt in range(3):
        r = urllib.request.Request(HOST + path, data=body, headers=h, method=method)
        try:
            with op.open(r, timeout=12) as resp:
                return resp.status, resp.read().decode('utf-8', 'ignore'), dict(resp.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'ignore'), dict(e.headers)
        except Exception as e:                      # 公网偶发抖动容错
            last = e
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))
    raise last


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(('  OK   ' if cond else '  FAIL ') + name +
          ((' -> ' + detail) if detail and not cond else ''))


print('=== A. 教学站与静态资源 ===')
c, b, _ = req('/')
check('首页 SPA 200', c == 200 and 'id="app"' in b, 'code=%d' % c)
assets = re.findall(r'/assets/([\w.-]+)', b)
check('index.html 引用构建产物', len(assets) >= 2, str(assets))
for a in assets:
    c2, _, _ = req('/assets/' + a)
    check('构建资源 ' + a, c2 == 200, 'code=%d' % c2)
for f in ('bootstrap.min.css', 'lab.css', 'lucide.svg', 'favicon.svg'):
    c2, b2, _ = req('/assets/' + f)
    check('开源组件 ' + f, c2 == 200 and len(b2) > 20, 'code=%d' % c2)

print('\n=== B. 内容接口 ===')
c, b, _ = req('/api/courses')
check('20 门课程', c == 200 and len(json.loads(b)) == 20)
c, b, _ = req('/api/levels')
d = json.loads(b)
check('5 级 / 30 关', len(d['levels']) == 5 and len(d['tasks']) == 30)
check('接口未泄露答案', 'SPIDERLAB-SESSION' not in b and 'REPORT-FINAL' not in b)
c, b, _ = req('/api/labs')
check('11 个示例靶站', len(json.loads(b)) == 11)
c, b, _ = req('/api/courses/beautifulsoup')
check('课程详情含 BS4 示例', 'BeautifulSoup' in b)

print('\n=== C. SSR 兜底页（无 JS 也能看） ===')
for path, kw in [('/courses', '课程目录'), ('/courses/xpath', 'XPath'),
                 ('/training', '分级训练场'), ('/training/L5-4', '结构化')]:
    c2, b2, _ = req(path)
    check(path, c2 == 200 and kw in b2, 'code=%d' % c2)

print('\n=== D. robots / sitemap ===')
c, b, _ = req('/robots.txt')
check('robots 允许 / 且含 Crawl-delay', c == 200 and 'Allow: /' in b and 'Crawl-delay' in b)
c, b, _ = req('/sitemap.xml')
check('sitemap 含靶场 URL', c == 200 and '/lab/books' in b)

print('\n=== E. 7 个靶场（服务端渲染，源码即数据） ===')
c, b, _ = req('/lab/')
check('靶站索引', c == 200 and '书城' in b)
c, b, _ = req('/lab/books?page=1')
check('书城 title 与 L1-1 一致', '<title>%s</title>' % ANSWERS['L1-1'] in b)
check('书城 4 个 div.book', b.count('class="book"') == 4)
c, b, _ = req('/lab/books/2')
check('详情页 data-stock', 'data-stock="7"' in b)
c, b, _ = req('/lab/quotes?page=1')
check('名言墙 span.author', 'class="author"' in b)
c, b, _ = req('/lab/movies')
check('电影榜 table', '<table' in b and 'class="rating"' in b)
c, b, _ = req('/lab/news')
check('新闻中心 data-id 与蜜罐', 'data-id="101"' in b and 'class="trap"' in b)
c, _, _ = req('/lab/trap/hidden')
check('蜜罐返回 403', c == 403, 'code=%d' % c)
c, b, _ = req('/lab/api')
check('接口说明页', c == 200 and 'X-Lab-Key' in b)
c, b, _ = req('/lab/vault')
check('保险库未登录 403', c == 403, 'code=%d' % c)
c, b, _ = req('/lab/guard')
check('守卫无请求头 403', c == 403, 'code=%d' % c)

print('\n=== F. 接口鉴权 / Session / 守卫 ===')
c, _, _ = req('/lab/api/v1/items?page=1&size=5')
check('接口缺 X-Lab-Key 返回 403', c == 403, 'code=%d' % c)
H = {'X-Lab-Key': 'spiderlab'}
c, b, _ = req('/lab/api/v1/items?page=1&size=5', headers=H)
check('接口分页 JSON', c == 200 and len(json.loads(b)['items']) == 5)
c, b, _ = req('/lab/api/v1/token', headers=H)
check('Token 值正确', json.loads(b)['token'] == ANSWERS['L3-1'])

jar = http.cookiejar.CookieJar()
sess = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
c, b, _ = req('/lab/vault/login', method='POST',
              data='username=student&password=spiderlab', opener=sess)
check('Session 登录成功', c == 200, 'code=%d' % c)
c, b, _ = req('/lab/vault', opener=sess)
check('保持会话读取 secret', ANSWERS['L3-2'] in b, 'code=%d' % c)
GH = {'User-Agent': 'SpiderBond-Student/1.0', 'Referer': BASE + '/lab/guard/'}
c, b, _ = req('/lab/guard', headers=GH)
check('合规请求头取得 guard-code', c == 200 and ANSWERS['L5-1'] in b, 'code=%d' % c)

print('\n=== G. 30 关判分（标准答案） ===')
all_ok = True
for tid, ans in ANSWERS.items():
    if isinstance(ans, list):
        payload = (json.dumps(ans, ensure_ascii=False)
                   if TASKS[tid]['type'] == 'json' else ','.join(str(x) for x in ans))
    else:
        payload = str(ans)
    c, b, _ = req('/api/check', method='POST',
                  data={'task_id': tid, 'answer': payload})
    d = json.loads(b)
    if not d.get('ok'):
        all_ok = False
        print('       %s: %s' % (tid, d.get('message')))
check('30 关标准答案全部通过', all_ok)
c, b, _ = req('/api/check', method='POST', data={'task_id': 'L2-3', 'answer': '错误答案'})
check('错误答案被拒绝且带提示', not json.loads(b)['ok'] and bool(json.loads(b)['hint']))

print('\n=== H. 零 emoji（渲染输出） ===')
pat = re.compile('[\U0001F300-\U0001FAFF\u2600-\u27BF]')
pages = ['/', '/courses', '/courses/xpath', '/training', '/lab/',
         '/lab/books?page=1', '/lab/movies', '/lab/news', '/lab/api',
         '/lab/vault', '/lab/guard']
bad = [p for p in pages if pat.search(req(p)[1])]
check('所有页面无 emoji 图标', not bad, str(bad))

print('\n' + '=' * 54)
print('PASS: %d   FAIL: %d' % (len(PASS), len(FAIL)))
if FAIL:
    for f in FAIL:
        print('  -', f)
    sys.exit(1)
print('REMOTE VERIFY OK -> ' + HOST)
