#!/usr/bin/env python3
"""Épisode muet « Le dernier morceau » : comédie sans voix ni musique (sous-titres + bruitages).

Usage :
  python src/mute.py out/mute_001.mp4
  python src/mute.py --still 5.0 out/still.png
"""
import math
import os
import random
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import sfx
import sitcom
from render import FPS, H, W, ease, font, seg, tag_overlay, wrap
from sitcom import OUT, Cv, S, SPEC, draw_char, eo

CHANNEL = "La Famille Sarr"
DUR = 25.5
for k, (x, sc) in dict(papa=(190, 0.8), moussa=(400, 0.66), awa=(560, 0.58), maman=(740, 0.8), mame=(960, 0.8)).items():
    SPEC[k]["x"], SPEC[k]["scale"] = x, sc
CAST = ["papa", "moussa", "awa", "maman", "mame"]
Y_B = sitcom.Y_B
PIECE = (540, 1262)  # position du morceau dans le bol (plan large)


def S_(t, a, b):
    return ease(seg(t, a, b))


# ---------- sprites ----------
def make_piece():
    c = Cv(320, 200)
    cream = (246, 236, 214, 255)
    c.line([(190, 100), (272, 100)], OUT, 30)
    c.line([(190, 100), (272, 100)], cream, 22)
    eo(c, 276, 86, 17, 17, cream, 4)
    eo(c, 276, 114, 17, 17, cream, 4)
    eo(c, 120, 100, 104, 74, (152, 78, 34, 255), 6)
    eo(c, 112, 112, 80, 48, (128, 62, 26, 255), 0)
    c.ell(88, 70, 34, 15, (214, 140, 80, 220))
    for x in (70, 112, 154):
        c.line([(x, 76), (x - 18, 134)], (96, 44, 18, 255), 7)
    return c.done()


def make_bowl():
    c = Cv(900, 520)
    c.ell(450, 440, 400, 54, (60, 40, 24, 70))
    eo(c, 450, 330, 430, 170, (252, 250, 244, 255), 7)
    for i in range(14):
        a = math.radians(20 + i * 10.5)
        c.ell(450 + 360 * math.cos(a), 330 + 118 * math.sin(a), 22, 14, (70, 120, 200, 255))
    eo(c, 450, 250, 430, 150, (240, 236, 224, 255), 7)
    eo(c, 450, 252, 392, 124, (214, 190, 150, 255), 4)
    eo(c, 450, 236, 350, 100, (232, 140, 48, 255), 5)
    rnd = random.Random(3)
    for _ in range(34):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.2, 0.9)
        col = rnd.choice([(214, 70, 40, 255), (120, 170, 70, 255), (250, 214, 120, 255), (190, 90, 30, 255)])
        c.ell(450 + 300 * r * math.cos(a), 236 + 82 * r * math.sin(a), rnd.randint(9, 16), rnd.randint(7, 11), col)
    return c.done()


def make_star(r):
    c = Cv(int(r * 2) + 4, int(r * 2) + 4)
    cx = cy = r + 2
    pts = []
    for i in range(8):
        a = math.radians(i * 45 - 90)
        rr_ = r if i % 2 == 0 else r * 0.28
        pts.append((cx + rr_ * math.cos(a), cy + rr_ * math.sin(a)))
    c.poly(pts, (255, 250, 200, 255))
    return c.done()


def make_dining(A):
    room = A.room.copy()
    strip = room.crop((372, 225, 432, 620)).resize((580, 395))
    room.paste(strip, (435, 225))
    d = ImageDraw.Draw(room)
    d.rounded_rectangle([690, 300, 920, 500], radius=14, fill=(120, 86, 56), outline=(90, 60, 38), width=6)
    d.rounded_rectangle([706, 316, 904, 484], radius=8, fill=(250, 226, 150))
    for x, h in ((760, 70), (805, 100), (850, 60)):
        d.ellipse([x - 22, 380 - h // 2, x + 22, 380 + 10], fill=(110, 70, 44))
        d.rectangle([x - 22, 400, x + 22, 484], fill=(110, 70, 44))
    return room


def make_table():
    im = Image.new("RGBA", (W, H - 1190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 270], fill=(250, 238, 204, 255))
    for x in range(0, W, 90):
        d.rectangle([x, 0, x + 38, 270], fill=(244, 222, 176, 255))
    d.rectangle([0, 0, W, 10], fill=(150, 104, 62, 255))
    d.rectangle([0, 250, W, 300], fill=(214, 70, 60, 255))
    d.rectangle([0, 300, W, H], fill=(226, 202, 160, 255))
    for x in range(0, W, 60):
        d.ellipse([x + 10, 330, x + 40, 360], fill=(214, 70, 60, 255))
    return im


class Assets:
    def __init__(self):
        self.base = sitcom.assets()
        self.room = make_dining(self.base)
        self.table = make_table()
        self.bowl = make_bowl()
        self.piece = make_piece()
        self.star = make_star(70)
        self.bowl_s = self.bowl.resize((int(900 * 0.62), int(520 * 0.62)), Image.LANCZOS)
        self.piece_s = self.piece.resize((160, 100), Image.LANCZOS)
        cb = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(cb)
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=(int(250 - 30 * t), int(228 - 40 * t), int(186 - 50 * t)))
        for x in range(0, W, 120):
            d.rectangle([x, 0, x + 50, H], fill=(244, 212, 160))
        self.close_bg = cb.convert("RGBA")


_A = None


def assets():
    global _A
    if _A is None:
        _A = Assets()
    return _A


# ---------- bras et accessoires ----------
def limb(p0, p1, width, sleeve, skin, prop=None, length=0):
    pad = 170
    x0, y0 = int(min(p0[0], p1[0])) - pad, int(min(p0[1], p1[1])) - pad
    w, h = int(abs(p0[0] - p1[0])) + 2 * pad, int(abs(p0[1] - p1[1])) + 2 * pad
    c = Cv(w, h)
    a, b = (p0[0] - x0, p0[1] - y0), (p1[0] - x0, p1[1] - y0)
    c.line([a, b], OUT, width + 10)
    c.line([a, b], tuple(sleeve) + (255,), width)
    dist = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    d = ((b[0] - a[0]) / dist, (b[1] - a[1]) / dist)
    if prop:
        tip = (b[0] + d[0] * length, b[1] + d[1] * length)
        col = (200, 204, 212, 255) if prop == "spoon" else (92, 58, 36, 255)
        c.line([b, tip], OUT, 18)
        c.line([b, tip], col, 11)
        r = 26 if prop == "spoon" else 36
        eo(c, tip[0], tip[1], r, r * 0.72, col, 5)
    eo(c, b[0], b[1], width * 0.62, width * 0.62, tuple(skin) + (255,), 4)
    return c.done(), (x0, y0)


def shoulder(name, dx=0, dy=0):
    sp = SPEC[name]
    sg = 1 if 540 > sp["x"] else -1
    return (sp["x"] + dx + sg * 48 * sp["scale"], Y_B - 300 * sp["scale"] + dy)


def draw_arm(f, name, hand, prop=None, length=0, dx=0, dy=0, prog=1.0):
    sh = shoulder(name, dx, dy)
    sp = SPEC[name]
    if prop:  # 'hand' est la position voulue du bout de l'accessoire
        dist = math.hypot(hand[0] - sh[0], hand[1] - sh[1]) or 1
        d = ((hand[0] - sh[0]) / dist, (hand[1] - sh[1]) / dist)
        hand = (sh[0] + d[0] * max(0, dist - length), sh[1] + d[1] * max(0, dist - length))
    p1 = (sh[0] + (hand[0] - sh[0]) * prog, sh[1] + (hand[1] - sh[1]) * prog)
    img, pos = limb(sh, p1, int(54 * sp["scale"] + 10), sp["outfit"], sp["skin"], prop, length)
    f.paste(img, pos, img)
    return p1


def reach(t, a, b, c_, d_):
    return S_(t, a, b) * (1 - S_(t, c_, d_))


# ---------- chronologie ----------
BANDS = {
    "papa": [(0, "smug", "flat"), (4.0, "surprised", "o"), (4.8, "smug", "smirk"), (7.0, "happy", "talk"), (8.7, "sad", "frown"),
             (9.6, "angry", "frown"), (11.0, "neutral", "flat"), (12.4, "angry", "wide"), (14.4, "surprised", "o"),
             (21.0, "sad", "frown")],
    "moussa": [(0, "smug", "flat"), (4.0, "angry", "small"), (4.8, "sad", "frown"), (7.0, "smug", "smirk"), (11.0, "neutral", "flat"),
               (12.4, "angry", "wide"), (14.4, "surprised", "o"), (21.0, "sad", "frown")],
    "awa": [(0, "smug", "flat"), (4.3, "angry", "wide"), (5.2, "smug", "smirk"), (7.0, "neutral", "flat"), (11.0, "sad", "cry"),
            (12.4, "angry", "wide"), (14.4, "surprised", "o"), (21.0, "sad", "frown")],
    "maman": [(0, "smug", "flat"), (4.0, "neutral", "flat"), (7.0, "angry", "small"), (8.9, "smug", "smirk"), (11.0, "sad", "frown"),
              (12.5, "angry", "wide"), (14.4, "surprised", "o"), (21.0, "sad", "frown")],
    "mame": [(16.0, "neutral", "flat"), (17.6, "smug", "smirk"), (18.4, "happy", "chew"), (20.8, "smug", "smirk")],
}


def band(name, t):
    cur = BANDS[name][0]
    for b in BANDS[name]:
        if t >= b[0]:
            cur = b
    return cur[1], cur[2]


def piece_pos(t):
    """Position et rotation du morceau (plan large), ou None s'il n'est pas visible."""
    if t < 14.4:
        jit = 0
        if 12.85 <= t < 14.4:
            jit = 7 * math.sin(t * 42)
        return (PIECE[0] + jit, PIECE[1] + (3 * jit if jit else 0) * 0.5), 0
    if t < 18.0:
        u = (t - 14.5) / 3.5
        if u < 0:
            return PIECE, 0
        u = ease(min(1, u)) * 0.6 + u * 0.4
        x = PIECE[0] + (870 - PIECE[0]) * u
        y = PIECE[1] + (1105 - PIECE[1]) * u - 640 * 4 * u * (1 - u)
        return (x, y), u * 720
    if t < 18.55:
        k = S_(t, 18.0, 18.5)
        return (870 + (958 - 870) * k, 1105 + (925 - 1105) * k), 0
    return None


def look_dir(name, t):
    x = SPEC[name]["x"]
    target = PIECE[0]
    if 7.3 <= t < 8.6:
        target = SPEC["papa"]["x"]
    elif 11.0 <= t < 12.3:
        target = SPEC["awa"]["x"]
    elif 14.8 <= t < 18.0:
        pp = piece_pos(t)
        target = pp[0][0] if pp else target
    elif 18.0 <= t < 23.0:
        target = SPEC["mame"]["x"]
    d = target - x
    return 0 if abs(d) < 60 else (1 if d > 0 else -1)


def mouth_of(name, t, kind):
    if kind == "talk":
        return "small" if math.sin(t * 16) > 0 else "mid"
    if kind == "cry":
        return "wide" if math.sin(t * 9) > -0.2 else "mid"
    if kind == "chew":
        if t < 18.7:
            return "small"
        if t < 20.8:
            return "mid" if math.sin(t * 22) > 0 else "small"
        return "smirk"
    return kind


CAPS = [(0.0, 2.0, "Il reste UN seul morceau."), (4.0, 6.8, "Moussa tente."), (7.0, 10.8, "Papa : « Allô ? C'est urgent ! »"),
        (11.0, 13.0, "Awa : stratégie larmes."), (13.0, 14.6, "Tout le monde tire !"), (17.0, 20.8, "Mame est arrivée."),
        (21.0, 23.0, "Quelqu'un a encore faim ?"), (23.9, 25.5, "Il reste UN seul morceau.")]


def caption_layer(text, t0, t):
    fnt = font(True, 66)
    lines = wrap(text, fnt, 880)
    h = 56 + len(lines) * 80
    img = Image.new("RGBA", (980, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 979, h - 1], radius=46, fill=(24, 30, 50, 225))
    for i, ln in enumerate(lines):
        d.text((490, 28 + i * 80 + 40), ln, font=fnt, fill=(255, 255, 255), anchor="mm")
    k = ease(seg(t, t0, t0 + 0.18))
    if k < 1:
        img.putalpha(img.getchannel("A").point(lambda v: int(v * k)))
    return img


def closeup(t):
    A = assets()
    f = A.close_bg.copy()
    f.alpha_composite(A.bowl, (90, 740))
    if t < 23.9:
        pos = (560, 925 + 4 * math.sin(t * 4))
        pc = A.piece.resize((272, 170), Image.LANCZOS)
        f.alpha_composite(pc, (int(pos[0] - 136), int(pos[1] - 85)))
        if 0.8 <= t < 1.6:
            r = 0.5 + 0.5 * math.sin((t - 0.8) / 0.8 * math.pi)
            st = A.star.resize((int(140 * r) + 2, int(140 * r) + 2), Image.LANCZOS)
            f.alpha_composite(st, (int(500 - st.width / 2), int(880 - st.height / 2)))
    if t >= 23.0:  # la main de Mame remet un morceau
        drop = 23.9
        if t < drop:
            hy = 300 + (740 - 300) * S_(t, 23.0, 23.9)
            py = hy + 40
        else:
            hy = 740 - 520 * S_(t, 24.15, 24.8)
            py = 925 if t < drop + 0.15 else 925
            py = 740 + 40 + (925 - 780) * min(1, (t - drop) / 0.15) if t < drop + 0.15 else 925
        hx = 640 + 0.4 * (740 - hy) * 0
        if t >= drop + 0.15:
            pc = A.piece.resize((272, 170), Image.LANCZOS)
            f.alpha_composite(pc, (int(560 - 136), int(925 - 85)))
        else:
            pc = A.piece.resize((272, 170), Image.LANCZOS)
            f.alpha_composite(pc, (int(hx - 136), int(py - 85)))
        sleeve = SPEC["mame"]["outfit"]
        img, pos = limb((1000, -80), (hx + 20, hy - 40), 120, sleeve, SPEC["mame"]["skin"])
        f.alpha_composite(img, (pos[0], pos[1]))
    z = 1.0 + 0.04 * min(1, t / 2.0) if t < 2.0 else 1.04
    if t >= 23.0:
        z = 1.0 + 0.04 * (1 - min(1, (t - 23.0) / 0.9)) * 0 + 0.0
    if z != 1.0:
        cw, ch = int(W / z), int(H / z)
        x0, y0 = (W - cw) // 2, (H - ch) // 2
        f = f.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)
    return f


def wide(t):
    A = assets()
    f = A.room.convert("RGBA")
    state = {}
    for i, name in enumerate(CAST):
        if name == "mame":
            if t < 16.0:
                continue
            dx, dy = 420 * (1 - S_(t, 16.2, 17.4)), 0
        else:
            dx, dy = 0, 360 * (1 - S_(t, 2.0 + i * 0.16, 2.9 + i * 0.16))
        expr, mk = band(name, t)
        mouth = mouth_of(name, t, mk)
        chew = name == "mame" and 18.7 <= t < 20.8
        draw_char(f, A.base, name, expr, look_dir(name, t) if name != "mame" else 0, mouth, t, chew or mk == "talk", 0.5, dx, dy)
        state[name] = (dx, dy)
    d = ImageDraw.Draw(f)
    # téléphone de Papa
    if 7.0 <= t < 9.0:
        px, py = SPEC["papa"]["x"] + 98, Y_B - 460 * SPEC["papa"]["scale"] + 40
        d.rounded_rectangle([px - 20, py - 46, px + 20, py + 46], radius=10, fill=(30, 34, 46), outline=(255, 255, 255), width=3)
    # larmes d'Awa
    if 11.0 <= t < 12.4:
        sp = SPEC["awa"]
        ox, oy = sp["x"] - 230 * sp["scale"], Y_B - 650 * sp["scale"]
        for k in range(3):
            ph = ((t - 11.0) * 1.6 + k / 3) % 1
            for ex in (185, 275):
                d.ellipse([ox + ex * sp["scale"] - 7, oy + (215 + ph * 150) * sp["scale"] - 10,
                           ox + ex * sp["scale"] + 7, oy + (215 + ph * 150) * sp["scale"] + 10], fill=(110, 190, 255))
    # table, bol
    f.alpha_composite(A.table, (0, 1190))
    f.alpha_composite(A.bowl_s, (int(540 - A.bowl_s.width / 2), 1154))
    # morceau
    pp = piece_pos(t)
    if pp:
        (x, y), rot = pp
        pc = A.piece_s.rotate(-rot, expand=True, resample=Image.BICUBIC)
        f.alpha_composite(pc, (int(x - pc.width / 2), int(y - pc.height / 2)))
    # bras
    jit = lambda k: (6 * math.sin(t * 40 + k), 6 * math.cos(t * 37 + k)) if 12.85 <= t < 14.4 else (0, 0)
    r = reach(t, 4.3, 4.55, 4.8, 5.3)
    if r > 0.02:
        draw_arm(f, "moussa", (PIECE[0] + 20, PIECE[1] + 4), prog=r)
    r = reach(t, 4.5, 4.65, 5.0, 5.5)
    if r > 0.02:
        draw_arm(f, "awa", (PIECE[0] + 15, PIECE[1] + 6), prop="spoon", length=95, prog=r)
    r = reach(t, 8.2, 8.6, 8.7, 9.2)
    if r > 0.02:
        draw_arm(f, "papa", (PIECE[0] - 22, PIECE[1] + 4), prog=r)
    r = reach(t, 8.55, 8.8, 8.95, 9.5)
    if r > 0.02:
        draw_arm(f, "maman", (PIECE[0] - 30, PIECE[1] - 6), prop="ladle", length=120, prog=r)
    for k, (nm, tx) in enumerate([("papa", -30), ("moussa", 22), ("awa", -6), ("maman", 36)]):
        a0 = {"papa": 12.55, "moussa": 12.5, "awa": 12.4, "maman": 12.6}[nm]
        r = reach(t, a0, a0 + 0.25, 14.4, 15.0)
        if r > 0.02:
            jx, jy = jit(k)
            draw_arm(f, nm, (PIECE[0] + tx + jx, PIECE[1] + 14 + jy), prog=r)
    # Mame attrape et mange
    if t >= 17.3:
        if t < 18.0:
            hand, prog = (870, 1105), S_(t, 17.3, 17.9)
        elif t < 18.55:
            k = S_(t, 18.0, 18.5)
            hand, prog = (870 + 88 * k, 1105 - 180 * k), 1.0
        elif t < 19.3:
            hand, prog = (958, 925), 1.0 - S_(t, 18.8, 19.3)
        else:
            hand, prog = None, 0
        if hand and prog > 0.02:
            dx = state["mame"][0]
            draw_arm(f, "mame", hand, dx=dx, prog=prog)
    return f


def frame(t):
    A = assets()
    f = closeup(t) if (t < 2.0 or t >= 23.0) else wide(t)
    f = f.convert("RGBA")
    tag = tag_overlay(CHANNEL)
    f.paste(tag, (40, 70), tag)
    for t0, t1, text in CAPS:
        if t0 <= t < t1:
            cap = caption_layer(text, t0, t)
            f.paste(cap, ((W - cap.width) // 2, 1470), cap)
    return f.convert("RGB")


# ---------- son ----------
def clink():
    sr = sfx.SR
    n = int(0.35 * sr)
    t = np.arange(n) / sr
    return (np.sin(2 * np.pi * 3100 * t) + 0.7 * np.sin(2 * np.pi * 4700 * t) + 0.4 * np.sin(2 * np.pi * 6100 * t)) * np.exp(-t * 18) * 0.5


EVENTS = [(0.1, "ding", .7), (2.3, "tick", .5), (2.75, "tick", .5), (3.2, "tick", .5), (3.65, "tick", .5), (4.4, "whoosh", .4),
          (4.62, "clink", .8), (7.1, "pop", .5), (8.82, "thud", .9), (9.0, "oops", .6), (11.0, "sad_boing", .7),
          (12.8, "pop", .6), (13.2, "tick", .4), (13.6, "tick", .4), (14.0, "tick", .4), (14.4, "pop", .8), (14.5, "whoosh", .8),
          (16.4, "step", .5), (16.8, "step", .5), (17.2, "step", .5), (18.0, "pop", .6), (18.7, "crunch", .9), (19.1, "crunch", .7),
          (19.5, "crunch", .6), (21.2, "sad_boing", .5), (23.9, "thud", .7), (23.95, "ding", .8)]


def build_audio():
    sr = sfx.SR
    out = np.zeros(int(DUR * sr))
    for t, name, g in EVENTS:
        s = (clink() if name == "clink" else sfx.SOUNDS[name]()) * g
        i = int(t * sr)
        out[i:i + len(s)] += s[: len(out) - i]
    return (out / max(1e-6, np.max(np.abs(out))) * 0.9).astype(np.float32)


# ---------- rendu ----------
def render_chunk(args):
    n0, n1, out = args
    tmp = Path(out).with_name(Path(out).stem + "_tmp.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(n0, n1):
        p.stdin.write(frame(n / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg a échoué")
    os.replace(tmp, out)
    return str(out)


def main():
    a = sys.argv[1:]
    if a and a[0] == "--still":
        frame(float(a[1])).save(a[2])
        return
    out = Path(a[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / (out.stem + "_chunks")
    work.mkdir(exist_ok=True)
    total = int(round(DUR * FPS))
    step = 60
    jobs = [(n, min(total, n + step), work / f"c_{n:04d}.mp4") for n in range(0, total, step)]
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        files = list(ex.map(render_chunk, jobs))
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{Path(x).resolve()}'\n" for x in files))
    silent = work / "silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)
    wav = work / "audio.wav"
    sfx.write_wav(wav, build_audio())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print("OK :", out, f"({DUR} s)")


if __name__ == "__main__":
    main()
