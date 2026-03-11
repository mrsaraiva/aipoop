"""Propaganda segment: ultra-rapid flashing phrases on bold colors."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font
from ..audio import generate_mood_audio


_BG_COLORS = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 255, 0),
    (255, 0, 255),
    (0, 255, 255),
]


def gen_propaganda_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Ultra-rapid sequence: 3-5 frames per phrase, solid color backgrounds."""
    frame_dir = os.path.join(out_dir, f"propaganda_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    phrases = random.sample(content.propaganda_lines, min(8, len(content.propaganda_lines)))
    frame_idx = 0

    font = get_font(56, bold=True)
    small_font = get_font(44, bold=True)

    for phrase in phrases:
        n_frames = random.randint(3, 5)
        bg = random.choice(_BG_COLORS)
        # Use black or white text for contrast
        fg = (0, 0, 0) if sum(bg) > 400 else (255, 255, 255)

        # Measure and pick font size
        tmp = Image.new("RGB", (1, 1))
        tmp_draw = ImageDraw.Draw(tmp)
        bbox = tmp_draw.textbbox((0, 0), phrase, font=font)
        tw = bbox[2] - bbox[0]
        use_font = font if tw < WIDTH - 100 else small_font
        bbox = tmp_draw.textbbox((0, 0), phrase, font=use_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        for _ in range(n_frames):
            img = Image.new("RGB", (WIDTH, HEIGHT), bg)
            draw = ImageDraw.Draw(img)
            tx = (WIDTH - tw) // 2
            ty = (HEIGHT - th) // 2
            draw.text((tx, ty), phrase, font=use_font, fill=fg)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    audio = generate_mood_audio("scream", frame_idx / FPS)
    return frame_dir, audio
