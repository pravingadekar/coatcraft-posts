"""Render CoatCraft scenes (reel 1080x1920 or carousel 1080x1350) from a JSON spec, and build the reel.

Spec (e.g. ad/ad.json, daily/<date>/content.json):
{
  "scenes": [
    {"kind": "hook",  "title": "Floor mein *CRACK*?", "chips": ["Dust", "Oil ke daag"], "photo": "photos/x.jpg"},
    {"kind": "brand"},
    {"kind": "grid",  "tag": "SERVICES", "title": "...", "items": ["...", "..."]},
    {"kind": "list",  "tag": "...", "title": "...", "items": ["..."], "note": "*small print"},
    {"kind": "text",  "tag": "...", "title": "...", "body": "..."},
    {"kind": "cta",   "title": "..."}
  ],
  "narration": ["one voiceover line per scene", ...]      (optional; needs ELEVENLABS_API_KEY)
}
Words wrapped in *stars* in a title are drawn in brand orange. "photo" (optional) puts a darkened site photo
behind any scene. Facts and contact details come from brand/facts.json.

    python tools/make_scenes.py SPEC.json OUT_DIR [--carousel] [--no-voice] [--secs 4.5]
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts  # noqa: E402
from make_reel import build_reel, voice_durations  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "brand", "fonts")
FACTS = json.load(open(os.path.join(ROOT, "brand", "facts.json"), encoding="utf-8"))

ORANGE = (231, 92, 12)
NAVY = (19, 41, 75)
NAVY_DEEP = (8, 20, 40)
WHITE = (255, 255, 255)
MUTED = (178, 192, 214)
CHIP = (27, 54, 94)


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONTS, f"Poppins-{weight}.ttf"), size)


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test.replace("*", ""), font=fnt) <= width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, weight, size, width, max_lines):
    """Largest font (down to 60%) that fits text into max_lines."""
    for s in range(size, int(size * 0.6), -4):
        f = font(weight, s)
        lines = wrap(draw, text, f, width)
        if len(lines) <= max_lines:
            return f, lines
    return f, lines


def draw_marked(draw, xy, line, fnt, base, mark, on=False):
    """Draw a line where *starred* words are in the accent colour. `on` carries a *phrase* that wraps across lines;
    returns the state for the next line."""
    x, y = xy
    parts = line.split("*")
    for i, part in enumerate(parts):
        if part:
            draw.text((x, y), part, font=fnt, fill=mark if on else base)
            x += draw.textlength(part, font=fnt)
        if i < len(parts) - 1:
            on = not on
    return on


def background(w, h, photo=None):
    if photo:
        img = Image.open(os.path.join(ROOT, photo)).convert("RGB")
        scale = max(w / img.width, h / img.height)
        img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1), Image.LANCZOS)
        left, top = (img.width - w) // 2, (img.height - h) // 2
        img = img.crop((left, top, left + w, top + h))
        shade = Image.new("RGB", (w, h), NAVY_DEEP)
        mask = Image.linear_gradient("L").resize((w, h)).point(lambda v: 110 + v * 120 // 255)
        return Image.composite(shade, img, mask)

    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(NAVY, NAVY_DEEP)))
    # glossy epoxy floor: perspective grid on the lower third plus a soft reflection
    horizon = int(h * 0.62)
    floor = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(floor)
    for i in range(-12, 13):
        fd.line([(w / 2 + i * 22, horizon), (w / 2 + i * 260, h)], fill=(120, 160, 210, 38), width=2)
    y, step = horizon, 10
    while y < h:
        fd.line([(0, y), (w, y)], fill=(120, 160, 210, 30), width=2)
        y += step
        step *= 1.32
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([w * 0.1, horizon - 40, w * 0.9, horizon + h * 0.22], fill=(231, 92, 12, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img.convert("RGBA"), floor)
    return Image.alpha_composite(img, glow).convert("RGB")


def brand_mark(img, x, y, size):
    icon = Image.open(os.path.join(ROOT, "brand", "icon.png")).convert("RGBA")
    icon = icon.resize((size, int(size * icon.height / icon.width)), Image.LANCZOS)
    img.paste(icon, (x, y), icon)
    d = ImageDraw.Draw(img)
    d.text((x + size + 18, y + size * 0.02), "CoatCraft", font=font("Bold", int(size * 0.46)), fill=WHITE)
    d.text((x + size + 20, y + size * 0.56), "S O L U T I O N S", font=font("Medium", int(size * 0.2)), fill=MUTED)


def pill(d, x, y, text, fnt, fill, color, pad=(26, 12)):
    tw = d.textlength(text, font=fnt)
    asc, desc = fnt.getmetrics()
    d.rounded_rectangle([x, y, x + tw + pad[0] * 2, y + asc + desc + pad[1] * 2], radius=(asc + desc) // 2 + pad[1],
                        fill=fill)
    d.text((x + pad[0], y + pad[1]), text, font=fnt, fill=color)
    return tw + pad[0] * 2, asc + desc + pad[1] * 2


def render(scene, w, h, index, total):
    img = background(w, h, scene.get("photo"))
    d = ImageDraw.Draw(img)
    pad = 80
    inner = w - 2 * pad
    tall = h > 1500
    kind = scene["kind"]

    if kind != "brand":
        brand_mark(img, pad, 70 if tall else 56, 92 if tall else 78)
        d.rectangle([0, 0, w, 10], fill=ORANGE)

    y = int(h * (0.24 if tall else 0.2))
    if scene.get("tag"):
        _, ph = pill(d, pad, y, scene["tag"], font("Bold", 30), ORANGE, WHITE)
        y += ph + 34

    if kind == "brand":
        size = 300 if tall else 230
        icon = Image.open(os.path.join(ROOT, "brand", "icon.png")).convert("RGBA")
        icon = icon.resize((size, int(size * icon.height / icon.width)), Image.LANCZOS)
        top = int(h * 0.3)
        img.paste(icon, ((w - size) // 2, top), icon)
        y = top + icon.height + 50
        for text, f, col in (("CoatCraft", font("ExtraBold", 120 if tall else 104), WHITE),
                             ("S O L U T I O N S", font("Medium", 40), MUTED),
                             (FACTS["tagline"], font("SemiBold", 52 if tall else 46), ORANGE)):
            tw = d.textlength(text, font=f)
            d.text(((w - tw) / 2, y), text, font=f, fill=col)
            y += f.getmetrics()[0] + f.getmetrics()[1] + 26
        if scene.get("body"):
            f = font("Medium", 38)
            for line in wrap(d, scene["body"], f, inner):
                tw = d.textlength(line, font=f)
                d.text(((w - tw) / 2, y + 20), line, font=f, fill=WHITE)
                y += 54
        return img

    title_size = 104 if tall else 84
    if kind == "cta":
        title_size = 86 if tall else 72
    f, lines = fit(d, scene.get("title", ""), "ExtraBold", title_size, inner, 4)
    lh = f.getmetrics()[0] + f.getmetrics()[1] + 4
    on = False
    for line in lines:
        on = draw_marked(d, (pad, y), line, f, WHITE, ORANGE, on)
        y += lh
    d.rectangle([pad, y + 18, pad + 150, y + 28], fill=ORANGE)
    y += 80

    if kind == "hook":
        x = pad
        cf = font("SemiBold", 44 if tall else 38)
        for chip in scene.get("chips", []):
            cw = d.textlength(chip, font=cf) + 60
            if x + cw > w - pad:
                x, y = pad, y + 100
            pill(d, x, y, chip, cf, CHIP, WHITE, pad=(30, 16))
            x += cw + 22
        y += 120
        if scene.get("body"):
            bf = font("Medium", 44 if tall else 38)
            for line in wrap(d, scene["body"], bf, inner):
                d.text((pad, y), line, font=bf, fill=MUTED)
                y += 62

    elif kind == "grid":
        items = scene["items"]
        cols = 2
        gap = 24
        cw = (inner - gap) // cols
        ch = 150 if tall else 118
        gf = font("SemiBold", 38 if tall else 32)
        for i, item in enumerate(items):
            cx = pad + (i % cols) * (cw + gap)
            cy = y + (i // cols) * (ch + gap)
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=22, fill=CHIP)
            d.rectangle([cx, cy + 22, cx + 8, cy + ch - 22], fill=ORANGE)
            lines = wrap(d, item, gf, cw - 60)[:2]
            lh2 = gf.getmetrics()[0] + gf.getmetrics()[1]
            ty = cy + (ch - lh2 * len(lines)) / 2
            for line in lines:
                d.text((cx + 34, ty), line, font=gf, fill=WHITE)
                ty += lh2

    elif kind == "list":
        lf = font("SemiBold", 46 if tall else 40)
        for item in scene["items"]:
            d.ellipse([pad, y + 12, pad + 44, y + 56], fill=ORANGE)
            d.line([(pad + 11, y + 35), (pad + 20, y + 45), (pad + 35, y + 23)], fill=WHITE, width=6)
            for j, line in enumerate(wrap(d, item, lf, inner - 80)):
                d.text((pad + 74, y), line, font=lf, fill=WHITE)
                y += 64
            y += 30
        if scene.get("note"):
            d.text((pad, y + 10), scene["note"], font=font("Regular", 28), fill=MUTED)

    elif kind == "text":
        bf = font("Medium", 46 if tall else 40)
        for line in wrap(d, scene.get("body", ""), bf, inner):
            d.text((pad, y), line, font=bf, fill=MUTED)
            y += 66

    elif kind == "cta":
        box_h = 330 if tall else 290
        d.rounded_rectangle([pad, y, w - pad, y + box_h], radius=36, fill=ORANGE)
        d.text((pad + 50, y + 40), "Call / WhatsApp", font=font("SemiBold", 40), fill=WHITE)
        pf = font("ExtraBold", 92 if tall else 80)
        d.text((pad + 50, y + 100), FACTS["phone"], font=pf, fill=WHITE)
        y += box_h + 50
        for text, f, col in ((FACTS["website"], font("Bold", 48), WHITE),
                             (FACTS["email"], font("Medium", 38), MUTED),
                             (f"{FACTS['city'].split(',')[0]}  |  {FACTS['coverage']} service", font("SemiBold", 42),
                              ORANGE)):
            d.text((pad, y), text, font=f, fill=col)
            y += 76

    # footer
    if total > 1 and not tall:
        sf = font("Medium", 28)
        d.text((w - pad - d.textlength(f"{index + 1} / {total}", font=sf), h - 80), f"{index + 1} / {total}", font=sf,
               fill=MUTED)
    if kind != "cta":
        d.text((pad, h - (110 if tall else 80)), f"{FACTS['phone']}  |  {FACTS['website']}", font=font("Medium", 30),
               fill=MUTED)
    return img


def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    carousel = "--carousel" in sys.argv
    secs = float(sys.argv[sys.argv.index("--secs") + 1]) if "--secs" in sys.argv else 4.5
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    scenes, narration = spec["scenes"], spec.get("narration")
    if "TODO" in json.dumps(spec):
        sys.exit("spec still has TODO placeholders")
    if narration and len(narration) != len(scenes):
        sys.exit(f"narration has {len(narration)} lines for {len(scenes)} scenes")
    os.makedirs(out, exist_ok=True)

    if carousel:
        for i, s in enumerate(scenes):
            render(s, 1080, 1350, i, len(scenes)).save(os.path.join(out, f"slide{i + 1}.png"), optimize=True)
        print("done carousel", out)
        return

    frames = []
    for i, s in enumerate(scenes):
        path = os.path.join(out, f"scene{i + 1}.png")
        render(s, 1080, 1920, i, len(scenes)).save(path)
        frames.append(path)
    voices = None
    if narration and "--no-voice" not in sys.argv:
        if not tts.available():
            sys.exit("spec has narration but ELEVENLABS_API_KEY is not set (use --no-voice to skip)")
        voices = tts.speak_all(narration, os.path.join(out, "voice"))
    durs = voice_durations(voices) if voices else [secs] * len(scenes)
    build_reel(frames, durs, os.path.join(out, "reel.mp4"), voices, zoom=True)
    print("done reel", out, "with voice" if voices else "music only")


if __name__ == "__main__":
    main()
