"""Voix anglaises (Kokoro) + bruitages pour TINY BUS ADVENTURES. Aucune musique.
Produit out/tinybus/audio.wav et out/tinybus/mouth.json (ouverture de bouche à 10 i/s)."""
import hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import sfx

MODEL_DIR = "/home/claude/models"
SRV = 24000
SR = sfx.SR
RFPS = 10
DUR = 30.0
OUT = Path("out/tinybus"); OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "voice_cache"; CACHE.mkdir(exist_ok=True)
_k = None


def tts(text, voice, speed):
    global _k
    f = CACHE / (hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16] + ".npy")
    if f.exists(): return np.load(f)
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(f"{MODEL_DIR}/kokoro-v1.0.int8.onnx", f"{MODEL_DIR}/voices-v1.0.bin")
    a, sr = _k.create(text, voice=voice, speed=speed, lang="en-us")
    a = a.astype(np.float32); np.save(f, a); return a


def pitch(a, r):
    if abs(r - 1) < 1e-3: return a
    cmd = ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SRV), "-ac", "1", "-i", "-",
           "-af", f"asetrate={SRV * r},aresample={SRV},atempo={1 / r}", "-f", "f32le", "-ar", str(SRV), "-ac", "1", "-"]
    out = subprocess.run(cmd, input=a.astype("<f4").tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype="<f4").copy()


# (instant, personnage, texte, voix, vitesse, hauteur, volume)
LINES = [
    (0.35, "sunny", "Don't press that button!", "am_puck", 1.0, 0.95, 1.0),
    (3.40, "bobo", "What's this?", "af_bella", 1.0, 1.28, 1.0),
    (6.40, "mimi", "Don't touch it, Bobo!", "af_nicole", 1.05, 1.22, 1.0),
    (9.40, "bobo", "Just one little press...", "af_bella", 0.8, 1.28, 0.85),
    (16.0, "bobby", "Whoooooa!", "am_liam", 0.6, 1.2, 1.0),
    (17.7, "mimi", "Aaaah!", "af_nicole", 0.8, 1.22, 0.9),
    (18.9, "bobo", "Wheeee!", "af_bella", 0.7, 1.3, 0.9),
    (21.55, "bobo", "Wow!", "af_bella", 0.9, 1.28, 1.0),
    (21.65, "mimi", "Wow!", "af_nicole", 0.9, 1.22, 0.9),
    (21.6, "bobby", "Wow!", "am_liam", 0.9, 1.2, 0.9),
    (25.45, "mimi", "Bobo, no!", "af_nicole", 1.1, 1.22, 1.0),
    (28.30, "bobo", "Again?", "af_bella", 0.75, 1.2, 0.75),
]


def beep(f=1000, d=0.12):
    t = np.arange(int(d * SR)) / SR
    return np.sin(2 * np.pi * f * t) * np.minimum(1, (d - t) * 60) * 0.5


def click():
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (np.random.RandomState(1).randn(n) * np.exp(-t * 120) + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)) * 0.5


def honk(d=0.45):
    t = np.arange(int(d * SR)) / SR
    f = 330 + 40 * np.sin(2 * np.pi * 6 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    w = np.sign(np.sin(ph)) * 0.35 + np.sin(ph) * 0.3
    return w * np.minimum(1, t * 40) * np.minimum(1, (d - t) * 20) * 0.6


def whoosh(d=1.6):
    n = int(d * SR); t = np.arange(n) / SR
    x = np.random.RandomState(3).randn(n)
    k = 40
    y = np.convolve(x, np.ones(k) / k, "same")
    env = np.sin(np.pi * t / d) ** 2
    return y * env * 1.6


EVENTS = [
    (0.20, beep(1000), 0.8), (0.55, beep(1000), 0.8), (1.30, beep(1250), 0.5),
    (12.20, click(), 1.0), (12.45, beep(1400, 0.1), 0.8), (12.70, beep(1400, 0.1), 0.8),
    (15.10, whoosh(2.0), 0.9), (17.00, honk(), 0.8), (20.00, honk(0.6), 0.8),
    (21.25, sfx.SOUNDS["thud"](), 0.8), (21.40, sfx.SOUNDS["sparkle"](), 0.8), (21.55, sfx.SOUNDS["ding"](), 0.5),
    (24.60, sfx.SOUNDS["sparkle"](), 0.6), (25.05, beep(1400, 0.1), 0.6),
    (28.9, beep(1000), 0.35), (29.3, beep(1000), 0.35),
]


def main():
    out = np.zeros(int(DUR * SR))
    mouth = {}
    nfr = int(DUR * RFPS) + 2
    for t0, who, text, voice, speed, pr, vol in LINES:
        a = pitch(tts(text, voice, speed), pr) * vol
        v = np.interp(np.arange(int(len(a) * SR / SRV)) * SRV / SR, np.arange(len(a)), a)
        i = int(t0 * SR); out[i:i + len(v)] += v[: len(out) - i]
        if who in ("bobo", "mimi", "bobby"):
            spf = SRV // RFPS
            e = np.array([np.sqrt(np.mean(a[k * spf:(k + 1) * spf] ** 2)) if k * spf < len(a) else 0 for k in range(len(a) // spf + 1)])
            ref = np.percentile(e[e > 0.002], 90) if np.any(e > 0.002) else 1
            e = np.sqrt(np.clip(e / ref, 0, 1))
            arr = mouth.setdefault(who, [0.0] * nfr)
            k0 = int(round(t0 * RFPS))
            for j, val in enumerate(e):
                if k0 + j < nfr: arr[k0 + j] = max(arr[k0 + j], float(val))
    for t0, s, g in EVENTS:
        i = int(t0 * SR); out[i:i + len(s)] += s[: len(out) - i] * g * 0.55
    out = out / max(1e-6, np.max(np.abs(out))) * 0.9
    sfx.write_wav(OUT / "audio.wav", out.astype(np.float32))
    json.dump(mouth, open(OUT / "mouth.json", "w"))
    print("OK audio + mouth", {k: round(sum(v), 1) for k, v in mouth.items()})


main()
