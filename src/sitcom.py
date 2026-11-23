#!/usr/bin/env python3
"""Mini-sitcom animée « La Famille Sarr » : personnages 2D originaux, lèvres synchronisées avec la voix,
sous-titres, bruitages. Aucune musique.

Usage :
  python src/sitcom.py stories/sitcom_001_papa_et_le_wifi.json out/sitcom_001.mp4
  python src/sitcom.py stories/sitcom_001_papa_et_le_wifi.json --still 4 1.0 out/image.png
"""
import json
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
import voice
from render import FPS, H, W, ease, font, seg, tag_overlay, wrap
from sprites import Cv, S

OUT = (52, 30, 20, 255)
WHITE = (255, 255, 255, 255)
MOUTH_IN = (122, 30, 42, 255)
PAUSE, LEAD = 0.25, 0.2
Y_B = 1240  # bas des bustes (caché par le canapé)

SPEC = {
    "papa": dict(skin=(124, 80, 54), hair=(30, 22, 20), outfit=(44, 112, 192), trim=(244, 214, 120), kind="short", mustache=True,
                 scale=0.9, x=255, color=(60, 130, 220), label="Papa"),
    "maman": dict(skin=(142, 94, 64), hair=(30, 22, 20), outfit=(236, 164, 44), wrap=(214, 66, 118), kind="wrap",
                  scale=0.88, x=830, color=(232, 90, 140), label="Maman"),
    "moussa": dict(skin=(134, 88, 60), hair=(28, 20, 18), outfit=(48, 156, 86), trim=(250, 214, 60), kind="short",
                   scale=0.7, x=505, color=(60, 170, 100), label="Moussa"),
    "awa": dict(skin=(154, 102, 68), hair=(28, 20, 18), outfit=(152, 92, 204), ribbon=(250, 214, 60), kind="puffs",
                scale=0.6, x=680, color=(170, 110, 220), label="Awa"),
}
SPEC["mame"] = dict(skin=(112, 72, 48), hair=(235, 235, 235), outfit=(30, 140, 130), trim=(244, 214, 120), kind="wrap",
                    wrap=(70, 120, 200), scale=0.8, x=960, color=(70, 120, 200), label="Mame")
ORDER = ["papa", "maman", "moussa", "awa"]
MOUTH_BY_EMOTION = {"neutral": "smile", "angry": "frown", "smug": "smirk", "sad": "frown", "surprised": "o", "happy": "smile"}


def dark(c, k=0.8):
    return tuple(int(v * k) for v in c[:3]) + (255,)


def rr(c, box, r, fill, outline=OUT, w=5):
    x0, y0, x1, y1 = box
    c.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=fill, outline=outline, width=int(w * S))


def eo(c, cx, cy, rx, ry, fill, w=5):
    c.ell(cx, cy, rx, ry, fill, outline=OUT, width=w)


# ---------- personnages ----------
def make_head(sp):
    c = Cv(300, 340)
    skin = tuple(sp["skin"]) + (255,)
    hair = tuple(sp["hair"]) + (255,)
    if sp["kind"] == "puffs":
        for x in (62, 238):
            eo(c, x, 100, 46, 46, hair)
            c.ell(x, 62, 14, 12, tuple(sp["ribbon"]) + (255,), )
    rr(c, (116, 262, 184, 340), 12, dark(skin, 0.86), w=4)
    eo(c, 52, 190, 18, 28, skin, 4)
    eo(c, 248, 190, 18, 28, skin, 4)
    eo(c, 150, 180, 100, 115, skin, 5)
    if sp["kind"] == "short":
        c.d.chord([46 * S, 58 * S, 254 * S, 300 * S], 202, 338, fill=hair, outline=OUT, width=5 * S)
    elif sp["kind"] == "puffs":
        c.d.chord([46 * S, 58 * S, 254 * S, 300 * S], 208, 332, fill=hair, outline=OUT, width=5 * S)
    elif sp["kind"] == "wrap":
        wr = tuple(sp["wrap"]) + (255,)
        eo(c, 150, 70, 92, 46, wr)
        eo(c, 214, 44, 30, 26, wr)
        c.d.chord([44 * S, 56 * S, 256 * S, 300 * S], 196, 344, fill=wr, outline=OUT, width=5 * S)
        rnd = random.Random(5)
        for _ in range(16):
            c.ell(rnd.randint(70, 230), rnd.randint(62, 112), 6, 6, (255, 226, 140, 230))
        eo(c, 54, 232, 9, 14, (250, 214, 60, 255), 3)
        eo(c, 246, 232, 9, 14, (250, 214, 60, 255), 3)
    c.ell(150, 202, 15, 10, dark(skin, 0.78))
    c.ell(90, 222, 20, 11, (220, 96, 96, 90))
    c.ell(210, 222, 20, 11, (220, 96, 96, 90))
    if sp.get("mustache"):
        eo(c, 150, 222, 38, 11, hair, 3)
    return c.done()


def make_eyes(expr, look, sp):
    c = Cv(300, 100)
    skin = tuple(sp["skin"]) + (255,)
    for i, (cx, cy) in enumerate([(105, 56), (195, 56)]):
        side = -1 if i == 0 else 1
        brow = None
        if expr == "happy":
            c.arc((cx - 24, cy - 14, cx + 24, cy + 22), 200, 340, OUT, 7)
            brow = ((cx - 22, cy - 40), (cx + 22, cy - 44))
        elif expr == "closed":
            c.arc((cx - 24, cy - 14, cx + 24, cy + 14), 20, 160, OUT, 7)
            brow = ((cx - 22, cy - 40), (cx + 22, cy - 40))
        else:
            rx, ry, pr = 24, 28, 11
            if expr == "surprised":
                rx, ry, pr = 28, 34, 8
            eo(c, cx, cy, rx, ry, WHITE, 4)
            px = cx + look * 8
            c.ell(px, cy + 2, pr, pr * 1.15, OUT)
            c.ell(px + 3, cy - 3, 3.5, 3.5, WHITE)
            if expr == "smug":
                c.poly([(cx - rx - 2, cy - ry - 3), (cx + rx + 2, cy - ry - 3), (cx + rx + 2, cy - 2), (cx - rx - 2, cy - 2)], skin)
                c.line([(cx - rx, cy - 2), (cx + rx, cy - 2)], OUT, 5)
                brow = ((cx - 22, cy - 50), (cx + 22, cy - 46)) if side < 0 else ((cx - 22, cy - 36), (cx + 22, cy - 38))
            elif expr == "angry":
                brow = ((cx + side * 24, cy - 50), (cx - side * 24, cy - 30))
            elif expr == "sad":
                brow = ((cx + side * 24, cy - 34), (cx - side * 24, cy - 52))
            elif expr == "surprised":
                brow = ((cx - 22, cy - 54), (cx + 22, cy - 54))
            else:
                brow = ((cx - 22, cy - 42), (cx + 22, cy - 42))
        c.line(list(brow), OUT, 7)
    return c.done()


def make_mouth(kind):
    c = Cv(120, 80)
    cx, cy = 60, 34
    if kind == "smile":
        c.arc((cx - 30, cy - 24, cx + 30, cy + 16), 15, 165, OUT, 6)
    elif kind == "flat":
        c.line([(cx - 20, cy + 4), (cx + 20, cy + 4)], OUT, 6)
    elif kind == "frown":
        c.arc((cx - 26, cy + 4, cx + 26, cy + 42), 200, 340, OUT, 6)
    elif kind == "smirk":
        c.line([(cx - 22, cy + 8), (cx + 22, cy - 4)], OUT, 6)
    else:
        rx, ry = {"small": (16, 9), "mid": (22, 16), "wide": (28, 24), "o": (13, 16)}[kind]
        eo(c, cx, cy + 8, rx, ry, MOUTH_IN, 4)
        c.ell(cx, cy + 8 + ry * 0.5, rx * 0.6, ry * 0.42, (230, 110, 120, 255))
        if kind == "wide":
            c.rrect((cx - rx * 0.66, cy + 8 - ry * 0.95, cx + rx * 0.66, cy + 8 - ry * 0.45), 4, WHITE)
    return c.done()


def make_body(sp, name):
    c = Cv(460, 320)
    outfit = tuple(sp["outfit"]) + (255,)
    rr(c, (24, 36, 436, 336), 100, outfit)
    c.poly([(150, 36), (310, 36), (230, 134)], dark(tuple(sp["skin"]) + (255,), 0.9))
    c.line([(150, 36), (230, 134), (310, 36)], OUT, 5)
    if name == "papa":
        c.line([(160, 44), (230, 124), (300, 44)], tuple(sp["trim"]) + (255,), 8)
        for y in (170, 210, 250):
            c.ell(230, y, 8, 8, tuple(sp["trim"]) + (255,))
    elif name == "maman":
        rnd = random.Random(9)
        for _ in range(26):
            c.ell(rnd.randint(70, 400), rnd.randint(150, 320), 10, 10, (214, 66, 118, 230))
    elif name == "moussa":
        c.rrect((24, 190, 436, 225), 0, tuple(sp["trim"]) + (255,))
    elif name == "awa":
        eo(c, 230, 70, 100, 30, WHITE, 4)
        c.poly([(150, 36), (310, 36), (230, 134)], dark(tuple(sp["skin"]) + (255,), 0.9))
    return c.done()


class Chars:
    def __init__(self):
        self.d = {}
        for name, sp in SPEC.items():
            eyes = {(e, lk): make_eyes(e, lk, sp) for e in ("neutral", "angry", "happy", "surprised", "sad", "smug", "closed") for lk in (-1, 0, 1)}
            mouths = {k: make_mouth(k) for k in ("smile", "flat", "frown", "smirk", "small", "mid", "wide", "o")}
            self.d[name] = dict(head=make_head(sp), body=make_body(sp, name), eyes=eyes, mouths=mouths)


# ---------- décor ----------
def make_room():
    k = 2
    im = Image.new("RGB", (W * k, H * k))
    d = ImageDraw.Draw(im)
    for y in range(1360 * k):
        t = y / (1360 * k)
        d.line([(0, y), (W * k, y)], fill=(int(250 - 12 * t), int(234 - 20 * t), int(204 - 30 * t)))
    d.rectangle([0, 1020 * k, W * k, 1360 * k], fill=(226, 196, 156))
    d.rectangle([0, 1010 * k, W * k, 1024 * k], fill=(190, 150, 110))
    for y in range(1360 * k, H * k):
        t = (y - 1360 * k) / ((H - 1360) * k)
        d.line([(0, y), (W * k, y)], fill=(int(184 - 20 * t), int(132 - 16 * t), int(88 - 12 * t)))
    for x in range(0, W * k, 180 * k):
        d.line([(x, 1360 * k), (x - 120 * k, H * k)], fill=(140, 98, 62), width=3 * k)
    # fenêtre
    d.rounded_rectangle([60 * k, 230 * k, 340 * k, 560 * k], radius=16 * k, fill=(255, 255, 255), outline=(120, 86, 56), width=8 * k)
    d.rectangle([76 * k, 246 * k, 324 * k, 544 * k], fill=(156, 214, 246))
    d.rectangle([196 * k, 246 * k, 204 * k, 544 * k], fill=(255, 255, 255))
    d.rectangle([76 * k, 390 * k, 324 * k, 398 * k], fill=(255, 255, 255))
    d.ellipse([240 * k, 270 * k, 300 * k, 330 * k], fill=(255, 238, 160))
    d.polygon([(40 * k, 220 * k), (120 * k, 220 * k), (100 * k, 600 * k), (40 * k, 600 * k)], fill=(212, 96, 70))
    d.polygon([(320 * k, 220 * k), (360 * k, 220 * k), (360 * k, 600 * k), (300 * k, 600 * k)], fill=(212, 96, 70))
    # télé
    d.rounded_rectangle([440 * k, 230 * k, 1010 * k, 560 * k], radius=22 * k, fill=(30, 30, 38))
    d.rectangle([700 * k, 560 * k, 750 * k, 600 * k], fill=(30, 30, 38))
    d.rounded_rectangle([620 * k, 596 * k, 830 * k, 616 * k], radius=8 * k, fill=(30, 30, 38))
    # horloge
    d.ellipse([480 * k, 90 * k, 580 * k, 190 * k], fill=(255, 255, 255), outline=(120, 86, 56), width=6 * k)
    d.line([(530 * k, 140 * k), (530 * k, 108 * k)], fill=(40, 40, 40), width=4 * k)
    d.line([(530 * k, 140 * k), (556 * k, 152 * k)], fill=(40, 40, 40), width=4 * k)
    return im.resize((W, H), Image.LANCZOS)


def make_tv(connected):
    w, h = 550, 310
    im = Image.new("RGB", (w, h), (42, 44, 56))
    d = ImageDraw.Draw(im)
    if connected:
        d.rectangle([0, 0, w, h], fill=(48, 150, 76))
        d.rectangle([20, 20, w - 20, h - 20], outline=(255, 255, 255), width=4)
        d.line([(w // 2, 20), (w // 2, h - 20)], fill=(255, 255, 255), width=4)
        d.ellipse([w // 2 - 50, h // 2 - 50, w // 2 + 50, h // 2 + 50], outline=(255, 255, 255), width=4)
        d.rounded_rectangle([20, 26, 190, 70], radius=10, fill=(214, 40, 40))
        d.text((105, 48), "EN DIRECT", font=font(True, 28), fill=(255, 255, 255), anchor="mm")
    else:
        for i, r in enumerate((90, 62, 34)):
            d.arc([w // 2 - r, h // 2 - r + 40, w // 2 + r, h // 2 + r + 40], 210, 330, fill=(120, 124, 140), width=12)
        d.ellipse([w // 2 - 9, h // 2 + 38, w // 2 + 9, h // 2 + 56], fill=(120, 124, 140))
        d.line([(w // 2 + 40, h // 2 - 70), (w // 2 + 100, h // 2 - 10)], fill=(220, 50, 50), width=12)
        d.line([(w // 2 + 100, h // 2 - 70), (w // 2 + 40, h // 2 - 10)], fill=(220, 50, 50), width=12)
        d.text((w // 2, h - 42), "Pas de connexion", font=font(True, 34), fill=(200, 204, 216), anchor="mm")
    return im


def make_sofa():
    c = Cv(W, 300)
    rr(c, (-20, 40, 1100, 330), 70, (196, 98, 56, 255), w=6)
    rr(c, (-20, 0, 150, 330), 60, (166, 78, 44, 255), w=6)
    rr(c, (930, 0, 1100, 330), 60, (166, 78, 44, 255), w=6)
    for x in (170, 540):
        rr(c, (x, 70, x + 370, 330), 40, (214, 118, 72, 255), w=5)
    return c.done()


class Assets:
    def __init__(self):
        self.room = make_room()
        self.tv = {False: make_tv(False), True: make_tv(True)}
        self.sofa = make_sofa()
        self.chars = Chars().d


_A = None


def assets():
    global _A
    if _A is None:
        _A = Assets()
    return _A


# ---------- dessin d'une image ----------
def draw_char(f, A, name, expr, look, mouth, t, speaking, amp, dx=0, dy=0):
    sp, ch = SPEC[name], A.chars[name]
    phase = {"papa": 0.0, "maman": 0.9, "moussa": 1.7, "awa": 2.4, "mame": 3.1}[name]
    blink = ((t + phase * 1.3) % 3.4) < 0.12
    comp = Image.new("RGBA", (460, 650), (0, 0, 0, 0))
    comp.alpha_composite(ch["body"], (0, 330))
    head = ch["head"].copy()
    head.alpha_composite(ch["eyes"][("closed" if blink else expr, look)], (0, 115))
    head.alpha_composite(ch["mouths"][mouth], (90, 197))
    tilt = (3.0 * math.sin(t * 5 + phase)) * (1.0 if speaking else 0.3)
    head = head.rotate(tilt, center=(150, 330), resample=Image.BICUBIC)
    bob = int(4 * math.sin(t * 2 + phase) + (-8 * amp if speaking else 0))
    comp.alpha_composite(head, (80, 20 + bob))
    s = sp["scale"] * (1.035 if speaking else 1.0) * (1 + 0.012 * math.sin(t * 2.2 + phase))
    comp = comp.resize((int(460 * s), int(650 * s)), Image.BILINEAR)
    f.paste(comp, (int(sp["x"] + dx - comp.width / 2), int(Y_B - comp.height + dy)), comp)


def mouth_for(env, emotion):
    if env < 0.12:
        return MOUTH_BY_EMOTION[emotion]
    return "small" if env < 0.35 else ("mid" if env < 0.65 else "wide")


def caption(who, text):
    fnt = font(True, 62)
    lines = wrap(text, fnt, 860)
    h = 100 + len(lines) * 80
    img = Image.new("RGBA", (960, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 40, 959, h - 1], radius=44, fill=(22, 30, 52, 220))
    sp = SPEC[who]
    lab = font(True, 44)
    w = int(d.textlength(sp["label"], font=lab)) + 60
    d.rounded_rectangle([30, 0, 30 + w, 80], radius=40, fill=tuple(sp["color"]) + (255,))
    d.text((30 + w / 2, 41), sp["label"], font=lab, fill=(255, 255, 255), anchor="mm")
    y = 96
    for ln in lines:
        d.text((480, y + 36), ln, font=fnt, fill=(255, 255, 255), anchor="mm")
        y += 80
    return img


def frame(story, li, t, env):
    A = assets()
    line = story["lines"][li]
    f = A.room.copy()
    f.paste(A.tv[bool(line.get("wifi"))], (450, 250))
    speaker = line["who"]
    n = min(len(env) - 1, int(t * FPS))
    e = float(env[n]) if len(env) else 0.0
    react = line.get("react", {})
    for name in ORDER:
        sp = SPEC[name]
        if name == speaker:
            draw_char(f, A, name, line["emotion"], 0, mouth_for(e, line["emotion"]), t, True, e)
        else:
            look = 1 if SPEC[speaker]["x"] > sp["x"] else -1
            emo = react.get(name, "neutral")
            draw_char(f, A, name, emo, look, MOUTH_BY_EMOTION[emo], t, False, 0)
    f.paste(A.sofa, (0, 1190), A.sofa)
    tag = tag_overlay(story["channel"])
    f.paste(tag, (40, 70), tag)
    cap = caption(speaker, line["text"])
    k = ease(seg(t, 0.0, 0.25))
    if k < 1:
        cap = cap.copy()
        cap.putalpha(cap.getchannel("A").point(lambda v: int(v * k)))
    f.paste(cap, ((W - cap.width) // 2, 1390), cap)
    return f


# ---------- voix ----------
def pitched(text, cfg, model_dir):
    base = voice.say(text, cfg["voice"], cfg["speed"], model_dir)
    r = cfg["pitch"]
    if abs(r - 1) < 1e-3:
        return base
    key = Path("out/voice_cache") / f"p_{abs(hash((text, cfg['voice'], cfg['speed'], r))) % 10**12}.npy"
    if key.exists():
        return np.load(key)
    cmd = ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", "24000", "-ac", "1", "-i", "-",
           "-af", f"asetrate={24000 * r},aresample=24000,atempo={1 / r}", "-f", "f32le", "-ar", "24000", "-ac", "1", "-"]
    out = subprocess.run(cmd, input=base.astype("<f4").tobytes(), capture_output=True, check=True).stdout
    arr = np.frombuffer(out, dtype="<f4").copy()
    np.save(key, arr)
    return arr


def envelope(clip, dur):
    spf = voice.SR_VOICE // FPS
    n = int(dur * FPS) + 1
    rms = np.array([np.sqrt(np.mean(clip[i * spf:(i + 1) * spf] ** 2)) if i * spf < len(clip) else 0 for i in range(n)])
    ref = np.percentile(rms[rms > 0.002], 90) if np.any(rms > 0.002) else 1
    e = np.clip(rms / ref, 0, 1)
    return np.maximum(e, np.concatenate([[0], e[:-1]]) * 0.7)


def timeline(story, model_dir):
    clips, durs = [], []
    for i, ln in enumerate(story["lines"]):
        c = pitched(ln["text"], story["voices"][ln["who"]], model_dir)
        clips.append(c)
        durs.append((LEAD if i == 0 else 0) + len(c) / voice.SR_VOICE + PAUSE)
    return clips, durs


def build_audio(story, clips, durs):
    sr = sfx.SR
    total = sum(durs)
    out = np.zeros(int(total * sr) + sr)
    starts = np.cumsum([0] + durs[:-1])
    fx = np.zeros_like(out)
    for i, c in enumerate(clips):
        off = starts[i] + (LEAD if i == 0 else 0)
        v = np.interp(np.arange(int(len(c) * sr / voice.SR_VOICE)) * voice.SR_VOICE / sr, np.arange(len(c)), c)
        out[int(off * sr):int(off * sr) + len(v)] += v
        for t, name, g in story["lines"][i].get("sfx", []):
            s = sfx.SOUNDS[name]() * g
            i0 = int((off + t) * sr)
            fx[i0:i0 + len(s)] += s[: len(fx) - i0]
    out = (out + fx * 0.5)[: int(total * sr)]
    return (out / max(1e-6, np.max(np.abs(out))) * 0.92).astype(np.float32)


def render_line(args):
    story, i, dur, env, out = args
    tmp = out.with_name(out.stem + "_tmp.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(tmp)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    lead = LEAD if i == 0 else 0
    for n in range(int(round(dur * FPS))):
        t = n / FPS
        p.stdin.write(frame(story, i, max(0, t - lead), env).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg a échoué (réplique {i + 1})")
    os.replace(tmp, out)
    return str(out)


def main():
    a = sys.argv[1:]
    story = json.loads(Path(a[0]).read_text(encoding="utf-8"))
    model_dir = os.environ.get("MODEL_DIR", "/home/claude/models" if Path("/home/claude/models").exists() else "models")
    clips, durs = timeline(story, model_dir)
    envs = [envelope(c, len(c) / voice.SR_VOICE) for c in clips]
    if "--still" in a:
        i = a.index("--still")
        li, t, out = int(a[i + 1]) - 1, float(a[i + 2]), a[i + 3]
        frame(story, li, t, envs[li]).save(out)
        print("durée totale :", round(sum(durs), 1), "s")
        return
    out = Path(a[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / (out.stem + "_scenes")
    work.mkdir(exist_ok=True)
    jobs = [(story, i, durs[i], envs[i], work / f"l_{i + 1:02d}.mp4") for i in range(len(durs))]
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        files = list(ex.map(render_line, jobs))
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{Path(x).resolve()}'\n" for x in files))
    silent = work / "video_silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)
    wav = work / "audio.wav"
    sfx.write_wav(wav, build_audio(story, clips, durs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    print("OK :", out, f"({sum(durs):.1f} s)")


if __name__ == "__main__":
    main()
