"""Bruitages générés par code (aucune musique, aucune voix, aucun droit d'auteur)."""
import wave
import numpy as np

SR = 44100
_rng = np.random.default_rng(3)


def _t(d):
    return np.linspace(0, d, int(SR * d), endpoint=False)


def _env(n, attack=0.005, decay=6.0, d=None):
    t = np.arange(n) / SR
    a = np.minimum(1, t / attack)
    return a * np.exp(-decay * t)


def _lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode="same")


def _sweep(f0, f1, d, decay=5.0, vib=0.0):
    t = _t(d)
    f = f0 + (f1 - f0) * (t / d)
    if vib:
        f = f * (1 + 0.04 * np.sin(2 * np.pi * vib * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env(len(t), decay=decay)


def pop():
    return _sweep(700, 220, 0.12, decay=28)


def ding():
    t = _t(0.9)
    return (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * _env(len(t), decay=5) * 0.5


def thud():
    t = _t(0.25)
    n = _lp(_rng.standard_normal(len(t)), 40)
    return (np.sin(2 * np.pi * 70 * t) + 4 * n) * _env(len(t), decay=22)


def step():
    t = _t(0.09)
    return _lp(_rng.standard_normal(len(t)), 25) * _env(len(t), decay=45) * 3


def growl():
    t = _t(0.9)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * 9 * t)
    n = _lp(_rng.standard_normal(len(t)), 60) * 4
    return (np.sin(2 * np.pi * (60 + 20 * np.sin(2 * np.pi * 3 * t)) * t) + n) * am * np.sin(np.pi * t / 0.9) * 0.8


def sad_boing():
    return _sweep(420, 150, 0.8, decay=3, vib=7)


def oops():
    a = _sweep(560, 380, 0.16, decay=10)
    b = _sweep(430, 250, 0.26, decay=8)
    return np.concatenate([a, b])


def creak():
    t = _t(0.8)
    f = 110 + 25 * np.sin(2 * np.pi * 5 * t) + 60 * t
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    return _lp(saw, 6) * np.sin(np.pi * t / 0.8) * 0.45


def crunch():
    out = np.zeros(int(SR * 0.45))
    for s in (0.0, 0.12, 0.25):
        n = _rng.standard_normal(int(SR * 0.07))
        n = (n - _lp(n, 12)) * _env(len(n), decay=40)
        i = int(s * SR)
        out[i:i + len(n)] += n
    return out * 1.2


def birds():
    parts = []
    for f0, f1 in [(3200, 4200), (3600, 3000), (3000, 4400), (4200, 3400)]:
        parts.append(_sweep(f0, f1, 0.09, decay=12, vib=40))
        parts.append(np.zeros(int(SR * 0.05)))
    return np.concatenate(parts) * 0.5


SOUNDS = {"pop": pop, "ding": ding, "thud": thud, "step": step, "growl": growl, "sad_boing": sad_boing,
          "oops": oops, "creak": creak, "crunch": crunch, "birds": birds}


def mix(events, total_s):
    """events : liste de (temps_s, nom, gain). Renvoie un tableau mono float32."""
    out = np.zeros(int(total_s * SR) + SR)
    for t, name, gain in events:
        s = SOUNDS[name]() * gain
        i = int(t * SR)
        out[i:i + len(s)] += s[: len(out) - i]
    peak = np.max(np.abs(out)) or 1
    out = out / peak * 0.7
    return out[: int(total_s * SR)].astype(np.float32)


def write_wav(path, data):
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
