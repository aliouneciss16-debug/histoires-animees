#!/usr/bin/env python3
"""Short « fait scientifique » : voix off française, visuels animés, sous-titres, bruitages. Aucune musique.

Usage :
  python src/factshort.py stories/fact_001_graine_2000_ans.json out/fact_001.mp4
  python src/factshort.py stories/fact_001_graine_2000_ans.json --still 4 2.0 out/image.png
"""
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import sfx
import voice
from render import FPS, H, W, clamp, ease, font, lerp, place_c, seg, tag_overlay, wrap
from sprites import Cv, S, paste_rot, sparkle

LEAD, TAIL = 0.25, 0.35


# ---------- sprites ----------
def _seed():
    c = Cv(300, 170)
    c.ell(150, 85, 128, 64, (112, 72, 38, 255))
    c.ell(118, 62, 62, 20, (158, 112, 68, 255))
    c.line([(48, 86), (252, 86)], (68, 42, 22, 255), 7)
    return c.done()


def _frond():
    c = Cv(360, 90)
    c.ell(180, 45, 175, 20, (70, 150, 60, 255))
    for x in range(30, 340, 16):
        c.line([(x, 45), (x + 12, 21)], (100, 180, 74, 255), 5)
        c.line([(x, 45), (x + 12, 69)], (100, 180, 74, 255), 5)
    c.line([(8, 45), (350, 45)], (40, 100, 40, 255), 6)
    return c.done()


def _dates():
    c = Cv(170, 160)
    for x, y in [(50, 40), (86, 56), (122, 40), (68, 92), (106, 96), (86, 128), (34, 76), (138, 78)]:
        c.ell(x, y, 17, 25, (176, 84, 24, 255))
        c.ell(x - 5, y - 8, 5, 9, (222, 140, 70, 255))
    c.line([(86, 0), (86, 40)], (96, 70, 40, 255), 6)
    return c.done()


def _pot():
    c = Cv(320, 260)
    c.poly([(30, 40), (290, 40), (250, 250), (70, 250)], (196, 98, 56, 255))
    c.rrect((12, 10, 308, 60), 18, (214, 116, 70, 255))
    c.ell(160, 38, 130, 22, (90, 58, 34, 255))
    return c.done()


def _hill(color):
    c = Cv(1080, 360)
    c.ell(540, 380, 760, 300, color)
    return c.done()


def _mesa():
    c = Cv(1080, 560)
    c.poly([(0, 560), (0, 440), (150, 330), (230, 250), (850, 250), (930, 330), (1080, 430), (1080, 560)], (178, 122, 74, 255))
    c.poly([(0, 560), (0, 500), (260, 360), (420, 300), (420, 560)], (150, 100, 60, 255))
    c.rrect((290, 190, 790, 252), 4, (236, 218, 184, 255))
    for x in (290, 540, 760):
        c.rrect((x - 10, 120, x + 40, 252), 4, (226, 204, 168, 255))
        c.rrect((x + 6, 150, x + 24, 190), 6, (90, 60, 40, 255))
    for x in range(310, 780, 60):
        c.rrect((x, 172, x + 28, 192), 2, (236, 218, 184, 255))
    return c.done()


def _cabinet():
    c = Cv(560, 560)
    c.rrect((20, 20, 540, 540), 26, (140, 96, 58, 255))
    c.rrect((50, 50, 510, 180), 14, (28, 18, 12, 255))      # tiroir du haut ouvert (vide)
    for y in (200, 360):
        c.rrect((50, y, 510, y + 140), 14, (170, 122, 76, 255))
        c.rrect((230, y + 56, 330, y + 84), 14, (230, 200, 120, 255))
    return c.done()


def _drawer_front():
    c = Cv(460, 130)
    c.rrect((0, 0, 460, 130), 14, (170, 122, 76, 255))
    c.rrect((180, 50, 280, 78), 14, (230, 200, 120, 255))
    return c.done()



def _clip_circle(layer_cv, margin, size):
    from PIL import ImageChops
    mask = Image.new("L", (size * S, size * S), 0)
    ImageDraw.Draw(mask).ellipse([margin * S, margin * S, (size - margin) * S, (size - margin) * S], fill=255)
    layer_cv.im.putalpha(ImageChops.multiply(layer_cv.im.getchannel("A"), mask))


def _earth():
    c = Cv(600, 600)
    c.ell(300, 300, 290, 290, (36, 98, 186, 255))
    land = Cv(600, 600)
    for x, y, rx, ry in [(220, 210, 110, 80), (400, 250, 70, 110), (280, 400, 120, 60), (440, 440, 60, 50), (150, 340, 50, 70), (330, 120, 70, 40)]:
        land.ell(x, y, rx, ry, (66, 164, 86, 255))
    for x, y, rx, ry in [(180, 150, 120, 16), (380, 330, 140, 14), (240, 470, 110, 14), (420, 150, 90, 12)]:
        land.ell(x, y, rx, ry, (255, 255, 255, 170))
    _clip_circle(land, 10, 600)
    c.im.alpha_composite(land.im)
    shade = Cv(600, 600)
    shade.ell(380, 330, 330, 330, (0, 0, 20, 0))
    c.arc((12, 12, 588, 588), 200, 340, (150, 200, 255, 255), 10)
    return c.done()


def _jupiter():
    c = Cv(600, 600)
    c.ell(300, 300, 290, 290, (214, 170, 120, 255))
    bands = Cv(600, 600)
    for y0, y1, col in [(40, 110, (190, 140, 96, 255)), (110, 170, (232, 206, 170, 255)), (170, 250, (176, 112, 70, 255)),
                        (250, 300, (240, 220, 190, 255)), (300, 370, (186, 128, 84, 255)), (370, 430, (232, 206, 170, 255)),
                        (430, 500, (170, 116, 76, 255)), (500, 560, (210, 168, 120, 255))]:
        bands.rrect((0, y0, 600, y1), 6, col)
    bands.ell(400, 370, 52, 30, (190, 70, 50, 255))
    _clip_circle(bands, 10, 600)
    c.im.alpha_composite(bands.im)
    return c.done()


def _radial(inner, outer, glow, size=1200, radius=500):
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - size / 2, yy - size / 2)
    k = np.clip(r / radius, 0, 1)[..., None]
    rgb = np.array(inner) * (1 - k) + np.array(outer) * k
    a = np.where(r <= radius, 255.0, np.clip(1 - (r - radius) / (size / 2 - radius), 0, 1) ** 2 * glow)
    arr = np.dstack([rgb, a]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def pill(text, fill=(255, 255, 255, 235), color=(40, 40, 60), size=46):
    fnt = font(True, size)
    d0 = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    w = int(d0.textlength(text, font=fnt)) + 70
    img = Image.new("RGBA", (w, size + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, size + 39], radius=(size + 40) // 2, fill=fill)
    d.text((w / 2, (size + 40) / 2), text, font=fnt, fill=color, anchor="mm")
    return img


class Assets:
    def __init__(self):
        self.seed, self.frond, self.dates, self.pot = _seed(), _frond(), _dates(), _pot()
        self.mesa, self.cabinet, self.front = _mesa(), _cabinet(), _drawer_front()
        self.hill = _hill((92, 168, 84, 255))
        self.earth, self.jupiter = _earth(), _jupiter()
        self.sun = _radial((255, 250, 190), (255, 150, 40), 140)
        self.giant = _radial((255, 190, 120), (200, 50, 30), 120)
        self.channel = ""
        rnd = __import__("random").Random(11)
        self.stars = [(rnd.randint(0, W), rnd.randint(0, H), rnd.choice([1, 1, 2, 2, 3]), rnd.random() * 6) for _ in range(150)]
        self.sparkle = sparkle()
        self.bgs = {}
        self.pills = {}

    def bg(self, colors):
        key = tuple(map(tuple, colors))
        if key not in self.bgs:
            top, bot = colors
            col = np.linspace(0, 1, H)[:, None, None]
            arr = (np.array(top) * (1 - col) + np.array(bot) * col).astype(np.uint8)
            self.bgs[key] = Image.fromarray(np.repeat(arr, W, axis=1), "RGB")
        return self.bgs[key]

    def label(self, text, **kw):
        k = (text, tuple(sorted(kw.items())))
        if k not in self.pills:
            self.pills[k] = pill(text, **kw)
        return self.pills[k]


def paste_anchor(f, spr, ax, ay, px, py, angle, scale=1.0):
    if scale != 1.0:
        spr = spr.resize((int(spr.width * scale), int(spr.height * scale)), Image.BILINEAR)
        ax, ay = ax * scale, ay * scale
    w, h = spr.size
    r = spr.rotate(angle, expand=True, resample=Image.BILINEAR)
    vx, vy = ax - w / 2, ay - h / 2
    th = math.radians(angle)
    rx = vx * math.cos(th) + vy * math.sin(th)
    ry = -vx * math.sin(th) + vy * math.cos(th)
    f.paste(r, (int(px - (r.width / 2 + rx)), int(py - (r.height / 2 + ry))), r)


# ---------- palmier ----------
def palm(f, A, x, base_y, h, grow=1.0, t=0.0, dates=0.0):
    hh = max(10, h * grow)
    sway = math.sin(t * 1.5) * 6
    top_x, top_y = x + sway, base_y - hh
    d = ImageDraw.Draw(f)
    d.polygon([(x - 28, base_y), (x + 28, base_y), (top_x + 16, top_y), (top_x - 16, top_y)], fill=(142, 98, 60))
    for k in range(1, int(hh / 40)):
        yy = base_y - k * 40
        xx = lerp(x, top_x, k * 40 / hh)
        wd = lerp(28, 16, k * 40 / hh)
        d.line([(xx - wd, yy), (xx + wd, yy - 6)], fill=(112, 76, 44), width=4)
    fs = 0.2 + 0.45 * grow
    for k, a in enumerate([8, 38, 72, 108, 142, 172, -26, 206]):
        paste_anchor(f, A.frond, 8, 45, top_x, top_y, a + math.sin(t * 1.8 + k) * 3, scale=fs)
    if dates > 0:
        place_c(f, A.dates, top_x - 10, top_y + 70 * dates, 0.35 + 0.35 * ease(dates))


# ---------- visuels ----------
def vis_counter_years(f, A, t, dur):
    cx = 540
    glow = Image.new("RGBA", (700, 700), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([60, 60, 640, 640], fill=(255, 244, 190, 150))
    place_c(f, glow, cx, 560, 1.0 + 0.04 * math.sin(t * 4))
    place_c(f, A.seed, cx, 560, 1.5, rot=-18 + 4 * math.sin(t * 3))
    n = int(2000 * ease(seg(t, 0.25, 2.2)))
    txt = f"{n:,}".replace(",", " ")
    d = ImageDraw.Draw(f)
    d.text((cx, 900), txt, font=font(True, 220), fill=(120, 62, 18), anchor="mm")
    d.text((cx, 1060), "ans", font=font(True, 110), fill=(150, 84, 28), anchor="mm")


def vis_masada(f, A, t, dur):
    p = t / dur
    sun_y = lerp(760, 470, ease(seg(t, 0, 1.6)))
    sun = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    ImageDraw.Draw(sun).ellipse([20, 20, 340, 340], fill=(255, 238, 170, 120))
    ImageDraw.Draw(sun).ellipse([80, 80, 280, 280], fill=(255, 220, 90, 255))
    place_c(f, sun, 790, sun_y, 1.0)
    f.paste(A.mesa, (0, 640), A.mesa)
    k = ease(seg(p, 0.45, 0.65))
    if k > 0:
        place_c(f, A.seed, 540, 770 - 30 * math.sin(math.pi * k), 0.5 * k + 0.2, rot=-20)
        if p > 0.5:
            place_c(f, A.sparkle, 600, 730, 0.6 * abs(math.sin(t * 6)), rot=t * 90)
    lab = A.label("Massada · Israël")
    f.paste(lab, ((W - lab.width) // 2, 330), lab)


def vis_drawer(f, A, t, dur):
    open_k = ease(seg(t, 0.4, 1.4))
    cx, cy = 540, 640
    place_c(f, A.cabinet, cx, cy, 1.45)
    place_c(f, A.seed, cx - 10, cy - 230, 0.8 * open_k + 0.01, rot=-10)
    place_c(f, A.front, cx + 160 * open_k, cy - 215 + 120 * open_k, 1.45 * (1 + 0.06 * open_k))
    d = ImageDraw.Draw(f)
    for i in range(14):
        ph = (t * 0.12 + i * 0.137) % 1
        x = 300 + (i * 71) % 480 + math.sin(t * 1.5 + i) * 18
        y = 920 - ph * 640
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 245, 220))


def _sprout_img(g, t):
    c = Cv(260, 560)
    h = 30 + 330 * g
    pts = []
    for k in range(11):
        u = k / 10
        pts.append((130 + math.sin(u * 3 + t) * 8 * u, 540 - h * u))
    c.line(pts, (74, 160, 62, 255), 14)
    tx, ty = pts[-1]
    k = 0.35 + 0.65 * g
    leaf = Cv(160, 70)
    leaf.ell(80, 35, 76, 24, (104, 190, 80, 255))
    leaf.line([(6, 35), (150, 35)], (60, 130, 50, 255), 4)
    right = leaf.im.resize((int(160 * S * k), int(70 * S * k)), Image.BILINEAR)
    left = right.transpose(Image.FLIP_LEFT_RIGHT)
    paste_rot(c, right, tx + 62 * k, ty - 18 * k, 30)
    paste_rot(c, left, tx - 62 * k, ty - 18 * k, -30)
    return c.done()


def vis_sprout(f, A, t, dur):
    p = t / dur
    pot_y = 960
    g = ease(seg(p, 0.3, 0.95))
    if g > 0:
        s = _sprout_img(g, t)
        f.paste(s, (540 - 130, pot_y - 112 - 540), s)
    place_c(f, A.pot, 540, pot_y, 1.2)
    if g == 0:
        place_c(f, A.seed, 540, pot_y - 110, 0.3, rot=-15)
    if 0.35 < p < 0.8:
        for k in range(4):
            a = t * 6 + k * 1.57
            place_c(f, A.sparkle, 540 + 130 * math.cos(a), pot_y - 330 + 90 * math.sin(a), 0.5, rot=a * 60)
    lab = A.label("2005", size=70)
    f.paste(lab, ((W - lab.width) // 2, 260), lab)


def ground(f, A, y=980):
    f.paste(A.hill, (0, y), A.hill)
    ImageDraw.Draw(f).rectangle([0, y + 250, W, H], fill=(92, 168, 84))


def vis_palm(f, A, t, dur):
    p = t / dur
    ground(f, A)
    grow = ease(seg(p, 0.0, 0.55))
    palm(f, A, 460, 1130, 620, grow, t)
    k = ease(seg(p, 0.55, 0.7))
    if k > 0:
        x = 840
        top = 1130 - 620 * grow
        d = ImageDraw.Draw(f)
        d.line([(x, 1130), (x, top)], fill=(40, 40, 60), width=8)
        for yy in range(1130, int(top) - 1, -70):
            d.line([(x - 18, yy), (x + 18, yy)], fill=(40, 40, 60), width=6)
        lab = A.label("3 m +", size=64)
        f.paste(lab, (x - lab.width // 2, int(top) - 120), lab)
    lab = A.label("2015", size=70)
    f.paste(lab, ((W - lab.width) // 2, 250), lab)


def vis_dates(f, A, t, dur):
    p = t / dur
    ground(f, A)
    palm(f, A, 290, 1130, 600, 1.0, t)
    palm(f, A, 800, 1130, 600, 1.0, t + 1, dates=ease(seg(p, 0.55, 0.8)))
    d = ImageDraw.Draw(f)
    if p < 0.8:
        for i in range(12):
            u = ((t * 0.55 + i / 12) % 1)
            x = lerp(290, 800, u)
            y = lerp(530, 530, u) - math.sin(math.pi * u) * 190
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, 214, 64))
    for x, txt in ((290, "mâle"), (800, "femelle")):
        lab = A.label(txt, size=46)
        f.paste(lab, (x - lab.width // 2, 1040), lab)


def vis_cta(f, A, t, dur):
    bounce = abs(math.sin(t * 4)) * 24
    place_c(f, A.seed, 540, 560 - bounce, 1.6, rot=-18)
    d = ImageDraw.Draw(f)
    d.text((540, 860), A.channel, font=font(True, 96), fill=(110, 56, 16), anchor="mm")
    for k in range(5):
        a = t * 3 + k * 1.25
        place_c(f, A.sparkle, 540 + 360 * math.cos(a), 640 + 230 * math.sin(a), 0.5, rot=a * 70)


def starfield(f, A, t):
    d = ImageDraw.Draw(f)
    for x, y, r, ph in A.stars:
        v = int(150 + 105 * abs(math.sin(t * 1.3 + ph)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, min(255, v + 20)))


def body(f, spr, base, cx, cy, diameter):
    place_c(f, spr, cx, cy, diameter / base)


def vis_s_earth(f, A, t, dur):
    starfield(f, A, t)
    k = 1 + 0.02 * math.sin(t * 3)
    body(f, A.earth, 580, 540, 560, 520 * k)
    lab = A.label("La Terre", size=52)
    f.paste(lab, ((W - lab.width) // 2, 880), lab)
    ImageDraw.Draw(f).text((540, 1030), "12 756 km", font=font(True, 96), fill=(255, 255, 255), anchor="mm")


def vis_s_jupiter(f, A, t, dur):
    starfield(f, A, t)
    jx = lerp(1500, 700, ease(seg(t, 0.3, 1.3)))
    body(f, A.jupiter, 580, jx, 600, 60 * 11.209)
    body(f, A.earth, 580, 200, 700, 60)
    lab = A.label("Terre", size=42)
    f.paste(lab, (200 - lab.width // 2, 750), lab)
    if t > 1.2:
        lab = A.label("Jupiter ×11", size=46)
        f.paste(lab, (700 - lab.width // 2, 960), lab)


def vis_s_sun(f, A, t, dur):
    starfield(f, A, t)
    e = ease(seg(t, 0.25, 2.6))
    sun_d = lerp(260, 800, e)
    sun_y = lerp(-120, 540, e)
    body(f, A.sun, 1000, 540, sun_y, sun_d)
    jd, ed = lerp(672, 82, e), lerp(60, 7.3, e)
    jx, jy = lerp(700, 300, e), lerp(600, 1020, e)
    ex, ey = lerp(200, 470, e), lerp(700, 1020, e)
    body(f, A.jupiter, 580, jx, jy, jd)
    body(f, A.earth, 580, ex, ey, ed)
    if e > 0.85:
        d = ImageDraw.Draw(f)
        d.ellipse([ex - 22, ey - 22, ex + 22, ey + 22], outline=(255, 255, 255), width=3)
        for x, txt in ((jx, "Jupiter"), (ex + 70, "Terre")):
            lab = A.label(txt, size=34)
            f.paste(lab, (int(x - lab.width // 2), 1065), lab)
        lab = A.label("Soleil ×109", size=54)
        f.paste(lab, ((W - lab.width) // 2, 500), lab)


def vis_s_fill(f, A, t, dur):
    starfield(f, A, t)
    body(f, A.sun, 1000, 540, 560, 800)
    n = int(700 * ease(seg(t, 0.3, 3.0)))
    d = ImageDraw.Draw(f)
    for i in range(n):
        r = 380 * math.sqrt((i + 0.5) / 700)
        a = i * 2.39996
        x, y = 540 + r * math.cos(a), 560 + r * math.sin(a)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(70, 140, 255), outline=(220, 240, 255))
    cnt = int(1304000 * ease(seg(t, 0.3, 3.0)))
    d.text((540, 1040), f"{cnt:,}".replace(",", " ") + " Terres", font=font(True, 76), fill=(255, 255, 255), anchor="mm")


def vis_s_giant(f, A, t, dur):
    starfield(f, A, t)
    gx = lerp(2400, 1500, ease(seg(t, 0.3, 1.6)))
    body(f, A.giant, 1000, gx, 1000, 2000)
    body(f, A.sun, 1000, 280, 640, 110)
    lab = A.label("Soleil", size=40)
    f.paste(lab, (280 - lab.width // 2, 720), lab)
    if t > 1.4:
        lab = A.label("Étoile géante", size=50)
        f.paste(lab, (760 - lab.width // 2, 560), lab)


def vis_cta2(f, A, t, dur):
    starfield(f, A, t)
    bounce = abs(math.sin(t * 4)) * 24
    body(f, A.earth, 580, 540, 560 - bounce, 420)
    ImageDraw.Draw(f).text((540, 860), A.channel, font=font(True, 92), fill=(255, 255, 255), anchor="mm")


VIS = {"counter_years": vis_counter_years, "masada": vis_masada, "drawer": vis_drawer,
       "sprout": vis_sprout, "palm": vis_palm, "dates": vis_dates, "cta": vis_cta,
       "s_earth": vis_s_earth, "s_jupiter": vis_s_jupiter, "s_sun": vis_s_sun, "s_fill": vis_s_fill,
       "s_giant": vis_s_giant, "cta2": vis_cta2}


# ---------- légende ----------
def caption_img(text):
    fnt = font(True, 76)
    lines = wrap(text, fnt, 880)
    h = 60 + len(lines) * 96
    img = Image.new("RGBA", (960, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, 959, h - 1], radius=48, fill=(22, 30, 52, 205))
    y = 30
    for ln in lines:
        d.text((480, y + 48), ln, font=fnt, fill=(255, 255, 255), anchor="mm")
        y += 96
    return img


_A = None


def assets():
    global _A
    if _A is None:
        _A = Assets()
    return _A


def frame(story, idx, t, dur):
    A = assets()
    sc = story["scenes"][idx]
    A.channel = story["channel"]
    f = A.bg(sc["bg"]).copy()
    VIS[sc["visual"]](f, A, t, dur)
    tag = tag_overlay(story["channel"])
    f.paste(tag, (40, 70), tag)
    cap = caption_img(sc["caption"])
    k = ease(seg(t, 0.05, 0.4))
    if k < 1:
        cap = cap.copy()
        cap.putalpha(cap.getchannel("A").point(lambda v: int(v * k)))
    f.paste(cap, ((W - cap.width) // 2, int(1150 + (1 - k) * 30)), cap)
    return f


def render_scene(args):
    story, idx, dur, out = args
    tmp = out.with_name(out.stem + "_tmp.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(int(round(dur * FPS))):
        p.stdin.write(frame(story, idx, n / FPS, dur).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg a échoué (scène {idx + 1})")
    os.replace(tmp, out)
    return str(out)


# ---------- audio ----------
def build_audio(story, clips, durs):
    sr = sfx.SR
    total = sum(durs)
    out = np.zeros(int(total * sr) + sr)
    starts = np.cumsum([0] + durs[:-1])
    for i, clip in enumerate(clips):
        v = np.interp(np.arange(int(len(clip) * sr / voice.SR_VOICE)) * voice.SR_VOICE / sr, np.arange(len(clip)), clip)
        s0 = int((starts[i] + LEAD) * sr)
        out[s0:s0 + len(v)] += v
    ev = []
    for i, sc in enumerate(story["scenes"]):
        vlen = len(clips[i]) / voice.SR_VOICE
        if i > 0:
            ev.append((starts[i] + 0.02, "whoosh", 0.35))
        for t, name, g in sc.get("sfx", []):
            ev.append((starts[i] + (LEAD + vlen + t if t < 0 else t), name, g))
        if sc.get("ticks"):
            t0, t1, dt = sc["ticks"]
            t = t0
            while t < t1:
                ev.append((starts[i] + t, "tick", 0.25))
                t += dt
    fx = np.zeros_like(out)
    for t, name, g in ev:
        s = sfx.SOUNDS[name]() * g
        i0 = int(t * sr)
        fx[i0:i0 + len(s)] += s[: len(fx) - i0]
    out = out + fx * 0.55
    out = out[: int(total * sr)]
    out = out / max(1e-6, np.max(np.abs(out))) * 0.92
    return out.astype(np.float32)


def timeline(story, model_dir):
    clips = [voice.say(sc["text"], story.get("voice", "ff_siwis"), story.get("speed", 0.95), model_dir)
             for sc in story["scenes"]]
    durs = [LEAD + len(c) / voice.SR_VOICE + TAIL for c in clips]
    return clips, durs


def main():
    a = sys.argv[1:]
    story = json.loads(Path(a[0]).read_text(encoding="utf-8"))
    model_dir = os.environ.get("MODEL_DIR", "/home/claude/models" if Path("/home/claude/models").exists() else "models")
    clips, durs = timeline(story, model_dir)
    if "--still" in a:
        i = a.index("--still")
        idx, t, out = int(a[i + 1]) - 1, float(a[i + 2]), a[i + 3]
        frame(story, idx, t, durs[idx]).save(out)
        print("durées des scènes :", [round(x, 2) for x in durs])
        return
    out = Path(a[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / (out.stem + "_scenes")
    work.mkdir(exist_ok=True)
    jobs = [(story, i, durs[i], work / f"scene_{i + 1}.mp4") for i in range(len(durs))]
    with ProcessPoolExecutor(max_workers=min(len(jobs), os.cpu_count() or 2)) as ex:
        files = list(ex.map(render_scene, jobs))
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{Path(x).resolve()}'\n" for x in files))
    silent = work / "video_silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(silent)], check=True)
    wav = work / "audio.wav"
    sfx.write_wav(wav, build_audio(story, clips, durs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
                    "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print("OK :", out, f"({sum(durs):.1f} s)")


if __name__ == "__main__":
    main()
