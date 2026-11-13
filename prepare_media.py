# -*- coding: utf-8 -*-
"""生成靶站用的媒体与文件资源（图片 / 视频 / PDF / CSV / JSON / ZIP）。

为什么要自己造：学员练「提取图片链接」「下载文件」「抓视频直链」时需要真实的
响应，而不是占位符。这些资源全部是合成的，不含任何版权素材。

产物写进 server/media/，由 build.py 复制到 dist/media/，
线上经 /media/ 路径访问（Nginx 直接服务，Python 有兜底路由）。

只在资源需要更新时手动运行：python prepare_media.py
依赖 Pillow（图片）、ffmpeg（视频）、reportlab（PDF）。
"""
import os
import random
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join('server', 'media')
FONT_DIR = r'C:\Windows\Fonts'
BOLD = os.path.join(FONT_DIR, 'msyhbd.ttc')
REG = os.path.join(FONT_DIR, 'msyh.ttc')

# 6 个主题色，对应图库里的 6 组照片
THEMES = [
    ('海港晨雾', (26, 103, 194), (120, 190, 235)),
    ('老街黄昏', (194, 84, 47), (240, 176, 120)),
    ('山谷雨后', (32, 122, 92), (140, 210, 170)),
    ('夜市灯河', (86, 58, 140), (180, 150, 230)),
    ('沙丘正午', (176, 128, 32), (240, 210, 140)),
    ('雪原破晓', (60, 78, 100), (200, 215, 230)),
]


def font(size, bold=True):
    for p in ([BOLD, REG] if bold else [REG, BOLD]):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def make_photo(w, h, c1, c2, idx, title):
    """画一张有层次的抽象风景图：渐变天空 + 地平线 + 若干几何剪影。"""
    img = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(
            int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)))

    rnd = random.Random(1000 + idx)
    horizon = int(h * 0.62)
    # 远山
    for layer in range(3):
        pts = [(0, horizon + layer * h * 0.05)]
        x = 0
        while x < w:
            x += rnd.randint(w // 8, w // 4)
            pts.append((min(x, w), horizon + layer * h * 0.05
                        - rnd.randint(0, int(h * 0.12))))
        pts.append((w, h))
        pts.append((0, h))
        shade = tuple(max(0, int(c1[i] * (0.75 - layer * 0.12))) for i in range(3))
        d.polygon(pts, fill=shade)
    # 前景剪影
    for _ in range(6):
        bx = rnd.randint(0, w)
        bw = rnd.randint(w // 20, w // 9)
        bh = rnd.randint(h // 6, h // 3)
        d.rectangle([bx, h - bh, bx + bw, h], fill=(20, 26, 34))

    d.text((int(w * 0.05), int(h * 0.06)), title, font=font(max(16, w // 34)),
           fill=(255, 255, 255))
    return img


def make_poster(w, h, c1, c2, title, sub):
    img = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(img)
    for i in range(h):
        t = i / max(1, h - 1)
        d.line([(0, i), (w, i)], fill=tuple(
            int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)))
    d.text((int(w * 0.08), int(h * 0.32)), title, font=font(max(20, w // 22)),
           fill=(255, 255, 255))
    d.text((int(w * 0.08), int(h * 0.32) + max(30, w // 12)), sub,
           font=font(max(12, w // 46), bold=False), fill=(235, 240, 248))
    return img


def build_images():
    print('[图片] 生成图库')
    for i, (title, c1, c2) in enumerate(THEMES, 1):
        full = make_photo(1200, 800, c1, c2, i, title)
        full.save(os.path.join(OUT, 'photo-%02d.jpg' % i), 'JPEG', quality=86,
                  optimize=True)
        # 中图：srcset 的中间档
        mid = make_photo(600, 400, c1, c2, i, title)
        mid.save(os.path.join(OUT, 'photo-%02d-600.jpg' % i), 'JPEG', quality=84,
                 optimize=True)
        # 缩略图：列表页用，原图在详情页
        thumb = full.resize((240, 160), Image.LANCZOS)
        thumb.save(os.path.join(OUT, 'thumb-%02d.jpg' % i), 'JPEG', quality=82,
                   optimize=True)

    poster = make_poster(960, 540, (18, 56, 110), (26, 103, 194),
                         'Spider Bond', '教学视频 · 合成素材')
    poster.save(os.path.join(OUT, 'video-poster.jpg'), 'JPEG', quality=86,
                optimize=True)

    # 头像：8 张纯色圆形，练「批量下载图片」很有用
    for i in range(1, 9):
        av = Image.new('RGB', (120, 120), THEMES[(i - 1) % 6][1])
        d = ImageDraw.Draw(av)
        d.ellipse([0, 0, 119, 119], fill=THEMES[(i - 1) % 6][2])
        d.text((44, 44), str(i), font=font(40), fill=(255, 255, 255))
        av.save(os.path.join(OUT, 'avatar-%02d.png' % i), 'PNG', optimize=True)


def build_videos():
    if not shutil.which('ffmpeg'):
        print('[视频] 跳过：找不到 ffmpeg')
        return
    print('[视频] 用 ffmpeg 合成 MP4')
    specs = [
        ('clip-01.mp4', 640, 360, 'testsrc2', 4),
        ('clip-02.mp4', 480, 270, 'smptebars', 3),
    ]
    for name, w, h, src, dur in specs:
        path = os.path.join(OUT, name)
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error',
            '-f', 'lavfi', '-i', '%s=duration=%d:size=%dx%d:rate=12'
            % (src, dur, w, h),
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
            '-c:v', 'libx264', '-crf', '32', path,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print('  失败 %s: %s' % (name, (r.stderr or '')[:120]))
        else:
            print('  %-14s %6.1f KB' % (name, os.path.getsize(path) / 1024))


def build_files():
    print('[文件] 生成 PDF / CSV / JSON / ZIP')

    # CSV：书籍数据，和 /lab/books 靶站同一套字段
    rows = [
        ('1', '深入理解计算机系统', 'Randal Bryant', '机械工业出版社', '139.00', '9.2'),
        ('2', 'Python 编程：从入门到实践', 'Eric Matthes', '人民邮电出版社', '89.80', '9.0'),
        ('3', '数据密集型应用系统设计', 'Martin Kleppmann', '中国电力出版社', '128.00', '9.4'),
        ('4', 'HTTP 权威指南', 'David Gourley', '人民邮电出版社', '109.00', '8.8'),
        ('5', '流畅的 Python', 'Luciano Ramalho', '人民邮电出版社', '139.00', '9.1'),
        ('6', '算法（第 4 版）', 'Robert Sedgewick', '人民邮电出版社', '99.00', '9.3'),
        ('7', '计算机网络：自顶向下方法', 'James Kurose', '机械工业出版社', '89.00', '9.2'),
        ('8', '重构：改善既有代码的设计', 'Martin Fowler', '人民邮电出版社', '118.00', '9.1'),
    ]
    with open(os.path.join(OUT, 'books-export.csv'), 'w', encoding='utf-8-sig',
              newline='') as f:
        f.write('id,title,author,publisher,price,rating\n')
        for r in rows:
            f.write(','.join(r) + '\n')

    # JSON：结构化条目
    import json as _json
    data = {
        'source': 'Spider Bond 示例数据集',
        'generated': '2026-11-13',
        'count': len(rows),
        'books': [
            {'id': int(r[0]), 'title': r[1], 'author': r[2],
             'publisher': r[3], 'price': float(r[4]), 'rating': float(r[5])}
            for r in rows
        ],
    }
    with open(os.path.join(OUT, 'books-export.json'), 'w', encoding='utf-8') as f:
        _json.dump(data, f, ensure_ascii=False, indent=2)

    # PDF：讲义
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as _canvas

        pdf = os.path.join(OUT, 'crawler-handbook.pdf')
        c = _canvas.Canvas(pdf, pagesize=A4)
        w, h = A4
        c.setFont('Helvetica-Bold', 20)
        c.drawString(60, h - 90, 'Spider Bond')
        c.setFont('Helvetica', 12)
        c.drawString(60, h - 115, 'Crawler Practice Handbook (synthetic sample)')
        c.setFont('Helvetica', 10)
        lines = [
            'This PDF exists so that crawlers can practise file downloads:',
            'checking Content-Type, reading Content-Disposition, and saving',
            'the response body to disk without corrupting binary data.',
            '',
            '1. Always send a User-Agent that identifies you.',
            '2. Respect robots.txt and Crawl-delay.',
            '3. Do not hammer a server; back off on 429 / 503.',
            '4. Only collect data you are allowed to collect.',
            '',
            'Sample dataset rows: %d' % len(rows),
        ]
        y = h - 150
        for ln in lines:
            c.drawString(60, y, ln)
            y -= 18
        c.setFont('Helvetica-Oblique', 9)
        c.drawString(60, 80, 'Generated for teaching purposes. No real personal data.')
        c.showPage()
        c.save()
    except ImportError:
        print('  跳过 PDF：reportlab 不可用')

    # 字幕轨道：视频页的 <track src> 指向它，练「抓字幕文件」用
    for name in ('clip-01', 'clip-02'):
        with open(os.path.join(OUT, '%s.vtt' % name), 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n\n'
                    '00:00:00.000 --> 00:00:02.000\n'
                    '这是合成素材，用于练习视频字幕轨道抓取。\n\n'
                    '00:00:02.000 --> 00:00:04.000\n'
                    '字幕文件本身就是纯文本，注意 Content-Type 是 text/vtt。\n')

    # ZIP：打包上面几个
    zpath = os.path.join(OUT, 'datasets.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in ('books-export.csv', 'books-export.json'):
            p = os.path.join(OUT, n)
            if os.path.exists(p):
                z.write(p, arcname=n)


def main():
    os.makedirs(OUT, exist_ok=True)
    build_images()
    build_videos()
    build_files()
    total = 0
    files = 0
    for n in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, n)
        if os.path.isfile(p):
            total += os.path.getsize(p)
            files += 1
    print('\n完成：%d 个文件，共 %.1f MB -> %s' % (files, total / 1048576, OUT))


if __name__ == '__main__':
    main()
