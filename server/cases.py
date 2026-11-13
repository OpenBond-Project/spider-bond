# -*- coding: utf-8 -*-
"""Spider Bond 在线实练案例：每节课一个可运行、可判分的爬虫小任务。

代码在浏览器 Web Worker 的 Pyodide 沙箱中运行，绝不在服务器进程里执行。
标准答案只保存在后端，通过 /api/check_case 比对，不下发到前端。
"""
from labs import (BOOKS, QUOTES, MOVIES, NEWS, API_ITEMS,
                  ANSWERS, page_of_books, VAULT_SECRET, GUARD_TOKEN,
                  REPORT_SECRET, LAB_KEY, REQUIRED_UA, REQUIRED_REFERER,
                  ROBOTS_DISALLOW)

# 站点同源基准由沙箱注入；案例代码统一用 BASE，避免硬编码域名/协议
HEAD = "import requests\nfrom lxml import etree\nfrom bs4 import BeautifulSoup\n\n"

CASES = [
    # ------------------------------------------------------------ 基础篇
    {
        'slug': 'intro-and-law', 'title': '读出 robots.txt 的禁区', 'points': 20,
        'brief': '写爬虫第一件事是看 robots.txt。请请求本站教学版 /lab/robots.txt，找出所有 Disallow 的路径（去重，顺序不限）。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/robots.txt')
print(r.status_code, r.text[:120])

disallow = []
for line in r.text.splitlines():
    line = line.strip()
    # TODO: 收集 Disallow: 后面的路径
    if line.startswith('Disallow:'):
        disallow.append(line.split(':', 1)[1].strip())

# 去重后赋给 answer（顺序不限）
answer = sorted(set(disallow))
print(answer)
""",
        'hint': '逐行 splitlines()，用 startswith("Disallow:") 过滤，再 split(":", 1)[1].strip() 取值，最后 set 去重。',
        'urls': ['/lab/robots.txt'], 'type': 'ulist',
        # 答案从 ROBOTS_DISALLOW 推导，改 robots 时不会再出现"题目答案没同步"
        'answer': sorted(ROBOTS_DISALLOW),
    },
    {
        'slug': 'http-and-html', 'title': '数一数页面里有多少本书', 'points': 20,
        'brief': 'HTML 是一棵树。请求书城第 1 页，统计 class="book" 的 div 节点数量。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/books', params={'page': 1})
print(r.status_code)

soup = BeautifulSoup(r.text, 'lxml')
# TODO: 用 CSS 选择器统计 .book 节点
count = len(soup.select('div.book'))

answer = count
print('书籍数量:', answer)
""",
        'hint': 'BeautifulSoup(r.text, "lxml").select("div.book") 返回列表，取 len()。',
        'urls': ['/lab/books'], 'type': 'number', 'answer': 4,
    },
    {
        'slug': 'requests', 'title': '取回页面标题', 'points': 20,
        'brief': '用 requests 发 GET，并提取 <title> 标签的文本。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/books', params={'page': 1})
r.raise_for_status()
r.encoding = 'utf-8'

tree = etree.HTML(r.text)
# TODO: 用 XPath 取 //title/text()
answer = tree.xpath('//title/text()')[0].strip()
print(answer)
""",
        'hint': 'etree.HTML(r.text).xpath("//title/text()")[0]，注意 strip()。',
        'urls': ['/lab/books'], 'type': 'text', 'answer': ANSWERS['L1-1'],
    },
    {
        'slug': 'encoding', 'title': '中文文本清洗', 'points': 20,
        'brief': '不联网，练文本清洗：把全角空格、&nbsp;、多余空白统一清掉。',
        'starter': """import re
import unicodedata

raw = '  Ｐｙｔｈｏｎ　爬虫\\xa0入门  '

def clean(s):
    s = unicodedata.normalize('NFKC', s)   # 全角转半角
    # TODO: 折叠所有空白并去掉首尾空白
    s = re.sub(r'\\s+', ' ', s).strip()
    return s

answer = clean(raw)
print(repr(answer))
""",
        'hint': "NFKC 归一化后，用 re.sub(r'\\s+', ' ', s).strip()。",
        'urls': [], 'type': 'text', 'answer': 'Python 爬虫 入门',
    },
    {
        'slug': 'urllib', 'title': '拼接绝对链接', 'points': 20,
        'brief': '书城列表页给的是相对链接。用 urljoin 拼成绝对路径（只提交路径部分，避免域名差异）。',
        'starter': HEAD + """from urllib.parse import urljoin, urlparse

r = requests.get(BASE + '/lab/books', params={'page': 1})
soup = BeautifulSoup(r.text, 'lxml')

paths = []
for a in BeautifulSoup(r.text, 'lxml').select('a.detail'):
    full = urljoin(BASE, a['href'])
    # TODO: 用 urlparse 取路径部分
    paths.append(urlparse(full).path)

answer = paths
print(answer)
""",
        'hint': 'urljoin(BASE, href) 得到绝对 URL，再用 urlparse(full).path 取路径。',
        'urls': ['/lab/books'], 'type': 'olist',
        'answer': ['/lab/books/%d' % b['id'] for b in page_of_books(1)],
    },

    # ------------------------------------------------------------ 解析篇
    {
        'slug': 'xpath', 'title': 'XPath 提取书名', 'points': 25,
        'brief': '用 XPath 一条语句取书城第 1 页所有书名，保持页面顺序。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/books', params={'page': 1})
tree = etree.HTML(r.text)

# TODO: 用 //div[@class="book"]/h2/text() 取书名
answer = [s.strip() for s in tree.xpath('//div[@class="book"]/h2/text()')]
print(answer)
""",
        'hint': 'XPath 永远返回列表；//div[@class="book"]/h2/text() 即可。',
        'urls': ['/lab/books'], 'type': 'olist', 'answer': ANSWERS['L1-2'],
    },
    {
        'slug': 'lxml', 'title': '表格解析找最高分', 'points': 25,
        'brief': '解析电影榜的 table，找出评分最高的片名。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/movies')
tree = etree.HTML(r.text)

rows = []
for tr in tree.xpath('//table[@id="movies"]//tbody/tr'):
    name = tr.xpath('./td[@class="title"]/text()')[0].strip()
    rating = float(tr.xpath('./td[@class="rating"]/text()')[0])
    rows.append((name, rating))

# TODO: 用 max 按评分取片名
answer = max(rows, key=lambda x: x[1])[0]
print(answer)
""",
        'hint': '逐 tr 取 td，评分 float 化后 max(rows, key=lambda x: x[1])[0]。',
        'urls': ['/lab/movies'], 'type': 'text', 'answer': ANSWERS['L2-3'],
    },
    {
        'slug': 'beautifulsoup', 'title': '名言作者去重', 'points': 25,
        'brief': '名言墙共 2 页。翻完两页，提取全部作者并去重（顺序不限）。',
        'starter': HEAD + """authors = []
for page in range(1, 3):
    r = requests.get(BASE + '/lab/quotes', params={'page': page})
    soup = BeautifulSoup(r.text, 'lxml')
    # TODO: 取 span.author 的文本
    authors += [s.get_text(strip=True) for s in soup.select('span.author')]

answer = sorted(set(authors))
print(len(answer), answer[:3])
""",
        'hint': '两页循环 + select("span.author") + set() 去重，本题顺序不限。',
        'urls': ['/lab/quotes'], 'type': 'ulist', 'answer': ANSWERS['L2-4'],
    },
    {
        'slug': 'css-selector', 'title': 'CSS 选择器取 data-id', 'points': 25,
        'brief': '新闻中心的每篇文章挂了 data-id 属性，用 CSS 选择器全部取出来。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/news')
soup = BeautifulSoup(r.text, 'lxml')

# TODO: 只选 article[data-id]，取 data-id 属性
answer = [a['data-id'] for a in soup.select('article[data-id]')]
print(answer)
""",
        'hint': 'soup.select("article[data-id]")，再用 a["data-id"] 取属性。',
        'urls': ['/lab/news'], 'type': 'olist', 'answer': ANSWERS['L4-3'],
    },
    {
        'slug': 'regex', 'title': '正则抠出价格求和', 'points': 25,
        'brief': '用正则从书城第 1 页源码里抠出所有价格并求和（保留 1 位小数）。',
        'starter': """import re
import requests

r = requests.get(BASE + '/lab/books', params={'page': 1})
prices = re.findall(r'class="price">([\\d.]+)<', r.text)

# TODO: 转 float 求和
answer = round(sum(float(p) for p in prices), 1)
print(answer)
""",
        'hint': 're.findall 拿到的都是字符串，必须 float() 再 sum()。',
        'urls': ['/lab/books'], 'type': 'number',
        'answer': round(sum(b['price'] for b in page_of_books(1)), 1),
    },
    {
        'slug': 'json-api', 'title': 'JSON 接口分页求和', 'points': 30,
        'brief': '接口 /lab/api/v1/items 需要 X-Lab-Key 请求头。翻完所有页，把所有条目的 id 相加。',
        'starter': """import requests

HEADERS = {'X-Lab-Key': '%s'}
page, ids = 1, []
while True:
    r = requests.get(BASE + '/lab/api/v1/items',
                     params={'page': page, 'size': 5}, headers=HEADERS)
    data = r.json()
    ids += [x['id'] for x in data['items']]
    # TODO: 用 has_next 判断是否继续
    if not data['has_next']:
        break
    page += 1

answer = sum(ids)
print(answer)
""" % LAB_KEY,
        'hint': '响应里的 has_next 决定终止，别靠猜页数。请求头 X-Lab-Key 不能少。',
        'urls': ['/lab/api/v1/items'], 'type': 'number', 'answer': ANSWERS['L4-1'],
    },

    # ------------------------------------------------------------ 进阶篇
    {
        'slug': 'pagination', 'title': '跨页采集全量书名', 'points': 30,
        'brief': '书城共 3 页，翻完所有页，按页面顺序汇总全部书名。',
        'starter': HEAD + """titles = []
for page in range(1, 4):
    r = requests.get(BASE + '/lab/books', params={'page': page})
    tree = etree.HTML(r.text)
    # TODO: 每页取书名并汇总
    titles += [s.strip() for s in tree.xpath('//div[@class="book"]/h2/text()')]

answer = titles
print(len(answer), '本')
""",
        'hint': 'for page in range(1, 4) 循环改 params，用 list 的 += 汇总，保持顺序。',
        'urls': ['/lab/books'], 'type': 'olist', 'answer': ANSWERS['L2-1'],
    },
    {
        'slug': 'session-cookie', 'title': 'Session 登录保险库', 'points': 35,
        'brief': 'POST 登录 /lab/vault/login 后保持会话，读取 /lab/vault 里的 secret code。',
        'starter': HEAD + """s = requests.Session()
r = s.post(BASE + '/lab/vault/login',
           data={'username': 'student', 'password': 'spiderlab'})
print('登录:', r.status_code)

page = s.get(BASE + '/lab/vault')
soup = BeautifulSoup(page.text, 'lxml')
# TODO: 取 #secret 里的文本
answer = soup.select_one('#secret p').get_text(strip=True)
print(answer)
""",
        'hint': '必须用同一个 Session 对象，否则 Cookie 不会带上，会得到 403。',
        'urls': ['/lab/vault/login', '/lab/vault'], 'type': 'text', 'answer': VAULT_SECRET,
    },
    {
        'slug': 'headers-and-status', 'title': '构造合规请求头', 'points': 35,
        'brief': '/lab/guard 校验 User-Agent 与 Referer，带对头才能拿到 guard-code。',
        'starter': HEAD + """headers = {
    'User-Agent': '%s',
    'Referer': BASE + '/lab/guard/',
}
r = requests.get(BASE + '/lab/guard', headers=headers)
print(r.status_code)

# TODO: 从返回页面里取 #guard-code 的文本
answer = BeautifulSoup(r.text, 'lxml').select_one('#guard-code p').get_text(strip=True)
print(answer)
""" % REQUIRED_UA,
        'hint': 'User-Agent 要包含 SpiderBond-Student/1.0；Referer 必须是 BASE + "/lab/guard/"。',
        'urls': ['/lab/guard'], 'type': 'text', 'answer': REPORT_SECRET,
    },
    {
        'slug': 'dynamic-page', 'title': '接口分类统计', 'points': 35,
        'brief': '现代站点数据常在 JSON 接口里。翻完分页，统计 category 为「技术」的条目数。',
        'starter': """import requests

HEADERS = {'X-Lab-Key': '%s'}
page, total = 1, 0
while True:
    data = requests.get(BASE + '/lab/api/v1/items',
                       params={'page': page, 'size': 5}, headers=HEADERS).json()
    # TODO: 统计 category == '技术'
    total += sum(1 for x in data['items'] if x['category'] == '技术')
    if not data['has_next']:
        break
    page += 1

answer = total
print(answer)
""" % LAB_KEY,
        'hint': '每页 items 是列表，用 sum(1 for x in ...) 计数，has_next 控制循环。',
        'urls': ['/lab/api/v1/items'], 'type': 'number', 'answer': ANSWERS['L4-2'],
    },
    {
        'slug': 'browser-automation', 'title': '源码与渲染 DOM 的差异', 'points': 25,
        'brief': '不联网练习：下面是一段「服务器原始 HTML」和一段「JS 渲染后的 DOM」，统计两者共有的链接数差异。',
        'starter': HEAD + """source = '''<html><body><div id="app"></div>
<script src="/app.js"></script></body></html>'''
rendered = '''<html><body><div id="app">
<a href="/lab/books/1">书一</a><a href="/lab/books/2">书二</a>
</div></body></html>'''

src_links = len(BeautifulSoup(source, 'lxml').select('a[href]'))
dom_links = len(BeautifulSoup(rendered, 'lxml').select('a[href]'))

# TODO: 求差值（渲染后 - 原始）
answer = dom_links - src_links
print(src_links, dom_links, answer)
""",
        'hint': '原始源码里通常是空壳 div，数据链接在 JS 渲染后才出现；相减即为差值。',
        'urls': [], 'type': 'number', 'answer': 2,
    },

    # ------------------------------------------------------------ 工程篇
    {
        'slug': 'concurrency', 'title': '多页采集与页数统计', 'points': 30,
        'brief': '顺序访问书城 3 页（教学场景请限速，不要高并发），统计成功返回 200 的页数。',
        'starter': """import requests
import time

ok = 0
for page in range(1, 4):
    r = requests.get(BASE + '/lab/books', params={'page': page})
    if r.status_code == 200:
        ok += 1
    time.sleep(0.1)   # 限速，别压垮对方

answer = ok
print(answer)
""",
        'hint': '逐页请求并判断 status_code == 200；真实项目要控制并发与间隔。',
        'urls': ['/lab/books'], 'type': 'number', 'answer': 3,
    },
    {
        'slug': 'scrapy', 'title': 'Item 字段清洗', 'points': 30,
        'brief': '框架里的 Item 一样要做字段校验。把下面脏数据清洗成标准价格列表。',
        'starter': """import re

dirty = ['45.00 元', '¥68', '59.5', ' 88.0 ', 'bad', '99.00元']

def to_price(s):
    # TODO: 抠出数字并转 float，失败返回 None
    m = re.search(r'[\\d.]+', str(s))
    return float(m.group()) if m else None

answer = [to_price(x) for x in dirty if to_price(x) is not None]
print(answer)
""",
        'hint': "re.search(r'[\\d.]+', s) 抠数字，float() 转换，脏数据跳过。",
        'urls': [], 'type': 'json', 'answer': [45.0, 68.0, 59.5, 88.0, 99.0],
    },
    {
        'slug': 'storage', 'title': '结构化书单输出', 'points': 40,
        'brief': '综合任务：翻完书城 3 页，筛出评分 >= 4.8 的书，输出 JSON 数组（字段 id / title / price）。',
        'starter': HEAD + """import json

items = []
for page in range(1, 4):
    r = requests.get(BASE + '/lab/books', params={'page': page})
    for card in BeautifulSoup(r.text, 'lxml').select('div.book'):
        rating = float(card.select_one('span.rating').get_text(strip=True))
        if rating >= 4.8:
            items.append({
                'id': int(card['data-id']),
                'title': card.select_one('h2').get_text(strip=True),
                'price': float(card.select_one('span.price').get_text(strip=True)),
            })

answer = items
print(json.dumps(answer, ensure_ascii=False))
""",
        'hint': '分页 + 数值筛选 + 结构化输出；price 记得转 float。答案按 id 顺序。',
        'urls': ['/lab/books'], 'type': 'json', 'answer': ANSWERS['L5-4'],
    },
    {
        'slug': 'anti-scraping', 'title': '避开蜜罐取新闻标题', 'points': 40,
        'brief': '新闻中心含隐藏的蜜罐链接。只取可见 article 里的标题，别盲目 follow 所有 a[href]。',
        'starter': HEAD + """r = requests.get(BASE + '/lab/news')
soup = BeautifulSoup(r.text, 'lxml')

# TODO: 只选 article 下的 h2，跳过 class="trap" 的隐藏区
answer = [h.get_text(strip=True) for h in soup.select('article h2')]
print(len(answer), answer[:2])
""",
        'hint': '蜜罐在 div.trap 里且被 CSS 隐藏；用 article h2 精确定位即可避开。',
        'urls': ['/lab/news'], 'type': 'olist', 'answer': ANSWERS['L4-4'],
    },
]

BY_SLUG = {c['slug']: c for c in CASES}
