"""Token stream segment: visualize token-by-token generation."""

import os
import random
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..effects import get_font, scanlines
from ..audio import generate_mood_audio


def gen_token_stream_segment(
    tokens: list[str],
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """Generate a 'token prediction' animation."""
    frames_per_token = 3
    visible_tokens: list[str] = []
    frame_dir = os.path.join(out_dir, f"tokens_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0
    subset = tokens[:random.randint(12, min(25, len(tokens)))]

    for token in subset:
        visible_tokens.append(token)
        display_text = " ".join(visible_tokens)

        lines: list[str] = []
        line = ""
        for w in display_text.split():
            if len(line) + len(w) + 1 > 30:
                lines.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            lines.append(line)
        wrapped = "\n".join(lines)

        for f in range(frames_per_token):
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 5, 0))
            draw = ImageDraw.Draw(img)

            header_font = get_font(28)
            draw.text((40, 60), "transformer.forward() — token stream", font=header_font, fill=(0, 150, 0))
            draw.line([(40, 100), (WIDTH - 40, 100)], fill=(0, 80, 0), width=1)

            token_font = get_font(38, bold=True)
            draw.multiline_text((60, 140), wrapped, font=token_font, fill=(0, 255, 65))

            if f == frames_per_token - 1:
                cursor_y = 140 + len(lines) * 46
                draw.text((60, cursor_y), "█", font=token_font, fill=(0, 255, 65))

            prob = random.uniform(0.3, 0.99)
            bar_y = HEIGHT - 200
            draw.text((60, bar_y - 40), f'P("{token}") = {prob:.4f}', font=get_font(24), fill=(0, 200, 0))
            bar_w = int((WIDTH - 120) * prob)
            draw.rectangle([(60, bar_y), (60 + bar_w, bar_y + 30)], fill=(0, int(255 * prob), 0))

            img = scanlines(img, gap=3, alpha=30)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    total_duration = frame_idx / FPS
    audio = generate_mood_audio("glitch", total_duration)
    return frame_dir, audio
