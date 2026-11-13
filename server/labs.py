# -*- coding: utf-8 -*-
"""Spider Bond 靶场数据与五级训练场关卡定义。

所有 /lab/ 页面均为教学用途，已在 robots.txt 中明确 Allow。
标准答案由数据实时推导，避免答案与靶场数据不一致。
"""
import os
from urllib.parse import urlencode

BASE = 'https://spider.skkk.uno'   # 学员侧基准地址：用域名，避免暴露源站 IP
BOOKS_PER_PAGE = 4
QUOTES_PER_PAGE = 5
API_PAGE_SIZE = 5

# ---------------------------------------------------------------- 书城靶场
BOOKS = [
    {'id': 1,  'title': 'Python 爬虫入门',      'author': '张三', 'price': 45.0, 'rating': 4.6, 'tag': '技术', 'stock': 12},
    {'id': 2,  'title': '数据结构与算法',        'author': '李四', 'price': 68.0, 'rating': 4.8, 'tag': '技术', 'stock': 7},
    {'id': 3,  'title': '计算机网络',            'author': '王五', 'price': 59.5, 'rating': 4.5, 'tag': '技术', 'stock': 20},
    {'id': 4,  'title': 'HTTP 权威指南',         'author': '赵六', 'price': 88.0, 'rating': 4.9, 'tag': '技术', 'stock': 3},
    {'id': 5,  'title': 'Python 数据分析',       'author': '张三', 'price': 52.0, 'rating': 4.7, 'tag': '数据', 'stock': 15},
    {'id': 6,  'title': '深度学习',              'author': '孙七', 'price': 99.0, 'rating': 4.8, 'tag': 'AI',   'stock': 9},
    {'id': 7,  'title': 'Web 前端开发',          'author': '周八', 'price': 39.0, 'rating': 4.3, 'tag': '技术', 'stock': 31},
    {'id': 8,  'title': 'Linux 系统管理',        'author': '吴九', 'price': 56.0, 'rating': 4.4, 'tag': '运维', 'stock': 11},
    {'id': 9,  'title': '正则表达式必知必会',     'author': '郑十', 'price': 32.0, 'rating': 4.2, 'tag': '技术', 'stock': 26},
    {'id': 10, 'title': 'Scrapy 实战',           'author': '张三', 'price': 72.0, 'rating': 4.9, 'tag': '技术', 'stock': 5},
    {'id': 11, 'title': '数据库系统概念',         'author': '李四', 'price': 78.0, 'rating': 4.6, 'tag': '数据', 'stock': 8},
    {'id': 12, 'title': '异步编程指南',           'author': '王五', 'price': 48.0, 'rating': 4.7, 'tag': '技术', 'stock': 18},
]

# ---------------------------------------------------------------- 名言靶场
QUOTES = [
    {'id': 1,  'text': 'Talk is cheap. Show me the code.',                    'author': 'Linus Torvalds',   'tags': ['编程', '实践']},
    {'id': 2,  'text': 'Simple is better than complex.',                      'author': 'Tim Peters',       'tags': ['Python', '设计']},
    {'id': 3,  'text': 'Premature optimization is the root of all evil.',     'author': 'Donald Knuth',     'tags': ['编程', '性能']},
    {'id': 4,  'text': 'Programs must be written for people to read.',        'author': 'Harold Abelson',   'tags': ['编程', '设计']},
    {'id': 5,  'text': 'The best way to predict the future is to invent it.', 'author': 'Alan Kay',         'tags': ['创新']},
    {'id': 6,  'text': 'Beautiful is better than ugly.',                      'author': 'Tim Peters',       'tags': ['Python', '设计']},
    {'id': 7,  'text': 'Simplicity is prerequisite for reliability.',         'author': 'Edsger Dijkstra',  'tags': ['设计', '工程']},
    {'id': 8,  'text': 'Any fool can write code that a computer can understand.', 'author': 'Martin Fowler', 'tags': ['编程', '工程']},
    {'id': 9,  'text': 'Code is like humor. When you have to explain it, it is bad.', 'author': 'Cory House', 'tags': ['编程']},
    {'id': 10, 'text': 'First, solve the problem. Then, write the code.',     'author': 'John Johnson',     'tags': ['实践']},
]

# ---------------------------------------------------------------- 电影榜靶场（表格）
MOVIES = [
    {'id': 1, 'title': '肖申克的救赎',   'year': 1994, 'rating': 9.7, 'director': '弗兰克·德拉邦特'},
    {'id': 2, 'title': '霸王别姬',       'year': 1993, 'rating': 9.6, 'director': '陈凯歌'},
    {'id': 3, 'title': '阿甘正传',       'year': 1994, 'rating': 9.5, 'director': '罗伯特·泽米吉斯'},
    {'id': 4, 'title': '泰坦尼克号',     'year': 1997, 'rating': 9.4, 'director': '詹姆斯·卡梅隆'},
    {'id': 5, 'title': '千与千寻',       'year': 2001, 'rating': 9.4, 'director': '宫崎骏'},
    {'id': 6, 'title': '这个杀手不太冷', 'year': 1994, 'rating': 9.4, 'director': '吕克·贝松'},
    {'id': 7, 'title': '美丽人生',       'year': 1997, 'rating': 9.5, 'director': '罗伯托·贝尼尼'},
    {'id': 8, 'title': '盗梦空间',       'year': 2010, 'rating': 9.4, 'director': '克里斯托弗·诺兰'},
    {'id': 9, 'title': '楚门的世界',     'year': 1998, 'rating': 9.3, 'director': '彼得·威尔'},
]

# ---------------------------------------------------------------- 新闻靶场（L5 综合）
NEWS = [
    {'id': 101, 'title': 'Python 3.14 正式发布',       'cat': '技术', 'views': 12045, 'date': '2026-11-01'},
    {'id': 102, 'title': '开源社区年度报告出炉',        'cat': '社区', 'views': 8321,  'date': '2026-11-02'},
    {'id': 103, 'title': '爬虫工程师的合规清单',        'cat': '技术', 'views': 15678, 'date': '2026-11-03'},
    {'id': 104, 'title': 'Web 标准更新速览',            'cat': '前端', 'views': 5410,  'date': '2026-11-04'},
    {'id': 105, 'title': '数据清洗的十个常见陷阱',      'cat': '数据', 'views': 9876,  'date': '2026-11-05'},
    {'id': 106, 'title': '异步并发性能对比',            'cat': '技术', 'views': 11230, 'date': '2026-11-06'},
    {'id': 107, 'title': '结构化存储选型指南',          'cat': '数据', 'views': 7654,  'date': '2026-11-07'},
    {'id': 108, 'title': '站点 robots 协议实践',        'cat': '社区', 'views': 6432,  'date': '2026-11-08'},
]

# ---------------------------------------------------------------- JSON 接口靶场
API_ITEMS = [
    {'id': i, 'name': '条目 %02d' % i, 'value': i * 3,
     'category': ['技术', '数据', 'AI', '运维'][(i - 1) % 4]}
    for i in range(1, 21)
]

# ---------------------------------------------------------------- 鉴权 / 会话 / 守卫
VAULT_USER = 'student'
VAULT_PASS = 'spiderlab'
VAULT_SECRET = 'SPIDERLAB-SESSION-SECRET-2026'
LAB_KEY = 'spiderlab'
GUARD_TOKEN = 'GUARD-TOKEN-2026'
REPORT_SECRET = 'REPORT-FINAL-2026'
REQUIRED_UA = 'SpiderBond-Student/1.0'
REQUIRED_REFERER = BASE + '/lab/guard/'

# ---------------------------------------------------------------- 商品库靶场（数值筛选 + 分页）
PRODUCTS = [
    {'id': 1,  'name': '机械键盘',     'price': 399.0, 'stock': 24, 'category': '外设'},
    {'id': 2,  'name': '无线鼠标',     'price': 129.0, 'stock': 61, 'category': '外设'},
    {'id': 3,  'name': '27 寸显示器',  'price': 1499.0, 'stock': 8,  'category': '显示'},
    {'id': 4,  'name': '降噪耳机',     'price': 899.0, 'stock': 15, 'category': '音频'},
    {'id': 5,  'name': 'USB 扩展坞',   'price': 259.0, 'stock': 0,  'category': '配件'},
    {'id': 6,  'name': '人体工学椅',   'price': 1899.0, 'stock': 5,  'category': '家具'},
    {'id': 7,  'name': '升降桌',       'price': 1299.0, 'stock': 11, 'category': '家具'},
    {'id': 8,  'name': '蓝牙音箱',     'price': 349.0, 'stock': 33, 'category': '音频'},
    {'id': 9,  'name': '固态硬盘 1T',  'price': 559.0, 'stock': 42, 'category': '存储'},
    {'id': 10, 'name': '摄像头',       'price': 299.0, 'stock': 19, 'category': '外设'},
    {'id': 11, 'name': '显示器支架',   'price': 199.0, 'stock': 27, 'category': '配件'},
    {'id': 12, 'name': '移动硬盘 2T',  'price': 699.0, 'stock': 6,  'category': '存储'},
]

# ---------------------------------------------------------------- 招聘板靶场（列表 + 详情）
JOBS = [
    {'id': 1, 'title': 'Python 爬虫工程师', 'company': '云图数据', 'city': '广州',
     'salary': '15-25K', 'exp': '1-3 年',
     'desc': '负责数据采集管道建设，要求熟悉 requests / Scrapy，理解 robots 与限速。'},
    {'id': 2, 'title': '数据采集实习生', 'company': '星海科技', 'city': '深圳',
     'salary': '4-6K', 'exp': '应届',
     'desc': '协助维护采集脚本，整理字段口径，编写清洗与校验逻辑。'},
    {'id': 3, 'title': '后端开发工程师', 'company': '木棉网络', 'city': '杭州',
     'salary': '20-35K', 'exp': '3-5 年',
     'desc': '负责接口服务与任务调度，要求熟悉 Python / 消息队列 / 关系型数据库。'},
    {'id': 4, 'title': '数据分析师', 'company': '鲸落信息', 'city': '上海',
     'salary': '18-28K', 'exp': '1-3 年',
     'desc': '负责业务指标体系建设，熟练使用 pandas 与 SQL，能独立完成数据校验。'},
    {'id': 5, 'title': '前端工程师', 'company': '拾光互娱', 'city': '成都',
     'salary': '13-22K', 'exp': '1-3 年',
     'desc': '负责管理后台与可视化页面，熟悉 Vue 3 与工程化构建。'},
    {'id': 6, 'title': '运维开发工程师', 'company': '南岭云', 'city': '广州',
     'salary': '16-26K', 'exp': '3-5 年',
     'desc': '负责自动化运维平台，熟悉 Linux / Nginx / 容器编排。'},
    {'id': 7, 'title': '算法工程师', 'company': '深蓝智能', 'city': '北京',
     'salary': '30-50K', 'exp': '3-5 年',
     'desc': '负责文本抽取与结构化，要求扎实的机器学习基础。'},
    {'id': 8, 'title': '技术文档工程师', 'company': '云图数据', 'city': '远程',
     'salary': '10-16K', 'exp': '1-3 年',
     'desc': '负责接口文档与教程撰写，需要能把技术细节讲给新手听。'},
]

# ---------------------------------------------------------------- 订阅源靶场（XML / 命名空间）
FEED_ITEMS = [
    {'id': 1, 'title': 'Python 3.14 正式发布', 'link': '/lab/news/101', 'pub': '2026-11-01', 'summary': '新版本带来的性能改进与语法变化。'},
    {'id': 2, 'title': '开源社区年度报告', 'link': '/lab/news/102', 'pub': '2026-11-02', 'summary': '过去一年最活跃的项目与贡献者。'},
    {'id': 3, 'title': '爬虫工程师的合规清单', 'link': '/lab/news/103', 'pub': '2026-11-03', 'summary': '十条可执行的合规检查项。'},
    {'id': 4, 'title': 'Web 标准更新速览', 'link': '/lab/news/104', 'pub': '2026-11-04', 'summary': '浏览器新特性与兼容性提示。'},
    {'id': 5, 'title': '数据清洗的十个陷阱', 'link': '/lab/news/105', 'pub': '2026-11-05', 'summary': '从编码到类型转换的常见问题。'},
    {'id': 6, 'title': '异步并发性能对比', 'link': '/lab/news/106', 'pub': '2026-11-06', 'summary': '线程池与协程在不同场景的实测。'},
    {'id': 7, 'title': '结构化存储选型指南', 'link': '/lab/news/107', 'pub': '2026-11-07', 'summary': 'JSON、CSV、SQLite 的适用边界。'},
    {'id': 8, 'title': '站点 robots 协议实践', 'link': '/lab/news/108', 'pub': '2026-11-08', 'summary': '如何写出对爬虫友好的声明。'},
]

# ---------------------------------------------------------------- 统计表靶场（表格汇总 + 合计行陷阱）
STATS_ROWS = [
    {'category': '外设', 'count': 3, 'amount': 827.0},
    {'category': '显示', 'count': 1, 'amount': 1499.0},
    {'category': '音频', 'count': 2, 'amount': 1248.0},
    {'category': '配件', 'count': 2, 'amount': 458.0},
    {'category': '家具', 'count': 2, 'amount': 3198.0},
    {'category': '存储', 'count': 2, 'amount': 1258.0},
]

# ---------------------------------------------------------------- 示例靶站清单
# robots.txt 里禁止抓取的路径。这里是唯一真相源：
# 靶站真实返回的 robots、第 1 课案例的判分答案都从它推导。
# 之前这两处各写一份，改了一处忘另一处，导致学员答对了却被判错。
ROBOTS_DISALLOW = ['/api/check', '/api/check_case', '/lab/trap/', '/admin', '/auth/']

SITES = [
    {'path': '/lab/books', 'name': '书城', 'tech': '静态 HTML / 分页 / 详情页',
     'level': 'L1-L2', 'learn': 'requests + 选择器 + urljoin',
     'desc': '最经典的列表页：div.book 卡片、span.price、a.href 相对链接，共 3 页 12 本书。'},
    {'path': '/lab/quotes', 'name': '名言墙', 'tech': '分页 / 标签 / 文本清洗',
     'level': 'L1-L2', 'learn': '文本提取 + 去空白 + set 去重',
     'desc': 'blockquote + span.author + 多标签，适合练文本提取、去空白与去重。'},
    {'path': '/lab/movies', 'name': '电影榜', 'tech': 'table 表格 / 行列映射',
     'level': 'L2', 'learn': 'tr/td 逐行解析 + 数值比较',
     'desc': '标准 thead/tbody 表格，练 tr 逐行解析、数值列比较与 pandas.read_html 对照。'},
    {'path': '/lab/products', 'name': '商品库', 'tech': 'GET 参数 / 数值区间 / 分页',
     'level': 'L2', 'learn': 'params 传参 + 价格区间筛选 + 库存判断',
     'desc': '支持 min/max 价格筛选与分页，练参数构造、数值区间过滤与缺货字段处理。'},
    {'path': '/lab/jobs', 'name': '招聘板', 'tech': '列表 + 详情两级采集',
     'level': 'L2-L3', 'learn': '收集链接 → 逐个跟进详情 → 限速',
     'desc': '列表页只给标题与公司，详细描述在 /lab/jobs/{id}，练两级采集与相对链接。'},
    {'path': '/lab/stats', 'name': '统计表', 'tech': '表格汇总 / 合计行陷阱',
     'level': 'L2', 'learn': '逐行累加 + 排除合计行',
     'desc': '含一行「合计」，直接 sum 会把合计重复计算，练解析时如何识别并排除汇总行。'},
    {'path': '/lab/news', 'name': '新闻中心', 'tech': 'data-* 属性 / 蜜罐链接',
     'level': 'L3-L4', 'learn': '属性提取 + 识别隐藏蜜罐',
     'desc': '带 data-id、data-views 的结构化列表，含隐藏 honeypot 链接，练属性提取与合规跟随。'},
    {'path': '/lab/feed', 'name': '订阅源', 'tech': 'XML / RSS / 命名空间',
     'level': 'L3', 'learn': 'lxml etree.XML + 命名空间前缀',
     'desc': '返回真实 RSS 结构（含 xmlns 命名空间），练 XML 解析与带命名空间的 XPath。'},
    {'path': '/lab/vault', 'name': '登录保险库', 'tech': 'POST 表单 / Session / Cookie',
     'level': 'L3', 'learn': 'requests.Session + 表单提交',
     'desc': '必须 POST 登录并保持 Cookie 才能拿到 secret，练 requests.Session。'},
    {'path': '/lab/guard', 'name': '请求头守卫', 'tech': 'UA / Referer 校验 / 频率限制',
     'level': 'L3（头）+ L5（退避）', 'learn': '多传一个 headers 字典；退避属于工程能力',
     'desc': '校验 User-Agent 与 Referer，超频返回 429。构造请求头本身很简单，难的是限速与退避策略。'},
    {'path': '/lab/api', 'name': 'JSON 接口', 'tech': 'AJAX / 自定义请求头 / 分页',
     'level': 'L4', 'learn': 'JSON 解析 + has_next 翻页 + 字段清洗',
     'desc': '模拟前后端分离站点：/lab/api/v1/items 返回 JSON，需要 X-Lab-Key 请求头。'},
    {'path': '/lab/gallery', 'name': '图库', 'tech': 'img / srcset / data-* / CSS 背景图',
     'level': 'L2-L3', 'learn': '属性提取 + srcset 解析 + 背景图地址',
     'desc': '缩略图与原图分离：原图地址藏在 data-src 和 srcset 的 1200w 里，'
             '详情页的大图是 CSS 背景图，用 img 选择器抓不到。'},
    {'path': '/lab/media', 'name': '视频中心', 'tech': 'video / source / poster / Range',
     'level': 'L3', 'learn': '媒体源提取 + Range 请求',
     'desc': '两段合成视频，地址在 source 的 src 上；支持 Range 请求，'
             '可以练习只取文件头部而不下载整段。'},
    {'path': '/lab/files', 'name': '文件下载', 'tech': 'Content-Type / 二进制 / ZIP',
     'level': 'L3', 'learn': '响应头判断 + 二进制落盘',
     'desc': 'PDF / CSV / JSON / ZIP 四种文件，练习按 Content-Type 判断类型、'
             '用 content 而不是 text 保存二进制。'},
]

# ---------------------------------------------------------------- 五级训练场
# 等级按「要写多少代码、涉及几个概念」划分，而不是按名词听起来高不高级。
LEVELS = [
    {'code': 'L1', 'name': '单页提取', 'badge': '入门', 'color': 'primary',
     'desc': '一条请求 + 一条选择器就能拿到答案，不写循环。',
     'need': '会 requests.get，会一种选择器',
     'skills': ['requests', 'HTML 结构', 'lxml / BS4 基础', 'XPath 基础'],
     'courses': ['3', '5', '6', '10'], 'tasks': ['L1-1', 'L1-2', 'L1-3', 'L1-4', 'L1-5', 'L1-6']},
    {'code': 'L2', 'name': '列表翻页', 'badge': '基础', 'color': 'success',
     'desc': '要写 for 循环、urljoin 拼链接、条件筛选与去重。',
     'need': '会循环、会类型转换、会 urljoin',
     'skills': ['分页循环', '条件筛选', '表格解析', 'urljoin', '去重'],
     'courses': ['7', '8', '9', '12'], 'tasks': ['L2-1', 'L2-2', 'L2-3', 'L2-4', 'L2-5', 'L2-6', 'L2-7']},
    {'code': 'L3', 'name': '身份与会话', 'badge': '进阶', 'color': 'warning',
     'desc': '要传自定义请求头、提交表单、用 Session 保持 Cookie。请求头只是多传一个字典。',
     'need': '会读接口说明、会 POST、会用 Session',
     'skills': ['自定义请求头', 'POST 表单', 'Session/Cookie', '状态码处理'],
     'courses': ['13', '14'], 'tasks': ['L3-1', 'L3-2', 'L3-3', 'L3-4', 'L3-5', 'L3-6', 'L3-7', 'L3-8']},
    {'code': 'L4', 'name': '接口与结构', 'badge': '高阶', 'color': 'danger',
     'desc': '要读 JSON 分页字段、清洗类型、处理 data-* 与蜜罐，比 L3 多一层数据加工。',
     'need': '会 JSON 翻页、会字段清洗、会识别蜜罐',
     'skills': ['JSON 接口分页', 'has_next 终止', 'data-* 提取', '蜜罐规避'],
     'courses': ['11', '12', '14'], 'tasks': ['L4-1', 'L4-2', 'L4-3', 'L4-4', 'L4-5', 'L4-6']},
    {'code': 'L5', 'name': '综合工程', 'badge': '挑战', 'color': 'dark',
     'desc': '要组合限速退避、多源合并、详情跟进与结构化输出，按真实项目标准交付。',
     'need': '会退避重试、会多源合并、会结构化输出',
     'skills': ['限速退避', '多源合并', '详情跟进', '结构化输出', 'robots 合规'],
     'courses': ['14', '19', '20'], 'tasks': ['L5-1', 'L5-2', 'L5-3', 'L5-4', 'L5-5', 'L5-6']},
]

TASKS = {
    # ---------------- L1 入门 ----------------
    'L1-1': {'title': '读出页面标题', 'level': 'L1', 'points': 10,
        'goal': '抓取书城第 1 页，提取 <title> 标签里的文本。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '一段纯文本', 'type': 'text',
        'hint': 'lxml: tree.xpath("//title/text()")[0]；BS4: soup.title.get_text(strip=True)。',
        'skills': ['requests', 'XPath', 'BeautifulSoup']},
    'L1-2': {'title': '提取本页书名', 'level': 'L1', 'points': 10,
        'goal': '提取书城第 1 页全部书名，按页面出现顺序，用英文逗号分隔提交。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '英文逗号分隔的有序列表，例如：甲,乙,丙', 'type': 'olist',
        'hint': '每本书在 <div class="book"> 里，书名是里面的 <h2>。XPath: //div[@class="book"]/h2/text()',
        'skills': ['XPath', 'CSS 选择器', '列表提取']},
    'L1-3': {'title': '统计书籍数量', 'level': 'L1', 'points': 10,
        'goal': '统计书城第 1 页共有多少本书，提交一个整数。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '一个整数', 'type': 'number',
        'hint': 'len(soup.select("div.book")) 或 XPath 的 count(//div[@class="book"])。',
        'skills': ['计数', 'CSS 选择器']},
    'L1-4': {'title': '拼接绝对链接', 'level': 'L1', 'points': 10,
        'goal': '提取书城第 1 页所有「详情」链接，用 urljoin 转成绝对 URL，按顺序用英文逗号分隔提交。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '英文逗号分隔的完整 URL 有序列表', 'type': 'olist',
        'hint': 'from urllib.parse import urljoin; urljoin(base, a["href"])。别用字符串相加。',
        'skills': ['@href 提取', 'urljoin', '相对 URL']},

    # ---------------- L2 基础 ----------------
    'L2-1': {'title': '跨页采集全量书名', 'level': 'L2', 'points': 20,
        'goal': '书城共 3 页。翻完所有页，提取全部书名，按页面顺序用英文逗号分隔提交，不要重复。',
        'target': '/lab/books?page=1', 'target_text': '书城（共 3 页）',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': 'for page in range(1, 4) 循环改 page 参数；每页取 //div[@class="book"]/h2/text()，list.extend 汇总，请求间 sleep。',
        'skills': ['分页循环', '限速', '结果汇总']},
    'L2-2': {'title': '条件筛选：高价书', 'level': 'L2', 'points': 20,
        'goal': '在全站 12 本书中找出价格严格大于 50 元的书，按书籍 id 顺序用英文逗号分隔提交书名。',
        'target': '/lab/books?page=1', 'target_text': '书城（共 3 页）',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': '价格是文本，先 float() 再比较。注意是「大于」不是「大于等于」。',
        'skills': ['类型转换', '条件筛选', '数值比较']},
    'L2-3': {'title': '表格解析：最高分电影', 'level': 'L2', 'points': 20,
        'goal': '解析电影榜表格，找出评分最高的那部电影，提交片名。',
        'target': '/lab/movies', 'target_text': '电影榜（表格）',
        'format': '一段纯文本（片名）', 'type': 'text',
        'hint': '逐个 <tr> 取 <td>，把评分列 float 化后 max()。也可对照 pandas.read_html。',
        'skills': ['表格解析', 'max / 排序', '行列映射']},
    'L2-4': {'title': '翻页 + 作者去重', 'level': 'L2', 'points': 20,
        'goal': '名言站共 2 页。抓完两页，提取全部作者并去重，用英文逗号分隔提交（顺序不限）。',
        'target': '/lab/quotes?page=1', 'target_text': '名言站（共 2 页）',
        'format': '英文逗号分隔的列表（顺序不限）', 'type': 'ulist',
        'hint': '作者节点是 <span class="author">。用 set() 去重，本题不要求顺序。',
        'skills': ['分页', 'set 去重', '文本清洗']},

    # ---------------- L3 进阶 ----------------
    'L3-1': {'title': '请求头鉴权取 token', 'level': 'L3', 'points': 30,
        'goal': '访问 /lab/api/v1/token 需要指定请求头。带上正确请求头取回 token 字段的值并提交。',
        'target': '/lab/api', 'target_text': 'JSON 接口靶场说明页',
        'format': '一段纯文本（token 值）', 'type': 'text',
        'hint': '说明页写明了请求头名和值。requests.get(url, headers={...}).json()["token"]。',
        'skills': ['请求头分析', '接口鉴权', 'JSON 解析']},
    'L3-2': {'title': 'Session 登录后取值', 'level': 'L3', 'points': 30,
        'goal': '先用 POST 登录 /lab/vault/login（表单字段见说明页），保持会话再访问 /lab/vault，提交 secret code。',
        'target': '/lab/vault', 'target_text': '登录保险库',
        'format': '一段纯文本（secret code）', 'type': 'text',
        'hint': 'requests.Session() 会自动保存 Set-Cookie；不带 Cookie 访问会返回 403。',
        'skills': ['POST 表单', 'Session', 'Cookie 保持']},
    'L3-3': {'title': '表单字段与状态码', 'level': 'L3', 'points': 30,
        'goal': '登录页说明中列出的用户名字段是什么？提交该字段名。',
        'target': '/lab/vault', 'target_text': '登录保险库说明页',
        'format': '一段纯文本（表单字段名）', 'type': 'text',
        'hint': '查看页面中的示例表单，或阅读说明页的表单字段表格，找到用户名输入框的 name。',
        'skills': ['表单分析', 'HTML 属性']},
    'L3-4': {'title': '未登录访问的状态码', 'level': 'L3', 'points': 30,
        'goal': '不带 Cookie 直接 GET /lab/vault，服务器返回什么 HTTP 状态码？提交一个整数。',
        'target': '/lab/vault', 'target_text': '登录保险库',
        'format': '一个整数（状态码）', 'type': 'number',
        'hint': '用 response.status_code 观察，别只看页面内容。403 表示拒绝访问。',
        'skills': ['状态码', '访问控制']},

    # ---------------- L4 高阶 ----------------
    'L4-1': {'title': 'JSON 接口分页求和', 'level': 'L4', 'points': 40,
        'goal': '调用 /lab/api/v1/items?page=N&size=5 翻完所有页（带 X-Lab-Key 头），把所有条目的 id 相加，提交总和。',
        'target': '/lab/api', 'target_text': 'JSON 接口靶场',
        'format': '一个整数', 'type': 'number',
        'hint': '响应 JSON 的 has_next 指示是否还有下一页，别靠猜页数。r.json()["items"] 是列表。',
        'skills': ['AJAX 接口', '自定义请求头', 'JSON 分页']},
    'L4-2': {'title': '接口中的分类统计', 'level': 'L4', 'points': 40,
        'goal': '翻完 /lab/api/v1/items 所有分页，统计 category 为「技术」的条目数量，提交一个整数。',
        'target': '/lab/api', 'target_text': 'JSON 接口靶场',
        'format': '一个整数', 'type': 'number',
        'hint': '遍历所有页的 items，用 Counter 或 sum(1 for x in items if x["category"] == "技术")。',
        'skills': ['JSON 遍历', '条件统计', 'Counter']},
    'L4-3': {'title': 'data-* 属性提取', 'level': 'L4', 'points': 40,
        'goal': '新闻中心列表里每篇文章都有 data-id 属性。提取全部 data-id，按页面顺序用英文逗号分隔提交。',
        'target': '/lab/news', 'target_text': '新闻中心',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': 'XPath: //article/@data-id；BS4: [a["data-id"] for a in soup.select("article")]。',
        'skills': ['@data-id', '属性提取', 'XPath 轴']},
    'L4-4': {'title': '避开蜜罐链接', 'level': 'L4', 'points': 40,
        'goal': '新闻中心含隐藏的蜜罐链接。只提取正常文章的标题（不含蜜罐），按页面顺序用英文逗号分隔提交。',
        'target': '/lab/news', 'target_text': '新闻中心',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': '蜜罐链接带 class="trap" 且被 CSS 隐藏。只取 <article> 里的 <h2>，不要盲目 follow 所有 a[href]。',
        'skills': ['蜜罐识别', '选择器过滤', '合规跟随']},

    # ---------------- L5 综合 ----------------
    'L5-1': {'title': '守卫页：构造合规请求头', 'level': 'L5', 'points': 60,
        'goal': '/lab/guard 校验 User-Agent 与 Referer。带上正确请求头取回页面中的 guard-code 并提交。',
        'target': '/lab/guard', 'target_text': '请求头守卫',
        'format': '一段纯文本（guard-code）', 'type': 'text',
        'hint': '说明页给出要求的 User-Agent 与 Referer。注意超频会返回 429，请加 sleep 与退避重试。',
        'skills': ['UA / Referer', '429 退避', '限速']},
    'L5-2': {'title': '多源合并：书名与电影名', 'level': 'L5', 'points': 60,
        'goal': '把书城全部书名与电影榜全部片名合并为一个列表，去重后按拼音无关的原始采集顺序提交（书在前、电影在后），英文逗号分隔。',
        'target': '/lab/books?page=1', 'target_text': '书城 + 电影榜',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': '分别采集两个源，用 list.extend 合并；本数据集无重名，直接拼接即可。注意控制请求频率。',
        'skills': ['多源采集', '结果合并', '限速']},
    'L5-3': {'title': '全站统计：库存总量', 'level': 'L5', 'points': 60,
        'goal': '翻完书城 3 页，从详情页的 data-stock 属性读取每本书库存，求总和，提交一个整数。',
        'target': '/lab/books?page=1', 'target_text': '书城（详情页）',
        'format': '一个整数', 'type': 'number',
        'hint': '列表页只有书名，详情页 /lab/books/{id} 的 <div id="stock" data-stock="N"> 里才有库存。12 次详情请求请限速。',
        'skills': ['详情页跟进', 'data-* 属性', '限速', '汇总']},
    'L5-4': {'title': '终章：结构化书单', 'level': 'L5', 'points': 100,
        'goal': '完成综合任务：筛出评分 >= 4.8 的书，按 id 顺序整理成 JSON 数组提交（见任务页的字段规范）。',
        'target': '/lab/books?page=1', 'target_text': '书城（共 3 页）',
        'format': 'JSON 字符串（数组）', 'type': 'json',
        'spec': '[{"id": 整数, "title": "书名", "price": 浮点数}, ...]',
        'example': '[{"id": 2, "title": "数据结构与算法", "price": 68.0}]',
        'hint': '翻页 + 数值筛选 + 结构化输出；用 json.dumps(ensure_ascii=False) 提交。请遵守 robots.txt 的 Crawl-delay。',
        'skills': ['综合采集', 'JSON 序列化', 'robots 合规', '数据清洗']},
}


# ---------------------------------------------------------------- 扩充关卡（每级 +2，覆盖更多题型）
TASKS.update({
    'L1-5': {'title': '用正则求和', 'level': 'L1', 'points': 15,
        'goal': '这题不许用 XPath 或 CSS 选择器。只用正则从页面源码里取出所有价格'
                '（HTML 里形如 <span class="price">45.00</span>），求和后保留两位小数。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '一个数字，保留两位小数，例如 512.34', 'type': 'number',
        'hint': '用 re.findall 匹配 class="price" 与 </span> 之间的数字，得到字符串列表，'
                '再逐个转 float 求和。注意 round(x, 2)。',
        'skills': ['正则表达式', '文本提取', '类型转换']},

    'L1-6': {'title': '找出评分最高的书', 'level': 'L1', 'points': 15,
        'goal': '提取书城第 1 页里评分（rating）最高的那本书的书名。若并列，取页面中先出现的。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '一段纯文本（书名）', 'type': 'text',
        'hint': '评分在 span.rating，书名是同一个 div.book 里的 h2。先把每本书抓成 (rating, title)，'
                '再取最大值（max 遇到并列会返回第一个）。',
        'skills': ['属性提取', '排序', '列表处理']},

    'L2-5': {'title': '价格区间筛选', 'level': 'L2', 'points': 20,
        'goal': '商品库支持 URL 参数 min / max 做价格区间筛选。提取价格在 300 到 1000 之间（含边界）'
                '的全部商品名，按页面顺序提交。',
        'target': '/lab/products?page=1&min=300&max=1000', 'target_text': '商品库（已筛选）',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': '把 min/max 拼进 URL 让服务端筛，比自己遍历全部再过滤更接近真实做法。'
                '商品名在 div.product 里的 h3。',
        'skills': ['URL 参数', '条件筛选', 'CSS 选择器']},

    'L2-6': {'title': '统计表的合计陷阱', 'level': 'L2', 'points': 25,
        'goal': '统计表末尾有一行「合计」。只对分类行的「数量」列求和（别把合计行也算进去），提交总数。',
        'target': '/lab/stats', 'target_text': '分类统计表',
        'format': '一个整数', 'type': 'number',
        'hint': '分类行在 tbody、合计行在 tfoot。XPath 写 //tbody/tr/td[@class="count"] '
                '就天然排除了 tfoot，不用额外判断。',
        'skills': ['表格解析', 'XPath 轴', '陷阱识别']},

    'L2-7': {'title': '图库的原图地址', 'level': 'L2', 'points': 25,
        'goal': '图库列表页显示的是缩略图，原图另有地址。提取全部 6 张原图的完整路径，'
                '按页面顺序用英文逗号分隔提交。',
        'target': '/lab/gallery', 'target_text': '图库',
        'format': '英文逗号分隔的有序列表，例如：/media/a.jpg,/media/b.jpg', 'type': 'olist',
        'hint': '缩略图在 src 属性，原图在 data-src；srcset 里 "1200w" 那一条也是原图。'
                'XPath: //figure/img/@data-src',
        'skills': ['属性提取', 'srcset', 'data-* 属性']},

    'L3-5': {'title': '关闭自动跳转看 302', 'level': 'L3', 'points': 25,
        'goal': 'requests 默认会自动跟随 302，所以你看不到跳转本身。关闭自动跳转后 POST 登录，'
                '提交响应头 Location 里的路径。',
        'target': '/lab/vault', 'target_text': '登录保险库',
        'format': '一个以 / 开头的路径，例如 /lab/xxx', 'type': 'text',
        'hint': 'requests.post(..., allow_redirects=False)。登录成功时 status_code 是 302，'
                '路径在 r.headers["Location"]。账号密码见 /lab/vault 页面里的说明表。',
        'skills': ['302 跳转', '响应头', 'allow_redirects']},

    'L3-6': {'title': '手动管理 Cookie', 'level': 'L3', 'points': 30,
        'goal': '这次不许用 Session。从登录响应的 Set-Cookie 里取出 lab_session 的值，'
                '手动拼进下一次请求的 Cookie 头，提交保险库里的 secret。',
        'target': '/lab/vault', 'target_text': '登录保险库',
        'format': '一段纯文本（secret code）', 'type': 'text',
        'hint': 'Set-Cookie 形如 lab_session=ok; Path=/; HttpOnly，取第一个分号前的 key=value；'
                '请求时 headers={"Cookie": "lab_session=ok"}。',
        'skills': ['Cookie 管理', '响应头解析', '会话保持']},

    'L3-7': {'title': '抓出视频直链', 'level': 'L3', 'points': 25,
        'goal': '视频中心第一段视频的主源是一个 mp4 直链。提取它的路径（以 / 开头）提交。',
        'target': '/lab/media', 'target_text': '视频中心',
        'format': '一个以 / 开头的路径，例如 /media/xxx.mp4', 'type': 'text',
        'hint': '地址在 <video> 内部的 <source src="..."> 上，不在 video 标签自身。'
                'XPath: (//video/source/@src)[1]',
        'skills': ['媒体源提取', 'source 标签', 'XPath 索引']},

    'L3-8': {'title': '下载 CSV 并数行数', 'level': 'L3', 'points': 25,
        'goal': '文件下载页提供了一个 CSV。下载它，统计除表头之外有多少行数据，提交这个数字。',
        'target': '/media/books-export.csv', 'target_text': 'CSV 数据集',
        'format': '一个整数', 'type': 'number',
        'hint': 'r = requests.get(url)；行数 = len(r.text.strip().splitlines()) - 1。'
                '文件是 UTF-8 with BOM，用 r.text 读不影响行数统计。',
        'skills': ['文件下载', '文本解析', '行数统计']},

    'L4-5': {'title': '解析 RSS 订阅源', 'level': 'L4', 'points': 30,
        'goal': '订阅源是 RSS 2.0（XML）格式，日期字段带 dc: 命名空间前缀。'
                '提取所有 item 的标题，按出现顺序提交。',
        'target': '/lab/feed', 'target_text': '教学订阅源（RSS）',
        'format': '英文逗号分隔的有序列表', 'type': 'olist',
        'hint': 'lxml.etree.fromstring(r.content) 后取 //item/title/text()。'
                '要注意 HTML 解析器（etree.HTML）对 XML 不友好，这里该用 XML 解析。',
        'skills': ['XML 解析', '命名空间', 'RSS']},

    'L4-6': {'title': '列表 + 详情两级采集', 'level': 'L4', 'points': 35,
        'goal': '招聘列表页只有职位摘要，薪资在详情页里。先取列表里的详情链接，逐个跟进，'
                '按职位顺序提交全部薪资区间。',
        'target': '/lab/jobs?page=1', 'target_text': '招聘板',
        'format': '英文逗号分隔的有序列表，例如 15-25K,4-6K', 'type': 'olist',
        'hint': '第一步取 a[href^="/lab/jobs/"] 的 href（注意别把 ?page=2 也算进去）；'
                '第二步对每个链接再发一次请求，取 .salary 的文本。',
        'skills': ['两级采集', '链接跟进', '循环']},

    'L5-5': {'title': '限速与退避重试', 'level': 'L5', 'points': 45,
        'goal': '守卫页 10 秒内超过 8 次请求就返回 429，并带 Retry-After 头。'
                '写出「触发限速 → 读 Retry-After → 等待 → 重试成功」的代码，提交页面里的口令。',
        'target': '/lab/guard', 'target_text': '请求头守卫',
        'format': '一段纯文本（口令）', 'type': 'text',
        'hint': '循环请求直到 status_code == 429，读 r.headers["Retry-After"]，'
                'time.sleep(int(...)) 后再发。别忘了带 User-Agent 和 Referer，否则先吃 403。',
        'skills': ['限速退避', '429 处理', '重试策略']},

    'L5-6': {'title': '多源合并去重', 'level': 'L5', 'points': 40,
        'goal': '把书城（/lab/books?page=1）和商品库（/lab/products?page=1）两个来源合并，'
                '按价格从高到低取前 3 个名称，提交名称列表。',
        'target': '/lab/books?page=1', 'target_text': '书城第 1 页',
        'format': '英文逗号分隔的有序列表（从高到低）', 'type': 'olist',
        'hint': '两边字段名不同（书城是 h2 + span.price，商品是 h3 + span.price），'
                '先各自归一成 (name, price)，合并后再按价格降序排序取前 3。',
        'skills': ['多源合并', '字段归一', '排序']},
})


# ---------------------------------------------------------------- 在线沙箱：起始代码
def _make_starter(task_id, t):
    """按靶站类型生成可运行的骨架。学员补 TODO 处即可，不用从零写起。"""
    target, goal, fmt = t['target'], t['goal'], t['format']

    # 这三题的方法和前面对应靶站不同，单独给骨架
    if task_id == 'L3-5':
        body = """import requests

BASE = 'https://spider.skkk.uno'

# 目标：%GOAL%
# 提交格式：%FMT%
# 关键：allow_redirects=False，否则 requests 会自己跟过去，你就看不到 302
r = requests.post(BASE + '/lab/vault/login',
                  data={'username': 'student', 'password': 'spiderlab'},
                  allow_redirects=False, timeout=15)

print('状态码:', r.status_code)          # 302 说明登录成功但被要求跳转
print('Location:', r.headers.get('Location'))
print('Set-Cookie:', r.headers.get('Set-Cookie', '')[:90])

# TODO: 把 Location 里的路径赋给 answer

answer = None
print('answer =', answer)
"""
        return body.replace('%GOAL%', goal).replace('%FMT%', fmt)

    if task_id == 'L3-6':
        body = """import requests

BASE = 'https://spider.skkk.uno'

# 目标：%GOAL%
# 提交格式：%FMT%
# 这题不许用 Session —— 自己把 Cookie 抠出来手动带上
r0 = requests.post(BASE + '/lab/vault/login',
                   data={'username': 'student', 'password': 'spiderlab'},
                   allow_redirects=False, timeout=8)
print('登录:', r0.status_code)
raw = r0.headers.get('Set-Cookie', '')
print('Set-Cookie:', raw[:120])

# TODO: 从 raw 里取出第一个分号前的 lab_session=...，
#       放进 headers={'Cookie': ...} 再请求 /lab/vault

r1 = requests.get(BASE + '/lab/vault', timeout=8)
print('还没带 Cookie 时:', r1.status_code)

answer = None
print('answer =', answer)
"""
        return body.replace('%GOAL%', goal).replace('%FMT%', fmt)

    if task_id == 'L4-5':
        body = """import requests
from lxml import etree

BASE = 'https://spider.skkk.uno'

# 目标：%GOAL%
# 提交格式：%FMT%
# 注意：RSS 是 XML，别用 etree.HTML（会当 HTML 补全，命名空间容易丢）
r = requests.get(BASE + '/lab/feed', timeout=8)
print('HTTP', r.status_code, '| Content-Type:', r.headers.get('Content-Type'))

tree = etree.fromstring(r.content)
items = tree.xpath('//item/title/text()')
print('抓到标题数:', len(items))
print('前两个:', items[:2])

answer = None
print('answer =', answer)
"""
        return body.replace('%GOAL%', goal).replace('%FMT%', fmt)

    if '/lab/vault' in target:
        body = """import requests

BASE = 'https://spider.skkk.uno'

# 目标：%GOAL%
# 提交格式：%FMT%
# 未登录时 /lab/vault 返回 403，但响应里写明了登录地址、字段名和账号
s = requests.Session()

r0 = s.get(BASE + '/lab/vault', timeout=8)
print('未登录:', r0.status_code, '| 页面里有登录说明表')

# 教学靶场的账号密码直接写在页面里
r1 = s.post(BASE + '/lab/vault/login',
            data={'username': 'student', 'password': 'spiderlab'}, timeout=8)
print('登录请求:', r1.status_code)

# 关键：必须复用同一个 Session，Cookie 才会带上
r2 = s.get(BASE + '/lab/vault', timeout=8)
print('登录后:', r2.status_code, '| 页面长度', len(r2.text))

# TODO: 从 r2.text 里把 secret 提出来（用 XPath 或正则），赋给 answer

answer = None
print('answer =', answer)
"""
    elif '/lab/guard' in target:
        body = """import requests

BASE = 'https://spider.skkk.uno'

# 目标：%GOAL%
# 提交格式：%FMT%
# 这个靶站同时校验 User-Agent 和 Referer，缺一个就 403
headers = {
    'User-Agent': 'SpiderBond-Student/1.0',
    'Referer': BASE + '/lab/guard/',
}

# 对比一下：带请求头 vs 不带
ok = requests.get(BASE + '/lab/guard', headers=headers, timeout=8)
print('带正确请求头:', ok.status_code)
print(ok.text[:300])

bad = requests.get(BASE + '/lab/guard', timeout=8)
print('不带请求头:', bad.status_code)

# TODO: 从 ok.text 里取出要求的信息，赋给 answer

answer = None
print('answer =', answer)
"""
    elif '/lab/api' in target:
        body = """import requests

BASE = 'https://spider.skkk.uno'
# 说明页 /lab/api 里公开了这个 key
HEADERS = {'X-Lab-Key': 'spiderlab'}

# 目标：%GOAL%
# 提交格式：%FMT%

tok = requests.get(BASE + '/lab/api/v1/token', headers=HEADERS, timeout=8)
print('token 接口:', tok.status_code, tok.text[:120])

# 列表接口支持 ?page=N&size=5，响应里有 has_next
r = requests.get(BASE + '/lab/api/v1/items',
                 headers=HEADERS, params={'page': 1, 'size': 5}, timeout=8)
print('items 接口:', r.status_code)
data = r.json()
print('顶层字段:', list(data), '| 本页条数:', len(data.get('items', [])))
print('第一条:', data.get('items', [{}])[0])

# TODO: 按 has_next 翻完所有页，把需要的值算出来赋给 answer

answer = None
print('answer =', answer)
"""
    else:
        body = """import requests
from lxml import etree

BASE = 'https://spider.skkk.uno'

r = requests.get(BASE + '%TARGET%', timeout=8)
print('HTTP', r.status_code, '| 页面长度', len(r.text))

tree = etree.HTML(r.text)

# 目标：%GOAL%
# 提交格式：%FMT%
# TODO: 用 tree.xpath(...) 把数据取出来，赋值给 answer
#   先探路： print(tree.xpath('//div')[:2])

answer = None
print('answer =', answer)
"""
    return (body.replace('%GOAL%', goal)
                .replace('%FMT%', fmt)
                .replace('%TARGET%', target))


for _tid, _task in TASKS.items():
    _task.setdefault('starter', _make_starter(_tid, _task))


def page_of_books(page):
    start = (page - 1) * BOOKS_PER_PAGE
    return BOOKS[start:start + BOOKS_PER_PAGE]


def page_of_quotes(page):
    start = (page - 1) * QUOTES_PER_PAGE
    return QUOTES[start:start + QUOTES_PER_PAGE]


def compute_answers():
    p1 = page_of_books(1)
    return {
        'L1-1': '书城 - 第 1 页 | Spider Bond 靶场',
        'L1-2': [b['title'] for b in p1],
        'L1-3': len(p1),
        'L1-4': ['%s/lab/books/%d' % (BASE, b['id']) for b in p1],
        'L2-1': [b['title'] for b in BOOKS],
        'L2-2': [b['title'] for b in BOOKS if b['price'] > 50],
        'L2-3': max(MOVIES, key=lambda m: m['rating'])['title'],
        'L2-4': sorted({q['author'] for q in QUOTES}),
        'L3-1': GUARD_TOKEN,
        'L3-2': VAULT_SECRET,
        'L3-3': 'username',
        'L3-4': 403,
        'L4-1': sum(i['id'] for i in API_ITEMS),
        'L4-2': sum(1 for i in API_ITEMS if i['category'] == '技术'),
        'L4-3': [str(n['id']) for n in NEWS],
        'L4-4': [n['title'] for n in NEWS],
        'L5-1': REPORT_SECRET,
        'L5-2': [b['title'] for b in BOOKS] + [m['title'] for m in MOVIES],
        'L5-3': sum(b['stock'] for b in BOOKS),
        'L5-4': [{'id': b['id'], 'title': b['title'], 'price': b['price']}
                 for b in BOOKS if b['rating'] >= 4.8],
        # ---- 扩充关卡 ----
        'L1-5': round(sum(b['price'] for b in p1), 2),
        'L1-6': max(p1, key=lambda b: b['rating'])['title'],
        'L2-5': [p['name'] for p in PRODUCTS if 300 <= p['price'] <= 1000],
        'L2-6': sum(r['count'] for r in STATS_ROWS),
        'L3-5': '/lab/vault',
        'L3-6': VAULT_SECRET,
        'L4-5': [f['title'] for f in FEED_ITEMS],
        'L4-6': [j['salary'] for j in JOBS],
        'L5-5': REPORT_SECRET,
        'L5-6': [x['name'] for x in sorted(
            [{'name': b['title'], 'price': b['price']} for b in p1]
            + [{'name': p['name'], 'price': p['price']} for p in PRODUCTS],
            key=lambda x: x['price'], reverse=True)][:3],
        # ---- 媒体与文件关卡 ----
        'L2-7': ['/media/photo-%02d.jpg' % i for i in range(1, 7)],
        'L3-7': '/media/clip-01.mp4',
        # CSV 行数从实际文件推导，避免改了数据集忘记同步答案
        'L3-8': media_csv_rows(),
    }


def media_csv_rows():
    """books-export.csv 的数据行数（不含表头）。文件缺失时退回当前已知值。"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'media', 'books-export.csv')
    try:
        with open(path, encoding='utf-8-sig') as f:
            lines = [x for x in f.read().strip().splitlines() if x.strip()]
        return max(0, len(lines) - 1)
    except OSError:
        return 8


ANSWERS = compute_answers()
