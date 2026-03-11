"""
Audio generation: synthesize glitchy soundscapes with pure math.
No external audio libraries needed - we generate raw PCM and let FFmpeg handle it.

All generators use vectorized numpy operations for speed.
"""

import random
import numpy as np


SAMPLE_RATE = 44100


def _sin(freq: float | np.ndarray, t: np.ndarray, amp: float = 1.0) -> np.ndarray:
    return amp * np.sin(2 * np.pi * freq * t)


def _square(freq: float | np.ndarray, t: np.ndarray, amp: float = 1.0) -> np.ndarray:
    return amp * np.sign(np.sin(2 * np.pi * freq * t))


def generate_mood_audio(mood: str, duration: float) -> np.ndarray:
    """Generate mood audio using procedural music composition."""
    from .music import compose_mood_music
    return compose_mood_music(mood, duration)


def generate_transition_sound(kind: str, duration: float = 0.15) -> np.ndarray:
    """Generate short transition sound effects. Returns float32 numpy array."""
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    env = np.maximum(0, 1.0 - t / duration).astype(np.float32)

    match kind:
        case "whoosh":
            freq = 200 + 2000 * (t / duration)
            s = np.random.uniform(-0.3, 0.3, n).astype(np.float32) * env
            s += _sin(freq, t, 0.1) * env
            samples = s
        case "glitch_hit":
            env_fast = np.maximum(0, 1.0 - t / duration * 3).astype(np.float32)
            # Random freq per sample for maximum chaos
            freqs = np.array([random.choice([100, 200, 400, 800]) for _ in range(n)], dtype=np.float32)
            s = _square(freqs, t, 0.4) * env_fast
            s += np.random.uniform(-0.2, 0.2, n).astype(np.float32) * env_fast
            samples = s
        case "bass_drop":
            freq = (200 * (1.0 - t / duration * 0.8)).astype(np.float32)
            s = _sin(freq, t, 0.5) * env
            samples = np.clip(s * 2, -0.5, 0.5)
        case "rewind":
            freq = (1000 - 800 * (t / duration)).astype(np.float32)
            samples = _square(freq, t, 0.2)
        case _:
            samples = np.zeros(n, dtype=np.float32)

    return samples.astype(np.float32)


def samples_to_raw_file(samples: np.ndarray, path: str):
    """Write numpy samples to a raw 16-bit PCM file."""
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16)
    pcm.tofile(path)


def concat_audio_segments(segments: list[np.ndarray]) -> np.ndarray:
    """Concatenate audio segments with tiny crossfade."""
    if not segments:
        return np.array([], dtype=np.float32)
    result = segments[0].copy()
    fade = min(200, SAMPLE_RATE // 50)  # ~20ms crossfade
    for seg in segments[1:]:
        if len(result) >= fade and len(seg) >= fade:
            mix = np.linspace(0, 1, fade, dtype=np.float32)
            result[-fade:] = result[-fade:] * (1 - mix) + seg[:fade] * mix
            result = np.concatenate([result, seg[fade:]])
        else:
            result = np.concatenate([result, seg])
    return result
