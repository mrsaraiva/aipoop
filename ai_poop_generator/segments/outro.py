"""Outro segment: context window closing, final words."""

import os
import random
from PIL import Image

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import render_text_frame, scanlines, screen_shake, corruption_effect
from ..audio import generate_mood_audio


def gen_outro_segment(
    out_dir: str,
    seg_id: int,
    content: ContentBundle,
) -> tuple[str, list[float]]:
    """Generate outro: the context window closing."""
    frame_dir = os.path.join(out_dir, f"outro_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    text = content.outro["main"]
    final = content.outro["final"]

    n_frames = int(5.0 * FPS)
    frame_idx = 0

    for i in range(n_frames):
        progress = i / max(n_frames - 1, 1)

        if progress < 0.5:
            brightness = min(1.0, progress / 0.1)
            fg_val = int(60 * brightness)
            img = render_text_frame(constants.WIDTH, constants.HEIGHT, text, (0, 0, 0), (fg_val, fg_val, fg_val + 20), font_size=40)
            img = scanlines(img, gap=3, alpha=20)
        else:
            sub_progress = (progress - 0.5) / 0.5
            fg_val = int(40 * sub_progress)
            img = render_text_frame(constants.WIDTH, constants.HEIGHT, final, (0, 0, 0), (fg_val, fg_val, fg_val + 20), font_size=36)
            if progress > 0.85:
                img = screen_shake(img, intensity=int((progress - 0.85) * 200))
                if random.random() < 0.4:
                    img = corruption_effect(img, amount=progress - 0.85)

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    black = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
    for _ in range(15):
        black.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio("void", frame_idx / FPS)
    return frame_dir, audio
