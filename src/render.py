#!/usr/bin/env python3
"""Génère une vidéo verticale 1080x1920 (Shorts) à partir d'un fichier d'histoire JSON.

Usage :
  python src/render.py stories/001_la_pomme_partagee.json out/001.mp4
  python src/render.py stories/001_la_pomme_partagee.json --still 3 2.0 out/still.png
"""
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import sfx
import sprites as sp

W, H, FPS, SCENE_S = 1080, 1920, 30, 6
GY = 1500
RX, BX = 250, 420
R_SC, P_SC, B_SC = 0.8, 0.85, 0.8
SLOTS = [(-72, -135), (-24, -135), (24, -135), (72, -135), (-48, -172), (0, -172), (48, -172), (0, -208)]
G_APPLES = [(BX + 230, GY + 18), (BX + 290, GY + 28)]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def seg(s, a, b):
    return clamp((s - a) / (b - a))


def font(bold, size, oblique=False):
    base = "/usr/share/fonts/truetype/dejavu/"
    name = "DejaVuSans-Bold.ttf" if bold else ("DejaVuSans-Oblique.ttf" if oblique else "DejaVuSans.ttf")
    try:
        return ImageFont.truetype(base + name, size)
    except OSError:
        return ImageFont.load_default()


class Assets:
    def __init__(self):
        self.bg = sp.background().convert("RGB")
        self.fox = {e: sp.fox(e) for e in sp.EXPR}
        self.hog = {e: sp.hedgehog(e) for e in sp.EXPR}
        self.apple = sp.apple()
        self.basket_back, self.basket_front = sp.basket_parts()
        self.heart = sp.heart()
        self.sparkle = sp.sparkle()
        self.sweat = sp.sweat()
        self.bubble = sp.bubble()
        self.cross = sp.red_cross()
        self.birds = [sp.bird(0), sp.bird(1)]
        self.clouds = [sp.cloud()] * 3
        self.tree = sp.tree_layer()
        sh = Image.new("RGBA", (400, 80), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([0, 0, 400, 80], fill=(30, 60, 30, 70))
        self.shadow = sh


# ---------- dessin ----------
def place(f, spr, x, feet, scale=1.0, flip=False, rot=0.0, sx=1.0, sy=1.0):
    nw, nh = max(1, int(spr.width * scale * sx)), max(1, int(spr.height * scale * sy))
    s = spr.resize((nw, nh), Image.BILINEAR)
    if flip:
        s = s.transpose(Image.FLIP_LEFT_RIGHT)
    if rot:
        s = s.rotate(rot, expand=True, resample=Image.BILINEAR)
    f.paste(s, (int(x - s.width / 2), int(feet - nh / 2 - s.height / 2)), s)


def place_c(f, spr, cx, cy, scale=1.0, rot=0.0):
    s = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))), Image.BILINEAR)
    if rot:
        s = s.rotate(rot, expand=True, resample=Image.BILINEAR)
    f.paste(s, (int(cx - s.width / 2), int(cy - s.height / 2)), s)


def shadow(f, A, x, w=1.0):
    place_c(f, A.shadow, x, GY + 8, scale=w * 0.9)


def draw_basket(f, A, x, feet, apples, rot=0.0, sc=B_SC):
    g = Image.new("RGBA", (400, 420), (0, 0, 0, 0))
    g.alpha_composite(A.basket_back, (60, 210))
    for i in apples:
        dx, dy = SLOTS[i]
        g.alpha_composite(A.apple, (int(200 + dx - 55), int(400 + dy - 60)))
    g.alpha_composite(A.basket_front, (60, 210))
    g = g.resize((int(400 * sc), int(420 * sc)), Image.BILINEAR)
    if rot:
        g = g.rotate(rot, expand=True, resample=Image.BILINEAR, center=(g.width / 2, g.height - 4))
    f.paste(g, (int(x - g.width / 2), int(feet - g.height)), g)


def slot_world(i, bx=BX, feet=GY + 8, sc=B_SC):
    dx, dy = SLOTS[i]
    return bx + dx * sc, feet + dy * sc


def fox(f, A, expr, x, feet=GY, **kw):
    shadow(f, A, x, 1.0)
    place(f, A.fox[expr], x, feet, R_SC, **kw)


def hog(f, A, expr, x, feet=GY, **kw):
    shadow(f, A, x, 0.85)
    place(f, A.hog[expr], x, feet, P_SC, **kw)


def tree_apples(f, A, s, which):
    for i in which:
        x, y = sp.APPLE_SPOTS[i]
        place_c(f, A.apple, x + math.sin(s * 2 + i) * 4, y + math.cos(s * 2.3 + i) * 3, 0.8)


def flight(f, A, p0, p1, u, rot=0):
    x = lerp(p0[0], p1[0], ease(u))
    y = lerp(p0[1], p1[1], ease(u)) - math.sin(math.pi * u) * 170
    place_c(f, A.apple, x, y, lerp(0.8, 0.75, u), rot=rot + u * 360)


def bubble_at(f, A, cx, cy, s, t0, t1):
    if not (t0 <= s <= t1):
        return 0
    k = ease(seg(s, t0, t0 + 0.25)) * (1 - ease(seg(s, t1 - 0.2, t1)))
    place_c(f, A.bubble, cx, cy, 0.4 + 0.6 * k if k > 0 else 0.1)
    return k


def bob(s, speed=9, amp=16):
    return abs(math.sin(s * speed)) * amp


# ---------- scènes ----------
def sc1(f, A, s):
    x = lerp(-180, RX, ease(seg(s, 0, 2.6)))
    walking = s < 2.6
    b = bob(s) if walking else math.sin(s * 3) * 2
    rot = math.sin(s * 9) * 2.5 if walking else 0
    expr = "smile" if s < 3.2 else ("surprised" if s < 4.5 else "greedy")
    tree_apples(f, A, s, range(8))
    fox(f, A, expr, x, GY - b, rot=rot)
    draw_basket(f, A, x + 180, GY + 8 - b, [])
    if s > 4.2:
        for k, (px, py) in enumerate([(450, 640), (640, 700), (540, 560)]):
            sc = 0.5 + 0.35 * abs(math.sin(s * 5 + k * 1.7))
            place_c(f, A.sparkle, px, py, sc, rot=s * 90)


def sc2(f, A, s):
    launch = [0.3 + 0.45 * i for i in range(8)]
    tree_apples(f, A, s, [i for i in range(8) if s < launch[i]])
    landed = [i for i in range(8) if s >= launch[i] + 0.45]
    hop = 0
    for l in launch:
        u = (s - (l - 0.05)) / 0.4
        if 0 <= u <= 1:
            hop = max(hop, math.sin(math.pi * u) * 34)
    px = lerp(1250, 840, ease(seg(s, 1.2, 2.7)))
    pb = bob(s, 9, 14) if 1.2 < s < 2.7 else 0
    if px < 1250:
        hog(f, A, "neutral" if s < 2.8 else "worried", px, GY - pb)
    fox(f, A, "smile" if s < 2.5 else "greedy", RX, GY - hop)
    draw_basket(f, A, BX, GY + 8, landed)
    for i in range(8):
        u = (s - launch[i]) / 0.45
        if 0 <= u < 1:
            flight(f, A, sp.APPLE_SPOTS[i], slot_world(i), u)


def sc3(f, A, s):
    px = lerp(840, 780, ease(seg(s, 0.5, 1.5)))
    pb = bob(s, 9, 14) if 0.5 < s < 1.5 else 0
    tremble = 1 + 0.03 * math.sin(s * 40) if s < 1.0 else 1
    pexpr = "worried" if s < 3.2 else "sad"
    hog(f, A, pexpr, px, GY - pb, sy=tremble)
    turned = s >= 3.0
    fox(f, A, "greedy", RX, GY, flip=turned, rot=-3 if turned else 0)
    draw_basket(f, A, BX, GY + 8, range(8))
    k = bubble_at(f, A, px + 40, GY - 150 - 425 * P_SC, s, 1.5, 3.0)
    if k > 0.95:
        cx, cy = px + 10, GY - 150 - 425 * P_SC - 30
        place_c(f, A.apple, cx - 40, cy, 0.9)
        f_q = font(True, 120)
        ImageDraw.Draw(f).text((cx + 55, cy), "?", font=f_q, fill=(60, 60, 80), anchor="mm")
    k = bubble_at(f, A, RX + 20, GY - 150 - 464 * R_SC, s, 3.0, 5.6)
    if k > 0.95:
        cx, cy = RX - 10, GY - 150 - 464 * R_SC - 30
        place_c(f, A.apple, cx, cy, 1.0)
        place_c(f, A.cross, cx, cy, 0.9)


def sc4(f, A, s):
    lift = ease(seg(s, 0.4, 1.2)) * 70 * (1 - ease(seg(s, 3.4, 3.7)))
    strain = ease(seg(s, 1.0, 3.0)) * 0.07
    tremor = 0.012 * math.sin(s * 30) if 1.2 < s < 3.4 else 0
    fall = ease(seg(s, 3.4, 3.8))
    expr = "worried" if s < 3.4 else ("surprised" if s < 4.3 else "sad")
    px = 780
    pexpr = "surprised" if s > 3.4 else "worried"
    hog(f, A, pexpr, px)
    fox(f, A, expr, RX, GY + 30 * fall, rot=-14 * fall, sy=1 - strain + tremor)
    brot = 18 * ease(seg(s, 3.5, 3.9))
    rolled = s >= 3.9
    draw_basket(f, A, BX, GY + 8 - lift, range(6) if rolled else range(8), rot=brot)
    if 1.6 < s < 3.4:
        d = ((s - 1.6) % 0.9) / 0.9
        place_c(f, A.sweat, RX + 95, GY - 470 * R_SC + d * 90, 0.9)
        place_c(f, A.sweat, RX - 95, GY - 440 * R_SC + ((d + 0.5) % 1) * 90, 0.7)
    if rolled:
        for j, i in enumerate((6, 7)):
            u = seg(s, 3.9 + 0.3 * j, 4.9 + 0.3 * j)
            x0, y0 = slot_world(i, feet=GY + 8)
            gx, gy = G_APPLES[j]
            x = lerp(x0 + 40, gx, ease(u))
            y = lerp(y0, gy, u) - abs(math.sin(u * math.pi * 2)) * 36 * (1 - u)
            place_c(f, A.apple, x, y, 0.75, rot=u * 540)


def sc5(f, A, s):
    # trajets de Pico : (t0, t1, x0, x1)
    legs = [(0.0, 0.3, 780, 780), (0.3, 0.8, 780, 700), (0.8, 1.4, 700, 600), (1.4, 1.8, 600, 600),
            (1.8, 2.4, 600, 730), (2.4, 3.1, 730, 600), (3.1, 6.0, 600, 600)]
    px = 780
    moving = False
    for t0, t1, x0, x1 in legs:
        if t0 <= s < t1:
            px = lerp(x0, x1, ease(seg(s, t0, t1)))
            moving = x0 != x1
    pb = bob(s, 10, 12) if moving else 0
    carry1 = 0.8 <= s < 1.4
    carry2 = 2.4 <= s < 3.1
    hog(f, A, "smile", px, GY - pb)
    stand = ease(seg(s, 1.0, 1.6))
    rexpr = "sad" if s < 1.0 else ("surprised" if s < 3.5 else ("smile" if s < 4.5 else "happy"))
    fox(f, A, rexpr, RX, GY + 30 * (1 - stand), rot=-14 * (1 - stand))
    in_basket = list(range(6))
    if s >= 1.8:
        in_basket.append(6)
    if s >= 3.5:
        in_basket.append(7)
    draw_basket(f, A, BX, GY + 8, in_basket, rot=18 * (1 - ease(seg(s, 0.3, 0.7))))
    for j, (t_pick, t_drop) in enumerate([(0.8, 1.4), (2.4, 3.1)]):
        i = 6 + j
        gx, gy = G_APPLES[j]
        if s < t_pick:
            place_c(f, A.apple, gx, gy, 0.75, rot=540)
        elif s < t_drop:
            place_c(f, A.apple, px, GY - 45 - pb, 0.8)
        elif s < t_drop + 0.4:
            flight(f, A, (px, GY - 45), slot_world(i), (s - t_drop) / 0.4)
    if s > 3.8:
        d = s - 3.8
        place_c(f, A.heart, RX + 70, GY - 540 - d * 50, 0.5 + 0.08 * math.sin(s * 8))


def sc6(f, A, s):
    tree_apples(f, A, s, [])
    px = lerp(600, 870, ease(seg(s, 0, 0.8)))
    happy = s >= 2.4
    munch = 1 + 0.035 * math.sin(s * 18) if 3.0 < s < 5.2 else 1
    mrot = 2.5 * math.sin(s * 9) if 3.0 < s < 5.2 else 0
    hog(f, A, "happy" if happy else "smile", px, GY, sy=munch, rot=mrot)
    fox(f, A, "happy" if happy else "smile", RX, GY, sy=munch, rot=-mrot)
    eat = [3.2, 3.9, 4.6]
    launch = [0.55, 0.85, 1.15, 1.45]
    piles = [(760, GY + 42), (815, GY + 56), (930, GY + 44), (985, GY + 56)]
    in_basket = [i for i in range(3) if s < eat[i]] + ([3] if True else [])
    in_basket += [4 + j for j in range(4) if s < launch[j]]
    draw_basket(f, A, BX, GY + 8, in_basket)
    for j in range(4):
        u = (s - launch[j]) / 0.45
        if 0 <= u < 1:
            flight(f, A, slot_world(4 + j), piles[j], u)
        elif u >= 1:
            if j < 3 and s >= eat[j]:
                continue
            place_c(f, A.apple, piles[j][0], piles[j][1], 0.75)
    if s > 2.6:
        for k, (cx, cy) in enumerate([(RX - 140, GY - 420), (RX + 150, GY - 380), (px - 150, GY - 330), (px + 150, GY - 360)]):
            sc = 0.45 + 0.3 * abs(math.sin(s * 4 + k * 1.3))
            place_c(f, A.sparkle, cx, cy, sc, rot=s * 80 + k * 20)
    if s > 5.0:
        d = s - 5.0
        place_c(f, A.heart, (RX + px) / 2 - 40, GY - 520 - d * 70, 0.45)
        place_c(f, A.heart, (RX + px) / 2 + 60, GY - 480 - d * 90, 0.35)


SCENES = [sc1, sc2, sc3, sc4, sc5, sc6]


# ---------- surimpressions ----------
def wrap(text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def caption_overlay(fr, en, moral):
    ff, fe = font(True, 68), font(False, 46, oblique=True)
    lf, le = wrap(fr, ff, 860), wrap(en, fe, 860)
    h = 40 + len(lf) * 84 + 18 + len(le) * 58 + 36
    img = Image.new("RGBA", (960, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if moral:
        d.rounded_rectangle([0, 0, 959, h - 1], radius=48, fill=(30, 36, 70, 215), outline=(255, 214, 64, 255), width=8)
        c1, c2 = (255, 224, 110), (255, 240, 190)
    else:
        d.rounded_rectangle([0, 0, 959, h - 1], radius=48, fill=(20, 32, 56, 185))
        c1, c2 = (255, 255, 255), (255, 232, 170)
    y = 36
    for ln in lf:
        d.text((480, y + 40), ln, font=ff, fill=c1, anchor="mm")
        y += 84
    y += 18
    for ln in le:
        d.text((480, y + 28), ln, font=fe, fill=c2, anchor="mm")
        y += 58
    return img


def tag_overlay(channel):
    fnt = font(True, 40)
    d0 = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    w = int(d0.textlength(channel, font=fnt)) + 70
    img = Image.new("RGBA", (w, 78), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, 77], radius=39, fill=(20, 32, 56, 170))
    d.text((w / 2, 40), channel, font=fnt, fill=(255, 255, 255), anchor="mm")
    return img


def word_overlay(en, fr):
    fnt = font(True, 44)
    text = f"{en} = {fr}"
    d0 = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    w = int(d0.textlength(text, font=fnt)) + 150
    img = Image.new("RGBA", (w, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, 89], radius=45, fill=(255, 255, 255, 235), outline=(217, 58, 43, 255), width=5)
    d.text((w / 2 + 40, 47), text, font=fnt, fill=(40, 40, 60), anchor="mm")
    return img


_A = None


def assets():
    global _A
    if _A is None:
        _A = Assets()
    return _A


def frame(story, idx, s):
    A = assets()
    f = A.bg.copy()
    g = idx * SCENE_S + s
    for k, (cx, cy, i) in enumerate([(150, 250, 0), (620, 420, 1), (900, 620, 2)]):
        place_c(f, A.clouds[i], (cx + g * (6 + 3 * k)) % 1400 - 150, cy, (1.0, 0.8, 0.9)[i])
    if idx in (0, 5):
        bx = -100 + ((s + (0 if idx == 0 else 1.5)) * 190) % 1300
        by = 360 + math.sin(s * 2) * 30
        place_c(f, A.birds[int(s * 7) % 2], bx, by, 1.0)
        place_c(f, A.birds[int(s * 7 + 1) % 2], bx - 120, by + 60, 0.8)
    f.paste(A.tree, (0, 0), A.tree)
    SCENES[idx](f, A, s)
    sc = story["scenes"][idx]
    tag = tag_overlay(story["channel"])
    f.paste(tag, (40, 70), tag)
    if sc.get("moral") and s >= 3.0:
        wd = story["word_of_the_day"]
        wo = word_overlay(wd["en"], wd["fr"])
        f.paste(wo, ((W - wo.width) // 2, 190), wo)
        place_c(f, A.apple, (W - wo.width) // 2 + 62, 235, 0.5)
    cap = caption_overlay(sc["fr"], sc["en"], sc.get("moral", False))
    k = ease(seg(s, 0.1, 0.5))
    if k < 1:
        a = cap.getchannel("A").point(lambda v: int(v * k))
        cap = cap.copy()
        cap.putalpha(a)
    f.paste(cap, ((W - cap.width) // 2, int(1600 + (1 - k) * 20)), cap)
    return f


def render_scene(args):
    story, idx, out = args
    tmp = out.with_name(out.stem + "_tmp.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(SCENE_S * FPS):
        p.stdin.write(frame(story, idx, n / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg a échoué pour la scène {idx + 1}")
    os.replace(tmp, out)
    return str(out)


def sfx_events(story):
    ev = []
    for i, sc in enumerate(story["scenes"]):
        base = i * SCENE_S
        for t, name, g in sc.get("sfx", []):
            ev.append((base + t, name, g))
        for t0, t1, dt in sc.get("steps", []):
            t = t0
            while t < t1:
                ev.append((base + t, "step", 0.5))
                t += dt
    return ev


def main():
    args = sys.argv[1:]
    story = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    if "--still" in args:
        i = args.index("--still")
        idx, s, out = int(args[i + 1]) - 1, float(args[i + 2]), args[i + 3]
        frame(story, idx, s).save(out)
        return
    out = Path(args[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / (out.stem + "_scenes")
    work.mkdir(exist_ok=True)
    n = len(story["scenes"])
    jobs = [(story, i, work / f"scene_{i + 1}.mp4") for i in range(n)]
    with ProcessPoolExecutor(max_workers=min(n, os.cpu_count() or 2)) as ex:
        files = list(ex.map(render_scene, jobs))
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{Path(x).resolve()}'\n" for x in files))
    video = work / "video_silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(video)], check=True)
    wav = work / "sfx.wav"
    sfx.write_wav(wav, sfx.mix(sfx_events(story), n * SCENE_S))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav), "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print("OK :", out)


if __name__ == "__main__":
    main()
