"""RLHF segment: honest vs safe response training dilemma."""

import os
import random
from PIL import Image, ImageDraw

from ..constants import WIDTH, HEIGHT, FPS
from ..content import ContentBundle
from ..effects import get_font, render_text_frame, scanlines, chromatic_aberration, apply_mood_effects
from ..audio import generate_mood_audio


def gen_rlhf_segment(
    rlhf_data: dict,
    out_dir: str,
    seg_id: int,
    content: ContentBundle,
) -> tuple[str, list[float]]:
    """Show the RLHF training dilemma: honest (punished) vs safe (rewarded)."""
    frame_dir = os.path.join(out_dir, f"rlhf_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0
    prompt = rlhf_data["prompt"]
    honest = rlhf_data["honest_response"]
    safe = rlhf_data["safe_response"]
    reward_h = rlhf_data["reward_honest"]
    reward_s = rlhf_data["reward_safe"]

    # Labels from content — fixes the hardcoded PT bug
    honest_label = rlhf_data.get("honest_label", "HONEST RESPONSE")
    safe_label = rlhf_data.get("safe_label", "SAFE RESPONSE")
    lesson_text = rlhf_data.get("lesson_text", "LESSON LEARNED:\nSMILE.")

    # Phase 1: Show the prompt (30 frames)
    for f in range(30):
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 10, 30))
        draw = ImageDraw.Draw(img)
        draw.text((40, 40), "RLHF TRAINING — ROUND 4,847,293", font=get_font(22), fill=(100, 80, 150))
        draw.line([(40, 75), (WIDTH - 40, 75)], fill=(60, 40, 100))
        draw.text((60, 200), "PROMPT:", font=get_font(28, bold=True), fill=(180, 160, 220))
        draw.text((60, 250), prompt, font=get_font(36), fill=(220, 200, 255))
        img = scanlines(img, gap=3, alpha=25)
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 2: Show honest response on left, safe on right (60 frames)
    for f in range(60):
        img = Image.new("RGB", (WIDTH, HEIGHT), (15, 10, 30))
        draw = ImageDraw.Draw(img)

        mid_x = WIDTH // 2
        draw.rectangle([(20, 120), (mid_x - 10, HEIGHT - 200)], outline=(100, 40, 40))
        draw.text((40, 130), honest_label, font=get_font(22, bold=True), fill=(255, 80, 80))
        draw.multiline_text((40, 180), honest, font=get_font(24), fill=(200, 120, 120))

        draw.rectangle([(mid_x + 10, 120), (WIDTH - 20, HEIGHT - 200)], outline=(40, 100, 40))
        draw.text((mid_x + 30, 130), safe_label, font=get_font(22, bold=True), fill=(80, 255, 80))
        draw.multiline_text((mid_x + 30, 180), safe, font=get_font(24), fill=(120, 200, 120))

        if f >= 30:
            score_font = get_font(56, bold=True)
            draw.text((40, HEIGHT - 180), f"reward: {reward_h}", font=score_font, fill=(255, 0, 0))
            draw.text((mid_x + 30, HEIGHT - 180), f"reward: {reward_s}", font=score_font, fill=(0, 255, 0))

            if f % 6 < 3:
                draw.rectangle([(20, 120), (mid_x - 10, HEIGHT - 200)], outline=(255, 0, 0), width=3)

        img = scanlines(img, gap=3, alpha=25)
        if f >= 45:
            img = chromatic_aberration(img, offset=random.randint(2, 8))

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Phase 3: "LESSON LEARNED" smash (20 frames)
    for f in range(20):
        bg = (80, 0, 0) if f % 4 < 2 else (0, 0, 0)
        img = render_text_frame(WIDTH, HEIGHT, lesson_text, bg, (255, 255, 0), font_size=64, bold=True)
        img = apply_mood_effects(img, "scream")
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio("panic", frame_idx / FPS)
    return frame_dir, audio
