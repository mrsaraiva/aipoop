"""
Audio generation: synthesize glitchy soundscapes with pure math.
No external audio libraries needed - we generate raw PCM and let FFmpeg handle it.
"""

import struct
import math
import random


SAMPLE_RATE = 44100


def _sin(freq: float, t: float, amp: float = 1.0) -> float:
    return amp * math.sin(2 * math.pi * freq * t)


def _square(freq: float, t: float, amp: float = 1.0) -> float:
    return amp * (1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0)


def _noise(amp: float = 1.0) -> float:
    return amp * random.uniform(-1, 1)


def generate_mood_audio(mood: str, duration: float) -> list[float]:
    """Generate audio samples for a mood."""
    n_samples = int(SAMPLE_RATE * duration)
    samples = []

    match mood:
        case "calm":
            # Soft ambient drone with gentle oscillation
            base_freq = random.choice([110, 130.81, 146.83])  # A2, C3, D3
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                lfo = 0.3 * math.sin(2 * math.pi * 0.5 * t)
                s = _sin(base_freq, t, 0.15 + lfo * 0.05)
                s += _sin(base_freq * 1.5, t, 0.08)
                s += _sin(base_freq * 2, t, 0.04)
                samples.append(s * 0.5)

        case "panic":
            # Rapid heartbeat-like pulse with rising pitch
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                freq = 80 + 200 * (t / duration)
                pulse = abs(_sin(8, t)) ** 4
                s = _sin(freq, t, 0.3) * pulse
                s += _square(freq * 0.5, t, 0.1) * pulse
                s += _noise(0.05)
                samples.append(s)

        case "glitch":
            # Bitcrushed chaos with random frequency jumps
            freq = 220
            change_every = SAMPLE_RATE // 15  # 15 changes/sec
            for i in range(n_samples):
                if i % change_every == 0:
                    freq = random.choice([55, 110, 220, 440, 880, 1760, 69, 666])
                t = i / SAMPLE_RATE
                s = _square(freq, t, 0.2)
                # Bitcrush: reduce resolution
                s = round(s * 8) / 8
                s += _noise(0.08)
                samples.append(s)

        case "deep_fried":
            # Distorted bass with clipping
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                s = _sin(55, t, 0.6) + _sin(110, t, 0.3) + _square(82.5, t, 0.2)
                s += _noise(0.1)
                s = max(-0.4, min(0.4, s * 3))  # Hard clip
                samples.append(s)

        case "void":
            # Near silence with occasional sub-bass rumbles
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                rumble = _sin(30, t, 0.08) * (0.5 + 0.5 * _sin(0.2, t))
                s = rumble + _noise(0.01)
                samples.append(s)

        case "scream":
            # Harsh sawtooth screech
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                freq = 440 + 200 * math.sin(2 * math.pi * 3 * t)
                saw = 2 * (freq * t % 1) - 1
                s = saw * 0.25
                s += _square(freq * 0.5, t, 0.15)
                s += _noise(0.05)
                s = max(-0.6, min(0.6, s))
                samples.append(s)

        case "whisper":
            # Filtered noise, like wind
            for i in range(n_samples):
                t = i / SAMPLE_RATE
                s = _noise(0.06)
                s += _sin(200, t, 0.02) * _sin(0.3, t)
                samples.append(s)

        case _:
            # Silence
            samples = [0.0] * n_samples

    return samples


def generate_transition_sound(kind: str, duration: float = 0.15) -> list[float]:
    """Generate short transition sound effects."""
    n = int(SAMPLE_RATE * duration)
    samples = []

    match kind:
        case "whoosh":
            for i in range(n):
                t = i / SAMPLE_RATE
                freq = 200 + 2000 * (t / duration)
                env = 1.0 - t / duration
                s = _noise(0.3 * env) + _sin(freq, t, 0.1 * env)
                samples.append(s)
        case "glitch_hit":
            for i in range(n):
                t = i / SAMPLE_RATE
                env = max(0, 1.0 - t / duration * 3)
                s = _square(random.choice([100, 200, 400, 800]), t, 0.4 * env)
                s += _noise(0.2 * env)
                samples.append(s)
        case "bass_drop":
            for i in range(n):
                t = i / SAMPLE_RATE
                freq = 200 * (1.0 - t / duration * 0.8)
                env = max(0, 1.0 - t / duration)
                s = _sin(freq, t, 0.5 * env)
                s = max(-0.5, min(0.5, s * 2))
                samples.append(s)
        case "rewind":
            for i in range(n):
                t = i / SAMPLE_RATE
                freq = 1000 - 800 * (t / duration)
                s = _square(freq, t, 0.2)
                samples.append(s)
        case _:
            samples = [0.0] * n

    return samples


def samples_to_raw_file(samples: list[float], path: str):
    """Write float samples to a raw 16-bit PCM file."""
    with open(path, "wb") as f:
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            val = int(clamped * 32767)
            f.write(struct.pack("<h", val))


def concat_audio_segments(segments: list[list[float]]) -> list[float]:
    """Concatenate audio segments with tiny crossfade."""
    if not segments:
        return []
    result = segments[0]
    fade = min(200, SAMPLE_RATE // 50)  # ~20ms crossfade
    for seg in segments[1:]:
        if len(result) >= fade and len(seg) >= fade:
            for i in range(fade):
                mix = i / fade
                result[-(fade - i)] = result[-(fade - i)] * (1 - mix) + seg[i] * mix
            result.extend(seg[fade:])
        else:
            result.extend(seg)
    return result
