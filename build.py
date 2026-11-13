# -*- coding: utf-8 -*-
"""SpiderLab 本地构建脚本（不部署到服务器）。

1. 从 lucide-static 生成 SVG symbol sprite（开源 ISC 图标库，零 emoji）
2. 本地化 Bootstrap 5 CSS（MIT）
3. 生成 favicon
4. 构建 Vue 3 教学站并复制产物
5. 打包 server/ 为 tar.gz
"""
import gzip
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
SERVER = ROOT / 'server'
ASSETS = SERVER / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)

# 仅保留服务端渲染页面实际引用的图标（Vue 教学站使用 lucide-vue-next，不依赖 sprite）。
# 精简后靶场 HTML 源码更干净，便于学员「查看网页源代码」练习。
ICONS = [
    'alert-triangle', 'arrow-right', 'bug', 'check-circle', 'chevron-right',
    'clock', 'code', 'flag', 'info', 'layers', 'lightbulb', 'list', 'lock',
    'send', 'shield-check', 'shield-x', 'target', 'unlock',
    # 少量常用备用
    'book-open', 'terminal', 'database', 'external-link', 'x-circle',
    'search', 'zap', 'filter',
]

ALIASES = {
    'unlock': 'lock-open',
    'home': 'house',
    'alert-triangle': 'triangle-alert',
    'shield-x': 'shield-x',
    'check-circle': 'circle-check',
    'x-circle': 'circle-x',
    'alert-circle': 'circle-alert',
    'globe-2': 'globe',
    'code-2': 'code-xml',
    'link-2': 'link',
    'table-2': 'table',
    'file-code': 'file-code-2',
    'file-json': 'file-json-2',
}


def find_icon(name):
    base = WEB / 'node_modules' / 'lucide-static' / 'icons'
    for candidate in (name, ALIASES.get(name, '')):
        if not candidate:
            continue
        fp = base / (candidate + '.svg')
        if fp.is_file():
            return fp
    return None


def build_sprite():
    symbols, missing = [], []
    for name in ICONS:
        fp = find_icon(name)
        if not fp:
            missing.append(name)
            continue
        text = fp.read_text(encoding='utf-8').strip()
        m = re.search(r'<svg[^>]*>(.*?)</svg>', text, re.S)
        if not m:
            missing.append(name)
            continue
        inner = m.group(1).strip()
        symbols.append(
            '<symbol id="i-%s" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round">%s</symbol>' % (name, inner))
    out = ('<svg xmlns="http://www.w3.org/2000/svg" '
           'style="position:absolute;width:0;height:0;overflow:hidden" '
           'aria-hidden="true">\n' + '\n'.join(symbols) + '\n</svg>\n')
    (ASSETS / 'lucide.svg').write_text(out, encoding='utf-8')
    print('[sprite] %d symbols -> assets/lucide.svg (%d bytes)'
          % (len(symbols), len(out.encode('utf-8'))))
    if missing:
        print('[sprite] skipped (not in lucide-static):', ', '.join(missing))

    # favicon 用 bug 图标
    bug = find_icon('bug')
    if bug:
        svg = bug.read_text(encoding='utf-8').strip()
        svg = svg.replace('<svg ', '<svg fill="#1a67c2" stroke="#ffffff" ', 1)
        svg = svg.replace('stroke="currentColor"', 'stroke="#ffffff"')
        (ASSETS / 'favicon.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" '
            'viewBox="0 0 24 24" fill="#1a67c2" stroke="#fff" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round">\n'
            + re.search(r'<svg[^>]*>(.*?)</svg>', svg, re.S).group(1).strip()
            + '\n</svg>\n', encoding='utf-8')
        print('[favicon] assets/favicon.svg')


LAB_CSS = """/* SpiderLab 靶场补充样式（Bootstrap 5 之上） */
.ico { display: inline-block; }
.sl-card a, .sl-tile a { text-decoration: none; }
.lab-table code { white-space: nowrap; }
.badge-lv .ico { vertical-align: -3px; }
@media print { header.sl, footer.sl, .lab-note { display: none; } }
"""


def copy_assets():
    src = WEB / 'node_modules' / 'bootstrap' / 'dist' / 'css' / 'bootstrap.min.css'
    if src.is_file():
        shutil.copy2(src, ASSETS / 'bootstrap.min.css')
        print('[css] bootstrap.min.css (%d bytes)' %
              (ASSETS / 'bootstrap.min.css').stat().st_size)
    else:
        print('[css] WARN: bootstrap.min.css not found')
    (ASSETS / 'lab.css').write_text(LAB_CSS, encoding='utf-8')
    print('[css] assets/lab.css')


def build_vue():
    print('[vue] vite build ...')
    r = subprocess.run(['npm', 'run', 'build'], cwd=str(WEB),
                       capture_output=True, text=True, shell=(os.name == 'nt'))
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-3000:])
        sys.exit('[vue] BUILD FAILED')
    print(r.stdout[-1200:])
    src = WEB / 'dist'
    dst = SERVER / 'dist'
    # 保留 pyodide/（15MB 运行时，下载一次即可复用），只替换前端产物
    if dst.exists():
        for child in list(dst.iterdir()):
            if child.name == 'pyodide':
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        dst.mkdir(parents=True)
    shutil.copytree(src, dst, dirs_exist_ok=True)
    # 把共享静态资源并入同一目录，Nginx 只需一条 location 即可服务全部静态文件
    (dst / 'assets').mkdir(parents=True, exist_ok=True)
    for f in ASSETS.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / 'assets' / f.name)

    # 主题层：SPA 打包进主 CSS，SSR 页单独引用这一份，保证两侧一致
    shutil.copy2(WEB / 'src' / 'theme.css', dst / 'assets' / 'theme.css')
    print('[theme] assets/theme.css (%d bytes)' %
          (dst / 'assets' / 'theme.css').stat().st_size)

    # 服务端渲染页的独立语法高亮脚本（IIFE，含常用语言）
    hl_out = dst / 'assets' / 'highlight.js'
    hr = subprocess.run(
        ['npx', 'esbuild', str(WEB / 'src' / 'hljs-standalone.js'),
         '--bundle', '--minify', '--format=iife', '--target=es2020',
         '--outfile=' + str(hl_out)],
        cwd=str(WEB), capture_output=True, text=True, shell=(os.name == 'nt'))
    if hr.returncode != 0 or not hl_out.is_file():
        print(hr.stdout[-1500:])
        print(hr.stderr[-1500:])
        sys.exit('[highlight] esbuild 打包失败')
    print('[highlight] assets/highlight.js (%d bytes)' % hl_out.stat().st_size)

    files = [f for f in dst.rglob('*') if f.is_file() and 'pyodide' not in f.parts]
    print('[vue] copied %d frontend files to server/dist' % len(files))
    for f in sorted(files):
        print('       ', f.relative_to(dst), f.stat().st_size)


def precompress():
    """为 Pyodide 运行时生成 .gz，配合 Nginx 的 gzip_static 直接下发压缩文件。

    pyodide.asm.wasm 有 9.2MB，在 4Mbps 出网带宽下要 18 秒才能下完；
    预压缩后约 3MB，首屏加载时间直接砍掉三分之二。
    只处理 .wasm / .mjs：.zip 和 .whl 本身就是压缩容器，再压收益很小。
    """
    base = SERVER / 'dist' / 'pyodide'
    if not base.exists():
        print('[gzip] 跳过：没有 dist/pyodide')
        return
    raw_total = gz_total = 0
    count = 0
    for f in sorted(base.rglob('*')):
        if not f.is_file() or f.suffix not in ('.wasm', '.mjs') or f.stat().st_size < 8192:
            continue
        gz = f.with_name(f.name + '.gz')
        if gz.exists() and gz.stat().st_mtime >= f.stat().st_mtime:
            raw_total += f.stat().st_size
            gz_total += gz.stat().st_size
            count += 1
            continue
        data = f.read_bytes()
        # mtime=0 让产物可复现（同样的输入永远得到同样的字节）
        with open(gz, 'wb') as fh:
            with gzip.GzipFile(filename='', mode='wb', fileobj=fh, compresslevel=9, mtime=0) as gz_fh:
                gz_fh.write(data)
        raw_total += len(data)
        gz_total += gz.stat().st_size
        count += 1
    if raw_total:
        print('[gzip] %d 个文件 %.1f MB -> %.1f MB (省 %.0f%%)' % (
            count, raw_total / 1048576, gz_total / 1048576,
            100 * (1 - gz_total / raw_total)))


def make_tarball():
    out = ROOT / 'spiderlab.tar.gz'
    if out.exists():
        out.unlink()

    def _skip(ti):
        if '__pycache__' in ti.name or ti.name.endswith('.pyc'):
            return None
        return ti

    with tarfile.open(out, 'w:gz', compresslevel=9) as tf:
        tf.add(SERVER, arcname='spiderlab', filter=_skip)
    print('[tar] %s (%d bytes)' % (out.name, out.stat().st_size))


if __name__ == '__main__':
    build_sprite()
    copy_assets()
    build_vue()
    import prepare_pyodide
    prepare_pyodide.main()
    precompress()
    make_tarball()
    print('\nBUILD OK ->', ROOT / 'spiderlab.tar.gz')
