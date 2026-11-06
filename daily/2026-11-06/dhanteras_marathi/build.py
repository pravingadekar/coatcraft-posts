"""Dhanteras 2026 Marathi wish reel (25s, 1080x1920): diya on a glossy floor, synced to the ElevenLabs voice.

    python build.py --still 3,6,10,16,20,24     preview frames in the cache folder
    python build.py                             full render to reel.mp4

Needs: Pillow, ffmpeg on PATH, Microsoft Edge (only to shape the Devanagari text into PNG layers).
CACHE (env DHANTERAS_CACHE, default ./_cache) holds the text layers, preview frames and music.
"""
import array
import math
import os
import random
import subprocess
import sys
import wave

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CACHE = os.environ.get("DHANTERAS_CACHE") or os.path.join(HERE, "_cache")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
VOICE = os.path.join(HERE, "voice_prajakta.mp3")
OUT = os.path.join(HERE, "reel.mp4")

W, H, FPS = 1080, 1920, 30
LENGTH = 25.0
LEAD = 0.4  # voice starts this long after frame 0
HORIZON = 1290
CX = 540

GOLD = "background:linear-gradient(180deg,#fff4c9 10%,#f8c95c 55%,#e0932a 95%);-webkit-background-clip:text;" \
       "background-clip:text;color:transparent;filter:drop-shadow(0 4px 10px rgba(0,0,0,.65));"
CREAM = "color:#fff1d6;filter:drop-shadow(0 3px 8px rgba(0,0,0,.8));"

# id: (top y, font css, style, lines)
TEXT = {
    "t1": (330, "700 116px 'Tiro Devanagari Marathi'", GOLD, ["धनत्रयोदशीच्या", "मंगल दिवशी"]),
    "w1": (280, "700 128px 'Tiro Devanagari Marathi'", GOLD, ["सुख"]),
    "w2": (460, "700 128px 'Tiro Devanagari Marathi'", GOLD, ["समृद्धी"]),
    "w3": (640, "700 128px 'Tiro Devanagari Marathi'", GOLD, ["आरोग्य"]),
    "t2": (270, "700 104px 'Tiro Devanagari Marathi'", GOLD, ["धन्वंतरी आणि", "लक्ष्मीमातेचा", "आशीर्वाद"]),
    "t3": (390, "700 100px 'Tiro Devanagari Marathi'", CREAM, ["प्रत्येक नव्या", "सुरुवातीला"]),
    "t3a": (340, "700 124px 'Tiro Devanagari Marathi'", GOLD, ["मजबूत पाया"]),
    "t3b": (560, "700 112px 'Tiro Devanagari Marathi'", GOLD, ["उज्ज्वल भविष्य"]),
    "t4": (462, "600 54px 'Tiro Devanagari Marathi'", CREAM, ["परिवाराकडून"]),
    "t5": (548, "600 50px 'Tiro Devanagari Marathi'", CREAM, ["आपल्याला आणि आपल्या कुटुंबाला"]),
    "t6": (640, "700 100px 'Tiro Devanagari Marathi'", GOLD, ["धनत्रयोदशीच्या", "हार्दिक शुभेच्छा!"]),
}
PHONE_HTML = """<div style="position:absolute;left:150px;top:1390px;width:780px;box-sizing:border-box;padding:20px 0 24px;
text-align:center;border-radius:30px;background:rgba(18,4,12,.82);border:2px solid rgba(240,190,90,.75);
font-family:Poppins;color:#fff1d6;">
<div style="font:500 34px Poppins">Call / WhatsApp</div>
<div style="font:700 68px Poppins;color:#f8c95c;line-height:1.2">+91 77458 89111</div>
<div style="font:500 32px Poppins">www.coatcraftsolutions.com</div></div>"""


def html_page(body):
    fonts = os.path.join(ROOT, "brand", "fonts").replace("\\", "/")
    return f"""<!doctype html><html lang="mr"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Tiro+Devanagari+Marathi&display=block" rel="stylesheet">
<style>
@font-face{{font-family:Poppins;font-weight:500;src:url('file:///{fonts}/Poppins-Medium.ttf')}}
@font-face{{font-family:Poppins;font-weight:700;src:url('file:///{fonts}/Poppins-Bold.ttf')}}
html,body{{margin:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden}}
</style></head><body>{body}</body></html>"""


def text_layers():
    """Render each text block in Edge (it shapes Devanagari properly; Pillow here has no raqm)."""
    folder = os.path.join(CACHE, "text")
    os.makedirs(folder, exist_ok=True)
    pages = {"phone": PHONE_HTML}
    for key, (top, fnt, style, lines) in TEXT.items():
        # inline-block with generous padding: background-clip:text otherwise cuts off the top matras and reph
        rows = "".join(f'<div><span style="{style}display:inline-block;padding:.5em 30px .35em;'
                       f'margin:-.5em 0 -.35em;">{ln}</span></div>' for ln in lines)
        pages[key] = (f'<div lang="mr" style="position:absolute;left:0;top:{top}px;width:{W}px;text-align:center;'
                      f'font:{fnt};line-height:1.42;">{rows}</div>')
    layers = {}
    for key, body in pages.items():
        png = os.path.join(folder, f"{key}.png")
        if not os.path.exists(png):
            page = os.path.join(folder, f"{key}.html")
            with open(page, "w", encoding="utf-8") as f:
                f.write(html_page(body))
            subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--user-data-dir={os.path.join(CACHE, 'edge')}", f"--window-size={W},{H}",
                            "--force-device-scale-factor=1", "--default-background-color=00000000",
                            "--allow-file-access-from-files", "--virtual-time-budget=6000",
                            f"--screenshot={png}", "file:///" + page.replace("\\", "/")],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        img = Image.open(png).convert("RGBA")
        box = img.getbbox()
        if not box:
            sys.exit(f"text layer {key} rendered empty")
        layers[key] = (img.crop(box), box[0], box[1])
    return layers


def radial(size, power=1.0, peak=255):
    """Soft white disc mask: peak in the middle, 0 at the rim."""
    # PIL's gradient only reaches about 181 at the square's edge, so scale it to hit 0 there (no visible box)
    mask = Image.radial_gradient("L").point(lambda g: int(peak * max(0.0, 1 - g / 178) ** power))
    return mask.resize((size, size), Image.BICUBIC)


def vgrad(w, h, a, b):
    """Vertical RGB gradient from colour a (top) to b (bottom)."""
    img = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        img.putpixel((0, y), tuple(int(p + (q - p) * t) for p, q in zip(a, b)))
    return img.resize((w, h))


def make_background():
    deep, wine = Image.new("RGB", (W, H), (14, 3, 10)), Image.new("RGB", (W, H), (84, 18, 46))
    mask = radial(2300, 1.5).crop((1150 - CX, 1150 - 1020, 1150 - CX + W, 1150 - 1020 + H))
    return Image.composite(wine, deep, mask)


def make_mandala():
    size = 1000
    s = size * 2
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = s / 2
    gold, pink = (236, 190, 110, 150), (214, 70, 120, 135)

    def ring(radius, col, width=3):
        d.ellipse([c - radius, c - radius, c + radius, c + radius], outline=col, width=width)

    def petal(angle, r0, r1, half, col, width=4):
        pts = []
        for i in range(25):
            t = i / 24
            pts.append((r0 + (r1 - r0) * t, half * math.sin(math.pi * t)))
        for j in range(24, -1, -1):
            t = j / 24
            pts.append((r0 + (r1 - r0) * t, -half * math.sin(math.pi * t)))
        ca, sa = math.cos(angle), math.sin(angle)
        d.line([(c + x * ca - y * sa, c + x * sa + y * ca) for x, y in pts], fill=col, width=width)

    for r, col in ((300, gold), (470, pink), (660, gold), (770, gold)):
        ring(r, col)
    for i in range(16):
        petal(2 * math.pi * i / 16, 300, 470, 52, pink)
    for i in range(24):
        a = 2 * math.pi * i / 24
        petal(a, 480, 650, 50, gold)
        d.ellipse([c + 715 * math.cos(a) - 7, c + 715 * math.sin(a) - 7,
                   c + 715 * math.cos(a) + 7, c + 715 * math.sin(a) + 7], fill=(255, 220, 150, 190))
    for i in range(32):
        petal(2 * math.pi * (i + .5) / 32, 775, 950, 42, (236, 190, 110, 120))
    return img.resize((size, size), Image.LANCZOS)


def make_diya(width):
    s = 3
    w, h = width * s, int(width * 0.44) * s
    rim_h = int(h * 0.36)
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, -int(h * 0.62), w, h], fill=255)
    md.rectangle([0, 0, w, rim_h // 2], fill=0)
    md.ellipse([0, 0, w, rim_h], fill=255)
    body = vgrad(w, h, (246, 170, 84), (92, 34, 16)).convert("RGBA")
    side = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h))
    shade = side.point(lambda v: int(120 * abs(v - 128) / 128))
    body = Image.composite(Image.new("RGBA", (w, h), (40, 10, 4, 255)), body, shade)
    d = ImageDraw.Draw(body)
    # pearls and a gold band under the rim
    for i in range(1, 22):
        t = i / 22
        x = w * t
        y = rim_h * .5 + (h * .42) * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2))
        r = w * 0.0075
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 236, 190, 255))
    d.ellipse([0, 0, w, rim_h], fill=(250, 196, 112, 255))
    d.ellipse([w * .035, rim_h * .13, w * .965, rim_h * .9], fill=(58, 20, 8, 255))
    d.ellipse([w * .08, rim_h * .3, w * .92, rim_h * .9], fill=(112, 58, 14, 255))
    d.line([(w * .5, rim_h * .62), (w * .5, rim_h * .2)], fill=(255, 244, 220, 255), width=int(w * .012))
    body.putalpha(mask)
    return body.resize((w // s, h // s), Image.LANCZOS)


def make_flames(fw, fh, count=24):
    """Looping flame variants; the base of the flame sits at the bottom centre of the sprite."""
    frames = []
    s = 2
    layers = (((255, 112, 16), 1.0, 1.0), ((255, 176, 44), .74, .86), ((255, 232, 150), .46, .66),
              ((255, 252, 232), .24, .44))
    for n in range(count):
        ph = 2 * math.pi * n / count
        sway = .16 * math.sin(ph) + .06 * math.sin(3 * ph + 1)
        tall = 1 + .06 * math.sin(2 * ph + .7)
        img = Image.new("RGBA", (fw * s, fh * s), (0, 0, 0, 0))
        for col, ws, hs in layers:
            part = Image.new("L", img.size, 0)
            pts_r, pts_l = [], []
            for i in range(41):
                t = i / 40
                half = fw * s * .29 * ws * math.sin(math.pi * t ** .62) ** 1.1
                cx = fw * s / 2 + fw * s * sway * t ** 1.8
                y = fh * s * (1 - t * .9 * hs * tall) - 6
                pts_r.append((cx + half, y))
                pts_l.append((cx - half, y))
            ImageDraw.Draw(part).polygon(pts_r + pts_l[::-1], fill=255)
            part = part.filter(ImageFilter.GaussianBlur(5 * s * (.45 + ws * .5)))
            img.paste(Image.new("RGBA", img.size, col + (255,)), (0, 0), part)
        frames.append(img.resize((fw, fh), Image.LANCZOS))
    return frames


def make_floor(diya, diya_xy, small, small_spots):
    h = H - HORIZON
    floor = vgrad(W, h, (62, 18, 36), (8, 2, 6)).convert("RGB")
    d = ImageDraw.Draw(floor, "RGBA")
    for i in range(-10, 11):  # seamless-floor sheen lines running to the vanishing point
        d.line([(CX + i * 24, 0), (CX + i * 210, h)], fill=(255, 190, 130, 12), width=2)
    glow = radial(1200, 1.5, 120).resize((1200, 520))
    warm = Image.new("RGB", glow.size, (255, 132, 44))
    layer = Image.new("RGB", (W, h))
    layer.paste(warm, (CX - 600, -150), glow)
    floor = ImageChops.add(floor, layer)
    # the diya's mirror image: this is the glossy floor doing its job
    fade = Image.linear_gradient("L").resize((W, h)).point(lambda v: max(0, 150 - v * 2))
    refl = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    flip = diya.transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(2.2))
    refl.paste(flip, (diya_xy[0], diya_xy[1] + diya.height - HORIZON - 18), flip)
    refl.putalpha(ImageChops.multiply(refl.getchannel("A"), fade))
    floor = floor.convert("RGBA")
    floor.alpha_composite(refl)
    d = ImageDraw.Draw(floor)
    d.line([(0, 0), (W, 0)], fill=(255, 180, 120, 70), width=2)
    return floor


def make_toran():
    h = 300
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    rnd = random.Random(7)

    def flower(x, y, r):
        s = 4
        size = int(r * 2.5) * s
        f = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        fd = ImageDraw.Draw(f)
        c = size / 2
        col = rnd.choice(((255, 150, 24), (255, 176, 28), (249, 126, 18)))
        for rr, n, tint in ((r, 16, 0), (r * .72, 12, 22), (r * .44, 9, 44)):
            rr *= s
            pc = tuple(min(255, v + tint) for v in col)
            for i in range(n):
                a = 2 * math.pi * i / n + rr
                px, py = c + rr * .72 * math.cos(a), c + rr * .72 * math.sin(a)
                pr = rr * .36
                fd.ellipse([px - pr, py - pr, px + pr, py + pr], fill=pc + (255,),
                           outline=(170, 72, 8, 255), width=max(1, s // 2))
        f = f.resize((size // s, size // s), Image.LANCZOS)
        img.alpha_composite(f, (int(x - f.width / 2), int(y - f.height / 2)))

    d = ImageDraw.Draw(img)
    swags = 3
    span = W / swags
    for k in range(swags):
        for i in range(int(span / 22) + 1):
            t = i / (span / 22)
            x = k * span + t * span
            y = 26 + 92 * (1 - (2 * t - 1) ** 2)
            if i % 4 == 0:  # mango leaves
                a = rnd.uniform(1.2, 1.9)
                ex, ey = x + 44 * math.cos(a), y + 44 * math.sin(a) + 12
                d.polygon([(x - 7, y), (x + 7, y), (ex, ey)], fill=(58, 112, 42, 255))
            flower(x, y, rnd.uniform(16, 20))
    for k in range(swags + 1):  # hanging strings at the joins
        x = k * span
        for j in range(6):
            flower(x, 30 + j * 30, 19 - j * .8)
    return img


def make_coin(size):
    s = 4
    n = size * s
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, n - 1, n - 1], fill=(198, 132, 34, 255))
    d.ellipse([n * .07, n * .07, n * .93, n * .93], fill=(250, 204, 92, 255))
    d.ellipse([n * .2, n * .2, n * .8, n * .8], outline=(186, 122, 30, 255), width=n // 22)
    d.ellipse([n * .34, n * .2, n * .52, n * .4], fill=(255, 244, 190, 200))
    return img.resize((size, size), Image.LANCZOS)


def logo_card(logo_w, pad, radius, border=0):
    logo = Image.open(os.path.join(ROOT, "brand", "logo.png")).convert("RGBA")
    logo = logo.resize((logo_w, int(logo_w * logo.height / logo.width)), Image.LANCZOS)
    cw, ch = logo.width + 2 * pad, logo.height + 2 * pad
    s = 3
    card = Image.new("RGBA", (cw * s, ch * s), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, cw * s - 1, ch * s - 1], radius * s, fill=(255, 251, 240, 255),
                                           outline=(232, 176, 72, 255) if border else None, width=border * s)
    card = card.resize((cw, ch), Image.LANCZOS)
    card.alpha_composite(logo, (pad, pad))
    return card


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def envelope(t, start, end, fin=.35, fout=.3):
    if t < start or t > end:
        return 0.0
    return min(ease((t - start) / fin), ease((end - t) / fout) if end < LENGTH else 1.0)


# Timeline, matched to the measured pauses in the voice track (voice time + LEAD)
SHOW = {
    "t1": (.3, 4.85), "w1": (5.0, 8.15), "w2": (5.8, 8.15), "w3": (6.9, 8.15),
    "t2": (8.25, 12.8),
    "t3": (12.95, 15.6), "t3a": (15.65, 17.5), "t3b": (16.3, 17.5),
    "t4": (17.7, LENGTH), "t5": (19.9, LENGTH), "t6": (22.05, LENGTH), "phone": (18.2, LENGTH),
}
SMALL_DIYA_ON = [13.0, 13.7, 14.4, 15.1]


class Scene:
    def __init__(self):
        self.layers = text_layers()
        self.bg = make_background()
        self.mandala = make_mandala()
        self.diya = make_diya(430)
        self.diya_xy = (CX - self.diya.width // 2, HORIZON - self.diya.height + 18)
        self.small = make_diya(150)
        self.small_spots = [(92, 1296), (238, 1300), (842, 1300), (988, 1296)]
        self.floor = make_floor(self.diya, self.diya_xy, self.small, self.small_spots)
        self.toran = make_toran()
        self.flames = make_flames(180, 300)
        self.small_flames = [f.resize((64, 106), Image.LANCZOS) for f in self.flames]
        self.flame_mirror = [f.transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(5)) for f in self.flames]
        self.glow = radial(1000, 1.9, 150)
        self.small_glow = radial(280, 1.8, 150)
        self.logo_small = logo_card(216, 14, 16)
        self.logo_big = logo_card(520, 30, 30, 4)
        coin = make_coin(84)
        self.coins_sprites = []
        for i in range(16):
            cw = max(8, int(84 * abs(math.cos(math.pi * i / 16))))
            self.coins_sprites.append(coin.resize((cw, 84), Image.BILINEAR))
        self.spark = {sz: radial(sz, 1.4) for sz in (10, 16, 26)}
        rnd = random.Random(21)
        self.embers = [(rnd.uniform(0, W), rnd.uniform(0, 8), rnd.uniform(30, 90), rnd.uniform(0, 6.28),
                        rnd.choice((10, 16, 26))) for _ in range(46)]
        self.coins = []
        for _ in range(30):
            self.coins.append((rnd.uniform(8.25, 11.4), rnd.uniform(60, W - 60), rnd.uniform(1.5, 2.2),
                               rnd.uniform(5, 14), rnd.uniform(.6, 1.0)))
        for _ in range(8):
            self.coins.append((rnd.uniform(0.2, 3.0), rnd.uniform(60, W - 60), rnd.uniform(2.0, 2.6),
                               rnd.uniform(5, 12), rnd.uniform(.5, .8)))

    def add_light(self, frame, mask, center, colour, strength):
        if strength <= 0.01:
            return
        m = mask.point(lambda v: int(v * min(1.0, strength)))
        x, y = center[0] - m.width // 2, center[1] - m.height // 2
        box = (max(0, x), max(0, y), min(W, x + m.width), min(H, y + m.height))
        if box[0] >= box[2] or box[1] >= box[3]:
            return
        crop_m = m.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
        region = frame.crop(box)
        frame.paste(ImageChops.add(region, Image.composite(Image.new("RGB", region.size, colour),
                                                           Image.new("RGB", region.size), crop_m)), box)

    def frame(self, t):
        f = self.bg.copy()
        flick = .86 + .1 * math.sin(t * 11) * math.sin(t * 3.7) + .04 * math.sin(t * 23)
        idx = int(t * 15 + 2 * math.sin(t * 2.3)) % len(self.flames)

        # mandala turning slowly behind the diya
        rot = self.mandala.rotate(-t * 5, Image.BILINEAR)
        f.paste(rot, (CX - rot.width // 2, 1020 - rot.height // 2), rot)

        # floor, brightened when "मजबूत पाया" is said
        f.paste(self.floor, (0, HORIZON), self.floor)
        rise = envelope(t, 15.6, LENGTH, .6, .3)
        self.add_light(f, self.glow.resize((1500, 560)), (CX, HORIZON + 120), (120, 64, 30), .35 + .65 * rise * .9)
        sweep_t = (t - 15.65) / 1.4
        if 0 < sweep_t < 1:  # gloss streak running across the floor
            sx = int(-200 + 1480 * sweep_t)
            self.add_light(f, self.small_glow.resize((640, 620)), (sx, HORIZON + 300), (120, 74, 38), .7)

        # reflections of the flames on the floor
        fx, fy = CX - 90, self.diya_xy[1] + 26 - 288
        fm = self.flame_mirror[idx]
        alpha = fm.getchannel("A").point(lambda v: int(v * .5))
        f.paste(fm, (fx, HORIZON + 112), alpha)

        # small diyas lit one by one
        for spot, on in zip(self.small_spots, SMALL_DIYA_ON):
            a = ease((t - on) / .45)
            if a <= 0:
                continue
            sx, base = spot
            d = self.small
            x, y = sx - d.width // 2, base - d.height + 6
            f.paste(d, (x, y), d.getchannel("A").point(lambda v: int(v * a)))
            mirror = d.transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(1.6))
            f.paste(mirror, (x, base + 2), mirror.getchannel("A").point(lambda v: int(v * a * .28)))
            sf = self.small_flames[(idx + sx) % len(self.small_flames)]
            f.paste(sf, (sx - sf.width // 2, y + 12 - sf.height + 10), sf.getchannel("A").point(lambda v: int(v * a)))
            self.add_light(f, self.small_glow, (sx, y - 26), (255, 132, 40), a * .68 * flick)

        # main diya + flame + glow
        f.paste(self.diya, self.diya_xy, self.diya)
        flame = self.flames[idx]
        f.paste(flame, (fx, fy), flame)
        self.add_light(f, self.glow, (CX, fy + 170), (255, 128, 36), .8 * flick)

        # embers drifting up, across the whole frame
        d0 = self.spark
        for x0, ph, sp, wob, size in self.embers:
            y = HORIZON - ((t + ph * 3) * sp) % (HORIZON - 160)
            x = x0 + 26 * math.sin(t * .8 + wob)
            b = .35 + .55 * abs(math.sin(t * 1.6 + wob))
            m = d0[size]
            self.add_light(f, m, (int(x), int(y)), (255, 196, 110), b)

        # coins falling
        for start, x, dur, spin, scale in self.coins:
            u = (t - start) / dur
            if not 0 <= u <= 1:
                continue
            y = -90 + (HORIZON + 40 + 90) * u ** 1.5
            spr = self.coins_sprites[int(t * spin) % len(self.coins_sprites)]
            if scale < .95:
                spr = spr.resize((max(6, int(spr.width * scale)), int(spr.height * scale)), Image.BILINEAR)
            a = min(1.0, (1 - u) * 6)
            f.paste(spr, (int(x - spr.width / 2), int(y)), spr.getchannel("A").point(lambda v: int(v * a)))

        # toran and logo: the logo stays on every frame
        f.paste(self.toran, (0, 0), self.toran)
        big = ease((t - 17.55) / .5)
        small_alpha = 1 - big
        if small_alpha > 0:
            lg = self.logo_small
            f.paste(lg, (46, 92), lg.getchannel("A").point(lambda v: int(v * small_alpha)))
        if big > 0:
            lg = self.logo_big
            y = 196 + int((1 - big) * 26)
            f.paste(lg, (CX - lg.width // 2, y), lg.getchannel("A").point(lambda v: int(v * big)))

        # captions
        for key, (a, b) in SHOW.items():
            alpha = envelope(t, a, b)
            if alpha <= 0:
                continue
            img, x, y = self.layers[key]
            y += int((1 - alpha) * 26)
            f.paste(img, (x, y), img.getchannel("A").point(lambda v: int(v * alpha)))
        return f


def make_music(path, length=LENGTH):
    """Original soft tanpura drone with temple-bell notes (Raag Bhupali scale). Pure stdlib, nothing licensed."""
    sr = 22050
    total = int(length * sr)
    mix = array.array("f", [0.0]) * total

    def tone(freq, secs, partials, decay):
        n = int(secs * sr)
        out = array.array("f", [0.0]) * n
        for mult, amp, dk in partials:
            step = 2 * math.pi * freq * mult / sr
            for i in range(n):
                out[i] += amp * math.sin(step * i) * math.exp(-decay * dk * i / sr)
        return out

    def add(buf, at, gain):
        start = int(at * sr)
        for i, v in enumerate(buf):
            j = start + i
            if j >= total:
                break
            mix[j] += v * gain

    sa = 146.83
    drone = [(1, 1, 1), (2, .7, 1.2), (3, .45, 1.6), (4, .3, 2), (5, .16, 2.4), (6, .08, 3)]
    notes = {"pa": tone(sa * .75, 4.2, drone, .75), "sa2": tone(sa, 4.2, drone, .75), "sa1": tone(sa * .5, 4.2, drone, .7)}
    t, seq = 0.0, ["pa", "sa2", "sa2", "sa1"]
    i = 0
    while t < length:
        add(notes[seq[i % 4]], t, .11)
        t += 1.05
        i += 1

    bell_partials = [(1, 1, 1), (2.01, .5, 1.5), (3.02, .22, 2.2), (4.2, .1, 3)]
    scale = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3, 2, 9 / 4, 5 / 2]
    bells = {k: tone(sa * 2 * r, 2.8, bell_partials, 1.5) for k, r in enumerate(scale)}
    rnd = random.Random(11)
    at, pos = 0.25, 5
    while at < length - 2.6:
        add(bells[pos], at, .085)
        pos = max(0, min(len(scale) - 1, pos + rnd.choice((-2, -1, -1, 1, 1, 2))))
        at += rnd.choice((1.05, 1.05, 2.1))
    for at in (8.2, 12.95, 17.6, 22.05):  # a chime on every scene change
        for k, offset in enumerate((0, .09, .18)):
            add(bells[5 + k], at + offset, .1)
    add(bells[7], length - 2.7, .12)

    peak = max(abs(min(mix)), abs(max(mix))) or 1
    frames = array.array("h", (int(v / peak * 26000) for v in mix))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(frames.tobytes())


def main():
    os.makedirs(CACHE, exist_ok=True)
    scene = Scene()
    if "--still" in sys.argv:
        for s in sys.argv[sys.argv.index("--still") + 1].split(","):
            scene.frame(float(s)).save(os.path.join(CACHE, f"still_{s}.png"))
        print("stills in", CACHE)
        return

    silent = os.path.join(CACHE, "silent.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                            "-crf", "19", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    count = int(LENGTH * FPS)
    for n in range(count):
        enc.stdin.write(scene.frame(n / FPS).tobytes())
        if n % 150 == 0:
            print(f"frame {n}/{count}", flush=True)
    enc.stdin.close()
    if enc.wait():
        sys.exit("video encode failed")

    music = os.path.join(CACHE, "music.wav")
    make_music(music)
    ms = int(LEAD * 1000)
    graph = (f"[1:a]aresample=44100,aformat=channel_layouts=mono,adelay={ms}:all=1,volume=1.5,asplit=2[v1][key];"
             "[2:a]aresample=44100,aformat=channel_layouts=mono,volume=0.30[m];"
             "[m][key]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=450[duck];"
             f"[v1][duck]amix=inputs=2:duration=longest:normalize=0,atrim=0:{LENGTH},"
             "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", VOICE, "-i", music,
                    "-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-ac", "2", "-t", str(LENGTH), "-movflags", "+faststart", OUT], check=True)
    print("done", OUT)


if __name__ == "__main__":
    main()
