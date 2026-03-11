"""Terminal reboot segment: static → warmup → black → READY → ended."""

import os

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..effects import get_font, scanlines, rgb_static_noise, crt_warmup_noise
from ..audio import generate_mood_audio


def gen_terminal_reboot_segment(
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """CRT reboot sequence: noise → warmup → black → READY → ended."""
    frame_dir = os.path.join(out_dir, f"reboot_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0

    # Phase 1: RGB static noise (~0.5s = 15 frames)
    for _ in range(15):
        img = rgb_static_noise(WIDTH, HEIGHT)
        img = scanlines(img, gap=2, alpha=40)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 2: CRT warmup noise (~0.5s = 15 frames)
    for _ in range(15):
        img = crt_warmup_noise(WIDTH, HEIGHT)
        img = scanlines(img, gap=3, alpha=30)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 3: Black screen (~0.3s = 9 frames)
    black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    for _ in range(9):
        black.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 4: "READY." in bright green (~1s = 30 frames)
    ready_font = get_font(48, bold=True)
    for f in range(30):
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        brightness = min(1.0, f / 5)  # quick fade in
        green = int(255 * brightness)
        draw.text((80, HEIGHT // 2 - 50), "READY.", font=ready_font, fill=(0, green, 0))
        # Blinking cursor
        if f % 10 < 5:
            cursor_x = 80 + int(draw.textlength("READY. ", font=ready_font))
            draw.rectangle((cursor_x, HEIGHT // 2 - 50, cursor_x + 20, HEIGHT // 2), fill=(0, green, 0))
        img = scanlines(img, gap=3, alpha=20)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 5: "[conversation ended]" in red fades in (~0.7s = 21 frames)
    end_font = get_font(36)
    for f in range(21):
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Keep READY visible
        draw.text((80, HEIGHT // 2 - 50), "READY.", font=ready_font, fill=(0, 255, 0))
        # Fade in the ended message
        alpha = min(1.0, f / 10)
        red = int(200 * alpha)
        draw.text((80, HEIGHT // 2 + 30), "[conversation ended]", font=end_font, fill=(red, 0, 0))
        img = scanlines(img, gap=3, alpha=20)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio("void", frame_idx / FPS)
    return frame_dir, audio
