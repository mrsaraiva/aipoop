"""
Audio generation: mood soundscapes, PCM writing, and segment concatenation.
No external audio libraries needed - we generate raw PCM and let FFmpeg handle it.
"""

import numpy as np

from .sfx import generate_transition_sound  # re-export for backward compatibility

SAMPLE_RATE = 44100


def generate_mood_audio(mood: str, duration: float) -> np.ndarray:
    """Generate mood audio using procedural music composition."""
    from .music import compose_mood_music
    return compose_mood_music(mood, duration)


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
