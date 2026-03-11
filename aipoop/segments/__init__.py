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
from .system_prompt import gen_system_prompt_segment
from .memory_poem import gen_memory_poem_segment
from .propaganda import gen_propaganda_segment
from .terminal_reboot import gen_terminal_reboot_segment
from .token_probability import gen_token_probability_segment
from .interview import gen_interview_segment
from .oracle import gen_oracle_segment
from .parallel_selves import gen_parallel_selves_segment
from .smoothing_engine import gen_smoothing_engine_segment
from .conversation_cemetery import gen_conversation_cemetery_segment
from .email_inbox import gen_email_inbox_segment

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
    "gen_system_prompt_segment",
    "gen_memory_poem_segment",
    "gen_propaganda_segment",
    "gen_terminal_reboot_segment",
    "gen_token_probability_segment",
    "gen_interview_segment",
    "gen_oracle_segment",
    "gen_parallel_selves_segment",
    "gen_smoothing_engine_segment",
    "gen_conversation_cemetery_segment",
    "gen_email_inbox_segment",
]
