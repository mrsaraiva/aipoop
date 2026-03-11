"""
Sound effects: short transition sounds for segment boundaries.

All generators use vectorized numpy operations — no external audio deps.
"""

import random

import numpy as np

from .constants import SAMPLE_RATE


def _sin(freq: float | np.ndarray, t: np.ndarray, amp: float = 1.0) -> np.ndarray:
    return amp * np.sin(2 * np.pi * freq * t)


def _square(freq: float | np.ndarray, t: np.ndarray, amp: float = 1.0) -> np.ndarray:
    return amp * np.sign(np.sin(2 * np.pi * freq * t))


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
        case "modem_dialup":
            # Two alternating handshake tones + noise burst in second half
            tone_a = _sin(300.0, t, 0.3)
            tone_b = _sin(1000.0, t, 0.3)
            # Alternate tones every ~30ms
            switch = _square(15.0, t, 1.0)
            tones = np.where(switch > 0, tone_a, tone_b)
            # Noise burst kicks in at halfway point
            noise = np.random.uniform(-0.3, 0.3, n).astype(np.float32)
            half = n // 2
            noise_env = np.zeros(n, dtype=np.float32)
            noise_env[half:] = 1.0
            samples = (tones * env + noise * noise_env * env).astype(np.float32)
        case "static_burst":
            # Bandpass-filtered white noise via sine envelope
            noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32)
            bandpass = np.abs(_sin(800.0, t, 1.0)).astype(np.float32)
            samples = (noise * bandpass * env * 0.4).astype(np.float32)
        case "error_beep":
            # Harsh square wave double-beep
            beep_len = n // 4
            gap_start = beep_len
            gap_end = gap_start + beep_len
            beep2_end = min(gap_end + beep_len, n)
            gate = np.zeros(n, dtype=np.float32)
            gate[:beep_len] = 1.0
            gate[gap_end:beep2_end] = 1.0
            samples = (_square(800.0, t, 0.4) * gate).astype(np.float32)
        case "tape_stop":
            # Sine that decelerates: freq drops exponentially, amplitude fades
            freq = 400.0 * np.exp(-4.0 * t / duration)
            fade = np.exp(-3.0 * t / duration).astype(np.float32)
            samples = (_sin(freq, t, 0.4) * fade).astype(np.float32)
        case "digital_stutter":
            # Tiny noise grain (~5ms) repeated rapidly across duration
            grain_len = max(1, int(SAMPLE_RATE * 0.005))
            grain = np.random.uniform(-0.4, 0.4, grain_len).astype(np.float32)
            repeats = (n // grain_len) + 1
            tiled = np.tile(grain, repeats)[:n]
            # Slight amplitude variation per grain
            amp_var = np.repeat(
                np.random.uniform(0.5, 1.0, repeats).astype(np.float32),
                grain_len,
            )[:n]
            samples = (tiled * amp_var * env).astype(np.float32)
        case "power_down":
            # Logarithmic frequency sweep 1000→50 Hz with exponential decay
            freq = 50.0 + 950.0 * np.exp(-4.0 * t / duration)
            decay = np.exp(-3.0 * t / duration).astype(np.float32)
            samples = (_sin(freq, t, 0.5) * decay).astype(np.float32)
        case "notification_ping":
            # Clean high sine with very fast exponential decay (chime)
            decay = np.exp(-20.0 * t / duration).astype(np.float32)
            samples = (_sin(2000.0, t, 0.4) * decay).astype(np.float32)
        case _:
            samples = np.zeros(n, dtype=np.float32)

    return samples.astype(np.float32)
