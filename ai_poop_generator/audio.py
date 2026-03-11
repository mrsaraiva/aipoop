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
    """Generate audio samples for a mood. Returns float32 numpy array."""
    n = int(SAMPLE_RATE * duration)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE

    match mood:
        case "calm":
            base_freq = random.choice([110, 130.81, 146.83])
            lfo = 0.3 * np.sin(2 * np.pi * 0.5 * t)
            s = _sin(base_freq, t, 0.15) + lfo * 0.05 * _sin(base_freq, t)
            s += _sin(base_freq * 1.5, t, 0.08)
            s += _sin(base_freq * 2, t, 0.04)
            samples = s * 0.5

        case "panic":
            freq = 80 + 200 * (t / duration)
            pulse = np.abs(_sin(8, t)) ** 4
            s = _sin(freq, t, 0.3) * pulse
            s += _square(freq * 0.5, t, 0.1) * pulse
            s += np.random.uniform(-0.05, 0.05, n).astype(np.float32)
            samples = s

        case "glitch":
            change_every = SAMPLE_RATE // 15
            freqs = [55, 110, 220, 440, 880, 1760, 69, 666]
            # Build per-sample frequency array
            n_changes = n // change_every + 1
            freq_choices = np.array([random.choice(freqs) for _ in range(n_changes)], dtype=np.float32)
            freq_arr = np.repeat(freq_choices, change_every)[:n]
            # Compute phase to avoid discontinuities within each freq block
            s = _square(freq_arr, t, 0.2)
            s = np.round(s * 8) / 8  # Bitcrush
            s += np.random.uniform(-0.08, 0.08, n).astype(np.float32)
            samples = s

        case "deep_fried":
            s = _sin(55, t, 0.6) + _sin(110, t, 0.3) + _square(82.5, t, 0.2)
            s += np.random.uniform(-0.1, 0.1, n).astype(np.float32)
            samples = np.clip(s * 3, -0.4, 0.4)

        case "void":
            rumble = _sin(30, t, 0.08) * (0.5 + 0.5 * _sin(0.2, t))
            s = rumble + np.random.uniform(-0.01, 0.01, n).astype(np.float32)
            samples = s

        case "scream":
            freq = 440 + 200 * np.sin(2 * np.pi * 3 * t)
            saw = 2 * (freq * t % 1) - 1
            s = saw * 0.25
            s += _square(freq * 0.5, t, 0.15)
            s += np.random.uniform(-0.05, 0.05, n).astype(np.float32)
            samples = np.clip(s, -0.6, 0.6)

        case "whisper":
            s = np.random.uniform(-0.06, 0.06, n).astype(np.float32)
            s += _sin(200, t, 0.02) * _sin(0.3, t)
            samples = s

        case _:
            samples = np.zeros(n, dtype=np.float32)

    return samples.astype(np.float32)


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
