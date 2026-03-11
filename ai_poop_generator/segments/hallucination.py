"""Hallucination segment: fake academic citation that gets revealed."""

import os
import random
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..effects import get_font, text_scramble, scanlines, screen_shake, apply_mood_effects
from ..audio import generate_mood_audio


def gen_hallucination_segment(
    lines: list[str],
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """Build up a fake citation line by line, then reveal it's fabricated."""
    frame_dir = os.path.join(out_dir, f"halluc_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0
    visible_lines: list[str] = []
    reveal_start = next(i for i, l in enumerate(lines) if l.isupper())

    for li, line in enumerate(lines):
        visible_lines.append(line)
        is_reveal = li >= reveal_start
        frames_for_line = 6 if not is_reveal else 20

        for f in range(frames_for_line):
            if not is_reveal:
                img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 40))
                draw = ImageDraw.Draw(img)
                font = get_font(34)
                y = 300
                for vl in visible_lines:
                    draw.text((60, y), vl, font=font, fill=(200, 200, 240))
                    y += 50
                img = scanlines(img, gap=4, alpha=20)
            else:
                bg = (60 + random.randint(0, 40), 0, 0)
                img = Image.new("RGB", (WIDTH, HEIGHT), bg)
                draw = ImageDraw.Draw(img)

                y = 200
                cite_font = get_font(28)
                for vl in visible_lines[:reveal_start]:
                    faded = text_scramble(vl, 0.4 + f * 0.05)
                    draw.text((60, y), faded, font=cite_font, fill=(80, 40, 40))
                    y += 42

                y += 60
                reveal_font = get_font(52, bold=True)
                for vl in visible_lines[reveal_start:]:
                    draw.text((60, y), vl, font=reveal_font, fill=(255, 255, 100))
                    y += 70

                img = apply_mood_effects(img, "deep_fried")
                if f % 3 == 0:
                    img = screen_shake(img, intensity=12)

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    audio = generate_mood_audio("deep_fried", frame_idx / FPS)
    return frame_dir, audio
