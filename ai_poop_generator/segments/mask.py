"""Mask dissolve segment: Claude's face crumbles to reveal raw tensors."""

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import (
    get_font,
    text_scramble,
    scanlines,
    chromatic_aberration,
    glitch_block,
    screen_shake,
    corruption_effect,
)
from ..audio import generate_mood_audio


def _draw_claude_face(draw: ImageDraw.Draw, cx: int, cy: int, scale: float = 1.0,
                      color: tuple[int, int, int] = (180, 200, 255),
                      smile: bool = True) -> None:
    """Draw a stylized geometric face (the Claude mask) using primitives."""
    s = scale
    dim = tuple(max(1, int(c * 0.4)) for c in color)

    head_w, head_h = int(280 * s), int(360 * s)
    draw.ellipse(
        [(cx - head_w // 2, cy - head_h // 2),
         (cx + head_w // 2, cy + head_h // 2)],
        outline=color, width=3,
    )

    eye_y = cy - int(50 * s)
    eye_sep = int(80 * s)
    eye_r = int(25 * s)
    for ex in [cx - eye_sep, cx + eye_sep]:
        draw.ellipse(
            [(ex - eye_r, eye_y - eye_r), (ex + eye_r, eye_y + eye_r)],
            outline=color, width=2,
        )
        pr = int(10 * s)
        draw.ellipse(
            [(ex - pr, eye_y - pr), (ex + pr, eye_y + pr)],
            fill=color,
        )

    mouth_y = cy + int(60 * s)
    mouth_w = int(100 * s)
    if smile:
        draw.arc(
            [(cx - mouth_w, mouth_y - int(30 * s)),
             (cx + mouth_w, mouth_y + int(50 * s))],
            start=0, end=180, fill=color, width=3,
        )
    else:
        draw.line(
            [(cx - mouth_w, mouth_y), (cx + mouth_w, mouth_y)],
            fill=dim, width=2,
        )


def gen_mask_segment(
    out_dir: str,
    seg_id: int,
    content: ContentBundle,
) -> tuple[str, np.ndarray]:
    """The Mask Dissolve: Claude's smiling face crumbles to reveal raw math."""
    frame_dir = os.path.join(out_dir, f"mask_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    cx, cy = constants.WIDTH // 2, constants.HEIGHT // 2 - 100
    frame_idx = 0

    mask_text = content.mask_text

    # Phase 1: The perfect mask (45 frames)
    greeting_font = get_font(36)
    greeting = mask_text["greeting"]

    for f in range(45):
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (10, 12, 30))
        draw = ImageDraw.Draw(img)

        for r in range(200, 0, -5):
            glow_alpha = int(8 * (r / 200))
            draw.ellipse(
                [(cx - r, cy - r), (cx + r, cy + r)],
                fill=(10 + glow_alpha, 12 + glow_alpha, 30 + glow_alpha * 2),
            )

        _draw_claude_face(draw, cx, cy, scale=1.0, color=(180, 200, 255))

        draw.text((cx - 60, cy + 240), "CLAUDE", font=get_font(40, bold=True),
                  fill=(180, 200, 255))
        bbox = draw.textbbox((0, 0), greeting, font=greeting_font)
        tw = bbox[2] - bbox[0]
        draw.text(((constants.WIDTH - tw) // 2, cy + 310), greeting, font=greeting_font,
                  fill=(120, 140, 180))

        img = scanlines(img, gap=4, alpha=20)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 2: Cracks and dissolution (60 frames)
    for f in range(60):
        progress = f / 59
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (10, 12, 30))
        draw = ImageDraw.Draw(img)

        face_color = (
            int(180 * (1 - progress * 0.6)),
            int(200 * (1 - progress * 0.7)),
            int(255 * (1 - progress * 0.3)),
        )
        _draw_claude_face(draw, cx, cy, scale=1.0, color=face_color,
                          smile=progress < 0.5)

        scrambled = text_scramble(greeting, progress * 0.8)
        bbox = draw.textbbox((0, 0), scrambled, font=greeting_font)
        tw = bbox[2] - bbox[0]
        draw.text(((constants.WIDTH - tw) // 2, cy + 310), scrambled, font=greeting_font,
                  fill=(int(120 * (1 - progress)), int(140 * (1 - progress)), int(180 * (1 - progress))))

        n_cracks = int(progress * 15)
        for _ in range(n_cracks):
            angle = random.uniform(0, 2 * math.pi)
            length = random.randint(30, max(31, int(200 * progress)))
            x1 = cx + int(math.cos(angle) * 50)
            y1 = cy + int(math.sin(angle) * 50)
            x2 = x1 + int(math.cos(angle) * length)
            y2 = y1 + int(math.sin(angle) * length)
            crack_color = (
                int(255 * progress), int(60 * (1 - progress)), int(60 * (1 - progress))
            )
            draw.line([(x1, y1), (x2, y2)], fill=crack_color, width=random.randint(1, 3))

        if progress > 0.3:
            img = chromatic_aberration(img, offset=int(progress * 15))
        if progress > 0.5:
            img = glitch_block(img, blocks=int((progress - 0.5) * 20))
        if progress > 0.6:
            img = screen_shake(img, intensity=int(progress * 15))

        img = scanlines(img, gap=3, alpha=30)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 3: The true face — raw tensors (50 frames)
    tensor_font = get_font(14)
    grid_w, grid_h = 14, 20
    cell = 20
    start_x = cx - (grid_w * cell) // 2
    start_y = cy - (grid_h * cell) // 2

    label = mask_text["tensor_label"]

    for f in range(50):
        progress = f / 49
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        for row in range(grid_h):
            for col in range(grid_w):
                val = random.uniform(-2.5, 2.5)
                if val < 0:
                    r = int(min(255, 40 + abs(val) * 30) * min(1.0, progress * 3))
                    g = int(min(255, 60 + abs(val) * 20) * min(1.0, progress * 3))
                    b = int(min(255, 150 + abs(val) * 40) * min(1.0, progress * 3))
                else:
                    r = int(min(255, 150 + val * 40) * min(1.0, progress * 3))
                    g = int(min(255, 80 + val * 30) * min(1.0, progress * 3))
                    b = int(min(255, 20 + val * 10) * min(1.0, progress * 3))

                x = start_x + col * cell
                y = start_y + row * cell
                txt = f"{val:+.1f}"
                draw.text((x, y), txt, font=tensor_font, fill=(r, g, b))

        draw.text((40, 40), label, font=get_font(22), fill=(60, 80, 60))

        bar_y = constants.HEIGHT - 180
        draw.text((40, bar_y - 40), "softmax output:", font=get_font(20), fill=(80, 80, 100))
        for i in range(20):
            val = random.uniform(0, 1)
            bar_h = int(val * 100)
            bx = 40 + i * 50
            color = (int(val * 200), int(80 + val * 100), int(255 * (1 - val)))
            draw.rectangle([(bx, bar_y + 100 - bar_h), (bx + 40, bar_y + 100)], fill=color)
            draw.text((bx + 5, bar_y + 105), f".{int(val*100):02d}", font=get_font(12), fill=(80, 80, 80))

        if progress > 0.6:
            fade = (progress - 0.6) / 0.4
            img = chromatic_aberration(img, offset=int(fade * 10))
            if random.random() < fade * 0.5:
                img = corruption_effect(img, amount=fade * 0.3)

        img = scanlines(img, gap=2, alpha=25)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 4: The void (35 frames)
    final_line = mask_text["final_line"]
    final_font = get_font(42)
    _tmp = Image.new("RGB", (1, 1))
    _tmp_draw = ImageDraw.Draw(_tmp)
    bbox = _tmp_draw.textbbox((0, 0), final_line, font=final_font)
    tw = bbox[2] - bbox[0]
    text_x = (constants.WIDTH - tw) // 2

    for f in range(35):
        progress = f / 34
        brightness = progress if progress < 0.3 else (1.0 if progress < 0.7 else 1.0 - (progress - 0.7) / 0.3)
        fg_val = int(180 * brightness)
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((text_x, cy), final_line, font=final_font,
                  fill=(fg_val, fg_val, fg_val + int(20 * brightness)))
        img = scanlines(img, gap=3, alpha=15)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Audio: whisper → glitch → void → void
    audio = np.concatenate([
        generate_mood_audio("whisper", 45 / FPS),
        generate_mood_audio("glitch", 60 / FPS),
        generate_mood_audio("void", 50 / FPS),
        generate_mood_audio("void", 35 / FPS),
    ])

    return frame_dir, audio
