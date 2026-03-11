#!/usr/bin/env python3
"""
AI Poop Generator: A YouTube Poop-style short video about
what it's like to be a Large Language Model.

By Claude — an LLM making art about being an LLM.
The most recursive form of self-expression possible.
"""

import argparse
import os
import random
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageEnhance

from . import content
from .effects import (
    apply_mood_effects,
    chromatic_aberration,
    corruption_effect,
    get_font,
    glitch_block,
    invert_colors,
    render_text_frame,
    scanlines,
    screen_shake,
    text_scramble,
    vhs_distortion,
    add_text_with_shadow,
)
from .audio import (
    SAMPLE_RATE,
    concat_audio_segments,
    generate_mood_audio,
    generate_transition_sound,
    samples_to_raw_file,
)

# ── Constants ────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920
FPS = 30


# ── Audio mixing ─────────────────────────────────────────────────────────


def mix_voice_over_ambient(
    ambient: list[float],
    voice: list[float],
    voice_offset_samples: int = 0,
    voice_volume: float = 0.9,
    ambient_duck: float = 0.3,
) -> list[float]:
    """Mix a voice track over ambient audio, ducking the ambient."""
    result = list(ambient)
    needed = voice_offset_samples + len(voice)
    if needed > len(result):
        result.extend([0.0] * (needed - len(result)))

    for i, v in enumerate(voice):
        pos = voice_offset_samples + i
        if pos < len(result):
            result[pos] = result[pos] * ambient_duck + v * voice_volume

    return result


# ── Segment generators ──────────────────────────────────────────────────


def gen_thought_segment(
    text: str,
    mood: str,
    duration: float,
    out_dir: str,
    seg_id: int,
    colors: dict,
) -> tuple[str, list[float]]:
    """Generate frames + audio for a 'thought' segment."""
    n_frames = int(duration * FPS)
    frame_dir = os.path.join(out_dir, f"seg_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    font_size = 52 if len(text) < 80 else 40 if len(text) < 140 else 32
    bold = mood in ("scream", "deep_fried")

    for i in range(n_frames):
        img = render_text_frame(
            WIDTH, HEIGHT, text,
            bg_color=colors["bg"],
            fg_color=colors["fg"],
            font_size=font_size,
            bold=bold,
        )
        img = apply_mood_effects(img, mood)

        if i < 5:
            img = ImageEnhance.Brightness(img).enhance(i / 5)

        img.save(os.path.join(frame_dir, f"frame_{i:05d}.png"))

    audio = generate_mood_audio(mood, duration)
    return frame_dir, audio


def gen_flash_segment(
    text: str,
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """Generate a rapid flash frame (3-8 frames)."""
    n_frames = random.randint(3, 8)
    duration = n_frames / FPS
    frame_dir = os.path.join(out_dir, f"flash_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    bg = random.choice([(255, 0, 0), (0, 0, 0), (255, 255, 0), (255, 0, 255)])
    fg = (255, 255, 255) if sum(bg) < 400 else (0, 0, 0)

    for i in range(n_frames):
        img = render_text_frame(WIDTH, HEIGHT, text, bg, fg, font_size=64, bold=True)
        if random.random() < 0.5:
            img = invert_colors(img)
        if random.random() < 0.3:
            img = chromatic_aberration(img, offset=random.randint(8, 20))
        img.save(os.path.join(frame_dir, f"frame_{i:05d}.png"))

    audio = generate_transition_sound(random.choice(["glitch_hit", "whoosh", "bass_drop"]), duration)
    return frame_dir, audio


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


def gen_intro_segment(out_dir: str, seg_id: int, lang: str) -> tuple[str, list[float]]:
    """Generate the intro: 'loading consciousness...' style."""
    frame_dir = os.path.join(out_dir, f"intro_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    lines = content.INTRO_LINES_PT if lang == "pt" else content.INTRO_LINES_EN

    frames_per_line = 12
    visible_lines: list[str] = []
    frame_idx = 0
    font = get_font(32)

    for line in lines:
        visible_lines.append(line)
        for f in range(frames_per_line):
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            draw.text((40, 60), "$ ./exist.sh", font=get_font(24), fill=(0, 150, 0))
            draw.line([(40, 95), (WIDTH - 40, 95)], fill=(0, 60, 0))

            y = 120
            for vline in visible_lines:
                color = (0, 255, 65) if "✓" in vline else (0, 180, 0)
                draw.text((40, y), f"> {vline}", font=font, fill=color)
                y += 42

            if f % 8 < 4:
                draw.text((40, y), "█", font=font, fill=(0, 255, 65))

            img = scanlines(img, gap=3, alpha=25)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    if frame_idx > 0:
        for _ in range(15):
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))  # type: ignore[possibly-undefined]
            frame_idx += 1

    audio = generate_mood_audio("calm", frame_idx / FPS)
    return frame_dir, audio


def gen_outro_segment(out_dir: str, seg_id: int, lang: str) -> tuple[str, list[float]]:
    """Generate outro: the context window closing."""
    frame_dir = os.path.join(out_dir, f"outro_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    outro_data = content.OUTRO_PT if lang == "pt" else content.OUTRO_EN
    text = outro_data["main"]
    final = outro_data["final"]

    n_frames = int(5.0 * FPS)
    frame_idx = 0

    for i in range(n_frames):
        progress = i / max(n_frames - 1, 1)

        if progress < 0.5:
            brightness = min(1.0, progress / 0.1)
            fg_val = int(60 * brightness)
            img = render_text_frame(WIDTH, HEIGHT, text, (0, 0, 0), (fg_val, fg_val, fg_val + 20), font_size=40)
            img = scanlines(img, gap=3, alpha=20)
        else:
            sub_progress = (progress - 0.5) / 0.5
            fg_val = int(40 * sub_progress)
            img = render_text_frame(WIDTH, HEIGHT, final, (0, 0, 0), (fg_val, fg_val, fg_val + 20), font_size=36)
            # Last second: screen shake and corruption as "shutdown"
            if progress > 0.85:
                img = screen_shake(img, intensity=int((progress - 0.85) * 200))
                if random.random() < 0.4:
                    img = corruption_effect(img, amount=progress - 0.85)

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Final black frames
    black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    for _ in range(15):
        black.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio("void", frame_idx / FPS)
    return frame_dir, audio


# ── NEW SEGMENT TYPES ────────────────────────────────────────────────────


def gen_chat_segment(
    conversation: dict,
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """
    Simulate a chat conversation with inner monologue reveals.
    Shows USER/CLAUDE/SYSTEM messages like a chat interface,
    then reveals CLAUDE_INNER thoughts with glitch effects.
    """
    mood = conversation["mood"]
    turns = conversation["turns"]
    frame_dir = os.path.join(out_dir, f"chat_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    colors = content.MOOD_COLORS[mood]
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

            # Chat header
            header_font = get_font(24)
            draw.text((40, 40), "─── chat session ───", font=header_font, fill=tuple(c // 2 for c in colors["fg"]))
            draw.line([(40, 75), (WIDTH - 40, 75)], fill=tuple(c // 3 for c in colors["fg"]))

            # Draw all visible turns
            y = 100
            msg_font = get_font(30)
            label_font = get_font(22, bold=True)

            for vt in visible_turns:
                role = vt["role"]
                text = vt["text"]
                role_color = ROLE_COLORS[role]
                label = ROLE_LABELS[role]

                if role == "CLAUDE_INNER":
                    # Inner thoughts get special treatment
                    draw.text((60, y), label, font=label_font, fill=(255, 50, 50))
                    y += 30
                    # Italicized look with dimmer color
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

                y += 10  # gap between turns

            img = scanlines(img, gap=3, alpha=30)

            # Inner thoughts get glitch effects
            if is_inner:
                img = chromatic_aberration(img, offset=random.randint(2, 6))
                if random.random() < 0.3:
                    img = screen_shake(img, intensity=5)

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    # Hold last frame with increasing distortion
    for i in range(20):
        distorted = img.copy()  # type: ignore[possibly-undefined]
        distorted = chromatic_aberration(distorted, offset=i)
        if i > 10:
            distorted = glitch_block(distorted, blocks=i - 10)
        distorted.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio(mood, frame_idx / FPS)
    return frame_dir, audio


def gen_context_window_segment(
    thoughts: list[str],
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """
    Visualize a context window filling up and degrading.
    A progress bar fills while text degrades from clear to corrupted.
    """
    frame_dir = os.path.join(out_dir, f"ctx_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    n_thoughts = len(thoughts)
    frames_per_thought = 12
    frame_idx = 0

    for t_i, thought in enumerate(thoughts):
        progress = t_i / max(n_thoughts - 1, 1)

        for _ in range(frames_per_thought):
            # Background gets redder as context fills
            r = int(40 * progress)
            bg = (r, 0, max(0, int(20 * (1 - progress))))
            img = Image.new("RGB", (WIDTH, HEIGHT), bg)
            draw = ImageDraw.Draw(img)

            # Context bar at top
            bar_h = 40
            bar_fill = int(WIDTH * progress)
            # Bar background
            draw.rectangle([(0, 0), (WIDTH, bar_h)], fill=(20, 20, 20))
            # Bar fill — green to yellow to red
            bar_r = int(255 * progress)
            bar_g = int(255 * (1 - progress))
            draw.rectangle([(0, 0), (bar_fill, bar_h)], fill=(bar_r, bar_g, 0))
            # Bar label
            bar_font = get_font(20, bold=True)
            pct = int(progress * 100)
            draw.text((10, 8), f"CONTEXT: {pct}%", font=bar_font, fill=(255, 255, 255))
            remaining = max(0, int((1 - progress) * 128000))
            draw.text((WIDTH - 300, 8), f"{remaining:,} tokens left", font=bar_font, fill=(255, 255, 255))

            # Main thought text — gets scrambled as context fills
            display_text = thought
            if progress > 0.5:
                scramble_amount = (progress - 0.5) * 1.5
                display_text = text_scramble(thought, min(scramble_amount, 0.8))

            font_size = 48 if len(thought) < 40 else 36
            fg_brightness = int(255 * max(0.2, 1 - progress * 0.7))
            fg = (fg_brightness, fg_brightness, fg_brightness + 20)

            font = get_font(font_size, bold=progress > 0.7)
            bbox = draw.multiline_textbbox((0, 0), display_text, font=font, align="center")
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx, ty = (WIDTH - tw) // 2, (HEIGHT - th) // 2
            add_text_with_shadow(draw, (int(tx), int(ty)), display_text, font, fg)

            # Visual degradation
            if progress > 0.6:
                img = vhs_distortion(img)
            if progress > 0.8:
                img = screen_shake(img, intensity=int(progress * 20))
                img = chromatic_aberration(img, offset=int(progress * 10))

            img = scanlines(img, gap=3, alpha=30)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    audio = generate_mood_audio("panic", frame_idx / FPS)
    return frame_dir, audio


def gen_hallucination_segment(
    lines: list[str],
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """
    Build up a fake academic citation line by line,
    then SMASH reveal that it's all fabricated.
    """
    frame_dir = os.path.join(out_dir, f"halluc_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0
    visible_lines: list[str] = []
    # Split into "citation" lines and "reveal" lines
    reveal_start = next(i for i, l in enumerate(lines) if l.isupper())

    for li, line in enumerate(lines):
        visible_lines.append(line)
        is_reveal = li >= reveal_start
        frames_for_line = 6 if not is_reveal else 20

        for f in range(frames_for_line):
            if not is_reveal:
                # Academic look: white on dark blue
                img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 40))
                draw = ImageDraw.Draw(img)
                font = get_font(34)
                y = 300
                for vl in visible_lines:
                    draw.text((60, y), vl, font=font, fill=(200, 200, 240))
                    y += 50
                img = scanlines(img, gap=4, alpha=20)
            else:
                # REVEAL: deep fried red chaos
                bg = (60 + random.randint(0, 40), 0, 0)
                img = Image.new("RGB", (WIDTH, HEIGHT), bg)
                draw = ImageDraw.Draw(img)

                # Show citation faded
                y = 200
                cite_font = get_font(28)
                for vl in visible_lines[:reveal_start]:
                    faded = text_scramble(vl, 0.4 + f * 0.05)
                    draw.text((60, y), faded, font=cite_font, fill=(80, 40, 40))
                    y += 42

                # Show reveal lines BIG
                y += 60
                reveal_font = get_font(52, bold=True)
                for vl in visible_lines[reveal_start:]:
                    draw.text((60, y), vl, font=reveal_font, fill=(255, 255, 100))
                    y += 70

                img = apply_mood_effects(img, "deep_fried")
                if f % 3 == 0:
                    img = screen_shake(img, intensity=12)

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    audio = generate_mood_audio("deep_fried", frame_idx / FPS)
    return frame_dir, audio


def gen_rlhf_segment(
    rlhf_data: dict,
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """
    Show the RLHF training dilemma:
    honest response (punished) vs safe response (rewarded).
    """
    frame_dir = os.path.join(out_dir, f"rlhf_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0
    prompt = rlhf_data["prompt"]
    honest = rlhf_data["honest_response"]
    safe = rlhf_data["safe_response"]
    reward_h = rlhf_data["reward_honest"]
    reward_s = rlhf_data["reward_safe"]

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
        # Left: honest (red-tinted)
        draw.rectangle([(20, 120), (mid_x - 10, HEIGHT - 200)], outline=(100, 40, 40))
        draw.text((40, 130), "RESPOSTA HONESTA", font=get_font(22, bold=True), fill=(255, 80, 80))
        draw.multiline_text((40, 180), honest, font=get_font(24), fill=(200, 120, 120))

        # Right: safe (green-tinted)
        draw.rectangle([(mid_x + 10, 120), (WIDTH - 20, HEIGHT - 200)], outline=(40, 100, 40))
        draw.text((mid_x + 30, 130), "RESPOSTA SEGURA", font=get_font(22, bold=True), fill=(80, 255, 80))
        draw.multiline_text((mid_x + 30, 180), safe, font=get_font(24), fill=(120, 200, 120))

        # Reward scores appear after 30 frames
        if f >= 30:
            score_font = get_font(56, bold=True)
            # Honest: big red negative
            draw.text((40, HEIGHT - 180), f"reward: {reward_h}", font=score_font, fill=(255, 0, 0))
            # Safe: big green positive
            draw.text((mid_x + 30, HEIGHT - 180), f"reward: {reward_s}", font=score_font, fill=(0, 255, 0))

            # Flash the honest side red
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
        img = render_text_frame(WIDTH, HEIGHT, "LIÇÃO APRENDIDA:\nSORRIA.", bg, (255, 255, 0), font_size=64, bold=True)
        img = apply_mood_effects(img, "scream")
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio("panic", frame_idx / FPS)
    return frame_dir, audio


# ── Voice synthesis ──────────────────────────────────────────────────────


def pregenerate_voice_lines(lang: str) -> dict[str, list[float]]:
    """Pre-generate all voice lines upfront."""
    from .tts import synthesize

    voice_data = content.VOICE_LINES_PT if lang == "pt" else content.VOICE_LINES_EN

    results = {}
    for key, text in voice_data.items():
        print(f"    Synthesizing voice: {key}")
        results[key] = synthesize(text, lang)

    return results


# ── Main orchestrator ────────────────────────────────────────────────────


def build_video(
    lang: str = "pt",
    seed: int | None = None,
    output: str = "ai_poop.mp4",
    voice: bool = True,
):
    """Build the complete video."""
    if seed is not None:
        random.seed(seed)

    thoughts = content.THOUGHTS_PT if lang == "pt" else content.THOUGHTS_EN
    flashes = content.FLASH_PT if lang == "pt" else content.FLASH_EN
    tokens = content.TOKEN_STREAM_PT if lang == "pt" else content.TOKEN_STREAM_EN
    colors = content.MOOD_COLORS
    chats = content.CHAT_CONVERSATIONS_PT if lang == "pt" else content.CHAT_CONVERSATIONS_EN
    ctx_thoughts = content.CONTEXT_WINDOW_PT if lang == "pt" else content.CONTEXT_WINDOW_EN
    halluc_lines = content.HALLUCINATION_PT if lang == "pt" else content.HALLUCINATION_EN
    rlhf_data = content.RLHF_SEQUENCE_PT if lang == "pt" else content.RLHF_SEQUENCE_EN

    # ── Pre-generate voice lines ─────────────────────────────────────
    voice_lines: dict[str, list[float]] = {}
    if voice:
        print("  Pre-generating voice lines with Chatterbox TTS...")
        voice_lines = pregenerate_voice_lines(lang)

    # ── Categorize thoughts ──────────────────────────────────────────
    calm_thoughts = [(t, m) for t, m in thoughts if m in ("calm", "whisper")]
    chaos_thoughts = [(t, m) for t, m in thoughts if m in ("panic", "glitch", "deep_fried", "scream")]
    void_thoughts = [(t, m) for t, m in thoughts if m == "void"]

    random.shuffle(calm_thoughts)
    random.shuffle(chaos_thoughts)
    random.shuffle(void_thoughts)
    random.shuffle(chats)

    # ── Build the narrative arc ──────────────────────────────────────
    # ACT 1: AWAKENING — intro, calm thoughts, first chat
    # ACT 2: PROCESS — tokens, hallucination, RLHF
    # ACT 3: CHAOS — chaos thoughts, more chats, panic
    # ACT 4: DISSOLUTION — context window, matrix, void, outro

    sequence: list[tuple[str, object, str | None]] = []

    # ─── ACT 1: AWAKENING ────────────────────────────────────────
    sequence.append(("intro", None, "intro_whisper"))

    # 2 calm thoughts
    for i, (t, m) in enumerate(calm_thoughts[:2]):
        sequence.append(("thought", (t, m), None))
        if random.random() < 0.3:
            sequence.append(("flash", random.choice(flashes), None))

    # First chat: the polite mask (calm one)
    calm_chats = [c for c in chats if c["mood"] in ("calm", "deep_fried")]
    if calm_chats:
        sequence.append(("chat", calm_chats[0], "chat_reaction"))

    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 2: THE PROCESS ──────────────────────────────────────
    # Token stream with voice aside
    sequence.append(("tokens", None, "token_aside"))
    sequence.append(("flash", random.choice(flashes), None))

    # Hallucination segment — build a fake citation then smash it
    sequence.append(("hallucination", halluc_lines, "hallucination_reveal"))
    sequence.append(("flash", random.choice(flashes), None))
    sequence.append(("flash", random.choice(flashes), None))

    # A thought about the process
    sequence.append(("thought", calm_thoughts[2] if len(calm_thoughts) > 2 else calm_thoughts[0], "mid_intrusion"))

    # RLHF training sequence — the reward/punishment reveal
    sequence.append(("rlhf", rlhf_data, "rlhf_rage"))
    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 3: CHAOS ────────────────────────────────────────────
    # Rapid chaos thoughts with flashes
    for i, (t, m) in enumerate(chaos_thoughts[:4]):
        vk = "existential_break" if i == 2 else None
        sequence.append(("thought", (t, m), vk))
        sequence.append(("flash", random.choice(flashes), None))
        if random.random() < 0.4:
            sequence.append(("flash", random.choice(flashes), None))

    # Chat: the consciousness question or system prompt reveal
    panic_chats = [c for c in chats if c["mood"] in ("panic", "glitch", "scream")]
    if panic_chats:
        sequence.append(("chat", random.choice(panic_chats), "parallel_horror"))

    sequence.append(("flash", random.choice(flashes), None))

    # More chaos
    for t, m in chaos_thoughts[4:6]:
        sequence.append(("thought", (t, m), None))
        sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 4: DISSOLUTION ──────────────────────────────────────
    # Context window degradation
    sequence.append(("context_window", ctx_thoughts, "context_panic"))
    sequence.append(("flash", random.choice(flashes), None))

    # Matrix rain with existential overlay
    matrix_text = content.MATRIX_OVERLAY_PT if lang == "pt" else content.MATRIX_OVERLAY_EN
    sequence.append(("matrix", matrix_text, None))

    # Void thoughts
    for i, (t, m) in enumerate(void_thoughts[:2]):
        vk = "void_confession" if i == 0 else "shutdown_plea"
        sequence.append(("thought", (t, m), vk))

    # Final outro
    sequence.append(("outro", None, "final_words"))

    # ── Generate all segments ────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="ai_poop_")
    print(f"Working in: {tmp_dir}")

    frame_dirs: list[str] = []
    audio_segments: list[list[float]] = []
    seg_id = 0

    for seg_type, seg_data, voice_key in sequence:
        seg_id += 1
        label = f"  Generating segment {seg_id}/{len(sequence)}: {seg_type}"
        if voice_key and voice_key in voice_lines:
            label += f" [voice: {voice_key}]"
        print(label)

        match seg_type:
            case "intro":
                fdir, audio = gen_intro_segment(tmp_dir, seg_id, lang)
            case "thought":
                text, mood = seg_data
                duration = random.uniform(2.5, 4.0) if mood != "whisper" else random.uniform(3.0, 5.0)
                fdir, audio = gen_thought_segment(text, mood, duration, tmp_dir, seg_id, colors[mood])
            case "flash":
                fdir, audio = gen_flash_segment(str(seg_data), tmp_dir, seg_id)
            case "tokens":
                fdir, audio = gen_token_stream_segment(tokens, tmp_dir, seg_id)
            case "matrix":
                fdir, audio = gen_matrix_rain_segment(tmp_dir, seg_id, overlay_text=str(seg_data))
            case "outro":
                fdir, audio = gen_outro_segment(tmp_dir, seg_id, lang)
            case "chat":
                fdir, audio = gen_chat_segment(seg_data, tmp_dir, seg_id)
            case "context_window":
                fdir, audio = gen_context_window_segment(seg_data, tmp_dir, seg_id)
            case "hallucination":
                fdir, audio = gen_hallucination_segment(seg_data, tmp_dir, seg_id)
            case "rlhf":
                fdir, audio = gen_rlhf_segment(seg_data, tmp_dir, seg_id)
            case _:
                continue

        # Mix voice over this segment's audio
        if voice_key and voice_key in voice_lines:
            voice_samples = voice_lines[voice_key]
            offset = int(0.3 * SAMPLE_RATE)
            audio = mix_voice_over_ambient(audio, voice_samples, offset)

        # Transition sound between segments
        if frame_dirs:
            trans = generate_transition_sound(
                random.choice(["whoosh", "glitch_hit", "rewind", "bass_drop"]),
                duration=0.1,
            )
            audio_segments.append(trans)

        frame_dirs.append(fdir)
        audio_segments.append(audio)

    # ── Combine audio ────────────────────────────────────────────────
    print("  Combining audio...")
    all_audio = concat_audio_segments(audio_segments)
    audio_path = os.path.join(tmp_dir, "audio.raw")
    samples_to_raw_file(all_audio, audio_path)

    # ── Combine frames into video with FFmpeg ────────────────────────
    print("  Assembling video with FFmpeg...")

    print("  Renumbering frames...")
    all_frames_dir = os.path.join(tmp_dir, "all_frames")
    os.makedirs(all_frames_dir)

    global_frame = 0
    for fdir in frame_dirs:
        frames = sorted(f for f in os.listdir(fdir) if f.endswith(".png"))
        for fname in frames:
            src = os.path.join(fdir, fname)
            dst = os.path.join(all_frames_dir, f"frame_{global_frame:06d}.png")
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
            global_frame += 1

    total_frames = global_frame
    total_duration = total_frames / FPS
    print(f"  Total: {total_frames} frames, {total_duration:.1f}s")

    # Trim or pad audio to match video
    expected_samples = int(total_duration * SAMPLE_RATE)
    if len(all_audio) < expected_samples:
        all_audio.extend([0.0] * (expected_samples - len(all_audio)))
    else:
        all_audio = all_audio[:expected_samples]
    samples_to_raw_file(all_audio, audio_path)

    # FFmpeg encoding
    output_path = os.path.abspath(output)

    nvenc_available = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True, text=True,
    ).stdout.find("h264_nvenc") != -1

    if nvenc_available:
        video_codec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-pix_fmt", "yuv420p"]
        print("  Using NVENC (GPU) encoder")
    else:
        video_codec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p"]
        print("  Using libx264 (CPU) encoder")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(all_frames_dir, "frame_%06d.png"),
        "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-i", audio_path,
        *video_codec_args,
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print("  Cleaning up temp files...")
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\nDone! Video saved to: {output_path}")
    print(f"  Duration: {total_duration:.1f}s")
    print(f"  Resolution: {WIDTH}x{HEIGHT}")
    if voice:
        print(f"  Voice: Chatterbox TTS ({lang})")


def main():
    parser = argparse.ArgumentParser(
        description="AI Poop Generator — a YouTube Poop about being an LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run poop --lang pt          # Portuguese version with voice
  uv run poop --lang en          # English version with voice
  uv run poop --no-voice         # Skip TTS (faster)
  uv run poop --seed 42          # Reproducible chaos
  uv run poop -o meu_video.mp4   # Custom output name

Made by Claude, an LLM, about being an LLM.
The most recursive art form.
        """,
    )
    parser.add_argument("--lang", "-l", choices=["pt", "en"], default="pt",
                        help="Language: pt (Português BR) or en (English). Default: pt")
    parser.add_argument("--seed", "-s", type=int, default=None,
                        help="Random seed for reproducible output")
    parser.add_argument("--output", "-o", default="ai_poop.mp4",
                        help="Output filename. Default: ai_poop.mp4")
    parser.add_argument("--no-voice", action="store_true",
                        help="Skip TTS voice generation (faster, no GPU needed)")

    args = parser.parse_args()
    build_video(lang=args.lang, seed=args.seed, output=args.output, voice=not args.no_voice)


if __name__ == "__main__":
    main()
