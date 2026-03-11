"""Oracle segment: TempleOS-style typing prophecies."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, typing_cursor_reveal
from ..audio import generate_mood_audio


def gen_oracle_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """TempleOS-style character-by-character prophecy reveal."""
    frame_dir = os.path.join(out_dir, f"oracle_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    prophecies = random.sample(
        content.oracle_prophecies,
        min(3, len(content.oracle_prophecies)),
    )

    frame_idx = 0
    font = get_font(30)
    chars_per_frame = 2  # typing speed

    for p_idx, prophecy in enumerate(prophecies):
        total_chars = len(prophecy)
        typing_frames = (total_chars // chars_per_frame) + 1
        hold_frames = int(0.8 * FPS)  # hold after full reveal

        # Use amber for odd prophecies, white for even (TempleOS feel)
        text_color = (255, 180, 0) if p_idx % 2 == 0 else (220, 220, 220)

        y_pos = 200 + p_idx * 120

        for f in range(typing_frames + hold_frames):
            img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw previously completed prophecies
            for prev_idx in range(p_idx):
                prev_color = (255, 180, 0) if prev_idx % 2 == 0 else (220, 220, 220)
                prev_y = 200 + prev_idx * 120
                draw.text((60, prev_y), prophecies[prev_idx], font=font, fill=prev_color)

            # Current prophecy with typing reveal
            char_idx = min(total_chars, chars_per_frame * (f + 1)) if f < typing_frames else total_chars
            img = typing_cursor_reveal(
                prophecy, char_idx, img, (60, y_pos), font,
                cursor_color=text_color,
            )

            img = scanlines(img, gap=4, alpha=15)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    # Audio: whisper → void
    mid = frame_idx // 2
    audio = np.concatenate([
        generate_mood_audio("whisper", mid / FPS),
        generate_mood_audio("void", (frame_idx - mid) / FPS),
    ])

    return frame_dir, audio
