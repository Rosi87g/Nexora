# app/core/chat_logic.py

import asyncio
import time
from typing import Optional, List

from app.core.orchestrator import Orchestrator
from app.tools.code_execution import safe_execute_code

# =========================================================
# CACHE CONFIG
# =========================================================

CACHE_TTL = 300  # seconds
_CACHE: dict[str, tuple[float, str]] = {}

# =========================================================
# CACHE HELPERS
# =========================================================

def _cache_get(query: str) -> Optional[str]:
    item = _CACHE.get(query)
    if not item:
        return None

    ts, value = item
    if time.time() - ts > CACHE_TTL:
        del _CACHE[query]
        return None

    return value


def _cache_set(query: str, value: str):
    _CACHE[query] = (time.time(), value)


# =========================================================
# SINGLE PUBLIC CHAT ENTRY (✅ ONLY ONE)
# =========================================================

async def generate_chat_response_orchestrated(
    message: str,
    user_id: str = "guest",
    chat_id: str | None = None,
    contexts=None,
    *args,
    **kwargs,
) -> str:
    """
    Unified public chat entry.
    Accepts ALL historical call signatures safely.
    """

    query = (message or "").strip()
    if not query:
        return "Please ask a valid question."

    # -----------------------------------------------------
    # CODE EXECUTION (UNCHANGED)
    # -----------------------------------------------------
    q_low = query.lower()
    if q_low.startswith("code:") or "run code" in q_low or "execute code" in q_low:
        try:
            code = query.split("code:", 1)[-1]
            output = await asyncio.to_thread(safe_execute_code, code)
            return f"📟 Code Output:\n\n{output}"
        except Exception as e:
            return f"❌ Code execution error: {e}"

    # -----------------------------------------------------
    # CACHE (UNCHANGED)
    # -----------------------------------------------------
    cached = _cache_get(query)
    if cached:
        return cached

    # -----------------------------------------------------
    # ORCHESTRATOR (SINGLE SOURCE OF TRUTH)
    # -----------------------------------------------------
    orchestrator = Orchestrator()
    try:
        answer = await orchestrator.handle(user_id or "guest", query)
    except Exception as e:
        return f"⚠️ AI internal error: {e}"

    _cache_set(query, answer)
    return answer

# =========================================================
# LEGACY SYNC WRAPPER (OPTIONAL, SAFE)
# =========================================================

def generate_chat_response_original(message: str) -> str:
    try:
        loop = asyncio.get_running_loop()
        return asyncio.run_coroutine_threadsafe(
            generate_chat_response_orchestrated(message),
            loop,
        ).result()
    except RuntimeError:
        return asyncio.run(generate_chat_response_orchestrated(message))


generate_chat_response = generate_chat_response_orchestrated
