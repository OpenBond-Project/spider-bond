# -*- coding: utf-8 -*-
"""提交前的敏感信息审计。

三种扫描范围，覆盖不同的泄漏途径：

    python audit.py             只扫 git 已跟踪的文件（提交前跑这个）
    python audit.py --all       扫整个工作区（更慢，能发现还没 git add 的）
    python audit.py --history   扫 git 历史里的每个 blob（最关键，见下）

为什么要扫历史：文件被删除后内容仍留在历史对象里，`git ls-files` 看不到，
但任何人 clone 下来都能 `git log` 翻出来。这是密钥泄漏最常见的盲区。

输出一律掩码，避免把密钥再打印一遍到终端或日志里。
"""
import os
import re
import subprocess
import sys

PATTERNS = [
    ('Cloudflare Token', r'cfat_[A-Za-z0-9_-]{10,}'),
    ('GitHub OAuth ID', r'Ov23li[A-Za-z0-9]{10,}'),
    ('GitHub Token', r'gh[pousr]_[A-Za-z0-9]{30,}'),
    ('私钥', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    ('云厂商 Key', r'(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})'),
    ('JWT', r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
    ('Bearer Token', r'Bearer\s+[A-Za-z0-9._-]{20,}'),
    ('公网 IPv4', r'\b(?!127\.0\.0\.1)(?!0\.0\.0\.0)'
                 r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'),
    ('邮箱地址', r'[\w.+-]+@[\w-]+\.[\w.]{2,}'),
]

# 二进制文件会匹配出无意义的乱码，跳过（它们本来也不该含密钥）
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.mp4', '.pdf', '.zip', '.gz',
            '.wasm', '.whl', '.ico', '.woff', '.woff2', '.ttf', '.svg'}

SKIP_DIRS = {'node_modules', 'dist', '.git', '__pycache__', '.venv', 'venv'}


def mask(s):
    return s[:6] + '***' + s[-3:] if len(s) > 10 else s[:3] + '***'


def scan_text(text, label):
    hits = []
    for name, pat in PATTERNS:
        for m in re.finditer(pat, text):
            line = text[:m.start()].count('\n') + 1
            hits.append((name, label, line, mask(m.group(0))))
    return hits


def iter_files(scope):
    """产出 (可读路径, 显示名)。"""
    if scope == 'staged':
        out = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
        for f in out.stdout.split('\n'):
            if f:
                yield f, f
        return
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            p = os.path.join(root, fn)
            yield p, p.replace(os.sep, '/').lstrip('./')


def scan_files(scope):
    hits = []
    count = 0
    for path, label in iter_files(scope):
        ext = os.path.splitext(path)[1].lower()
        if ext in SKIP_EXT:
            continue
        try:
            if os.path.getsize(path) > 3_000_000:
                continue
            text = open(path, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        count += 1
        hits.extend(scan_text(text, label))
    return hits, count


def scan_history():
    """遍历所有 history blob。必须用字节模式读，否则遇到二进制会解码失败。"""
    listing = subprocess.run(['git', 'rev-list', '--objects', '--all'],
                             capture_output=True, text=True).stdout.strip().split('\n')
    blobs = {}
    for line in listing:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            blobs.setdefault(parts[0], parts[1])

    hits = []
    for oid, path in blobs.items():
        r = subprocess.run(['git', 'cat-file', '-p', oid], capture_output=True)
        if r.returncode != 0 or not r.stdout:
            continue
        raw = r.stdout
        if len(raw) > 1_500_000:
            continue
        hits.extend(scan_text(raw.decode('utf-8', 'ignore'), path))
    return hits, len(blobs)


def main():
    scope = 'staged'
    if '--all' in sys.argv:
        scope = 'all'
    if '--history' in sys.argv:
        scope = 'history'

    if scope == 'history':
        hits, n = scan_history()
        print('已扫描 %d 个历史对象\n' % n)
    else:
        hits, n = scan_files(scope)
        print('已扫描 %d 个文本文件（范围：%s）\n'
              % (n, '工作区' if scope == 'all' else 'git 已跟踪'))

    if hits:
        seen = set()
        by_kind = {}
        for name, path, line, val in hits:
            key = (name, path, val)
            if key in seen:
                continue
            seen.add(key)
            by_kind.setdefault(name, []).append((path, line, val))
        for name, items in by_kind.items():
            print('=== %s（%d 处）===' % (name, len(items)))
            for path, line, val in items:
                print('  %-40s L%-5s %s' % (path[:40], line, val))
            print()

    print('=' * 58)
    if not hits:
        print('通过：未发现密钥或隐私信息')
        return 0
    print('发现 %d 处，逐条确认后再提交' % len(set((h[0], h[1], h[3]) for h in hits)))
    return 1


if __name__ == '__main__':
    sys.exit(main())
