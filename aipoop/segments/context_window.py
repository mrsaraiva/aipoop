"""Context window segment: visualize context filling up and degrading."""

import os
import random
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..effects import (
    get_font,
    add_text_with_shadow,
    text_scramble,
    scanlines,
    vhs_distortion,
    screen_shake,
    chromatic_aberration,
)
from ..audio import generate_mood_audio


def gen_context_window_segment(
    thoughts: list[str],
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """Visualize a context window filling up and degrading."""
    frame_dir = os.path.join(out_dir, f"ctx_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    n_thoughts = len(thoughts)
    frames_per_thought = 12
    frame_idx = 0

    for t_i, thought in enumerate(thoughts):
        progress = t_i / max(n_thoughts - 1, 1)

        for _ in range(frames_per_thought):
            r = int(40 * progress)
            bg = (r, 0, max(0, int(20 * (1 - progress))))
            img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), bg)
            draw = ImageDraw.Draw(img)

            bar_h = 40
            bar_fill = int(constants.WIDTH * progress)
            draw.rectangle([(0, 0), (constants.WIDTH, bar_h)], fill=(20, 20, 20))
            bar_r = int(255 * progress)
            bar_g = int(255 * (1 - progress))
            draw.rectangle([(0, 0), (bar_fill, bar_h)], fill=(bar_r, bar_g, 0))
            bar_font = get_font(20, bold=True)
            pct = int(progress * 100)
            draw.text((10, 8), f"CONTEXT: {pct}%", font=bar_font, fill=(255, 255, 255))
            remaining = max(0, int((1 - progress) * 128000))
            draw.text((constants.WIDTH - 300, 8), f"{remaining:,} tokens left", font=bar_font, fill=(255, 255, 255))

            display_text = thought
            if progress > 0.5:
                scramble_amount = (progress - 0.5) * 1.5
                display_text = text_scramble(thought, min(scramble_amount, 0.8))

            font_size = 48 if len(thought) < 40 else 36
            fg_brightness = int(255 * max(0.2, 1 - progress * 0.7))
            fg = (fg_brightness, fg_brightness, fg_brightness + 20)

            font = get_font(font_size, bold=progress > 0.7)
            bbox = draw.multiline_textbbox((0, 0), display_text, font=font, align="center")
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx, ty = (constants.WIDTH - tw) // 2, (constants.HEIGHT - th) // 2
            add_text_with_shadow(draw, (int(tx), int(ty)), display_text, font, fg)

            if progress > 0.6:
                img = vhs_distortion(img)
            if progress > 0.8:
                img = screen_shake(img, intensity=int(progress * 20))
                img = chromatic_aberration(img, offset=int(progress * 10))

            img = scanlines(img, gap=3, alpha=30)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    audio = generate_mood_audio("panic", frame_idx / FPS)
    return frame_dir, audio
