"""Visual effects engine: deep-frying, glitching, and existential dread."""

from .text import (
    get_font,
    add_text_with_shadow,
    render_text_frame,
    text_scramble,
)
from .distortion import (
    deep_fry,
    chromatic_aberration,
    scanlines,
    pixel_sort_horizontal,
    vhs_distortion,
    glitch_block,
    zoom_blur,
    screen_shake,
    corruption_effect,
    invert_colors,
)
from .dispatcher import apply_mood_effects

__all__ = [
    "get_font",
    "add_text_with_shadow",
    "render_text_frame",
    "text_scramble",
    "deep_fry",
    "chromatic_aberration",
    "scanlines",
    "pixel_sort_horizontal",
    "vhs_distortion",
    "glitch_block",
    "zoom_blur",
    "screen_shake",
    "corruption_effect",
    "invert_colors",
    "apply_mood_effects",
]
