# -*- coding: utf-8 -*-
"""Spider Bond 课程内容：20 课覆盖 Python 爬虫全链路。

所有示例代码均指向本站 /lab/ 靶场，可直接复制运行。
"""
BASE = 'https://spider.skkk.uno'

COURSES = [
    # ============================================================ 基础篇
    {
        "slug": "intro-and-law", "no": 1, "title": "爬虫是什么与合规底线",
        "track": "基础篇", "level": "入门", "minutes": 20,
        "summary": "爬虫的本质是「用程序模拟浏览器发 HTTP 请求，拿到响应，再把想要的数据结构化地取出来」。写爬虫之前，先搞清楚哪些能爬、怎么爬才不越界——这是第一课，也是最重要的一课。",
        "points": [
            "通用流程：构造请求 → 获取响应 → 解析提取 → 清洗 → 存储 → 调度",
            "robots.txt 是站点对爬虫的公开声明，位于域名根目录；核心指令有 User-agent、Allow、Disallow、Crawl-delay、Sitemap",
            "只抓公开数据；不碰需要登录才能看的个人信息、不绕过权限校验、不抓取敏感数据",
            "控制频率：并发数 + 请求间隔 + 指数退避重试，别把对方站点打挂，这既是礼貌也是法律红线",
            "标明身份：使用带联系方式的 User-Agent，方便对方站长联系你",
            "遵守目标站服务条款、著作权与数据合规要求；商用前务必确认授权",
            "本站所有 /lab/ 靶场页面已在 robots.txt 中明确 Allow，可以放心练手，别拿生产站练兵",
        ],
        "code": """from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import time

BASE = 'https://spider.skkk.uno'

def allowed(url, ua='*'):
    p = urlparse(url)
    rp = RobotFileParser()
    rp.set_url(f'{p.scheme}://{p.netloc}/robots.txt')
    rp.read()
    return rp.can_fetch(ua, url)

url = BASE + '/lab/books?page=1'
if allowed(url):
    print('允许抓取，开始')
    time.sleep(0.5)          # 遵守 Crawl-delay
else:
    print('robots.txt 不允许，停止')""",
        "pitfalls": [
            "robots.txt 是约定不是技术封锁，但绕过它在很多场景会构成违约或不正当竞争",
            "404 页面与 honeypot 隐藏链接常被用来识别恶意爬虫，别见链接就 follow",
            "把学习流量打到别人的生产站上是最容易踩的坑，所以才需要本地靶场",
        ],
        "exercise": "打开 /robots.txt，找出哪些路径是 Allow、哪些是 Disallow，再用 RobotFileParser 验证 /lab/books 是否可抓。",
        "lab": "/robots.txt", "lab_text": "查看本站 robots.txt",
    },
    {
        "slug": "http-and-html", "no": 2, "title": "HTTP 协议与 HTML/DOM 基础",
        "track": "基础篇", "level": "入门", "minutes": 30,
        "summary": "解析页面的前提是理解页面的结构。这一课讲清请求/响应、状态码、Header、Cookie，以及 HTML 的 DOM 树、标签、属性和文本节点。后面所有 XPath 与 CSS 选择器都建立在这棵树上。",
        "points": [
            "一次请求 = 方法(GET/POST) + URL + 请求头 + 请求体；响应 = 状态码 + 响应头 + 响应体",
            "常见状态码：200 成功、301/302 跳转、403 拒绝、404 不存在、429 限流、5xx 服务端错误",
            "关键请求头：User-Agent、Referer、Accept、Cookie、Content-Type；关键响应头：Set-Cookie、Content-Type、Content-Encoding",
            "HTML 是树：元素节点(html/head/body/div)、属性节点(class/id/href/data-*)、文本节点与注释节点",
            "id 全页唯一，class 可复用；data-* 属性常被前端用来挂数据，也是爬虫的好抓手",
            "相对 URL（/lab/books/3）需要用 urljoin 和 base URL 拼成绝对地址",
            "浏览器「查看网页源代码」看到的是服务器原始 HTML；DevTools Elements 面板看到的是 JS 渲染后的 DOM，两者可能完全不同",
        ],
        "code": """<!DOCTYPE html>
<html lang="zh-CN">
  <body>
    <div id="list" class="container">
      <div class="book" data-id="7">
        <h2>Python 爬虫入门</h2>
        <a href="/lab/books/7">详情</a>
        <span class="price">45.00</span>
      </div>
    </div>
  </body>
</html>

# 对应的树结构：
# html
#   └── body
#        └── div#list.container
#             └── div.book[data-id=7]
#                  ├── h2            -> 文本「Python 爬虫入门」
#                  ├── a[href]       -> 文本「详情」
#                  └── span.price    -> 文本「45.00」""",
        "pitfalls": [
            "class 可能含多个值（如 class=\"book featured\"），用 //div[@class='book'] 会漏掉，应用 contains 或 CSS 的 .book",
            "文本节点里的空白、换行、&nbsp; 需要 strip() 清洗",
            "把 JS 渲染后的 DOM 当成原始 HTML 去写 XPath，是最常见的「本地能跑、代码抓不到」原因",
        ],
        "exercise": "打开 /lab/books?page=1 并查看网页源代码，数一数有几个 div.book，指出每个节点属于元素、属性还是文本。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "requests", "no": 3, "title": "requests 发出第一个请求",
        "track": "基础篇", "level": "入门", "minutes": 30,
        "summary": "requests 是 Python 爬虫的事实标准库。这一课把 GET、参数、请求头、超时、响应对象、异常处理和编码设置一次讲透，并给出一段可复用的请求模板。",
        "points": [
            "安装：pip install requests；GET 用 requests.get(url, params=..., headers=..., timeout=...)",
            "params 会自动做 URL 编码，比手工拼 query string 安全",
            "永远设置 timeout，否则遇到不响应的站点会永久挂起",
            "响应对象：r.status_code、r.headers、r.text、r.content、r.json()、r.url、r.encoding",
            "检查状态码：r.raise_for_status() 会把 4xx/5xx 抛成 HTTPError",
            "编码：requests 会猜 encoding，猜错时手动设 r.encoding = r.apparent_encoding 或 'utf-8'",
            "异常要分类处理：ConnectionError、Timeout、HTTPError，配合重试与退避",
        ],
        "code": """import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError

BASE = 'https://spider.skkk.uno'
HEADERS = {
    'User-Agent': 'SpiderBond-Student/1.0 (+course practice)',
    'Accept': 'text/html,application/xhtml+xml',
}

def fetch(path, **params):
    try:
        r = requests.get(BASE + path, params=params,
                         headers=HEADERS, timeout=8)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except Timeout:
        print('请求超时')
    except ConnectionError:
        print('连接失败')
    except HTTPError as e:
        print('HTTP 错误:', e.response.status_code)
    return None

html = fetch('/lab/books', page=1)
print(html[:200] if html else '未取到内容')""",
        "pitfalls": [
            "不设 timeout 是生产事故高发原因",
            "params 传了 None 或嵌套结构会产生意外结果",
            "r.text 用猜出来的编码解码，中文站乱码先检查 r.encoding 与 <meta charset>",
        ],
        "exercise": "用 params 依次请求书城第 1、2、3 页，打印每页的 r.url，观察 URL 编码结果。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "encoding", "no": 4, "title": "字符编码与中文乱码",
        "track": "基础篇", "level": "入门", "minutes": 20,
        "summary": "乱码不是玄学，是「字节按错的编码表解码」的必然结果。搞清楚 bytes / str 的边界，中文站就再也不会糊成一片。",
        "points": [
            "r.content 是 bytes（原始字节），r.text 是 str（已解码文本）",
            "解码顺序：HTTP Content-Type charset → HTML <meta charset> → requests 猜测 → apparent_encoding(chardet)",
            "UTF-8 与 GBK 互不相容：用 UTF-8 解 GBK 字节会得到「锟斤拷」或替换符号",
            "写文件统一用 encoding='utf-8'；CSV 给 Excel 用可加 utf-8-sig（带 BOM）",
            "JSON 接口一律用 r.json()，它内部按 UTF-8 族解码，别自己 decode",
            "全角空格 \\u3000、不换行空格 \\xa0 用 str.replace 或 normalize 处理",
        ],
        "code": """import requests

r = requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8)

# 明确指定编码，避免依赖猜测
r.encoding = 'utf-8'
text = r.text

# 常见空白清洗
def clean(s):
    return (s.replace('\\xa0', ' ')
             .replace('\\u3000', ' ')
             .strip())

print(repr(text[:80]))
print(clean('  Python 爬虫\\xa0入门  '))   # 'Python 爬虫 入门'

# 存盘
with open('books.html', 'w', encoding='utf-8') as f:
    f.write(text)""",
        "pitfalls": [
            "不要对 r.content 再调用 r.text 的逻辑，两者是不同抽象层",
            "Windows 下 open() 默认 GBK，忘记 encoding 会写坏中文",
            "BeautifulSoup 传 bytes 会自行猜编码，传 str 最可控：BeautifulSoup(r.text, 'lxml')",
        ],
        "exercise": "打印本站首页响应头里的 Content-Type，确认 charset，再用 r.apparent_encoding 对比。",
        "lab": "/lab/quotes?page=1", "lab_text": "名言墙第 1 页",
    },
    {
        "slug": "urllib", "no": 5, "title": "标准库 urllib 与 URL 处理",
        "track": "基础篇", "level": "入门", "minutes": 20,
        "summary": "不装第三方库也能爬。urllib 与 urllib.parse 负责 URL 拆分、拼接、编码和 robots 解析，是每个爬虫工程师的底层工具箱。",
        "points": [
            "urlparse / urlunparse 拆分与重组 URL 六元组（scheme/netloc/path/params/query/fragment）",
            "urljoin(base, relative) 是拼接相对链接的唯一正确姿势，会自动处理 .. 与根路径",
            "parse_qs / parse_qsl 解析查询串；urlencode 构造查询串",
            "quote / unquote 处理路径中的中文与特殊字符",
            "urllib.robotparser.RobotFileParser 读取 robots.txt 并判断 can_fetch",
            "urllib.request.urlopen 可发请求，但没有 Session、连接池等便利能力",
        ],
        "code": """from urllib.parse import (urlparse, urljoin, parse_qs,
                          urlencode, quote)
from urllib.request import urlopen, Request

BASE = 'https://spider.skkk.uno'

# 拼接：base 必须是绝对 URL
print(urljoin(BASE + '/lab/books?page=1', '/lab/books/7'))
# https://spider.skkk.uno/lab/books/7

p = urlparse(BASE + '/lab/books?page=2&size=4')
print(p.path, parse_qs(p.query))       # /lab/books  {'page': ['2'], 'size': ['4']}

qs = urlencode({'page': 3, 'size': 4, 'kw': 'Python 爬虫'})
print(qs)                              # page=3&size=4&kw=Python+%E7%88%AC%E8%99%AB

req = Request(BASE + '/robots.txt',
              headers={'User-Agent': 'SpiderBond-Student/1.0'})
with urlopen(req, timeout=8) as resp:
    print(resp.status, resp.read(80).decode('utf-8'))""",
        "pitfalls": [
            "用字符串相加拼 URL 会产生 //、重复参数、丢失 query 等问题",
            "urljoin 的第二参数若本身是绝对 URL，会直接覆盖 base，注意来源可信度",
            "parse_qs 返回的是列表（因为同名参数可出现多次），取值要 [0]",
        ],
        "exercise": "把书城第 1 页所有详情链接用 urljoin 转成绝对 URL，完成 L1-4 关卡。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },

    # ============================================================ 解析篇
    {
        "slug": "xpath", "no": 6, "title": "XPath 语法全解",
        "track": "解析篇", "level": "入门", "minutes": 45,
        "summary": "XPath 是在 XML/HTML 树上定位节点的查询语言，表达力远超正则。掌握路径、谓语、轴、函数四件套，绝大多数页面都能一行取到数据。",
        "points": [
            "路径：/ 从根开始、// 任意后代、. 当前节点、.. 父节点、@attr 取属性、text() 取文本",
            "谓语：[1] 位置（XPath 从 1 开始）、[@class='book'] 属性等于、[contains(@class,'book')] 包含、[last()] 最后",
            "逻辑与比较：and / or / not()、position()<=3、number(text())>50",
            "常用轴：ancestor::、parent::、child::、following-sibling::、preceding-sibling::、descendant::",
            "函数：text()、string(.)、count()、contains()、starts-with()、normalize-space()、substring()、translate()",
            "取属性用 //a/@href，取文本用 //h2/text()；想连标签一起拿用 //h2 再 .text_content()",
            "//div[@class='book'] 要求 class 完全相等，多 class 节点请用 contains 或 CSS 选择器",
        ],
        "code": """from lxml import etree
import requests

html = requests.get('https://spider.skkk.uno/lab/books?page=1',
                    timeout=8).text
tree = etree.HTML(html)

# 路径与文本
print(tree.xpath('//title/text()'))
print(tree.xpath('//div[@class="book"]/h2/text()'))

# 谓语：第 2 本书
print(tree.xpath('(//div[@class="book"])[2]/h2/text()'))

# 属性
print(tree.xpath('//div[@class="book"]/a/@href'))

# 数值比较（价格 > 50 的书名，注意 price 文本里的单位处理）
print(tree.xpath('//div[contains(@class,"book")]'
                 '[number(span[@class="price"]/text()) > 50]'
                 '/h2/text()'))

# 轴：由 h2 回到父节点，再取兄弟
print(tree.xpath('//h2[text()="Python 爬虫入门"]'
                 '/following-sibling::span[@class="price"]/text()'))

# 函数
print('书籍数:', tree.xpath('count(//div[@class="book"])'))
print(tree.xpath('normalize-space(//h1/text())'))""",
        "pitfalls": [
            "lxml 的 //div[@class='book'] 是精确匹配，前端框架常加动态 class，改用 contains 或 CSS",
            "XPath 位置从 1 开始，Python 列表从 0 开始，别混",
            "text() 只取直接文本子节点；标签内还有 <span> 时要用 string(.) 或 .xpath('string(.)')",
            "浏览器 DevTools 复制的 XPath 常含绝对路径与动态 id，非常脆，学会手写相对路径",
        ],
        "exercise": "用 XPath 完成 L1-2（书名列表）与 L2-2（价格大于 50 的书名）。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "lxml", "no": 7, "title": "lxml 实战与容错解析",
        "track": "解析篇", "level": "入门", "minutes": 35,
        "summary": "lxml 是 C 实现的解析器，速度快、XPath 支持完整，还能容忍残缺 HTML。这一课讲 etree.HTML、html.fromstring、元素对象操作与清洗流水线。",
        "points": [
            "安装：pip install lxml；解析：etree.HTML(text) 或 lxml.html.fromstring(text)",
            "元素对象：el.tag、el.attrib、el.text、el.tail、el.get('href')、el.xpath(...)、el.text_content()",
            "etree.HTML 对不闭合标签、缺引号属性有容错；etree.XML 用于严格 XML",
            "序列化回 HTML：etree.tostring(el, encoding='unicode', method='html')",
            "清洗流水线：取节点 → text_content() → normalize-space → 类型转换 → 校验",
            "大页面用 iterparse 或分块处理，避免一次性构建整棵树",
            "lxml 也支持 CSS 选择器（需 pip install cssselect）：el.cssselect('div.book')",
        ],
        "code": """from lxml import html as lh
from lxml import etree
import requests

r = requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8)
r.encoding = 'utf-8'
doc = lh.fromstring(r.text)

books = []
for card in doc.cssselect('div.book') if hasattr(doc, 'cssselect') else doc.xpath('//div[@class="book"]'):
    title = card.xpath('./h2/text()')
    price = card.xpath('./span[@class="price"]/text()')
    link = card.xpath('./a/@href')
    books.append({
        'id': int(card.get('data-id') or 0),
        'title': (title[0].strip() if title else ''),
        'price': float(price[0]) if price else None,
        'href': link[0] if link else '',
        'raw': etree.tostring(card, encoding='unicode', method='html')[:60],
    })

print(books[0])
print('共解析', len(books), '本')""",
        "pitfalls": [
            "没装 cssselect 时 cssselect() 会抛异常，生产代码先用 XPath 或捕获异常",
            "xpath() 永远返回列表，取 [0] 前先判空，否则 IndexError",
            "残缺 HTML 下 lxml 可能自动补 <tbody>、调整节点层级，XPath 要按补全后的树写",
        ],
        "exercise": "用 lxml 解析电影榜表格 /lab/movies，输出评分最高的片名，完成 L2-3。",
        "lab": "/lab/movies", "lab_text": "电影榜表格",
    },
    {
        "slug": "beautifulsoup", "no": 8, "title": "BeautifulSoup 全解",
        "track": "解析篇", "level": "入门", "minutes": 40,
        "summary": "BeautifulSoup 以 API 友好著称，find / find_all / select / get_text 组合起来非常顺手。它不自带解析器，通常搭配 lxml 或 html.parser。",
        "points": [
            "安装：pip install beautifulsoup4 lxml；构造：BeautifulSoup(html, 'lxml')",
            "find(name, attrs, text, recursive) 返回单个 Tag；find_all(..., limit=) 返回列表",
            "按 class 查找要用 class_（class 是 Python 关键字）：soup.find_all('div', class_='book')",
            "select('div.book h2') 使用 CSS 选择器，select_one 返回第一个",
            "取文本：get_text(strip=True)、get_text(' | ', strip=True)、.string、.strings、.stripped_strings",
            "取属性：tag['href']、tag.get('href', '')、tag.attrs；多值属性 class 返回列表",
            "导航：.parent、.children、.find_parent()、.find_next_sibling()、.find_all_next()",
        ],
        "code": """import requests
from bs4 import BeautifulSoup

r = requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'lxml')

print(soup.title.get_text(strip=True))
print(soup.find('h1').get_text(strip=True))

for card in soup.select('div.book'):
    title = card.select_one('h2').get_text(strip=True)
    price = float(card.select_one('span.price').get_text(strip=True))
    author = card.select_one('span.author').get_text(strip=True)
    href = card.select_one('a.detail')['href']
    print(title, price, author, href)

# 多 class 匹配、属性存在判断、文本搜索
print(len(soup.find_all('div', class_='book')))
print([a['href'] for a in soup.find_all('a', href=True)][:4])
print(soup.find_all(string=lambda t: t and 'Python' in t)[:2])""",
        "pitfalls": [
            "传 bytes 给 BeautifulSoup 会让它猜编码，中文乱码时改传 r.text",
            "'html.parser' 容错差于 lxml，残缺页面结果可能不同",
            "class_ 后面漏下划线是最常见语法错误",
            "get_text() 默认会把子孙文本全拼起来，可能夹带脚本或广告，必要时逐节点取",
        ],
        "exercise": "用 BeautifulSoup 完成 L1-2 与 L2-4（名言作者去重）。",
        "lab": "/lab/quotes?page=1", "lab_text": "名言墙第 1 页",
    },
    {
        "slug": "css-selector", "no": 9, "title": "CSS 选择器与解析方案对照",
        "track": "解析篇", "level": "入门", "minutes": 30,
        "summary": "CSS 选择器写起来比 XPath 短，前端同学几乎零成本上手。这一课系统对照三种方案，并给出「什么时候该用谁」的决策依据。",
        "points": [
            "基础：tag、.class、#id、[attr]、[attr=value]、[attr^=]、[attr$=]、[attr*=]",
            "组合：后代空格、子元素 >、相邻兄弟 +、后续兄弟 ~、分组逗号",
            "伪类：:first-child、:last-child、:nth-child(n)、:not()（soupsieve 支持较全）",
            "对照：XPath //div[@class='book']/h2/text() ≈ CSS div.book > h2",
            "XPath 独有优势：轴（父/兄弟/祖先）、文本匹配 text()=、数值比较、count()",
            "CSS 独有优势：语法短、可直接粘到 DevTools 的 $$() 里验证",
            "工程建议：结构稳定的页面用 CSS，需要沿轴回溯或复杂条件时用 XPath",
        ],
        "code": """import requests
from bs4 import BeautifulSoup

soup = BeautifulSoup(
    requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8).text,
    'lxml')

print([x.get_text(strip=True) for x in soup.select('div.book h2')])
print([x['href'] for x in soup.select('div.book > a.detail')])
print([x.get('data-id') for x in soup.select('div.book[data-id]')])
print([x.get_text(strip=True) for x in soup.select('div.book:nth-child(2) h2')])

# 三种方案对照表（同一目标：所有书名）
# XPath      //div[@class="book"]/h2/text()
# CSS        div.book > h2
# BS4 find   [d.h2.get_text(strip=True) for d in soup.find_all('div', class_='book')]

# 在 DevTools Console 里可直接验证选择器：
# $$('div.book h2').map(e => e.textContent.trim())""",
        "pitfalls": [
            "soupsieve 与浏览器 CSS 引擎并非 100% 一致，复杂伪类先在 Python 里验证",
            ":contains() 不是标准 CSS，soupsieve 用 :-soup-contains()",
            "CSS 取不到文本节点本身，只能取元素再 get_text()",
        ],
        "exercise": "用 CSS 选择器提取 /lab/news 中所有 article 的 data-id，完成 L4-3。",
        "lab": "/lab/news", "lab_text": "新闻中心",
    },
    {
        "slug": "regex", "no": 10, "title": "正则表达式与文本清洗",
        "track": "解析篇", "level": "入门", "minutes": 30,
        "summary": "正则适合处理「非结构化的字符串片段」，不适合解析整棵 HTML 树。用对地方是利器，用错地方是灾难。",
        "points": [
            "re.findall / re.search / re.match / re.sub / re.split / re.compile",
            "常见元字符：. \\d \\w \\s、量词 * + ? {m,n}、分组 ()、非贪婪 .*?、或 |、字符集 []",
            "修饰符：re.S 让 . 匹配换行、re.I 忽略大小写、re.M 多行锚点",
            "命名分组 (?P<name>...) 让提取结果可读：m.groupdict()",
            "适用：从 JS 变量、JSONP、日志、文本片段里抠数字/日期/ID",
            "不适用：解析嵌套 HTML 标签（HTML 不是正则语言，嵌套会失控）",
            "清洗：normalize-space 思路、去 HTML 标签、去空白、全半角转换、unicodedata.normalize",
        ],
        "code": """import re
import unicodedata
import requests

html = requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8).text

# 从 data-id 属性中抠数字（属性场景可用）
print(re.findall(r'data-id="(\\d+)"', html)[:4])

# 从价格文本中抠数值
print(re.findall(r'class="price">([\\d.]+)<', html)[:4])

# 命名分组 + 非贪婪
m = re.search(r'<h2>(?P<title>.*?)</h2>', html, re.S)
print(m.groupdict() if m else None)

# 清洗
def clean(s):
    s = unicodedata.normalize('NFKC', s)      # 全角转半角
    s = re.sub(r'<[^>]+>', '', s)             # 去标签
    s = re.sub(r'\\s+', ' ', s).strip()        # 折叠空白
    return s

print(clean('  Ｐｙｔｈｏｎ　爬虫 <b>入门</b>  '))

# 反例：不要用正则解析嵌套 div
# re.findall(r'<div class="book">(.*?)</div>', html, re.S)  # 会在第一个 </div> 截断""",
        "pitfalls": [
            "默认 . 不匹配换行，抓多行 HTML 必须加 re.S",
            "贪婪 .* 会一路吃到最后一个标签，务必用 .*?",
            "用正则解析嵌套 HTML 是经典反模式，请交给 lxml / BS4",
        ],
        "exercise": "用正则从 /lab/news 的 data-views 属性中取出所有浏览量并求和。",
        "lab": "/lab/news", "lab_text": "新闻中心",
    },
    {
        "slug": "json-api", "no": 11, "title": "JSON 接口与前后端分离站点",
        "track": "解析篇", "level": "入门", "minutes": 35,
        "summary": "现代站点大量数据不在 HTML 里，而是由 XHR/fetch 拉取 JSON 接口。找到接口往往比硬啃 DOM 简单十倍——这一课讲怎么找、怎么调、怎么翻页。",
        "points": [
            "DevTools → Network → Fetch/XHR，按类型筛选，看 Request URL / Method / Headers / Response",
            "接口常见鉴权：自定义 Header、Token、Cookie、签名参数、时间戳",
            "r.json() 直接得到 dict/list；用 .get() 取键避免 KeyError",
            "分页三种形态：page/size、offset/limit、cursor/next_token；看响应里的 has_next / total / next",
            "JSONPath（可选）用于深嵌套取值，简单场景直接字典索引即可",
            "一定要读接口文档或页面说明，别靠猜参数",
            "接口也受 robots.txt 与服务条款约束，同样要限速",
        ],
        "code": """import requests
import time

BASE = 'https://spider.skkk.uno'
HEADERS = {'X-Lab-Key': 'spiderlab',
           'User-Agent': 'SpiderBond-Student/1.0'}
s = requests.Session()
s.headers.update(HEADERS)

page, items = 1, []
while True:
    r = s.get(BASE + '/lab/api/v1/items',
              params={'page': page, 'size': 5}, timeout=8)
    r.raise_for_status()
    data = r.json()
    items.extend(data['items'])
    print('page', page, 'got', len(data['items']),
          'total', data.get('total'))
    if not data.get('has_next'):
        break
    page += 1
    time.sleep(0.5)          # 限速

print('条目总数:', len(items))
print('id 之和:', sum(x['id'] for x in items))""",
        "pitfalls": [
            "忘记带鉴权 Header 会拿到 403，先看说明页再写请求",
            "靠猜页数容易漏数据，优先用响应里的 has_next / next",
            "接口返回的 JSON 字段可能是字符串数字，比较前先转换类型",
        ],
        "exercise": "调用 /lab/api/v1/items 翻完所有分页，完成 L4-1 与 L4-2。",
        "lab": "/lab/api", "lab_text": "JSON 接口靶场说明页",
    },

    # ============================================================ 进阶篇
    {
        "slug": "pagination", "no": 12, "title": "分页策略与链接拼接",
        "track": "进阶篇", "level": "进阶", "minutes": 30,
        "summary": "真实采集几乎都要翻页。页码翻页、相对链接、下一页链接、无限滚动各有套路，核心是「找到终止条件」并「控制请求频率」。",
        "points": [
            "页码型：?page=N，从 1 循环；终止条件可用 total、has_next 或「本页为空 / 内容重复」",
            "下一页型：解析 a[rel=next] / a.next，用 urljoin 拼绝对地址，直到没有下一页",
            "游标型：?cursor=xxx，从响应里取 next_cursor，适合动态数据流",
            "列表页 + 详情页两级采集：先收所有详情链接，再逐个请求，注意去重与限速",
            "用 set 做 URL 去重，避免循环链接导致死循环",
            "每页之间 time.sleep(0.3~1)，并记录进度便于断点续跑",
            "robots.txt 的 Crawl-delay 是下限，不是建议值",
        ],
        "code": """import requests, time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE = 'https://spider.skkk.uno'
titles, seen = [], set()

for page in range(1, 4):
    url = BASE + '/lab/books?page=%d' % page
    if url in seen:
        continue
    seen.add(url)
    soup = BeautifulSoup(requests.get(url, timeout=8).text, 'lxml')

    for card in soup.select('div.book'):
        titles.append(card.select_one('h2').get_text(strip=True))
        detail = urljoin(BASE, card.select_one('a.detail')['href'])
        # 详情请求也限速
        time.sleep(0.3)
        _ = requests.get(detail, timeout=8)

    time.sleep(0.5)

print('共采集', len(titles), '本:', titles[:3], '...')""",
        "pitfalls": [
            "不判终止条件会一直请求到 404 或永远重复最后一页",
            "相对链接直接字符串相加会产生 /lab/lab/books/... 这类错误",
            "翻页太快容易触发 429，且会给对方造成压力",
        ],
        "exercise": "翻完书城 3 页完成 L2-1，再跟进详情页的 data-stock 完成 L5-3。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "session-cookie", "no": 13, "title": "Session、Cookie 与 POST 表单",
        "track": "进阶篇", "level": "进阶", "minutes": 35,
        "summary": "登录态、CSRF Token、隐藏字段、重定向……这类站点需要用会话对象把多次请求串起来，而不是每次都发一个孤立的 GET。",
        "points": [
            "requests.Session() 自动持久化 Cookie、复用连接池、可统一设置 headers",
            "POST 表单：data={...} 对应 application/x-www-form-urlencoded；json={...} 对应 application/json",
            "登录前先 GET 表单页，提取隐藏字段（csrfmiddlewaretoken、token、hidden input）",
            "Set-Cookie 由 Session 自动保存；也可手动用 requests.utils.dict_from_cookiejar 查看",
            "allow_redirects 控制是否跟随 302；r.history 查看跳转链",
            "登录后用同一个 session 访问受保护页面，否则 403",
            "只采集自己有权限查看的内容，不尝试绕过他人权限",
        ],
        "code": """import requests
from bs4 import BeautifulSoup

BASE = 'https://spider.skkk.uno'
s = requests.Session()
s.headers.update({'User-Agent': 'SpiderBond-Student/1.0'})

# 1. 先取表单页，读隐藏字段
form_html = s.get(BASE + '/lab/vault', timeout=8).text
soup = BeautifulSoup(form_html, 'lxml')
hidden = {i.get('name'): i.get('value', '')
          for i in soup.select('input[type="hidden"]') if i.get('name')}
print('隐藏字段:', hidden)

# 2. POST 登录（字段见靶场说明页）
payload = {'username': 'student', 'password': 'spiderlab'}
payload.update(hidden)
r = s.post(BASE + '/lab/vault/login', data=payload, timeout=8)
print('登录状态:', r.status_code, 'Cookie:', s.cookies.get_dict())

# 3. 同一 Session 访问受保护页
page = s.get(BASE + '/lab/vault', timeout=8)
print('受保护页状态:', page.status_code)
print('secret:', BeautifulSoup(page.text, 'lxml')
      .select_one('#secret').get_text(strip=True))""",
        "pitfalls": [
            "用 requests.get() 而不是 session.get()，Cookie 不会带上，必然 403",
            "把 data 写成 json 会导致服务端解析不到表单字段",
            "登录接口常有频率限制，调试时别反复撞库式重试",
        ],
        "exercise": "用 Session 登录保险库，完成 L3-2 与 L3-4。",
        "lab": "/lab/vault", "lab_text": "登录保险库",
    },
    {
        "slug": "headers-and-status", "no": 14, "title": "请求头、身份标识与状态码处理",
        "track": "进阶篇", "level": "进阶", "minutes": 30,
        "summary": "请求头是与服务器沟通的「礼貌用语」。UA、Referer、Accept、自定义鉴权头各有用途；同时要建立完整的状态码处理策略，让爬虫遇到异常能优雅退让。",
        "points": [
            "常用请求头：User-Agent、Accept、Accept-Language、Referer、X-Requested-With、Authorization、自定义 X-*",
            "负责任的做法：UA 里带上项目名与联系方式，方便对方站长联系",
            "Referer 表示来源页，部分接口会校验它是否来自本站",
            "状态码策略：200 正常、3xx 跟随、403/401 停止并告警、404 跳过、429 退避、5xx 有限重试",
            "429 常带 Retry-After 响应头，优先按它等待，否则指数退避（1, 2, 4, 8 秒）",
            "重试要有上限（一般 3 次）与幂等性判断，POST 不要盲目重试",
            "所有异常处理都要记日志，别静默吞掉错误",
        ],
        "code": """import time, logging
import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
BASE = 'https://spider.skkk.uno'

def get_with_retry(path, headers=None, retries=3):
    url = BASE + path
    h = {'User-Agent': 'SpiderBond-Student/1.0 (+contact: course@spiderlab)'}
    if headers:
        h.update(headers)
    for n in range(retries):
        try:
            r = requests.get(url, headers=h, timeout=8)
            if r.status_code == 200:
                return r
            if r.status_code == 429:
                wait = int(r.headers.get('Retry-After', 2 ** n))
                logging.warning('被限流，等待 %s 秒', wait)
                time.sleep(wait)
                continue
            if r.status_code in (401, 403):
                logging.error('无权限，停止重试: %s', r.status_code)
                return None
            if r.status_code >= 500:
                time.sleep(2 ** n)
                continue
            logging.warning('非预期状态 %s，跳过', r.status_code)
            return None
        except requests.RequestException as e:
            logging.warning('第 %d 次请求异常: %s', n + 1, e)
            time.sleep(2 ** n)
    return None

r = get_with_retry('/lab/guard', headers={
    'User-Agent': 'SpiderBond-Student/1.0',
    'Referer': BASE + '/lab/guard/',
})
print(r.status_code if r else '失败')""",
        "pitfalls": [
            "把 UA 伪装成浏览器去规避明确的技术限制，可能违反服务条款，教学场景请标明身份",
            "429 时立刻重试只会加重限流，必须退避",
            "只判断 status_code == 200 会漏掉 2xx 的其他成功码（201、204）",
        ],
        "exercise": "构造合规请求头访问 /lab/guard，完成 L5-1，并观察超频后的 429。",
        "lab": "/lab/guard", "lab_text": "请求头守卫",
    },
    {
        "slug": "dynamic-page", "no": 15, "title": "动态页面分析与浏览器自动化",
        "track": "进阶篇", "level": "进阶", "minutes": 40,
        "summary": "页面内容由 JS 渲染时，requests 拿到的 HTML 里没有数据。优先去找背后的接口；确实需要渲染时，再用 Selenium / Playwright。",
        "points": [
            "判断方法：对比「查看网页源代码」与 DevTools Elements；源码里只有空壳 div 就是客户端渲染",
            "优先方案：Network 面板找 XHR/fetch 接口，直接请求 JSON（第 11 课）",
            "次选方案：找页面内嵌的初始状态（window.__INITIAL_STATE__、<script type=\"application/json\">）",
            "最后方案：Selenium / Playwright 驱动真实浏览器，成本高、速度慢",
            "Playwright 的 page.wait_for_selector / route 拦截请求，比盲目 sleep 稳",
            "无头浏览器要设置合理 viewport、UA，并控制并发实例数",
            "渲染方案内存与 CPU 开销大，能不用就不用",
        ],
        "code": """# 方案一（推荐）：直接打接口
import requests
r = requests.get('https://spider.skkk.uno/lab/api/v1/items',
                 params={'page': 1, 'size': 5},
                 headers={'X-Lab-Key': 'spiderlab'}, timeout=8)
print(r.json()['items'][0])

# 方案二：需要真实渲染时（pip install playwright && playwright install chromium）
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://spider.skkk.uno/lab/books?page=1',
              wait_until='networkidle')
    page.wait_for_selector('div.book')
    titles = page.locator('div.book h2').all_text_contents()
    print('渲染后取到:', titles[:2])
    browser.close()

# 方案三：拦截 XHR，直接拿数据而不渲染 DOM
# page.on('response', lambda res: ... if '/api/v1/' in res.url)""",
        "pitfalls": [
            "一上来就用 Selenium 是最常见的性能反模式，先花 5 分钟找接口",
            "wait_until='networkidle' 在长轮询站点会一直等，改用 wait_for_selector",
            "浏览器渲染同样要限速，别开十几个实例并发",
        ],
        "exercise": "对比 /lab/books 的网页源代码与渲染后 DOM，说明本站为什么能被 requests 直接解析。",
        "lab": "/lab/api", "lab_text": "JSON 接口靶场",
    },
    {
        "slug": "browser-automation", "no": 16, "title": "Selenium 与元素定位进阶",
        "track": "进阶篇", "level": "进阶", "minutes": 30,
        "summary": "补上 Selenium 的定位体系与等待机制。显式等待、隐式等待、Expected Conditions 是让自动化脚本稳定的三个关键。",
        "points": [
            "定位：By.ID / CSS_SELECTOR / XPATH / CLASS_NAME / LINK_TEXT",
            "显式等待 WebDriverWait + expected_conditions 优于 time.sleep",
            "常见坑：元素在 iframe 内需 switch_to.frame、新窗口需 switch_to.window",
            "执行 JS：driver.execute_script('window.scrollTo(0, document.body.scrollHeight)') 处理懒加载",
            "无头模式、禁用图片、设置 UA 可显著提速",
            "退出务必 driver.quit()，否则残留进程吃内存",
            "本站靶场全部服务端渲染，实际上用不到浏览器自动化——这里是知识补全",
        ],
        "code": """from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--disable-gpu')
opts.add_argument('--blink-settings=imagesEnabled=false')
opts.add_argument('--user-agent=SpiderBond-Student/1.0')

driver = webdriver.Chrome(options=opts)
try:
    driver.get('https://spider.skkk.uno/lab/books?page=1')
    cards = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.book')))
    for c in cards:
        print(c.find_element(By.CSS_SELECTOR, 'h2').text)
finally:
    driver.quit()""",
        "pitfalls": [
            "time.sleep(3) 在慢网络下不够、在快网络下浪费，一律用显式等待",
            "StaleElementReferenceException 常因页面刷新后重用了旧元素引用",
            "忘记 quit() 会留下大量 chrome 进程，服务器内存很快耗尽",
        ],
        "exercise": "思考题：本站 /lab/ 全部服务端渲染，若用 Selenium 抓取，相比 requests + lxml 多了哪些开销？",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },

    # ============================================================ 工程篇
    {
        "slug": "concurrency", "no": 17, "title": "并发、异步与速率控制",
        "track": "工程篇", "level": "高阶", "minutes": 40,
        "summary": "串行抓 1000 页可能要十几分钟，但盲目开 100 个线程会把目标站打挂，也把自己送进 429。并发的核心是「有上限、可退让、可观测」。",
        "points": [
            "ThreadPoolExecutor(max_workers=N)：I/O 密集场景最简单有效，N 一般 4~8",
            "asyncio + aiohttp：单线程高并发，适合上万级请求，注意 Semaphore 限并发",
            "速率控制：令牌桶 / Semaphore / 每请求间隔；永远设置上限",
            "任务队列 + 失败重试队列 + 去重集合（Bloom Filter 用于大规模）",
            "多进程适合 CPU 密集的解析，注意进程间通信与内存",
            "并发下日志要带任务标识，便于定位",
            "对本站练习请把并发控制在 2~3，遵守 Crawl-delay",
        ],
        "code": """import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE = 'https://spider.skkk.uno'
HEADERS = {'User-Agent': 'SpiderBond-Student/1.0'}

def fetch(page):
    r = requests.get(BASE + '/lab/books', params={'page': page},
                     headers=HEADERS, timeout=8)
    r.raise_for_status()
    time.sleep(0.5)          # 每个 worker 内部限速
    return page, len(r.text)

# 并发上限 3，避免压垮目标站
with ThreadPoolExecutor(max_workers=3) as pool:
    futures = [pool.submit(fetch, p) for p in range(1, 4)]
    for f in as_completed(futures):
        try:
            print('完成:', f.result())
        except Exception as e:
            print('失败:', e)

# 异步版本骨架（pip install aiohttp）
# import asyncio, aiohttp
# sem = asyncio.Semaphore(3)
# async def one(s, url):
#     async with sem:
#         async with s.get(url) as r:
#             return await r.text()
# async def main():
#     async with aiohttp.ClientSession() as s:
#         return await asyncio.gather(*(one(s, u) for u in urls))""",
        "pitfalls": [
            "max_workers 设到 50+ 几乎必然触发限流或封禁",
            "requests.Session 不是线程安全的，多线程里每线程各建一个",
            "没做去重与失败重试，断点续跑就无从谈起",
        ],
        "exercise": "用 ThreadPoolExecutor(max_workers=3) 重做 L2-1，对比串行耗时。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "scrapy", "no": 18, "title": "Scrapy 框架与项目结构",
        "track": "工程篇", "level": "高阶", "minutes": 45,
        "summary": "当爬虫从脚本长成项目，就需要框架来管调度、去重、管道与中间件。Scrapy 把这套能力标准化了。",
        "points": [
            "核心组件：Engine、Scheduler、Downloader、Spider、ItemPipeline、Middleware",
            "Spider 里 parse() 返回 Request 或 Item；用 response.xpath() / response.css()",
            "Item / dataclass 定义字段，Pipeline 做清洗、校验、去重、入库",
            "settings.py 关键项：ROBOTSTXT_OBEY、DOWNLOAD_DELAY、CONCURRENT_REQUESTS、USER_AGENT、AUTOTHROTTLE_ENABLED",
            "中间件处理 UA 池、代理、重试、Cookie；AUTOTHROTTLE 自动按延迟调整并发",
            "Feed 导出：scrapy crawl name -O books.json / csv / jl",
            "调试：scrapy shell 'URL' 交互式试 XPath，scrapy crawl -s LOG_LEVEL=DEBUG",
        ],
        "code": """# pip install scrapy && scrapy startproject spiderlab && cd spiderlab
# spiders/books.py
import scrapy

class BooksSpider(scrapy.Spider):
    name = 'books'
    allowed_domains = ['spider.skkk.uno']
    start_urls = ['https://spider.skkk.uno/lab/books?page=1']

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'USER_AGENT': 'SpiderBond-Student/1.0 (+course practice)',
        'FEEDS': {'books.jl': {'format': 'jsonlines', 'encoding': 'utf8'}},
    }

    def parse(self, response):
        for card in response.css('div.book'):
            yield {
                'id': card.attrib.get('data-id'),
                'title': card.css('h2::text').get().strip(),
                'price': float(card.css('span.price::text').get()),
                'href': response.urljoin(card.css('a.detail::attr(href)').get()),
            }
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

# 运行：scrapy crawl books
# 试选择器：scrapy shell 'https://spider.skkk.uno/lab/books?page=1'""",
        "pitfalls": [
            "ROBOTSTXT_OBEY=False 会直接忽略 robots，教学与生产都不建议",
            "response.css('::text') 与 XPath text() 一样只取直接文本",
            "Pipeline 里没做去重会产生大量重复 Item",
        ],
        "exercise": "把 L2-1 的任务改写成 Scrapy Spider，导出 JSON Lines 并与手写脚本结果比对。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "storage", "no": 19, "title": "数据清洗、存储与结构化输出",
        "track": "工程篇", "level": "高阶", "minutes": 35,
        "summary": "抓到数据只是开始。字段校验、类型转换、去重、编码统一，再落到合适的存储介质，才算交付一份能用的数据集。",
        "points": [
            "清洗：strip、空白折叠、全半角、单位剥离（¥、元、万）、日期标准化、缺失值处理",
            "校验：必填字段、类型、范围、枚举值；脏数据单独记录而不是静默丢弃",
            "JSON：json.dump(..., ensure_ascii=False, indent=2)；增量用 JSON Lines",
            "CSV：csv.DictWriter，newline='' 防空行；给 Excel 用 encoding='utf-8-sig'",
            "SQLite：零配置，适合十万级以下；加唯一索引实现 upsert 去重",
            "MySQL / PostgreSQL / MongoDB：按数据结构与查询需求选型",
            "pandas.read_html 可快速解析表格，但生产代码建议手写解析以便容错",
        ],
        "code": """import csv, json, sqlite3, re
import requests
from bs4 import BeautifulSoup

soup = BeautifulSoup(
    requests.get('https://spider.skkk.uno/lab/books?page=1', timeout=8).text,
    'lxml')

def to_float(s):
    m = re.search(r'[\\d.]+', s or '')
    return float(m.group()) if m else None

rows = []
for c in soup.select('div.book'):
    row = {
        'id': int(c.get('data-id')),
        'title': c.select_one('h2').get_text(strip=True),
        'author': c.select_one('span.author').get_text(strip=True),
        'price': to_float(c.select_one('span.price').get_text()),
        'rating': to_float(c.select_one('span.rating').get_text()),
    }
    if row['title'] and row['price'] is not None:   # 校验
        rows.append(row)

# JSON
with open('books.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

# CSV（utf-8-sig 便于 Excel 打开）
with open('books.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# SQLite + 唯一索引去重
db = sqlite3.connect('books.db')
db.execute('CREATE TABLE IF NOT EXISTS books '
           '(id INTEGER PRIMARY KEY, title TEXT, author TEXT, '
           ' price REAL, rating REAL)')
db.executemany('INSERT OR REPLACE INTO books VALUES '
               '(:id,:title,:author,:price,:rating)', rows)
db.commit()
print('入库', db.execute('SELECT COUNT(*) FROM books').fetchone()[0], '条')""",
        "pitfalls": [
            "Windows 写 CSV 不加 newline='' 会出现隔行空行",
            "json.dumps 默认 ensure_ascii=True，中文会变成 \\uXXXX",
            "入库前不建唯一索引，重跑一次数据就翻倍",
        ],
        "exercise": "按 L5-4 的字段规范输出 JSON 数组并提交判分。",
        "lab": "/lab/books?page=1", "lab_text": "书城第 1 页",
    },
    {
        "slug": "anti-scraping", "no": 20, "title": "反爬机制认知、限速与工程化",
        "track": "工程篇", "level": "高阶", "minutes": 45,
        "summary": "最后一课把「对抗」正名为「合规与稳健」：理解站点为什么设限，学会识别蜜罐与限流，写出有日志、有退避、有监控、可断点续跑的爬虫。",
        "points": [
            "常见机制：UA/Referer 校验、频率限制(429)、Cookie/Token、验证码、JS 挑战、蜜罐链接、数据投毒",
            "蜜罐：CSS 隐藏的链接，正常人点不到，只有盲目 follow 所有 a[href] 的爬虫会中招；识别方式是检查 display:none、visibility:hidden、class 含 trap",
            "正确姿态：先读 robots.txt 与服务条款，标明身份，低频访问，遇到限制主动退让而非硬闯",
            "限速：固定间隔 + 抖动 jitter + 指数退避 + Retry-After 遵从",
            "可观测：logging 分级、请求成功率/状态码分布、失败队列、进度落盘",
            "健壮性：超时、重试上限、幂等、断点续跑、数据去重、字段校验",
            "工程清单：配置外置、任务队列、监控告警、定期快照、合规复核",
        ],
        "code": """import logging, random, time
import requests

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('spider')

BASE = 'https://spider.skkk.uno'
HEADERS = {'User-Agent': 'SpiderBond-Student/1.0 (+contact: course@spiderlab)',
           'Referer': BASE + '/lab/guard/'}

def polite_get(path, session, retries=3):
    for n in range(retries):
        r = session.get(BASE + path, headers=HEADERS, timeout=8)
        log.info('%s -> %s', path, r.status_code)
        if r.status_code == 200:
            time.sleep(0.5 + random.random() * 0.3)   # 固定间隔 + 抖动
            return r
        if r.status_code == 429:
            wait = int(r.headers.get('Retry-After', 2 ** n))
            log.warning('触发限流，退避 %ss', wait)
            time.sleep(wait)
            continue
        if r.status_code in (401, 403):
            log.error('权限不足，停止（不要尝试绕过）')
            return None
        time.sleep(2 ** n)
    log.error('重试耗尽: %s', path)
    return None

with requests.Session() as s:
    resp = polite_get('/lab/guard', s)
    if resp:
        print('拿到守卫页，长度', len(resp.text))""",
        "pitfalls": [
            "把「绕过」当成技术成就是危险的：绕过访问控制可能触及法律责任",
            "蜜罐链接一旦跟进去，对方即可标记你的 IP；只 follow 明确可见的链接",
            "没有日志和进度落盘，跑到 80% 崩了就得从头再来",
        ],
        "exercise": "在 /lab/news 中识别并避开蜜罐链接，完成 L4-4；再按合规要求完成 L5-4 终章。",
        "lab": "/lab/news", "lab_text": "新闻中心",
    },
]

TRACKS = [
    {"name": "基础篇", "desc": "HTTP、HTML、requests、编码与合规，建立正确的底层认知", "count": 5},
    {"name": "解析篇", "desc": "XPath、lxml、BeautifulSoup、CSS 选择器、正则与 JSON，四大解析体系全覆盖", "count": 6},
    {"name": "进阶篇", "desc": "分页、Session、请求头、动态页面与浏览器自动化", "count": 5},
    {"name": "工程篇", "desc": "并发、Scrapy、存储与反爬合规，把脚本变成项目", "count": 4},
]

# ---------------------------------------------------------------- 课程正文增强
# enrich.py 为每课补齐开场、类比、目标、分节精讲、逐步演练、小结、自测题、延伸。
from enrich import ENRICH  # noqa: E402

for _c in COURSES:
    _e = ENRICH.get(_c['slug'])
    if _e:
        _c.update(_e)
    _c['has_case'] = True
    _c['section_count'] = len(_c.get('sections', []))

