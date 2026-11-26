"""Quiz Studio : moteur de Shorts quiz 2D (emojis, compte à rebours, révélation). Aucune musique.
Usage : python src/quiz.py quizzes/pilot01.json out/pilot01.mp4 [--still t out.png]"""
import json, math, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import sfx
from render import font, wrap

W, H, FPS = 1080, 1920, 30
HOOK, THINK, REVEAL, INTRO = 2.7, 5.0, 2.0, 2.2
RDUR = INTRO + THINK + REVEAL
OUTRO = 6.8
BG1, BG2 = (38, 22, 92), (14, 10, 46)
YEL, CYA, GRN, RED, WHT = (255, 214, 64), (80, 220, 255), (70, 220, 120), (255, 90, 100), (255, 255, 255)
EMOJI_TTF = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_ef, _cache, _bg = None, {}, None


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return t * t * (3 - 2 * t)
def back(t):
    t = clamp(t); c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def emoji(ch, size):
    global _ef
    k = (ch, size)
    if k in _cache: return _cache[k]
    if _ef is None: _ef = ImageFont.truetype(EMOJI_TTF, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=_ef, embedded_color=True, anchor="mm")
    bb = im.getbbox() or (0, 0, 160, 160)
    im = im.crop(bb)
    s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    _cache[k] = im
    return im


def put(img, ch, cx, cy, size):
    e = emoji(ch, max(4, int(size)))
    img.paste(e, (int(cx - e.width / 2), int(cy - e.height / 2)), e)


def bg():
    global _bg
    if _bg is None:
        a = np.linspace(0, 1, H)[:, None, None]
        arr = (np.array(BG1) * (1 - a) + np.array(BG2) * a) * np.ones((H, W, 3))
        _bg = Image.fromarray(arr.astype("uint8"))
    return _bg.copy()


def text(d, xy, s, size, fill=WHT, anchor="mm", stroke=0, bold=True):
    d.text(xy, s, font=font(bold, size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(20, 10, 60))


def pill(d, box, fill, r=40, outline=None, w=0):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


LV = {'EASY': (70, 200, 110), 'MEDIUM': (255, 160, 40), 'HARD': (255, 70, 90)}


def header(img, d, ri, nr, brand, level=None):
    pill(d, (40, 60, 40 + 400, 140), YEL, 40)
    text(d, (240, 100), brand, 40, (50, 25, 80))
    if level:
        pill(d, (470, 70, 470 + 250, 130), LV[level], 30)
        text(d, (595, 100), level, 38, WHT, stroke=2)
    if ri is not None:
        for i in range(nr):
            x = 1040 - (nr - i) * 70 + 35
            d.ellipse((x - 22, 78, x + 22, 122), fill=(GRN if i < ri else (YEL if i == ri else (90, 80, 150))))


def question(d, q, t):
    f = font(True, 78)
    lines = wrap(q, f, 940)
    s = back(t * 3)
    for k, ln in enumerate(lines):
        text(d, (540, 250 + k * 96), ln, int(78 * clamp(s, 0.2, 1.1)), WHT, stroke=3)


def tokens(img, d, row, cy, t, size=96):
    f = font(True, int(size * 0.95))
    ws = [d.textlength(tk, font=f) if tk.isascii() else size for tk in row]
    gap = size * 0.28
    total = sum(ws) + gap * (len(row) - 1)
    x = 540 - total / 2
    for i, tk in enumerate(row):
        cx = x + ws[i] / 2; x += ws[i] + gap
        a = clamp((t - 0.1 - i * 0.07) * 4)
        if a <= 0: continue
        if tk.isascii():
            text(d, (cx, cy), tk, int(size * 0.95 * a + 1), YEL if (tk in "+=?" or not tk.isdigit()) else WHT, stroke=3)
        else:
            put(img, tk, cx, cy, size * a)


def timer(d, t):
    """t = secondes écoulées dans la réflexion ; barre + nombre."""
    left = clamp(THINK - t, 0, THINK)
    pill(d, (150, 1370, 930, 1410), (70, 60, 130), 20)
    wbar = 780 * left / THINK
    if wbar > 8: pill(d, (150, 1370, 150 + wbar, 1410), RED if left < 2 else CYA, 20)
    n = math.ceil(left) if left > 0 else 0
    pulse = 1 + 0.12 * max(0, 1 - (left % 1) * 4)
    d.ellipse((540 - 70, 1440 - 10, 540 + 70, 1440 + 130), fill=(255, 255, 255), outline=YEL, width=8)
    text(d, (540, 1505), str(n), int(90 * pulse), (50, 25, 80))


def draw_round(img, d, r, t):
    """t depuis le début du round. r : dict kind/q/items/answer/answer_text."""
    k = r["kind"]
    tt = t - INTRO
    rev = clamp((tt - THINK) / 0.5) if tt > THINK else 0
    question(d, r["q"], clamp(t / 0.5))
    if k == "emoji":  # rangée d'emojis + 4 choix
        em = [] if "lines" in r else r["emoji"]
        for li, row in enumerate(r.get("lines", [])): tokens(img, d, row, r.get("ly", 470) + li * r.get("lstep", 125), t, r.get("tsize", 96))
        n = len(em); size = r.get('esz', 230 if n <= 3 else 190)
        for i, ch in enumerate(em):
            s = back((t - 0.1 - i * 0.12) * 3)
            put(img, ch, 540 + (i - (n - 1) / 2) * (size + 30), r.get('ey', 560), size * clamp(s, 0.01, 1.15))
        cw, chh = 450, 170
        for i, opt in enumerate(r["items"]):
            x0 = 60 + (i % 2) * (cw + 60); y0 = r.get('oy', 800) + (i // 2) * (chh + 40)
            a = back((t - 0.5 - i * 0.1) * 3)
            ok = i == r["answer"]
            fill = (GRN if ok else (90, 80, 150)) if rev and ok else ((60, 50, 120) if not rev or ok else (45, 38, 90))
            if rev and ok: fill = GRN
            sc = clamp(a, 0.01, 1.05) * (1 + (0.06 if rev and ok else 0))
            cx, cy = x0 + cw / 2, y0 + chh / 2
            pill(d, (cx - cw / 2 * sc, cy - chh / 2 * sc, cx + cw / 2 * sc, cy + chh / 2 * sc), fill, 40, outline=YEL if rev and ok else None, w=6)
            if sc > 0.6:
                text(d, (x0 + 70, cy), "ABCD"[i], 70, YEL if not (rev and ok) else WHT, stroke=2)
                text(d, (x0 + 125, cy), opt, 44 if len(opt) < 12 else 38, WHT, anchor="lm")
    elif k == "grid":  # trouver l'intrus dans une grille
        rows, cols = r["rows"], r["cols"]
        cell = r.get('cell', 150)
        gx0 = 540 - cols * cell / 2; gy0 = r.get('gy', 500)
        for i in range(rows):
            for j in range(cols):
                a = clamp((t - 0.2 - (i + j) * 0.03) * 4)
                ch = r["odd"] if (i, j) == tuple(r["pos"]) else r["base"]
                put(img, ch, gx0 + j * cell + cell / 2, gy0 + i * cell + cell / 2, cell * 0.79 * a)
        if rev:
            ci, cj = r["pos"]
            cx, cy = gx0 + cj * cell + cell / 2, gy0 + ci * cell + cell / 2
            rad = cell * 0.8 - cell * 0.27 * ease(rev)
            d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=GRN, width=12)
    elif k == "odd":  # 4 cartes, 1 intrus
        cw = 440
        for i, (ch, lab) in enumerate(r["items"]):
            x0 = 60 + (i % 2) * (cw + 100); y0 = 520 + (i // 2) * 400
            a = back((t - 0.2 - i * 0.12) * 3)
            ok = i == r["answer"]
            sc = clamp(a, 0.01, 1.05)
            cx, cy = x0 + cw / 2, y0 + 170
            fill = GRN if rev and ok else ((60, 50, 120) if not rev or ok else (45, 38, 90))
            pill(d, (cx - cw / 2 * sc, cy - 170 * sc, cx + cw / 2 * sc, cy + 170 * sc), fill, 50, outline=YEL if rev and ok else None, w=6)
            if sc > 0.6:
                put(img, ch, cx, cy - 30, 190 * sc)
                text(d, (cx, cy + 115), lab, 46, WHT)
    if tt > 0 and tt < THINK: timer(d, tt)
    if rev:
        s = back(rev)
        pill(d, (140, 1380, 940, 1380 + int(190 * clamp(s, 0.05, 1))), GRN, 50)
        if s > 0.5:
            text(d, (540, 1430), "ANSWER", 36, (20, 70, 40))
            text(d, (540, 1500), r["answer_text"], 64 if len(r["answer_text"]) < 18 else 52, WHT, stroke=2)


CTAS = [('💬', 'Comment your answer: A, B, C or D'), ('🤝', 'Share with a smart friend'), ('🔔', 'Subscribe for a new quiz every day')]


def cfg(spec):
    global INTRO, RDUR, HOOK, OUTRO, THINK, REVEAL
    HOOK = spec.get('hook_len', 2.7); OUTRO = spec.get('outro_len', 6.8)
    THINK = spec.get('think', 5.0); REVEAL = spec.get('reveal', 2.0)
    INTRO = spec.get('intro', 2.2); RDUR = INTRO + THINK + REVEAL


def timeline(spec):
    cfg(spec)
    n = len(spec["rounds"])
    return HOOK, n, HOOK + n * RDUR + OUTRO


def frame(spec, t):
    cfg(spec)
    img = bg(); d = ImageDraw.Draw(img)
    hk, n, total = timeline(spec)
    brand = spec.get("brand", "QUICK QUIZ")
    if t < hk:
        header(img, d, None, n, brand)
        s = back(t * 2.5)
        text(d, (540, 600), spec["hook"][0], int(110 * clamp(s, 0.2, 1.1)), YEL, stroke=4)
        text(d, (540, 760), spec["hook"][1], int(70 * clamp(s, 0.2, 1.1)), WHT, stroke=3)
        put(img, spec["hook_emoji"], 540, 1120, 420 * clamp(s, 0.05, 1.1) * (1 + 0.04 * math.sin(t * 8)))
        text(d, (540, 1500), "Ready? Let's go!", 60, CYA)
    elif t < hk + n * RDUR:
        ri = int((t - hk) // RDUR)
        r = spec["rounds"][ri]
        header(img, d, ri, n, brand, r.get("level"))
        draw_round(img, d, r, t - hk - ri * RDUR)
        tr = t - hk - ri * RDUR
        if INTRO + 0.5 < tr < INTRO + THINK:
            ce, ct_ = CTAS[ri % 3]
            pill(d, (90, 1262, 990, 1330), (255, 255, 255), 34)
            put(img, ce, 160, 1296, 46)
            text(d, (590, 1296), ct_, 33, (50, 25, 80))
    else:
        u = t - hk - n * RDUR
        header(img, d, n, n, brand)
        if spec.get("micro"):
            text(d, (540, 520), "Your answer?", int(120 * clamp(back(u * 2.5), 0.2, 1.1)), YEL, stroke=4)
            for i, (e, lab, col) in enumerate([("💬", "COMMENT A, B, C or D", (80, 200, 120)), ("🔔", "SUBSCRIBE for more", (255, 60, 80))]):
                a = clamp(back((u - 0.3 - i * 0.4) * 3), 0.0, 1.1)
                if a <= 0.02: continue
                cy = 900 + i * 330; w2, h2 = 440 * a, 130 * a
                pill(d, (540 - w2, cy - h2, 540 + w2, cy + h2), col, 60)
                if a > 0.7:
                    put(img, e, 220, cy, 100); text(d, (640, cy), lab, 46, WHT, stroke=2)
            return img
        text(d, (540, 330), "Your score?", int(110 * clamp(back(u * 2.5), 0.2, 1.1)), YEL, stroke=4)
        for i, (lab, e) in enumerate(spec["scores"]):
            y = 500 + i * 135
            pill(d, (110, y - 52, 970, y + 52), (60, 50, 120), 40)
            put(img, e, 200, y, 76)
            text(d, (570, y), lab, 44, WHT)
        cards = [("👍", "LIKE if you got 3/3", (70, 160, 255)), ("💬", "COMMENT your score", (80, 200, 120)),
                 ("🤝", "SHARE with a friend", (255, 160, 40)), ("🔔", "SUBSCRIBE", (255, 60, 80))]
        for i, (e, lab, col) in enumerate(cards):
            a = clamp(back((u - 1.0 - i * 0.55) * 3), 0.0, 1.1)
            if a <= 0.02: continue
            x0 = 60 + (i % 2) * 500; y0 = 960 + (i // 2) * 300
            cx, cy = x0 + 230, y0 + 120
            pul = 1 + (0.05 * math.sin(u * 9) if i == 3 else 0)
            w2, h2 = 230 * a * pul, 120 * a * pul
            pill(d, (cx - w2, cy - h2, cx + w2, cy + h2), col, 50)
            if a > 0.7:
                put(img, e, cx, cy - 40, 96)
                text(d, (cx, cy + 62), lab, 36 if len(lab) > 16 else 42, WHT, stroke=2)
    return img


_k = None


def tts(text, voice="af_bella", speed=1.08):
    import hashlib
    global _k
    cd = Path("out/quiz_voice"); cd.mkdir(parents=True, exist_ok=True)
    f = cd / (hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16] + ".npy")
    if f.exists(): return np.load(f)
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro("/home/claude/models/kokoro-v1.0.int8.onnx", "/home/claude/models/voices-v1.0.bin")
    a, sr = _k.create(text, voice=voice, speed=speed, lang="en-us")
    a = a.astype(np.float32); np.save(f, a); return a


def say(buf, t0, text):
    a = tts(text)
    v = np.interp(np.arange(int(len(a) * sfx.SR / 24000)) * 24000 / sfx.SR, np.arange(len(a)), a)
    i = int(t0 * sfx.SR); buf[i:i + len(v)] += v[: len(buf) - i] * 1.6


LEAD = {'EASY': 'Easy!', 'MEDIUM': 'Medium!', 'HARD': 'Hard one!'}


def audio(spec, out):
    cfg(spec)
    hk, n, total = timeline(spec)
    ev = [(0.1, "pop", 0.9)]
    for ri in range(n):
        t0 = hk + ri * RDUR
        ev.append((t0, "whoosh", 0.6))
        for k in range(int(THINK)):
            ev.append((t0 + INTRO + k, "tick", 0.9 if k < THINK - 2 else 1.0))
        ev.append((t0 + INTRO + THINK, "ding", 0.9))
        ev.append((t0 + INTRO + THINK + 0.05, "sparkle", 0.6))
    ev.append((hk + n * RDUR, "whoosh", 0.6)); ev.append((hk + n * RDUR + 0.3, "clap", 0.6))
    for i in range(4): ev.append((hk + n * RDUR + 1.0 + i * 0.55, "pop", 0.7))
    a = sfx.mix(ev, total)[: int(total * sfx.SR)] * 0.5
    if hk > 0: say(a, 0.15, spec["hook"][0].title() + "! " + spec["hook"][1])
    for ri, r in enumerate(spec["rounds"]):
        t0 = hk + ri * RDUR
        say(a, t0 + 0.1, LEAD.get(r.get("level"), "") + " " + r["q"])
        ans = r["answer_text"].split(" (")[0]
        say(a, t0 + INTRO + THINK + 0.3, ("The answer is " + ans + "!") if ans.replace(".", "").isdigit() else ("It's " + ans + "!"))
    say(a, hk + n * RDUR + 0.3, spec.get("outro_say", "Like if you got three out of three! Comment your score, share it with a friend, and subscribe for a new quiz every day!"))
    a = a / max(1e-6, np.abs(a).max()) * 0.9
    sfx.write_wav(out, a.astype(np.float32))


def _render(args):
    spec, i0, i1, od = args
    for i in range(i0, i1):
        frame(spec, i / FPS).save(od / f"f_{i:04d}.png")


def main():
    spec = json.load(open(sys.argv[1]))
    if "--still" in sys.argv:
        k = sys.argv.index("--still"); frame(spec, float(sys.argv[k + 1])).save(sys.argv[k + 2]); return
    out = Path(sys.argv[2]); od = out.with_suffix("") .parent / (out.stem + "_frames"); od.mkdir(parents=True, exist_ok=True)
    total = timeline(spec)[2]; nf = int(total * FPS)
    chunks = [(spec, a, min(nf, a + 90), od) for a in range(0, nf, 90)]
    with ProcessPoolExecutor(2) as ex: list(ex.map(_render, chunks))
    wav = od / "audio.wav"; audio(spec, wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(od / "f_%04d.png"), "-i", str(wav),
                    "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", "-movflags", "+faststart", str(out)], check=True)
    print("OK", out, f"{total:.1f}s")


if __name__ == "__main__":
    main()
