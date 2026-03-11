"""Thought segment: display existential text with mood-based effects."""

import os

import numpy as np
from PIL import ImageEnhance

from ..constants import WIDTH, HEIGHT, FPS
from ..effects import apply_mood_effects, render_text_frame
from ..audio import generate_mood_audio


def gen_thought_segment(
    text: str,
    mood: str,
    duration: float,
    out_dir: str,
    seg_id: int,
    colors: dict,
) -> tuple[str, np.ndarray]:
    """Generate frames + audio for a 'thought' segment."""
    n_frames = int(duration * FPS)
    frame_dir = os.path.join(out_dir, f"seg_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    font_size = 52 if len(text) < 80 else 40 if len(text) < 140 else 32
    bold = mood in ("scream", "deep_fried")

    base_img = render_text_frame(
        WIDTH, HEIGHT, text,
        bg_color=colors["bg"],
        fg_color=colors["fg"],
        font_size=font_size,
        bold=bold,
    )

    for i in range(n_frames):
        img = apply_mood_effects(base_img.copy(), mood)

        if i < 5:
            img = ImageEnhance.Brightness(img).enhance(i / 5)

        img.save(os.path.join(frame_dir, f"frame_{i:05d}.png"))

    audio = generate_mood_audio(mood, duration)
    return frame_dir, audio
