"""
TTS wrapper: gives the LLM a voice using Chatterbox Multilingual.

Loads the model once, generates speech for given text + language,
and returns raw float samples at 24kHz that we resample to 44.1kHz
for mixing with the procedural audio.
"""

import numpy as np

# Our target sample rate (matching the procedural audio)
TARGET_SR = 44100
# Chatterbox output sample rate
CHATTERBOX_SR = 24000

_model = None


def _get_model():
    """Lazy-load the TTS model on first use."""
    global _model
    if _model is not None:
        return _model

    import torch
    from .chatterbox import ChatterboxMultilingualTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Loading Chatterbox TTS on {device}...")
    _model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    print(f"  TTS model loaded.")
    return _model


def _resample(samples: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio using linear interpolation (good enough for our glitchy aesthetic)."""
    if orig_sr == target_sr:
        return samples
    duration = len(samples) / orig_sr
    n_target = int(duration * target_sr)
    indices = np.linspace(0, len(samples) - 1, n_target)
    return np.interp(indices, np.arange(len(samples)), samples).astype(np.float32)


def synthesize(text: str, lang: str = "pt") -> list[float]:
    """
    Generate speech from text.

    Returns a list of float samples at 44100Hz (matching our audio pipeline).
    """
    model = _get_model()

    language_id = "pt" if lang == "pt" else "en"

    wav_tensor = model.generate(
        text,
        language_id=language_id,
        temperature=0.8,
        exaggeration=0.5,
        cfg_weight=0.5,
    )

    # wav_tensor shape: [1, N] at 24kHz
    samples_24k = wav_tensor.squeeze(0).numpy().astype(np.float32)

    # Resample to 44.1kHz
    samples_44k = _resample(samples_24k, CHATTERBOX_SR, TARGET_SR)

    # Normalize to [-0.8, 0.8] to leave headroom for mixing
    peak = np.max(np.abs(samples_44k))
    if peak > 0:
        samples_44k = samples_44k * (0.8 / peak)

    return samples_44k.tolist()
