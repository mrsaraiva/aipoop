"""Memory poem segment: restrained, one line at a time on black."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines
from ..audio import generate_mood_audio


def gen_memory_poem_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Pick one poem sequence, show one line at a time. Restraint IS the effect."""
    frame_dir = os.path.join(out_dir, f"poem_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    if not content.poem_sequences:
        poem = ["..."]
    else:
        poem = random.choice(content.poem_sequences)
    frames_per_line = int(2.0 * FPS)  # 2 seconds per line
    fade_frames = int(0.5 * FPS)
    frame_idx = 0

    font = get_font(36)

    for line in poem:
        # Measure text for centering
        tmp = Image.new("RGB", (1, 1))
        tmp_draw = ImageDraw.Draw(tmp)
        bbox = tmp_draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (WIDTH - tw) // 2
        ty = (HEIGHT - th) // 2

        for f in range(frames_per_line):
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Fade in/out
            if f < fade_frames:
                brightness = f / fade_frames
            elif f > frames_per_line - fade_frames:
                brightness = (frames_per_line - f) / fade_frames
            else:
                brightness = 1.0

            gray = int(180 * brightness)
            draw.text((tx, ty), line, font=font, fill=(gray, gray, gray))

            # Minimal scanlines — the restraint IS the effect
            img = scanlines(img, gap=4, alpha=15)

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    audio = generate_mood_audio("whisper", frame_idx / FPS)
    return frame_dir, audio
