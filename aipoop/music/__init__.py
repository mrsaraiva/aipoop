"""Procedural music composition system for aipoop."""

import random

import numpy as np

from ..constants import SAMPLE_RATE
from .sequencer import render_events
from .composers import (
    compose_calm,
    compose_whisper,
    compose_void,
    compose_panic,
    compose_glitch,
    compose_deep_fried,
    compose_scream,
)

_COMPOSERS = {
    "calm": compose_calm,
    "whisper": compose_whisper,
    "void": compose_void,
    "panic": compose_panic,
    "glitch": compose_glitch,
    "deep_fried": compose_deep_fried,
    "scream": compose_scream,
}


def compose_mood_music(mood: str, duration: float, seed: int | None = None) -> np.ndarray:
    """Compose and render a musical piece for the given mood and duration."""
    if seed is None:
        seed = random.randint(0, 2**30)

    composer = _COMPOSERS.get(mood)
    if composer is None:
        return np.zeros(int(SAMPLE_RATE * duration), dtype=np.float32)

    events, tempo = composer(duration, seed)
    return render_events(events, tempo, duration)
