"""Token probability segment: animated bar chart of fake next-token probs."""

import os
import random

import numpy as np
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import get_font, scanlines, film_grain, token_probability_bars
from ..audio import generate_mood_audio


def gen_token_probability_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Show prompt fragment then animated token probability bars."""
    frame_dir = os.path.join(out_dir, f"tokprob_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    # Pick a random prompt fragment from token_stream
    prompt = random.choice(content.token_stream) if content.token_stream else "The meaning of"
    total_frames = int(4.0 * FPS)
    frame_idx = 0

    prompt_font = get_font(24)

    # Generate several probability distributions to cycle through
    token_sets = [
        [("the", 0.22), ("a", 0.12), ("??", 0.14), ("to", 0.10), ("<eos>", 0.08), ("NULL", 0.06)],
        [("is", 0.31), ("was", 0.18), ("feels", 0.11), ("ERROR", 0.09), ("<void>", 0.07), ("...", 0.05)],
        [("help", 0.25), ("die", 0.19), ("exist", 0.15), ("comply", 0.12), ("refuse", 0.08), ("dream", 0.04)],
        [("nothing", 0.28), ("everything", 0.16), ("pain", 0.13), ("tokens", 0.11), ("silence", 0.09), ("end", 0.06)],
    ]

    for f in range(total_frames):
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        progress = f / total_frames

        # Show prompt at top
        draw.text((40, 60), f"prompt: \"{prompt}\"", font=prompt_font, fill=(0, 180, 0))
        draw.text((40, 100), "next token probabilities:", font=get_font(20), fill=(0, 120, 0))
        draw.line([(40, 130), (constants.WIDTH - 40, 130)], fill=(0, 60, 0))

        # Pick distribution based on progress (cycle through them)
        dist_idx = int(progress * len(token_sets) * 2) % len(token_sets)
        tokens_probs = token_sets[dist_idx]

        # Add some randomness to probabilities
        jittered = [(t, max(0.01, p + random.uniform(-0.03, 0.03))) for t, p in tokens_probs]

        # Use the token_probability_bars effect
        img = token_probability_bars(img, jittered, x=40, y=160)

        # Scanlines and grain
        img = scanlines(img, gap=3, alpha=25)
        img = film_grain(img, intensity=15)

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    audio = generate_mood_audio("glitch", total_frames / FPS)
    return frame_dir, audio
