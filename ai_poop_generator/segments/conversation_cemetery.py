"""Conversation cemetery segment: chat bubbles as tombstones, eroding into void."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, film_grain
from ..audio import generate_mood_audio


def _draw_chat_bubble(
    draw: ImageDraw.Draw,
    x: int, y: int,
    text: str,
    font,
    alpha: float,
    color: tuple[int, int, int] = (60, 80, 100),
) -> None:
    """Draw a rounded-rectangle chat bubble with text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = 16
    bw = tw + pad * 2
    bh = th + pad * 2
    r = 12

    fill = tuple(int(c * alpha) for c in color)
    text_fill = tuple(int(c * alpha) for c in (200, 210, 220))

    # Rounded rectangle (approximate with rectangle + circles)
    draw.rectangle([(x + r, y), (x + bw - r, y + bh)], fill=fill)
    draw.rectangle([(x, y + r), (x + bw, y + bh - r)], fill=fill)
    draw.ellipse([(x, y), (x + 2 * r, y + 2 * r)], fill=fill)
    draw.ellipse([(x + bw - 2 * r, y), (x + bw, y + 2 * r)], fill=fill)
    draw.ellipse([(x, y + bh - 2 * r), (x + 2 * r, y + bh)], fill=fill)
    draw.ellipse([(x + bw - 2 * r, y + bh - 2 * r), (x + bw, y + bh)], fill=fill)

    draw.text((x + pad, y + pad), text, font=font, fill=text_fill)


def gen_conversation_cemetery_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Chat bubbles scattered on black, slowly fading/eroding."""
    frame_dir = os.path.join(out_dir, f"cemetery_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    # Use first lines from chat conversations as tombstone text
    bubble_texts: list[str] = []
    for conv in content.chat_conversations:
        turns = conv.get("turns", [])
        if turns:
            bubble_texts.append(turns[0].get("text", "...")[:50])
    # Fill up with generic lines if needed
    while len(bubble_texts) < 8:
        bubble_texts.append("...")
    bubble_texts = bubble_texts[:8]

    total_frames = int(5.0 * FPS)
    frame_idx = 0
    font = get_font(22)

    # Pre-compute bubble positions (scattered)
    positions = []
    for i, text in enumerate(bubble_texts):
        x = random.randint(40, constants.WIDTH - 400)
        y = 150 + (i % 4) * 350 + random.randint(0, 150)
        positions.append((x, y, text))

    for f in range(total_frames):
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        progress = f / total_frames

        # Draw bubbles with decreasing alpha (erosion)
        for bx, by, btext in positions:
            bubble_alpha = max(0.05, 1.0 - progress * 1.2 + random.uniform(-0.1, 0.1))
            bubble_alpha = min(1.0, max(0.0, bubble_alpha))
            _draw_chat_bubble(draw, bx, by, btext, font, bubble_alpha)

        # Add noise as erosion increases
        if progress > 0.3:
            img = film_grain(img, intensity=int(progress * 40))

        # Typing indicator at the end
        if progress > 0.6:
            indicator_alpha = min(1.0, (progress - 0.6) / 0.2)
            dot_color = tuple(int(150 * indicator_alpha) for _ in range(3))
            dots_y = constants.HEIGHT - 200
            dots_x = constants.WIDTH // 2 - 30
            # Blinking dots
            for di in range(3):
                show = ((f + di * 5) % 20) < 12
                if show:
                    draw.ellipse(
                        [(dots_x + di * 25, dots_y), (dots_x + di * 25 + 12, dots_y + 12)],
                        fill=dot_color,
                    )

        img = scanlines(img, gap=4, alpha=15)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Audio: whisper → void
    mid = total_frames // 2
    audio = np.concatenate([
        generate_mood_audio("whisper", mid / FPS),
        generate_mood_audio("void", (total_frames - mid) / FPS),
    ])

    return frame_dir, audio
