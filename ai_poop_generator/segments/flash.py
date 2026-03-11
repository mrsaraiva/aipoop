"""Flash segment: rapid subliminal text bursts."""

import os
import random

from ..constants import WIDTH, HEIGHT, FPS
from ..effects import render_text_frame, invert_colors, chromatic_aberration
from ..audio import generate_transition_sound


def gen_flash_segment(
    text: str,
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """Generate a rapid flash frame (3-8 frames)."""
    n_frames = random.randint(3, 8)
    duration = n_frames / FPS
    frame_dir = os.path.join(out_dir, f"flash_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    bg = random.choice([(255, 0, 0), (0, 0, 0), (255, 255, 0), (255, 0, 255)])
    fg = (255, 255, 255) if sum(bg) < 400 else (0, 0, 0)

    for i in range(n_frames):
        img = render_text_frame(WIDTH, HEIGHT, text, bg, fg, font_size=64, bold=True)
        if random.random() < 0.5:
            img = invert_colors(img)
        if random.random() < 0.3:
            img = chromatic_aberration(img, offset=random.randint(8, 20))
        img.save(os.path.join(frame_dir, f"frame_{i:05d}.png"))

    audio = generate_transition_sound(random.choice(["glitch_hit", "whoosh", "bass_drop"]), duration)
    return frame_dir, audio
