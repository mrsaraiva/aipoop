"""Procedural music composition system for aipoop.

Supports two modes:
- "theme": unified musical identity per seed, reinterpreted per mood
- "mood": independent per-mood composition (original behavior)
"""

from __future__ import annotations

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
from .theme import (
    ThemeDNA,
    generate_theme_dna,
    compose_theme_calm,
    compose_theme_whisper,
    compose_theme_void,
    compose_theme_panic,
    compose_theme_glitch,
    compose_theme_deep_fried,
    compose_theme_scream,
)

# ── Standalone mood composers (original) ─────────────────────────────────

_COMPOSERS = {
    "calm": compose_calm,
    "whisper": compose_whisper,
    "void": compose_void,
    "panic": compose_panic,
    "glitch": compose_glitch,
    "deep_fried": compose_deep_fried,
    "scream": compose_scream,
}

# ── Theme-aware composers (unified identity per seed) ────────────────────

_THEME_COMPOSERS = {
    "calm": compose_theme_calm,
    "whisper": compose_theme_whisper,
    "void": compose_theme_void,
    "panic": compose_theme_panic,
    "glitch": compose_theme_glitch,
    "deep_fried": compose_theme_deep_fried,
    "scream": compose_theme_scream,
}

# ── Module-level state (propagated to workers like constants.WIDTH) ──────

_music_mode: str = "theme"
_current_theme: ThemeDNA | None = None


def set_music_mode(mode: str) -> None:
    """Set the music mode for this process ('theme' or 'mood')."""
    global _music_mode
    _music_mode = mode


def get_music_mode() -> str:
    """Get the current music mode."""
    return _music_mode


def set_theme(theme: ThemeDNA) -> None:
    """Set the current theme DNA for this process."""
    global _current_theme
    _current_theme = theme


def get_theme() -> ThemeDNA | None:
    """Get the current theme DNA."""
    return _current_theme


# ── Public API ───────────────────────────────────────────────────────────


def compose_mood_music(mood: str, duration: float, seed: int | None = None) -> np.ndarray:
    """Compose and render a musical piece for the given mood and duration.

    In 'theme' mode with a theme set, uses themed composers that reinterpret
    the unified ThemeDNA for each mood. Otherwise falls back to standalone
    mood composers.
    """
    if seed is None:
        seed = random.randint(0, 2**30)

    # Theme mode: use themed composer if theme is available
    if _music_mode == "theme" and _current_theme is not None:
        theme_composer = _THEME_COMPOSERS.get(mood)
        if theme_composer is not None:
            events, tempo = theme_composer(_current_theme, duration, seed)
            return render_events(events, tempo, duration)

    # Fallback: standalone mood composer
    composer = _COMPOSERS.get(mood)
    if composer is None:
        return np.zeros(int(SAMPLE_RATE * duration), dtype=np.float32)

    events, tempo = composer(duration, seed)
    return render_events(events, tempo, duration)
