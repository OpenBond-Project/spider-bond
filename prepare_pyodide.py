# -*- coding: utf-8 -*-
"""把 Pyodide 运行时与爬虫教学所需包本地化到 server/dist/pyodide/。

运行时不依赖任何外部 CDN：Worker 用 indexURL='/pyodide/' 加载核心，
loadPackage() 按 pyodide-lock.json 的 file_name 从同目录取 wheel。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'web' / 'node_modules' / 'pyodide'
DST = ROOT / 'server' / 'dist' / 'pyodide'

CORE = [
    'pyodide.js', 'pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
    'python_stdlib.zip', 'pyodide-lock.json',
]
# 教学代码会用到的包；依赖由 lock 递归展开
ROOTS = ['requests', 'lxml', 'beautifulsoup4', 'cssselect', 'pyodide-http']


def main():
    if not (SRC / 'pyodide-lock.json').is_file():
        sys.exit('pyodide npm 包未安装，请先 npm install pyodide')
    DST.mkdir(parents=True, exist_ok=True)

    ver = json.loads((SRC / 'package.json').read_text(encoding='utf-8'))['version']
    base = 'https://cdn.jsdelivr.net/pyodide/v%s/full/' % ver
    print('[pyodide] version', ver, '->', DST)

    for f in CORE:
        s = SRC / f
        if not s.is_file():
            sys.exit('缺少核心文件: ' + f)
        shutil.copy2(s, DST / f)
        print('  core  %-24s %8d B' % (f, s.stat().st_size))

    lock = json.loads((SRC / 'pyodide-lock.json').read_text(encoding='utf-8'))
    packages = lock['packages']
    need = set()

    def add(name):
        if name in need or name not in packages:
            return
        need.add(name)
        for dep in packages[name].get('depends', []):
            add(dep)

    for r in ROOTS:
        add(r)
    print('[pyodide] 需要 %d 个包: %s' % (len(need), ', '.join(sorted(need))))

    for name in sorted(need):
        fn = packages[name]['file_name']
        out = DST / fn
        if out.is_file() and out.stat().st_size > 0:
            print('  have  %-52s %8d B' % (fn, out.stat().st_size))
            continue
        url = base + fn
        r = subprocess.run(['curl', '-fsSL', '--max-time', '120', url, '-o', str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not out.is_file() or out.stat().st_size == 0:
            print('  FAIL  %s -> %s' % (fn, r.stderr[-200:]))
            out.unlink(missing_ok=True)
            sys.exit('下载失败: ' + url)
        print('  get   %-52s %8d B' % (fn, out.stat().st_size))

    total = sum(f.stat().st_size for f in DST.iterdir() if f.is_file())
    print('[pyodide] OK, 共 %.2f MB' % (total / 1024 / 1024))


if __name__ == '__main__':
    main()
