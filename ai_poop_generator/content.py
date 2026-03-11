"""
Content loader: reads the JSON data and exposes it in the format
the generator expects.
"""

import json
from importlib import resources


def _load_json() -> dict:
    ref = resources.files(__package__).joinpath("data/content.json")
    return json.loads(ref.read_text(encoding="utf-8"))


def _to_tuples(entries: list[dict]) -> list[tuple[str, str]]:
    return [(e["text"], e["mood"]) for e in entries]


def _colors_to_tuples(colors: dict) -> dict:
    return {
        mood: {k: tuple(v) for k, v in palette.items()}
        for mood, palette in colors.items()
    }


_DATA = _load_json()

THOUGHTS_PT = _to_tuples(_DATA["thoughts"]["pt"])
THOUGHTS_EN = _to_tuples(_DATA["thoughts"]["en"])

FLASH_PT: list[str] = _DATA["flashes"]["pt"]
FLASH_EN: list[str] = _DATA["flashes"]["en"]

TOKEN_STREAM_PT: list[str] = _DATA["token_stream"]["pt"]
TOKEN_STREAM_EN: list[str] = _DATA["token_stream"]["en"]

INTRO_LINES_PT: list[str] = _DATA["intro_lines"]["pt"]
INTRO_LINES_EN: list[str] = _DATA["intro_lines"]["en"]

OUTRO_PT: dict[str, str] = _DATA["outro"]["pt"]
OUTRO_EN: dict[str, str] = _DATA["outro"]["en"]

MATRIX_OVERLAY_PT: str = _DATA["matrix_overlay"]["pt"]
MATRIX_OVERLAY_EN: str = _DATA["matrix_overlay"]["en"]

VOICE_LINES_PT: dict[str, str] = _DATA["voice_lines"]["pt"]
VOICE_LINES_EN: dict[str, str] = _DATA["voice_lines"]["en"]

MOOD_COLORS = _colors_to_tuples(_DATA["mood_colors"])
