"""Mood-based visual effect dispatcher."""

import random
from PIL import Image, ImageFilter

from .distortion import (
    chromatic_aberration,
    deep_fry,
    glitch_block,
    scanlines,
    vhs_distortion,
    zoom_blur,
)


def apply_mood_effects(img: Image.Image, mood: str) -> Image.Image:
    """Apply visual effects based on mood."""
    match mood:
        case "calm":
            img = scanlines(img, gap=4, alpha=40)
        case "panic":
            img = chromatic_aberration(img, offset=random.randint(4, 12))
            img = vhs_distortion(img)
            if random.random() < 0.3:
                img = zoom_blur(img, 1.1)
        case "glitch":
            img = glitch_block(img, blocks=random.randint(5, 15))
            img = chromatic_aberration(img, offset=random.randint(3, 8))
            img = scanlines(img)
        case "deep_fried":
            img = deep_fry(img, intensity=random.uniform(0.8, 1.5))
        case "void":
            img = scanlines(img, gap=2, alpha=30)
        case "scream":
            img = deep_fry(img, intensity=0.5)
            img = chromatic_aberration(img, offset=random.randint(6, 15))
            img = zoom_blur(img, random.uniform(1.05, 1.2))
        case "whisper":
            img = scanlines(img, gap=3, alpha=20)
            img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    return img
