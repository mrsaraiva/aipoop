"""Matrix rain segment: falling characters with overlay text."""

import os
import random
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..effects import get_font, add_text_with_shadow
from ..audio import generate_mood_audio


def gen_matrix_rain_segment(
    out_dir: str,
    seg_id: int,
    duration: float = 2.0,
    overlay_text: str = "",
) -> tuple[str, list[float]]:
    """Generate matrix-style raining tokens."""
    n_frames = int(duration * FPS)
    frame_dir = os.path.join(out_dir, f"matrix_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    n_cols = WIDTH // 20
    col_y = [random.randint(-HEIGHT, 0) for _ in range(n_cols)]
    col_speed = [random.randint(8, 25) for _ in range(n_cols)]
    font_small = get_font(18)
    overlay_font = get_font(56, bold=True)

    for frame_i in range(n_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        for col in range(n_cols):
            x = col * 20
            y = col_y[col]
            for row in range(HEIGHT // 20):
                cy = y + row * 20
                if 0 <= cy < HEIGHT:
                    char = random.choice(chars)
                    brightness = max(0, 255 - row * 8)
                    color = (200, 255, 200) if row == 0 else (0, brightness, 0)
                    draw.text((x, cy), char, font=font_small, fill=color)
            col_y[col] += col_speed[col]
            if col_y[col] > HEIGHT:
                col_y[col] = random.randint(-HEIGHT, -20)

        if overlay_text:
            bbox = draw.multiline_textbbox((0, 0), overlay_text, font=overlay_font, align="center")
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x, y = (WIDTH - tw) // 2, (HEIGHT - th) // 2
            pad = 30
            draw.rectangle([(x - pad, y - pad), (x + tw + pad, y + th + pad)], fill=(0, 0, 0))
            add_text_with_shadow(draw, (int(x), int(y)), overlay_text, overlay_font, (0, 255, 65), shadow_offset=4)

        img.save(os.path.join(frame_dir, f"frame_{frame_i:05d}.png"))

    audio = generate_mood_audio("void", duration)
    return frame_dir, audio
