# -*- coding: utf-8 -*-
"""IndexNow 推送：把 sitemap 里的 URL 主动告诉 Bing / Yandex / Naver / Seznam。

用法：
    python indexnow.py                 # 推送 sitemap 里的全部 URL
    python indexnow.py <url> [<url>..] # 只推指定 URL（改完某课想立刻重抓时用）

原理：参与引擎约定，站点根放一个 {key}.txt（内容即 key），再把 URL 列表
POST 到 api.indexnow.org，对方会立刻来抓。不需要注册账号，也不需要
Search Console 那种域名验证。Google 不参与这个协议。
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request

HOST = 'spider.skkk.uno'
KEY = '05a9b8d38a0f0b7cb167bb8095d8b2c7'
ENDPOINT = 'https://api.indexnow.org/indexnow'

# 本地有时挂着系统代理，直连才通；服务器上没有代理，这样写两边都能跑
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'SpiderBond-IndexNow'})
    with OPENER.open(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8', 'ignore')


def sitemap_urls():
    _, body = fetch('https://%s/sitemap.xml' % HOST)
    urls = re.findall(r'<loc>(.*?)</loc>', body)
    return [u.replace('&amp;', '&') for u in urls]


def check_key():
    url = 'https://%s/%s.txt' % (HOST, KEY)
    status, body = fetch(url)
    if body.strip() != KEY:
        raise SystemExit('[!] key 验证失败：%s 返回内容与 key 不一致（HTTP %s）'
                         % (url, status))
    print('[OK] key 文件可访问：%s' % url)


def submit(urls):
    payload = json.dumps({
        'host': HOST,
        'key': KEY,
        'keyLocation': 'https://%s/%s.txt' % (HOST, KEY),
        'urlList': urls,
    }).encode('utf-8')
    req = urllib.request.Request(
        ENDPOINT, data=payload, method='POST',
        headers={'Content-Type': 'application/json; charset=utf-8',
                 'User-Agent': 'SpiderBond-IndexNow'})
    try:
        with OPENER.open(req, timeout=60) as r:
            return r.status, r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')


def main():
    explicit = [a for a in sys.argv[1:] if a.startswith('http')]
    check_key()
    urls = explicit or sitemap_urls()
    if not urls:
        raise SystemExit('[!] 没有可推送的 URL')
    print('[..] 推送 %d 个 URL 到 %s' % (len(urls), ENDPOINT))

    # 单次上限 10000 条，这里分批只是为了防止超时，不是协议要求
    for i in range(0, len(urls), 100):
        batch = urls[i:i + 100]
        code, body = submit(batch)
        meaning = {200: '成功', 202: '已接受，等待验证 key', 400: '格式错误',
                   403: 'key 无效', 422: 'URL 不属于该 host 或 key 不匹配',
                   429: '请求过频，稍后重试'}.get(code, '未知')
        print('    第 %d 批（%d 条）-> HTTP %s %s' %
              (i // 100 + 1, len(batch), code, meaning))
        if body.strip():
            print('      %s' % body.strip()[:200])
        if code not in (200, 202):
            return 1
        time.sleep(1)

    print('[OK] 完成。Bing / Yandex 通常几分钟到几小时内开始抓取，'
          'Google 需走 Search Console。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
