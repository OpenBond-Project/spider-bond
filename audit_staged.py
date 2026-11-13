# -*- coding: utf-8 -*-
"""对「将要提交的文件」做最终审计。

与 audit_secrets.py 的区别：这个只扫 git 已暂存的文件，
所以 dist/、node_modules/、.env.local 这些被 .gitignore 排除的不会误报。
提交前跑这个，结果为空才算过关。
"""
import re
import subprocess

PATTERNS = [
    ('Cloudflare Token', r'cfat_[A-Za-z0-9_-]{10,}'),
    ('GitHub OAuth ID', r'Ov23li[A-Za-z0-9]{10,}'),
    ('GitHub Secret', r'c965cff5[0-9a-f]{10,}'),
    ('服务器密码', r'Dh\+gVUj9[^\s\'"]*'),
    ('私钥', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('云厂商 Key', r'(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})'),
    ('公网 IPv4', r'\b(?!127\.0\.0\.1)(?!0\.0\.0\.0)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'),
    ('邮箱地址', r'[\w.+-]+@[\w-]+\.[\w.]{2,}'),
    ('Bearer Token', r'Bearer\s+[A-Za-z0-9._-]{20,}'),
]


def mask(s):
    return s[:6] + '***' + s[-3:] if len(s) > 10 else s[:3] + '***'


files = subprocess.run(['git', 'ls-files'], capture_output=True, text=True).stdout.split('\n')
files = [f for f in files if f]

total = 0
found = {}
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.mp4', '.pdf', '.zip', '.gz',
            '.wasm', '.whl', '.ico', '.woff', '.woff2', '.ttf'}

for f in files:
    # 二进制文件会匹配出无意义的乱码，跳过（它们本来也不该含密钥）
    if f.lower().rsplit('.', 1)[-1] not in ('', ) and ('.' + f.lower().rsplit('.', 1)[-1]) in SKIP_EXT:
        continue
    try:
        txt = open(f, encoding='utf-8', errors='ignore').read()
    except OSError:
        continue
    for label, pat in PATTERNS:
        for m in re.finditer(pat, txt):
            line = txt[:m.start()].count('\n') + 1
            found.setdefault(label, []).append((f, line, mask(m.group(0))))

print('审计暂存文件 %d 个\n' % len(files))
for label, _ in PATTERNS:
    items = found.get(label, [])
    if not items:
        continue
    print('=== %s（%d 处）===' % (label, len(items)))
    for path, line, val in items:
        total += 1
        print('  %-38s L%-5s %s' % (path[:38], line, val))
    print()

print('=' * 56)
if total == 0:
    print('通过：暂存内容未发现密钥或隐私信息')
else:
    print('发现 %d 处，逐条确认是否需要保留后再提交' % total)
