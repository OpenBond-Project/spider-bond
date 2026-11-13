# 生成社交分享封面 og-cover.png（1200x630）
#
# 只在需要改封面时手动运行：python make_og.py
# 依赖 Pillow + svglib + rlPyCairo（仅构建期需要，服务端运行时仍只用标准库）。
#   pip install pillow svglib reportlab rlPyCairo
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG_TOP = (13, 22, 36)
BG_BOTTOM = (22, 38, 60)
ORANGE = (224, 108, 66)
INK = (240, 245, 252)
MUTED = (150, 168, 190)

FONT_DIR = r"C:\Windows\Fonts"
BOLD = os.path.join(FONT_DIR, "msyhbd.ttc")
REG = os.path.join(FONT_DIR, "msyh.ttc")
LOGO_SVG = os.path.join("server", "assets", "bond-logo.svg")


def font(size, bold=False):
    for path in ([BOLD, REG] if bold else [REG, BOLD]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def load_logo(target_h):
    """把 SVG 标渲染成位图，并把白底转为透明。

    renderPM 输出的是白底 RGB；直接贴到深色封面上会带一圈白边。
    这里按「logo 色 = 橙色基准、其余 = 白底」的假设反预乘：
        p = a * C + (1 - a) * 255
    用绿通道求解 a（logo 的绿通道约 113，白底是 255），再反解出纯色 C。
    """
    from reportlab.graphics import renderPM
    from svglib.svglib import svg2rlg

    tmp = "logo_render_tmp.png"
    renderPM.drawToFile(svg2rlg(LOGO_SVG), tmp, fmt="PNG", dpi=300)
    im = Image.open(tmp).convert("RGB")
    px = im.load()
    w, h = im.size

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    base_g = 113.0  # logo 色的绿通道基准
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            a = (255.0 - g) / (255.0 - base_g)
            if a <= 0.004:
                continue
            a = min(1.0, a)
            # 反预乘，去掉混入的白，边缘在深色上才干净
            rr = (r - (1 - a) * 255) / a if a > 0 else r
            bb = (b - (1 - a) * 255) / a if a > 0 else b
            op[x, y] = (max(0, min(255, int(rr))),
                        max(0, min(255, int(g))),
                        max(0, min(255, int(bb))),
                        int(a * 255))

    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    scale = target_h / out.height
    out = out.resize((max(1, int(out.width * scale)), target_h), Image.LANCZOS)
    os.remove(tmp)
    return out


def vgradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return img.resize((w, h), Image.BILINEAR)


img = vgradient((W, H), BG_TOP, BG_BOTTOM).convert("RGBA")

# 细网格
grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
for x in range(0, W, 40):
    gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
for y in range(0, H, 40):
    gd.line([(0, y), (W, y)], fill=(255, 255, 255, 8), width=1)
img = Image.alpha_composite(img, grid)

# 右侧蜘蛛网装饰
web = Image.new("RGBA", (W, H), (0, 0, 0, 0))
wd = ImageDraw.Draw(web)
cx, cy, R = 1010, 300, 330
for i in range(14):
    a = 2 * math.pi * i / 14
    wd.line([(cx, cy), (cx + R * math.cos(a), cy + R * math.sin(a))],
            fill=(255, 255, 255, 20), width=1)
for r in range(1, 7):
    rr = R * r / 7
    pts = [(cx + rr * math.cos(2 * math.pi * i / 14),
            cy + rr * math.sin(2 * math.pi * i / 14)) for i in range(14)]
    wd.line(pts + [pts[0]],
            fill=(255, 255, 255, 20) if r % 2 else (255, 255, 255, 30), width=1)
img = Image.alpha_composite(img, web)

# Bond 标（替代原来的左侧色条）
logo = load_logo(84)
img.alpha_composite(logo, (108, 84))

d = ImageDraw.Draw(img)

# 品牌小字：与 logo 垂直居中对齐
d.text((108 + logo.width + 22, 84 + 84 // 2 - 15), "OPENBOND PROJECT",
       font=font(22, True), fill=MUTED)

# 主标题
d.text((106, 206), "Spider", font=font(96, True), fill=INK)
sb = d.textbbox((0, 0), "Spider ", font=font(96, True))
d.text((108 + sb[2] - sb[0] - 4, 206), "Bond", font=font(96, True), fill=ORANGE)

# 副标题
d.text((108, 336), "Python 爬虫实训平台", font=font(44, True), fill=INK)

# 说明
d.text((110, 404), "在真实服务器上练，不在模拟环境里猜", font=font(26), fill=MUTED)

# 特性标签
tags = ["20 节系统课程", "36 关在线实战", "15 个靶站"]
x = 108
for text in tags:
    f = font(22, True)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    pw = tw + 34
    d.rounded_rectangle([x, 472, x + pw, 472 + 44], radius=22,
                        outline=(255, 255, 255, 46), width=1)
    d.text((x + 17, 472 + 22 - th / 2 - 4), text, font=f, fill=(206, 218, 232))
    x += pw + 14

# 底部域名
d.text((108, 556), "spider.skkk.uno", font=font(22, True), fill=(126, 146, 170))

out = os.path.join("server", "assets", "og-cover.png")
img.convert("RGB").save(out, "PNG", optimize=True)
print("已生成 %s  (%d x %d, %d KB)" % (out, W, H, os.path.getsize(out) // 1024))
