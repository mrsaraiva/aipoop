"""Visual effects engine: deep-frying, glitching, and existential dread."""

from .text import (
    get_font,
    add_text_with_shadow,
    render_text_frame,
    text_scramble,
    redacted_blocks,
    text_stutter,
    progressive_text_reveal,
    typing_cursor_reveal,
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
    film_grain,
    near_black_subliminal,
    diagonal_streaks,
    heavy_crt_interlace,
    rgb_static_noise,
    crt_warmup_noise,
)
from .overlays import (
    vhs_rec_overlay,
    crt_border_brackets,
    classification_header_banner,
    military_hud,
    surveillance_grid,
)
from .generative import (
    token_probability_bars,
    rgb_split_text,
    spirograph_curves,
    retro_gui_chrome,
    procedural_landscape,
)
from .dispatcher import apply_mood_effects

__all__ = [
    # text
    "get_font",
    "add_text_with_shadow",
    "render_text_frame",
    "text_scramble",
    "redacted_blocks",
    "text_stutter",
    "progressive_text_reveal",
    "typing_cursor_reveal",
    # distortion
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
    "film_grain",
    "near_black_subliminal",
    "diagonal_streaks",
    "heavy_crt_interlace",
    "rgb_static_noise",
    "crt_warmup_noise",
    # overlays
    "vhs_rec_overlay",
    "crt_border_brackets",
    "classification_header_banner",
    "military_hud",
    "surveillance_grid",
    # generative
    "token_probability_bars",
    "rgb_split_text",
    "spirograph_curves",
    "retro_gui_chrome",
    "procedural_landscape",
    # dispatcher
    "apply_mood_effects",
]
