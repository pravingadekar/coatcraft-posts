"""Assemble the AI story ad from the chosen takes: shots 1-3, a stock-photo work montage, shots 5-6 and the end card,
with the CoatCraft logo, the AI disclosure line, a lower third and original music under the dialogue.

    python ad/ai-story/build.py OUT.mp4
"""
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_music  # noqa: E402
import make_scenes  # noqa: E402
from make_reel import FFMPEG, audio_seconds  # noqa: E402

TAKES = os.path.join(HERE, "takes")
SHOTS = ["shot1_c", "shot2_a", "shot3_a", "MONTAGE", "shot5_b", "shot6_b", "END"]   # 5b/6b: client thanks + CTA
MONTAGE = [("stock/power-trowel-worker.jpg", "Surface preparation"),
           ("stock/apply-selfleveling-workers.jpg", "Epoxy / PU coating"),
           ("stock/roller-floor-worker.jpg", "Roller finish"),
           ("stock/glossy-warehouse-1.jpg", "Seamless floor ready")]
W, H, FPS = 1080, 1920, 30
MUSIC_UNDER_DIALOGUE, MUSIC_ALONE = 0.10, 0.55


def font(weight, size):
    return ImageFont.truetype(os.path.join(ROOT, "brand", "fonts", f"Poppins-{weight}.ttf"), size)


def overlay_png(path, lower_third=False):
    """Transparent 1080x1920 layer: logo top-left, optional lower third. The AI disclosure is the platform's AI label
    (set when scheduling) plus a caption line, not on-screen text."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 50, 470, 160], radius=55, fill=(8, 20, 40, 170))
    make_scenes.brand_mark(img, 60, 60, 88)
    if lower_third:
        d.rectangle([0, 1380, 760, 1530], fill=(8, 20, 40, 215))
        d.rectangle([0, 1380, 14, 1530], fill=make_scenes.ORANGE)
        d.text((50, 1398), "CoatCraft Solutions", font=font("Bold", 50), fill=(255, 255, 255, 255))
        d.text((52, 1465), "Site Engineer", font=font("Medium", 36), fill=make_scenes.ORANGE)
    img.save(path)


def run(cmd):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error"] + cmd, check=True)


def norm(src, out, layer):
    run(["-i", src, "-i", layer, "-filter_complex",
         f"[0:v]scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p[v];[v][1:v]overlay=0:0[o]",
         "-map", "[o]", "-map", "0:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-c:a", "aac", "-ar", "48000", "-ac", "2", out])


def still_clip(png, secs, out, layer=None, zoom=True):
    inputs = ["-loop", "1", "-framerate", str(FPS), "-t", str(secs), "-i", png]
    vf = f"[0:v]scale=2160:-1,zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" \
         f":d=1:s={W}x{H}:fps={FPS},format=yuv420p" if zoom else f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p"
    graph = vf + "[v]"
    if layer:
        inputs += ["-i", layer]
        graph += ";[v][1:v]overlay=0:0[o]"
    run(inputs + ["-f", "lavfi", "-t", str(secs), "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex", graph,
                  "-map", "[o]" if layer else "[v]", "-map", f"{2 if layer else 1}:a", "-c:v", "libx264", "-crf", "18",
                  "-c:a", "aac", "-shortest", out])


def montage_frame(photo, label, out):
    scene = {"kind": "text", "tag": "KAAM KAISE HOTA HAI", "title": f"*{label}*", "body": "", "photo": photo}
    make_scenes.render(scene, W, H, 0, 1).save(out)


def concat_list(path, files):
    with open(path, "w") as f:
        f.write("".join(f"file '{p.replace(os.sep, '/')}'\n" for p in files))


def main():
    out = sys.argv[1]
    with tempfile.TemporaryDirectory() as tmp:
        plain, lower = os.path.join(tmp, "o1.png"), os.path.join(tmp, "o2.png")
        overlay_png(plain)
        overlay_png(lower, lower_third=True)
        segs, quiet = [], []   # quiet = (start, end) spans with no dialogue, where the music comes up
        t = 0.0
        for name in SHOTS:
            seg = os.path.join(tmp, f"{len(segs):02d}.mp4")
            if name == "MONTAGE":
                parts = []
                for i, (photo, label) in enumerate(MONTAGE):
                    png = os.path.join(tmp, f"m{i}.png")
                    montage_frame(photo, label, png)
                    part = os.path.join(tmp, f"m{i}.mp4")
                    still_clip(png, 1.9, part)
                    parts.append(part)
                lst = os.path.join(tmp, "m.txt")
                open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
                run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", seg])
            elif name == "END":
                png = os.path.join(tmp, "end.png")
                make_scenes.render({"kind": "cta", "title": "Apne floor ka *solution* paayein",
                                    "photo": "stock/glossy-warehouse-1.jpg"}, W, H, 0, 1).save(png)
                still_clip(png, 4.5, seg)
            else:
                norm(os.path.join(TAKES, f"{name}.mp4"), seg, lower if name == "shot2_a" else plain)
            d = audio_seconds(seg)
            if name in ("MONTAGE", "END"):
                quiet.append((t, t + d))
            segs.append(seg)
            t += d

        lst = os.path.join(tmp, "all.txt")
        open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
        joined = os.path.join(tmp, "joined.mp4")
        run(["-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy", "-c:a", "aac", joined])

        music = os.path.join(tmp, "music.wav")
        make_music.main(music, t, [a for a, _ in quiet])
        loud = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in quiet)
        run(["-i", joined, "-i", music, "-filter_complex",
             f"[1:a]volume='if({loud},{MUSIC_ALONE},{MUSIC_UNDER_DIALOGUE})':eval=frame[m];"
             f"[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", out])
    print("done", out, f"{t:.1f}s")


if __name__ == "__main__":
    main()
