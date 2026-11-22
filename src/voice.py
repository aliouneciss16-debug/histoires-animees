"""Voix off française gratuite et hors ligne (Kokoro, via kokoro-onnx).

Modèles à télécharger une fois dans models/ :
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
"""
import hashlib
from pathlib import Path

import numpy as np

SR_VOICE = 24000
_k = None


def _kokoro(model_dir):
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(str(Path(model_dir) / "kokoro-v1.0.int8.onnx"), str(Path(model_dir) / "voices-v1.0.bin"))
    return _k


def say(text, voice="ff_siwis", speed=0.95, model_dir="models", cache_dir="out/voice_cache"):
    """Renvoie un tableau float32 mono à 24 kHz. Les phrases déjà générées sont mises en cache."""
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
    f = cache / f"{key}.npy"
    if f.exists():
        return np.load(f)
    audio, sr = _kokoro(model_dir).create(text, voice=voice, speed=speed, lang="fr-fr")
    assert sr == SR_VOICE
    audio = audio.astype(np.float32)
    np.save(f, audio)
    return audio
