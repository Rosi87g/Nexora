# backend/app/core/orchestrator.py

import asyncio
from functools import lru_cache
from typing import Optional

# UPDATED IMPORT: Now directly uses your new multi-turn generate_chat_response
from app.core.llm_inference import generate_chat_response
from app.data_processing.learning_system import learning_system
from app.core.vector import index_knowledge_entry

from dotenv import load_dotenv
load_dotenv()

class Orchestrator:

    def __init__(self):
        self.learning = learning_system

    @lru_cache(maxsize=100)
    def _cache_key(self, query: str) -> str:
        """Generate cache key for repeated queries"""
        return query.lower().strip()[:200]

    async def handle(self, user_id: Optional[str], query: str) -> str:
        """
        Handle user query with knowledge storage.

        Flow:
        1. Generate LLM response using new multi-turn engine
        2. Return response immediately
        3. Store & index knowledge in background

        Args:
            user_id: User identifier (optional for guests)
            query: User's question/message

        Returns:
            AI response string
        """
        q = (query or "").strip()
        if not q:
            return "Please ask a valid question."

        if len(q) > 4096:
            return "Question too long (max 4096 characters)."

        try:
            print(f"[ORCHESTRATOR] Handling query | user={user_id or 'guest'} | len={len(q)}")

            answer = await generate_chat_response(
                question=q,
                user_id=user_id or "guest",
                contexts=None,  # Multi-turn handled internally
                enable_web_search=True
            )

            if not answer or "Generation failed" in answer or "Ollama is not running" in answer:
                return "I'm sorry, I couldn't generate a response. Please try again."

            # 2️⃣ Background learning + vector indexing (fire-and-forget)
            asyncio.create_task(
                self._store_and_index_knowledge(
                    user_id=user_id,
                    question=q,
                    answer=answer,
                )
            )

            # 3️⃣ Return immediately (UX first)
            return answer

        except Exception as e:
            print(f"[ORCHESTRATOR ERROR] {e}")
            return "An error occurred. Please try again."

    async def _store_and_index_knowledge(
        self,
        user_id: Optional[str],
        question: str,
        answer: str,
    ):
        """
        Background task:
        - Store Q&A in KnowledgeMemory
        - Index refined answer into vector DB
        """
        try:
            loop = asyncio.get_event_loop()

            # 1️⃣ Store knowledge (Postgres + SQLite mirror)
            knowledge_id: Optional[str] = await loop.run_in_executor(
                None,
                self.learning.learn_from_interaction,
                user_id or "guest",
                question,
                answer,
                "llm",
            )

            if not knowledge_id:
                print("[LEARNING] Skipped low-quality response")
                return

            # 2️⃣ Index refined answer into knowledge vector DB
            # Confidence is pulled later dynamically during retrieval
            index_knowledge_entry(
                knowledge_id=knowledge_id,
                text=f"{question}\n{answer}",
                confidence=0.5,  # base; refined later via feedback
            )

            print(f"[LEARNING] Stored & indexed knowledge {knowledge_id[:8]}")

        except Exception as e:
            print(f"[LEARNING ERROR] Knowledge indexing failed: {e}")
            # Never raise — learning must not affect chat UX


# =====================================================
# SINGLETON INSTANCE
# =====================================================
_orchestrator = Orchestrator()


async def handle_query(user_id: Optional[str], query: str) -> str:
    """
    Public interface for query handling.

    Usage:
        from app.core.orchestrator import handle_query
        response = await handle_query("user123", "What is Python?")

    Guarantees:
    - Fast response
    - Safe learning
    - Persistent intelligence
    - Full multi-turn memory support
    """
    return await _orchestrator.handle(user_id, query)