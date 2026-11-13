# -*- coding: utf-8 -*-
"""深度复查：扫描 Git 历史中的每一个 blob，而不只是当前工作区。

为什么需要这个：文件被删除后，内容仍留在历史对象里，`git ls-files` 看不到，
但任何人 clone 下来都能 `git log` 翻出来。这是密钥泄漏最常见的盲区。

同时检查 .git/config（remote 里可能带 token）、异常大的 blob、以及所有 ref。
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
    ('真实服务器 IP', r'139\.199\.7\.211'),
    ('GitHub Token', r'gh[pousr]_[A-Za-z0-9]{30,}'),
    ('Bearer Token', r'Bearer\s+[A-Za-z0-9._-]{20,}'),
    ('JWT', r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
]


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def mask(s):
    return s[:6] + '***' + s[-3:] if len(s) > 10 else s[:3] + '***'


print('=== 1. Git 历史对象扫描 ===')
listing = run(['git', 'rev-list', '--objects', '--all']).stdout.strip().split('\n')
blobs = {}
for line in listing:
    parts = line.split(' ', 1)
    if len(parts) == 2:
        blobs.setdefault(parts[0], parts[1])

print('唯一对象 %d 个（路径去重后）' % len(blobs))

hits = []
big = []
for oid, path in blobs.items():
    # 用字节模式读：仓库里有 PNG 等二进制文件，text=True 会解码失败
    r = subprocess.run(['git', 'cat-file', '-p', oid], capture_output=True)
    if r.returncode != 0 or r.stdout is None:
        continue
    raw = r.stdout
    if len(raw) > 1_500_000:
        big.append((path, len(raw)))
        continue
    content = raw.decode('utf-8', 'ignore')
    for label, pat in PATTERNS:
        for m in re.finditer(pat, content):
            hits.append((label, path, mask(m.group(0))))

if hits:
    print('\n命中 %d 处：' % len(hits))
    for label, path, val in hits:
        print('  [%s] %s -> %s' % (label, path, val))
else:
    print('  未发现任何密钥 / 真实 IP')

print('\n=== 2. 体积异常对象（>1.5MB，可能误入的数据库或构建包）===')
if big:
    for path, size in big:
        print('  %8.1f MB  %s' % (size / 1048576, path))
else:
    print('  无')

print('\n=== 3. .git/config 检查（remote 是否夹带凭据）===')
cfg = run(['git', 'config', '--list', '--local']).stdout
for line in cfg.strip().split('\n'):
    if any(k in line for k in ('url', 'user.email', 'credential', 'token')):
        # 只看是否存在凭据字段，不打印可能的密码
        safe = re.sub(r'://[^@/]+@', '://***@', line)
        print('  ' + safe)

print('\n=== 4. 所有 ref ===')
refs = run(['git', 'for-each-ref', '--format=%(refname) %(objectname:short)']).stdout
for line in refs.strip().split('\n'):
    if line:
        print('  ' + line)

print('\n=== 5. stash / 其他工作副本残留 ===')
st = run(['git', 'stash', 'list']).stdout.strip()
print('  stash: ' + (st if st else '无'))

print('\n' + '=' * 58)
if hits:
    print('需要处理：历史中存在 %d 处敏感内容' % len(hits))
else:
    print('通过：Git 历史中不含密钥或真实服务器 IP')
