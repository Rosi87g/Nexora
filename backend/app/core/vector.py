# backend/app/core/vector.py
import os
import json
import threading
from typing import List, Dict, Any

import numpy as np
import faiss

from app.db.database import SessionLocal
from app.db.models import KnowledgeMemory

# =====================================================
# PATHS (EXISTING + NEW)
# =====================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

# EXISTING (DO NOT TOUCH)
TEXTS_PATH = os.path.join(DATA_DIR, "texts.json")
VECTORS_PATH = os.path.join(DATA_DIR, "vectors.npy")

# NEW (KNOWLEDGE VECTORS)
K_TEXTS_PATH = os.path.join(DATA_DIR, "knowledge_texts.json")
K_VECTORS_PATH = os.path.join(DATA_DIR, "knowledge_vectors.npy")

os.makedirs(DATA_DIR, exist_ok=True)


# =====================================================
# GLOBAL STATE - THREAD-SAFE SINGLETON MODEL
# =====================================================

_sentence_transformer = None
_model_lock = threading.Lock()  # Ensures thread-safe lazy loading


def get_sentence_transformer():
    """
    Thread-safe singleton for SentenceTransformer.
    Loads the model only once, even under concurrent requests.
    Prints only in non-production environments.
    """
    global _sentence_transformer

    if _sentence_transformer is not None:
        return _sentence_transformer

    with _model_lock:
        if _sentence_transformer is None:
            # Only show loading message in development
            if os.getenv("ENV", "development") != "production":
                print("🔥 Loading SentenceTransformer (first time only)...")

            from sentence_transformers import SentenceTransformer

            # Optional: specify device ("cuda" if available, else "cpu")
            # You can also set cache_folder to avoid re-downloading
            _sentence_transformer = SentenceTransformer(
                "all-MiniLM-L6-v2",
                device="cpu",  # Change to "cuda" if you have GPU support
                cache_folder=os.path.join(BASE_DIR, "model_cache")
            )

            if os.getenv("ENV", "development") != "production":
                print("✅ SentenceTransformer loaded successfully")

    return _sentence_transformer


# ---- Legacy file vectors ----
_index = None
_documents: List[str] = []
_vectors = None
_loaded = False

# ---- Knowledge vectors ----
_k_index = None
_k_vectors = None
_k_meta: List[Dict[str, Any]] = []
_k_loaded = False

_lock = threading.Lock()  # For file/vector modifications


# =====================================================
# UTILS
# =====================================================

def _normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return v / norm


# =====================================================
# EXISTING FILE VECTOR STORE (UNCHANGED LOGIC)
# =====================================================

def load_vector_store():
    global _index, _documents, _vectors, _loaded

    if _loaded:
        return

    if not os.path.exists(TEXTS_PATH) or not os.path.exists(VECTORS_PATH):
        _loaded = True
        return

    try:
        with open(TEXTS_PATH, "r", encoding="utf-8") as f:
            _documents = json.load(f)

        _vectors = _normalize(np.load(VECTORS_PATH).astype("float32"))

        dim = _vectors.shape[1]
        _index = faiss.IndexFlatIP(dim)
        _index.add(_vectors)
    finally:
        _loaded = True


def retrieve_context(query: str, k: int = 4) -> List[str]:
    if not _loaded:
        load_vector_store()

    if _index is None:
        return []

    model = get_sentence_transformer()
    q_vec = _normalize(model.encode([query], convert_to_numpy=True).astype("float32"))

    D, I = _index.search(q_vec, min(k, len(_documents)))
    return [_documents[i] for i in I[0] if i < len(_documents)]


def append_documents(new_texts: List[str]) -> int:
    global _vectors, _documents, _index, _loaded

    if not new_texts:
        return 0

    if not _loaded:
        load_vector_store()

    model = get_sentence_transformer()
    vecs = _normalize(model.encode(new_texts, convert_to_numpy=True).astype("float32"))

    with _lock:
        if _vectors is None:
            _vectors = vecs
            _documents = list(new_texts)
            dim = vecs.shape[1]
            _index = faiss.IndexFlatIP(dim)
            _index.add(vecs)
        else:
            _vectors = np.vstack([_vectors, vecs])
            _documents.extend(new_texts)
            _index.add(vecs)

        with open(TEXTS_PATH, "w", encoding="utf-8") as f:
            json.dump(_documents, f)
        np.save(VECTORS_PATH, _vectors)

    return len(new_texts)


# =====================================================
# NEW: KNOWLEDGE VECTOR STORE (LLM LEARNING)
# =====================================================

def load_knowledge_vectors():
    global _k_index, _k_vectors, _k_meta, _k_loaded

    if _k_loaded:
        return

    if not os.path.exists(K_TEXTS_PATH) or not os.path.exists(K_VECTORS_PATH):
        _k_loaded = True
        return

    with open(K_TEXTS_PATH, "r", encoding="utf-8") as f:
        _k_meta = json.load(f)

    _k_vectors = _normalize(np.load(K_VECTORS_PATH).astype("float32"))

    dim = _k_vectors.shape[1]
    _k_index = faiss.IndexFlatIP(dim)
    _k_index.add(_k_vectors)

    _k_loaded = True


def index_knowledge_entry(knowledge_id: str, text: str, confidence: float):
    global _k_vectors, _k_meta, _k_index, _k_loaded

    if not _k_loaded:
        load_knowledge_vectors()

    model = get_sentence_transformer()
    vec = _normalize(model.encode([text], convert_to_numpy=True).astype("float32"))

    meta = {
        "knowledge_id": knowledge_id,
        "confidence": confidence,
    }

    with _lock:
        if _k_vectors is None:
            _k_vectors = vec
            _k_meta = [meta]
            dim = vec.shape[1]
            _k_index = faiss.IndexFlatIP(dim)
            _k_index.add(vec)
        else:
            _k_vectors = np.vstack([_k_vectors, vec])
            _k_meta.append(meta)
            _k_index.add(vec)

        with open(K_TEXTS_PATH, "w", encoding="utf-8") as f:
            json.dump(_k_meta, f)
        np.save(K_VECTORS_PATH, _k_vectors)


def retrieve_knowledge(query: str, k: int = 5) -> List[Dict[str, Any]]:
    if not _k_loaded:
        load_knowledge_vectors()

    if _k_index is None:
        return []

    model = get_sentence_transformer()
    q_vec = _normalize(model.encode([query], convert_to_numpy=True).astype("float32"))

    D, I = _k_index.search(q_vec, min(k, len(_k_meta)))

    results = []
    for score, idx in zip(D[0], I[0]):
        if idx >= len(_k_meta):
            continue
        meta = _k_meta[idx]
        final_score = float(score) * float(meta["confidence"])
        results.append(
            {
                "knowledge_id": meta["knowledge_id"],
                "score": final_score,
            }
        )

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =====================================================
# EXPORTS
# =====================================================

__all__ = [
    "retrieve_context",
    "append_documents",
    "index_knowledge_entry",
    "retrieve_knowledge",
    "load_vector_store",
    "get_sentence_transformer",  # Optional: expose if needed elsewhere
]