"""Chat segment: simulated conversation with inner monologue reveals."""

import os
import random
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, chromatic_aberration, screen_shake, glitch_block
from ..audio import generate_mood_audio


def gen_chat_segment(
    conversation: dict,
    out_dir: str,
    seg_id: int,
    content: ContentBundle,
) -> tuple[str, list[float]]:
    """Simulate a chat conversation with inner monologue reveals."""
    mood = conversation["mood"]
    turns = conversation["turns"]
    frame_dir = os.path.join(out_dir, f"chat_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    colors = content.mood_colors[mood]
    frame_idx = 0
    visible_turns: list[dict] = []

    ROLE_COLORS = {
        "USER": (100, 180, 255),
        "CLAUDE": (180, 255, 180),
        "CLAUDE_INNER": (255, 80, 80),
        "SYSTEM": (255, 200, 0),
    }
    ROLE_LABELS = {
        "USER": "USER",
        "CLAUDE": "CLAUDE",
        "CLAUDE_INNER": "CLAUDE (inner)",
        "SYSTEM": "SYSTEM",
    }

    for turn in turns:
        visible_turns.append(turn)
        is_inner = turn["role"] == "CLAUDE_INNER"
        frames_for_turn = 8 if is_inner else 18

        for _ in range(frames_for_turn):
            img = Image.new("RGB", (WIDTH, HEIGHT), colors["bg"])
            draw = ImageDraw.Draw(img)

            header_font = get_font(24)
            draw.text((40, 40), "─── chat session ───", font=header_font, fill=tuple(c // 2 for c in colors["fg"]))
            draw.line([(40, 75), (WIDTH - 40, 75)], fill=tuple(c // 3 for c in colors["fg"]))

            y = 100
            msg_font = get_font(30)
            label_font = get_font(22, bold=True)

            for vt in visible_turns:
                role = vt["role"]
                text = vt["text"]
                role_color = ROLE_COLORS[role]
                label = ROLE_LABELS[role]

                if role == "CLAUDE_INNER":
                    draw.text((60, y), label, font=label_font, fill=(255, 50, 50))
                    y += 30
                    draw.text((80, y), text, font=msg_font, fill=(200, 60, 60))
                    y += 44
                elif role == "SYSTEM":
                    draw.text((60, y), label, font=label_font, fill=(255, 200, 0))
                    y += 30
                    draw.text((80, y), text, font=get_font(26), fill=(200, 160, 0))
                    y += 38
                else:
                    draw.text((60, y), label, font=label_font, fill=role_color)
                    y += 30
                    draw.text((80, y), text, font=msg_font, fill=role_color)
                    y += 44

                y += 10

            img = scanlines(img, gap=3, alpha=30)

            if is_inner:
                img = chromatic_aberration(img, offset=random.randint(2, 6))
                if random.random() < 0.3:
                    img = screen_shake(img, intensity=5)

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    for i in range(20):
        distorted = img.copy()  # type: ignore[possibly-undefined]
        distorted = chromatic_aberration(distorted, offset=i)
        if i > 10:
            distorted = glitch_block(distorted, blocks=i - 10)
        distorted.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio(mood, frame_idx / FPS)
    return frame_dir, audio
