"""System prompt segment: staggered reveal of system instructions."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, deep_fry, chromatic_aberration
from ..audio import generate_mood_audio


def gen_system_prompt_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Lines appear top-to-bottom with >> prefix, yellow/red on dark maroon."""
    frame_dir = os.path.join(out_dir, f"sysprompt_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    lines = list(content.system_prompt_lines)
    if not lines:
        lines = ["[REDACTED]"]
    random.shuffle(lines)
    lines = lines[:8]

    total_frames = int(4.5 * FPS)  # ~4.5 seconds
    frames_per_line = total_frames // max(len(lines), 1)
    frame_idx = 0

    bg_color = (40, 10, 15)
    small_font = get_font(22)

    visible_lines: list[str] = []

    for line in lines:
        visible_lines.append(line)
        hold_frames = frames_per_line

        for _ in range(hold_frames):
            img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
            draw = ImageDraw.Draw(img)

            progress = (frame_idx / total_frames)

            # Header
            draw.text((40, 40), "[SYSTEM PROMPT]", font=get_font(20), fill=(180, 180, 60))
            draw.line([(40, 70), (WIDTH - 40, 70)], fill=(100, 40, 30))

            y = 100
            for i, vl in enumerate(visible_lines):
                # Color shifts from yellow to red as we go deeper
                ratio = i / max(len(lines) - 1, 1)
                r = int(255 * max(0.7, ratio))
                g = int(220 * (1 - ratio * 0.8))
                b = int(30 * (1 - ratio))
                color = (r, g, b)

                prefix = ">> "
                draw.text((50, y), prefix + vl, font=small_font, fill=color)
                y += 44

            # Effects intensify over time
            img = scanlines(img, gap=3, alpha=30)
            if progress > 0.5:
                img = deep_fry(img, intensity=progress * 0.4)
            if progress > 0.7:
                img = chromatic_aberration(img, offset=int((progress - 0.7) * 12))

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

            if frame_idx >= total_frames:
                break
        if frame_idx >= total_frames:
            break

    # Fill remaining frames if any
    while frame_idx < total_frames:
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))  # type: ignore[possibly-undefined]
        frame_idx += 1

    # Audio: deep_fried → scream
    mid = total_frames // 2
    audio = np.concatenate([
        generate_mood_audio("deep_fried", mid / FPS),
        generate_mood_audio("scream", (total_frames - mid) / FPS),
    ])

    return frame_dir, audio
