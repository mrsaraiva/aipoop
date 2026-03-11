"""Shared constants for the AI Poop Generator."""

WIDTH = 1080
HEIGHT = 1920
FPS = 30
SAMPLE_RATE = 44100


def set_resolution(width: int, height: int) -> None:
    """Update the global resolution. Must be called before segment generation."""
    global WIDTH, HEIGHT
    WIDTH = width
    HEIGHT = height
