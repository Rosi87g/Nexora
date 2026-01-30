# backend/app/data_processing/learning_system.py
"""
UPDATED LEARNING SYSTEM FOR Nexora 1.1

CHANGES (NON-DESTRUCTIVE):
1. Postgres KnowledgeMemory is the primary brain
2. SQLite kept for legacy + fast lookup
3. Feedback-aware confidence refinement
4. Safe learning even if chats are deleted
5. Refined answers stored permanently
"""

import sqlite3
import hashlib
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import os
import traceback
import time

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import SessionLocal
from app.db.models import KnowledgeMemory, AnswerFeedback

DEFAULT_DB_PATH = "data/knowledge.db"

class AI1LearningSystem:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.global_knowledge: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.knowledge_lock = threading.Lock()

        # Existing thresholds (UNCHANGED)
        self.quality_threshold = 0.4

        self._source_quality = {
            "llm": 0.95,
            "vector": 0.75,
            "combined": 0.85,
            "aggregate": 0.82,
            "file": 0.70,
            None: 0.65,
        }

        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self.init_database()

    # =====================================================
    # SQLITE (LEGACY / CACHE) — UNCHANGED
    # =====================================================
    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
            cursor = conn.cursor()

            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    question_hash TEXT UNIQUE,
                    quality_score REAL DEFAULT 1.0,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT
                )
                """
            )

            conn.commit()
            conn.close()
        except Exception as e:
            print("[LEARNING ERROR] SQLite init failed:", e)

    # =====================================================
    # UTILITIES
    # =====================================================
    def _compute_hash(self, text: str) -> str:
        return hashlib.md5((text or "").strip().lower().encode()).hexdigest()

    # ────────────────────────────────────────────────
    # FIX 4: Replace _refine_confidence_from_feedback()
    # ────────────────────────────────────────────────
    def _refine_confidence_from_feedback(self, db: Session, knowledge_id) -> float:
        """
        Aggregate feedback with proper normalization.
        Returns adjustment value (not absolute confidence).
        """
        feedback = (
            db.query(AnswerFeedback)
            .filter(AnswerFeedback.knowledge_id == knowledge_id)
            .all()
        )

        if not feedback:
            return 0.0

        positive = sum(1 for fb in feedback if fb.rating == 1)
        negative = sum(1 for fb in feedback if fb.rating == -1)
        total = len(feedback)
        
        if total == 0:
            return 0.0
        
        net_sentiment = (positive - negative) / total
        adjustment = net_sentiment * 0.3
        
        return adjustment

    # =====================================================
    # MAIN LEARNING ENTRYPOINT
    # =====================================================
    def learn_from_interaction(
        self,
        user_id: Optional[str],
        question: str,
        answer: str,
        source: Optional[str] = None,
    ) -> Optional[str]:
        """
        Learn permanently from interaction.
        Returns knowledge_id if stored/updated.
        """

        if not question or not answer:
            return None

        if len(answer.split()) < 5:
            return None

        base_quality = self._source_quality.get(source, 0.7)
        if base_quality < self.quality_threshold:
            return None

        q_clean = question.strip()
        a_clean = answer.strip()
        q_hash = self._compute_hash(q_clean)

        db: Session = SessionLocal()
        try:
            # =================================================
            # POSTGRES — PRIMARY STORAGE
            # =================================================
            knowledge = (
                db.query(KnowledgeMemory)
                .filter(KnowledgeMemory.question == q_clean)
                .first()
            )

            if knowledge:
                knowledge.answer = a_clean
                knowledge.usage_count += 1
                knowledge.last_used_at = datetime.utcnow()
            else:
                knowledge = KnowledgeMemory(
                    question=q_clean,
                    answer=a_clean,
                    source=source or "llm",
                    confidence=base_quality,
                )
                db.add(knowledge)
                db.flush()  # Get ID before commit

            # ────────────────────────────────────────────────
            # FIX 4B: Improved confidence calculation
            # ────────────────────────────────────────────────
            feedback_adjustment = self._refine_confidence_from_feedback(
                db, knowledge.id
            )
            
            # Clamp final confidence to [0.0, 1.0]
            raw_confidence = base_quality + feedback_adjustment
            knowledge.confidence = max(0.0, min(1.0, raw_confidence))

            db.commit()

            # =================================================
            # SQLITE — LEGACY MIRROR (UNCHANGED BEHAVIOR)
            # =================================================
            with self.knowledge_lock:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT id, usage_count FROM knowledge WHERE question_hash = ?",
                    (q_hash,),
                )
                row = cursor.fetchone()

                if row:
                    cursor.execute(
                        """
                        UPDATE knowledge
                        SET usage_count = usage_count + 1,
                            last_used = CURRENT_TIMESTAMP,
                            answer = ?
                        WHERE question_hash = ?
                        """,
                        (a_clean, q_hash),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO knowledge
                        (question, answer, question_hash, quality_score, source)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (q_clean, a_clean, q_hash, base_quality, source),
                    )

                conn.commit()
                conn.close()

            return str(knowledge.id)

        except SQLAlchemyError as e:
            db.rollback()
            print("[LEARNING ERROR] Postgres failure:", e)
            traceback.print_exc()
            return None
        except Exception as e:
            db.rollback()
            print("[LEARNING ERROR] Unexpected error:", e)
            traceback.print_exc()
            return None
        finally:
            db.close()

    # =====================================================
    # SEARCH (POSTGRES FIRST)
    # =====================================================
    def search_internal_knowledge(
        self, question: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        db: Session = SessionLocal()
        try:
            results = (
                db.query(KnowledgeMemory)
                .order_by(
                    (KnowledgeMemory.confidence * 0.7)
                    + (KnowledgeMemory.usage_count * 0.3)
                )
                .limit(top_k)
                .all()
            )

            return [
                {
                    "knowledge_id": str(k.id),
                    "question": k.question,
                    "answer": k.answer,
                    "confidence": k.confidence,
                    "usage_count": k.usage_count,
                }
                for k in results
            ]
        except Exception as e:
            print("[LEARNING ERROR] Search failed:", e)
            return []
        finally:
            db.close()

    # =====================================================
    # STATS
    # =====================================================
    def get_stats(self) -> Dict[str, Any]:
        db: Session = SessionLocal()
        try:
            total = db.query(KnowledgeMemory).count()
            return {"total_entries": total}
        except Exception:
            return {"total_entries": 0}
        finally:
            db.close()


# =====================================================
# GLOBAL INSTANCE
# =====================================================
learning_system = AI1LearningSystem()

try:
    stats = learning_system.get_stats()
    print(f"[LEARNING] KnowledgeMemory entries: {stats['total_entries']}")
except Exception:
    pass