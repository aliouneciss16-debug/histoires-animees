"""Assemble les images 3D (10 i/s) en Short 1080x1920 30 i/s avec sous-titres et audio."""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from render import font, wrap

OUT = Path("out/tinybus")
CAPS = [(0.0, 3.0, "DON'T PRESS THAT BUTTON!"), (3.0, 6.0, "What's this?"), (6.0, 9.0, "Don't touch it, Bobo!"),
        (9.0, 12.0, "Just one little press..."), (12.0, 15.0, "CLICK! BEEP-BEEP!"), (15.0, 21.0, "WHOOOOA!"),
        (21.0, 25.0, "WOW!"), (25.0, 28.0, "BOBO, NO!"), (28.0, 30.0, "Again?")]
COL = {"DON'T": (255, 70, 70)}


def cap(text, i):
    f = font(True, 92)
    lines = wrap(text, f, 900)
    h = 40 + len(lines) * 112
    im = Image.new("RGBA", (1000, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 999, h - 1], radius=50, fill=(20, 24, 48, 215))
    for k, ln in enumerate(lines):
        d.text((500, 20 + k * 112 + 56), ln, font=f, fill=(255, 235, 90) if i in (0, 4, 5, 7) else (255, 255, 255), anchor="mm",
               stroke_width=4, stroke_fill=(20, 24, 48))
    p = OUT / f"cap_{i}.png"; im.save(p); return p, h


def tag():
    f = font(True, 40)
    t = "TINY BUS ADVENTURES"
    im = Image.new("RGBA", (640, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, 639, 79], radius=40, fill=(255, 200, 30, 235))
    d.text((320, 41), t, font=f, fill=(60, 30, 10), anchor="mm")
    p = OUT / "tag.png"; im.save(p); return p


def main():
    out = sys.argv[1]
    inputs = ["-framerate", "10", "-i", str(OUT / "frames" / "f_%04d.png")]
    paths = [cap(t, i) for i, (_, _, t) in enumerate(CAPS)]
    tagp = tag()
    for p, _ in paths: inputs += ["-i", str(p)]
    inputs += ["-i", str(tagp), "-i", str(OUT / "audio.wav")]
    n = len(CAPS)
    fc = "[0:v]scale=1080:1920:flags=lanczos,fps=30,format=yuv420p[v0];"
    last = "v0"
    for i, (a, b, _) in enumerate(CAPS):
        h = paths[i][1]
        fc += f"[{last}][{i + 1}:v]overlay=40:{1420 - (h - 150) // 2}:enable='between(t,{a},{b})'[v{i + 1}];"
        last = f"v{i + 1}"
    fc += f"[{last}][{n + 1}:v]overlay=40:70[vout]"
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", fc, "-map", "[vout]", "-map", f"{n + 2}:a",
           "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-t", "30", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("OK", out)


main()
