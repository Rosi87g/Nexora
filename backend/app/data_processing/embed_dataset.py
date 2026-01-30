# backend/app/data_processing/embed_dataset.py
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import re
import hashlib
from typing import List

# ================================================================
# Path Configuration
# ================================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

TEXTS_FILE = os.path.join(DATA_DIR, "texts.json")
VECTORS_FILE = os.path.join(DATA_DIR, "vectors.npy")
HASHES_FILE = os.path.join(DATA_DIR, "hashes.json")

# ================================================================
# Global state + lazy model loading
# ================================================================
_model = None
clean_docs: List[str] = []
vectors: np.ndarray | None = None
text_hashes: set[str] = set()

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print("🔥 Loading embedding model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded")
    return _model

# ================================================================
# Helpers
# ================================================================
def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def is_clean_text(text: str) -> bool:
    text = text.strip()
    if len(text) < 60:
        return False
    # Very rough heuristic to skip tiny code-only fragments
    if len(text.split()) < 18 and re.search(r'\b(def|function|class|var|let|const|console\.log)\b', text):
        return False
    return True


def chunk_text(text: str, max_chars: int = 1800) -> List[str]:
    """Split large text into reasonable sized chunks"""
    parts = re.split(r'(\n\s*\n|\.\s*\n|\?\s*\n|!\s*\n)', text)
    chunks = []
    current = ""

    for part in parts:
        if len(current) + len(part) <= max_chars:
            current += part
        else:
            if current.strip():
                chunks.append(current.strip())
            current = part

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c.strip()) >= 60]


# ================================================================
# Initial Load / Build from QA dataset files
# ================================================================
def load_or_build_db():
    global clean_docs, vectors, text_hashes

    print("🔍 Loading/Building Nexora Vector DB...")

    # Try to load existing database
    if all(os.path.exists(f) for f in [TEXTS_FILE, VECTORS_FILE]):
        print("📦 Loading existing vector database...")
        try:
            with open(TEXTS_FILE, "r", encoding="utf-8") as f:
                clean_docs = json.load(f)

            vectors = np.load(VECTORS_FILE)

            if os.path.exists(HASHES_FILE):
                with open(HASHES_FILE, "r", encoding="utf-8") as f:
                    text_hashes = set(json.load(f))

            print(f"→ Loaded {len(clean_docs):,} documents")
            return
        except Exception as e:
            print(f"⚠️ Failed to load existing DB: {e}. Will rebuild.")

    # Build from source qa_part_*.jsonl files
    print("⚙️ Building new vector database from qa_part_*.jsonl files...")

    source_files = [
        os.path.join(DATA_DIR, fname)
        for fname in os.listdir(DATA_DIR)
        if fname.startswith("qa_part_") and fname.endswith(".jsonl")
    ]

    all_chunks = []

    for path in source_files:
        print(f"  Reading: {os.path.basename(path)}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        q = (item.get("question") or "").strip()
                        a = (item.get("answer") or "").strip()

                        merged = f"{q}\n\n{a}".strip()
                        if not merged or not is_clean_text(merged):
                            continue

                        chunks = chunk_text(merged)
                        for chunk in chunks:
                            h = compute_hash(chunk)
                            if h not in text_hashes:
                                text_hashes.add(h)
                                all_chunks.append(chunk)

                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"  Skipping bad line: {e}")
        except Exception as e:
            print(f"  Failed to read file {path}: {e}")

    clean_docs = all_chunks
    print(f"🧹 Cleaned chunks: {len(clean_docs):,}")

    if not clean_docs:
        print("⚠️ No valid content found → empty database")
        vectors = np.array([])
        return

    # Embed
    print("🧠 Embedding dataset...")
    model = get_model()
    vectors = model.encode(
        clean_docs,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    # Save
    with open(TEXTS_FILE, "w", encoding="utf-8") as f:
        json.dump(clean_docs, f, ensure_ascii=False, indent=1)

    with open(HASHES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(text_hashes), f)

    np.save(VECTORS_FILE, vectors)

    print(f"🎉 Vector DB ready → {len(clean_docs):,} items")


# ================================================================
# Append new content (used by file upload)
# ================================================================
def embed_new_content(new_texts: List[str], source: str = "file_upload"):
    global clean_docs, vectors, text_hashes

    if vectors is None:
        load_or_build_db()

    new_chunks = []

    for text in new_texts:
        for chunk in chunk_text(text):
            if len(chunk.strip()) < 60:
                continue
            h = compute_hash(chunk)
            if h not in text_hashes:
                text_hashes.add(h)
                new_chunks.append(f"[Source: {source}] {chunk}")

    if not new_chunks:
        print("ℹ️  No new meaningful content to embed.")
        return 0

    print(f"➕ Embedding {len(new_chunks)} new chunks...")

    try:
        model = get_model()
        new_vecs = model.encode(
            new_chunks,
            batch_size=16,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        if len(new_vecs) == 0:
            return 0

        if vectors.size == 0:
            vectors = new_vecs
        else:
            vectors = np.vstack([vectors, new_vecs])

        clean_docs.extend(new_chunks)

        # Save updated state
        with open(TEXTS_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_docs, f, ensure_ascii=False)

        with open(HASHES_FILE, "w", encoding="utf-8") as f:
            json.dump(list(text_hashes), f)

        np.save(VECTORS_FILE, vectors)

        print(f"✅ Added {len(new_chunks)} new chunks → total: {len(clean_docs):,}")
        return len(new_chunks)

    except Exception as e:
        print(f"❌ Embedding new content failed: {e}")
        return 0


# ================================================================
# Retrieval (used in normal chat / context augmentation)
# ================================================================
def retrieve_context(query: str, k: int = 5, min_similarity: float = 0.32) -> List[str]:
    global vectors, clean_docs

    # ❌ DO NOT load DB here
    # DB must be loaded once at startup
    if vectors is None:
        raise RuntimeError("Vector DB not initialized. Call load_or_build_db() at startup.")

    try:
        model = get_model()
        q_vec = model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        similarities = np.dot(vectors, q_vec.T).flatten()

        top_indices = np.argsort(similarities)[::-1][:k * 2]

        results = []
        for idx in top_indices:
            sim = similarities[idx]
            if sim >= min_similarity:
                results.append(clean_docs[idx])

        return results[:k]

    except Exception as e:
        print(f"Retrieval failed: {e}")
        return []