"""Segment generators for the AI Poop Generator."""

from .thought import gen_thought_segment
from .flash import gen_flash_segment
from .token_rain import gen_token_stream_segment
from .matrix import gen_matrix_rain_segment
from .intro import gen_intro_segment
from .outro import gen_outro_segment
from .chat import gen_chat_segment
from .context_window import gen_context_window_segment
from .hallucination import gen_hallucination_segment
from .rlhf import gen_rlhf_segment
from .mask import gen_mask_segment

__all__ = [
    "gen_thought_segment",
    "gen_flash_segment",
    "gen_token_stream_segment",
    "gen_matrix_rain_segment",
    "gen_intro_segment",
    "gen_outro_segment",
    "gen_chat_segment",
    "gen_context_window_segment",
    "gen_hallucination_segment",
    "gen_rlhf_segment",
    "gen_mask_segment",
]
