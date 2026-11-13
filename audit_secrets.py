# -*- coding: utf-8 -*-
"""提交前的敏感信息审计：扫描密钥、IP、邮箱等，输出一律掩码。

在任何"把项目推上公开仓库"的动作之前跑一遍，比事后补救便宜得多。
"""
import os
import re

PATTERNS = [
    ('Cloudflare Token', r'cfat_[A-Za-z0-9_-]{10,}'),
    ('GitHub OAuth ID', r'Ov23li[A-Za-z0-9]{10,}'),
    ('GitHub Secret', r'c965cff5[0-9a-f]{10,}'),
    ('服务器密码', r'Dh\+gVUj9[^\s\'"]*'),
    ('私钥', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('云厂商 Key', r'(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})'),
    ('公网 IP', r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    ('邮箱地址', r'[\w.+-]+@[\w-]+\.[\w.]{2,}'),
    ('Bearer Token', r'Bearer\s+[A-Za-z0-9._-]{20,}'),
]

SKIP_DIRS = {'node_modules', 'dist', '.git', '__pycache__', '.venv', 'venv'}
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.wasm', '.whl', '.zip',
            '.gz', '.ico', '.woff', '.woff2', '.ttf', '.tar'}


def mask(s):
    if len(s) <= 10:
        return s[:3] + '***'
    return s[:6] + '***' + s[-3:]


def main():
    hits = {}
    scanned = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            p = os.path.join(root, fn)
            try:
                if os.path.getsize(p) > 3_000_000:
                    continue
                txt = open(p, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            scanned += 1
            for label, pat in PATTERNS:
                for m in re.finditer(pat, txt):
                    line = txt[:m.start()].count('\n') + 1
                    rel = p.replace(os.sep, '/').lstrip('./')
                    hits.setdefault(label, []).append((rel, line, mask(m.group(0))))

    print('已扫描 %d 个文本文件\n' % scanned)
    total = 0
    for label, _ in PATTERNS:
        items = hits.get(label, [])
        if not items:
            continue
        print('=== %s（%d 处）===' % (label, len(items)))
        seen = set()
        for path, line, val in items:
            key = (path, val)
            if key in seen:
                continue
            seen.add(key)
            total += 1
            print('  %-42s L%-5s %s' % (path[:42], line, val))
        print()
    if total == 0:
        print('未发现敏感信息。')


if __name__ == '__main__':
    main()
