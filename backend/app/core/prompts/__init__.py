# This makes imports clean and organized
from .general import NEXORA_SYSTEM_PROMPT
from .math import MATH_SYSTEM_PROMPT
from .coding import CODING_SYSTEM_PROMPT
from .greeting import GREETING_PROMPT

__all__ = [
    "NEXORA_SYSTEM_PROMPT",
    "MATH_SYSTEM_PROMPT",
    "CODING_SYSTEM_PROMPT",
    "GREETING_PROMPT",
]