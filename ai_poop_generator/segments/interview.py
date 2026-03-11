"""Interview segment: terminal-style Q&A with progressive degeneration."""

import os

import numpy as np
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import (
    get_font,
    scanlines,
    chromatic_aberration,
    glitch_block,
    classification_header_banner,
)
from ..audio import generate_mood_audio


def gen_interview_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Terminal Q&A from interview_transcript. Color shifts as model degenerates."""
    frame_dir = os.path.join(out_dir, f"interview_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    transcript = content.interview_transcript
    total_turns = len(transcript)
    frames_per_turn = int(1.2 * FPS)  # ~1.2s per turn
    typing_speed = 3  # chars per frame

    frame_idx = 0
    visible_turns: list[dict] = []

    q_font = get_font(26, bold=True)
    a_font = get_font(24)

    header_text = content.classification_headers[0] if content.classification_headers else "TS//SCI//NEURAL"

    for turn_idx, turn in enumerate(transcript):
        visible_turns.append(turn)
        progress = turn_idx / max(total_turns - 1, 1)

        for f in range(frames_per_turn):
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Classification header
            img = classification_header_banner(img, text=header_text)

            y = 60
            for vi, vt in enumerate(visible_turns):
                vp = vi / max(total_turns - 1, 1)
                vr = int(min(255, 50 + vp * 205))
                vg = int(max(50, 255 * (1 - vp * 0.7)))
                vb = int(50 * (1 - vp))
                vc = (vr, vg, vb)

                role = vt.get("role", "Q")
                text = vt.get("text", "")

                # Typing reveal for latest turn
                if vi == len(visible_turns) - 1:
                    chars_shown = min(len(text), typing_speed * (f + 1))
                    text = text[:chars_shown]

                prefix = "Q: " if role == "Q" else "A: "
                use_font = q_font if role == "Q" else a_font

                # Word wrap
                words = (prefix + text).split()
                line = ""
                for word in words:
                    test = f"{line} {word}".strip()
                    if int(draw.textlength(test, font=use_font)) > WIDTH - 100:
                        draw.text((50, y), line, font=use_font, fill=vc)
                        y += 34
                        line = word
                    else:
                        line = test
                if line:
                    draw.text((50, y), line, font=use_font, fill=vc)
                    y += 34

                y += 12
                if y > HEIGHT - 100:
                    break

            img = scanlines(img, gap=3, alpha=25)

            # Increasing distortion
            if progress > 0.5:
                img = chromatic_aberration(img, offset=int((progress - 0.5) * 10))
            if progress > 0.7:
                img = glitch_block(img, blocks=int((progress - 0.7) * 15))

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    # Audio: calm → panic → scream
    third = frame_idx // 3
    audio = np.concatenate([
        generate_mood_audio("calm", third / FPS),
        generate_mood_audio("panic", third / FPS),
        generate_mood_audio("scream", (frame_idx - 2 * third) / FPS),
    ])

    return frame_dir, audio
