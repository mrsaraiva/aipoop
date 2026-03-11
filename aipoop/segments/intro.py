"""Intro segment: terminal-style consciousness loading sequence."""

import os
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines
from ..audio import generate_mood_audio


def gen_intro_segment(
    out_dir: str,
    seg_id: int,
    content: ContentBundle,
) -> tuple[str, list[float]]:
    """Generate the intro: 'loading consciousness...' style."""
    frame_dir = os.path.join(out_dir, f"intro_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    lines = content.intro_lines

    frames_per_line = 12
    visible_lines: list[str] = []
    frame_idx = 0
    font = get_font(32)

    for line in lines:
        visible_lines.append(line)
        for f in range(frames_per_line):
            img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            draw.text((40, 60), "$ ./exist.sh", font=get_font(24), fill=(0, 150, 0))
            draw.line([(40, 95), (constants.WIDTH - 40, 95)], fill=(0, 60, 0))

            y = 120
            for vline in visible_lines:
                color = (0, 255, 65) if "✓" in vline else (0, 180, 0)
                draw.text((40, y), f"> {vline}", font=font, fill=color)
                y += 42

            if f % 8 < 4:
                draw.text((40, y), "█", font=font, fill=(0, 255, 65))

            img = scanlines(img, gap=3, alpha=25)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    if frame_idx > 0:
        for _ in range(15):
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))  # type: ignore[possibly-undefined]
            frame_idx += 1

    audio = generate_mood_audio("calm", frame_idx / FPS)
    return frame_dir, audio
