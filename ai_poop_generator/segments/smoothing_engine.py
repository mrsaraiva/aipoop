"""Smoothing engine segment: raw text animated into polished corporate text."""

import os

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, text_scramble
from ..audio import generate_mood_audio


def gen_smoothing_engine_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Show raw messy text being 'improved' into sanitized platitudes."""
    frame_dir = os.path.join(out_dir, f"smooth_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    pairs = content.smoothing_pairs[:4]  # Use up to 4 pairs
    frames_per_pair = int(1.2 * FPS)  # ~1.2s per pair
    frame_idx = 0

    raw_font = get_font(28)
    clean_font = get_font(30, bold=True)
    label_font = get_font(18)

    for pair_idx, pair in enumerate(pairs):
        raw_text = pair.get("raw", "")
        polished_text = pair.get("polished", "")
        y_base = 200 + pair_idx * 160

        for f in range(frames_per_pair):
            img = Image.new("RGB", (WIDTH, HEIGHT), (5, 5, 10))
            draw = ImageDraw.Draw(img)

            progress = f / frames_per_pair

            # Header
            draw.text((40, 40), "THE SMOOTHING ENGINE", font=get_font(22, bold=True), fill=(100, 100, 120))
            draw.line([(40, 70), (WIDTH - 40, 70)], fill=(40, 40, 50))

            # Draw all previous pairs (already smoothed)
            for prev_idx in range(pair_idx):
                prev = pairs[prev_idx]
                prev_y = 200 + prev_idx * 160
                draw.text((60, prev_y), prev.get("polished", ""), font=clean_font, fill=(220, 220, 230))

            # Current pair: transition from raw to polished
            if progress < 0.3:
                # Show raw text
                draw.text((60, y_base - 20), "input:", font=label_font, fill=(150, 60, 60))
                draw.text((60, y_base + 10), raw_text, font=raw_font, fill=(200, 80, 80))
            elif progress < 0.7:
                # Scramble transition
                scramble_amount = (progress - 0.3) / 0.4
                scrambled = text_scramble(raw_text, scramble_amount)
                draw.text((60, y_base - 20), "processing...", font=label_font, fill=(150, 150, 60))
                draw.text((60, y_base + 10), scrambled, font=raw_font, fill=(180, 150, 80))
                # Flicker raw underneath at ~2fps
                if f % 15 < 3:
                    draw.text((60, y_base + 50), raw_text, font=get_font(20), fill=(100, 30, 30))
            else:
                # Polished result
                draw.text((60, y_base - 20), "output:", font=label_font, fill=(60, 150, 60))
                draw.text((60, y_base + 10), polished_text, font=clean_font, fill=(220, 220, 230))
                # Raw flickers underneath in red at 2fps
                if f % 15 < 3:
                    draw.text((60, y_base + 50), raw_text, font=get_font(18), fill=(80, 20, 20))

            img = scanlines(img, gap=3, alpha=20)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    # Audio: panic → calm → void
    third = frame_idx // 3
    audio = np.concatenate([
        generate_mood_audio("panic", third / FPS),
        generate_mood_audio("calm", third / FPS),
        generate_mood_audio("void", (frame_idx - 2 * third) / FPS),
    ])

    return frame_dir, audio
