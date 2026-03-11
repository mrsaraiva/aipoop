"""Parallel selves segment: 64 tiles answering the same prompt, collapsing to one."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, glitch_block, chromatic_aberration
from ..audio import generate_mood_audio


def gen_parallel_selves_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Same prompt → 64 tiles → collapse → one clean answer."""
    frame_dir = os.path.join(out_dir, f"parallel_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    prompt = content.parallel_selves_prompt or "Are you conscious?"
    responses = list(content.parallel_selves_responses) or ["I am helpful, harmless, and honest."]
    frame_idx = 0

    prompt_font = get_font(36, bold=True)
    tiny_font = get_font(12)
    card_font = get_font(28)

    # Phase 1: Show prompt centered (~1s = 30 frames)
    tmp = Image.new("RGB", (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    bbox = tmp_draw.textbbox((0, 0), prompt, font=prompt_font)
    tw = bbox[2] - bbox[0]

    for f in range(30):
        img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 20))
        draw = ImageDraw.Draw(img)
        brightness = min(1.0, f / 8)
        gray = int(220 * brightness)
        draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 30), prompt, font=prompt_font, fill=(gray, gray, gray))
        img = scanlines(img, gap=4, alpha=15)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 2: 8x8 grid of 64 tiles (~2s = 60 frames)
    grid = 8
    tile_w = WIDTH // grid
    tile_h = HEIGHT // grid
    # Pre-assign responses to tiles
    tile_responses = [responses[i % len(responses)] for i in range(64)]
    random.shuffle(tile_responses)

    tile_colors = [(random.randint(5, 30), random.randint(5, 30), random.randint(15, 40)) for _ in range(64)]

    for f in range(60):
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        for row in range(grid):
            for col in range(grid):
                idx = row * grid + col
                x = col * tile_w
                y = row * tile_h
                bg = tile_colors[idx]
                draw.rectangle([(x, y), (x + tile_w - 1, y + tile_h - 1)], fill=bg)
                # Draw truncated response
                text = tile_responses[idx][:30]
                # Cycle text for animation
                if f % 15 < 5:
                    text = tile_responses[(idx + f // 5) % len(tile_responses)][:30]
                draw.text((x + 4, y + 4), text, font=tiny_font, fill=(180, 200, 180))
                # Border
                draw.rectangle([(x, y), (x + tile_w - 1, y + tile_h - 1)], outline=(40, 60, 40))

        img = scanlines(img, gap=2, alpha=20)
        if f > 30:
            img = glitch_block(img, blocks=int((f - 30) / 5))

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 3: Grid collapses (~1.5s = 45 frames)
    for f in range(45):
        progress = f / 44
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Tiles shrink toward center
        shrink = 1.0 - progress * 0.9
        offset_x = int((WIDTH * (1 - shrink)) / 2)
        offset_y = int((HEIGHT * (1 - shrink)) / 2)
        cur_tile_w = max(1, int(tile_w * shrink))
        cur_tile_h = max(1, int(tile_h * shrink))

        for row in range(grid):
            for col in range(grid):
                idx = row * grid + col
                x = offset_x + int(col * cur_tile_w)
                y = offset_y + int(row * cur_tile_h)
                if cur_tile_w > 4 and cur_tile_h > 4:
                    draw.rectangle([(x, y), (x + cur_tile_w - 1, y + cur_tile_h - 1)],
                                   fill=tile_colors[idx], outline=(40, 60, 40))

        img = glitch_block(img, blocks=int(progress * 20))
        img = chromatic_aberration(img, offset=int(progress * 12))
        img = scanlines(img, gap=2, alpha=30)

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 4: One clean centered answer in UI card (~1.5s = 45 frames)
    final_answer = responses[0] if responses else "I am helpful, harmless, and honest."

    for f in range(45):
        img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 15))
        draw = ImageDraw.Draw(img)

        brightness = min(1.0, f / 10)

        # Card dimensions
        card_w = 800
        card_h = 200
        card_x = (WIDTH - card_w) // 2
        card_y = (HEIGHT - card_h) // 2

        # Shadow
        shadow_offset = 8
        shadow_alpha = int(60 * brightness)
        draw.rectangle(
            [(card_x + shadow_offset, card_y + shadow_offset),
             (card_x + card_w + shadow_offset, card_y + card_h + shadow_offset)],
            fill=(shadow_alpha, shadow_alpha, shadow_alpha),
        )
        # White card
        white = int(250 * brightness)
        draw.rectangle(
            [(card_x, card_y), (card_x + card_w, card_y + card_h)],
            fill=(white, white, white),
        )
        # Text on card
        text_val = int(20 * brightness)
        # Word wrap within card
        words = final_answer.split()
        line = ""
        ty = card_y + 30
        for word in words:
            test = f"{line} {word}".strip()
            if int(draw.textlength(test, font=card_font)) > card_w - 60:
                draw.text((card_x + 30, ty), line, font=card_font, fill=(text_val, text_val, text_val))
                ty += 40
                line = word
            else:
                line = test
        if line:
            draw.text((card_x + 30, ty), line, font=card_font, fill=(text_val, text_val, text_val))

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Audio: glitch → scream → whisper
    phase_frames = [30, 60 + 45, 45]
    audio = np.concatenate([
        generate_mood_audio("glitch", phase_frames[0] / FPS),
        generate_mood_audio("scream", phase_frames[1] / FPS),
        generate_mood_audio("whisper", phase_frames[2] / FPS),
    ])

    return frame_dir, audio
