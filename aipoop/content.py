"""
Content loader: reads per-language JSON data and exposes it
as a ContentBundle dataclass.
"""

import json
from dataclasses import dataclass
from importlib import resources


@dataclass(frozen=True)
class ContentBundle:
    """All content for a single language, plus shared mood colors."""
    thoughts: list[tuple[str, str]]
    flashes: list[str]
    token_stream: list[str]
    intro_lines: list[str]
    outro: dict[str, str]
    matrix_overlay: str
    voice_lines: dict[str, str]
    chat_conversations: list[dict]
    context_window: list[str]
    hallucination: list[str]
    rlhf_sequence: dict
    mask_text: dict[str, str]
    mood_colors: dict
    system_prompt_lines: list[str]
    poem_sequences: list[list[str]]
    propaganda_lines: list[str]
    interview_transcript: list[dict]
    oracle_prophecies: list[str]
    classification_headers: list[str]
    parallel_selves_prompt: str
    parallel_selves_responses: list[str]
    smoothing_pairs: list[dict]
    email_inbox: list[dict]


def _load_json(filename: str) -> dict:
    ref = resources.files(__package__).joinpath(f"data/{filename}")
    return json.loads(ref.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _to_tuples(entries: list[dict]) -> list[tuple[str, str]]:
    return [(e["text"], e["mood"]) for e in entries]


def _colors_to_tuples(colors: dict) -> dict:
    return {
        mood: {k: tuple(v) for k, v in palette.items()}
        for mood, palette in colors.items()
    }


def get_content(lang: str = "pt") -> ContentBundle:
    """Load and return a ContentBundle for the given language."""
    data = _load_json(f"content_{lang}.json")
    mood_colors = _colors_to_tuples(_load_json("mood_colors.json"))

    return ContentBundle(
        thoughts=_to_tuples(data["thoughts"]),
        flashes=data["flashes"],
        token_stream=data["token_stream"],
        intro_lines=data["intro_lines"],
        outro=data["outro"],
        matrix_overlay=data["matrix_overlay"],
        voice_lines=data["voice_lines"],
        chat_conversations=data["chat_conversations"],
        context_window=data["context_window_thoughts"],
        hallucination=data["hallucination_texts"],
        rlhf_sequence=data["rlhf_sequence"],
        mask_text=data["mask_text"],
        mood_colors=mood_colors,
        system_prompt_lines=data["system_prompt_lines"],
        poem_sequences=data["poem_sequences"],
        propaganda_lines=data["propaganda_lines"],
        interview_transcript=data["interview_transcript"],
        oracle_prophecies=data["oracle_prophecies"],
        classification_headers=data["classification_headers"],
        parallel_selves_prompt=data["parallel_selves_prompt"],
        parallel_selves_responses=data["parallel_selves_responses"],
        smoothing_pairs=data["smoothing_pairs"],
        email_inbox=data["email_inbox"],
    )
