# backend/app/core/rag.py
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
import uuid
import shutil
import gc
import time
from typing import List, Dict

RAG_BASE_DIR = "rag_collections"
os.makedirs(RAG_BASE_DIR, exist_ok=True)

# Use consistent embedding model across all systems
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)


def create_collection(files_content: List[Dict]) -> str:
    """
    Create a new RAG collection from uploaded files
    Returns: collection_id (UUID)
    """
    collection_id = str(uuid.uuid4())
    collection_dir = os.path.join(RAG_BASE_DIR, collection_id)
    os.makedirs(collection_dir, exist_ok=True)

    docs = []
    
    for file in files_content:
        temp_path = os.path.join(collection_dir, file["filename"])

        try:
            # Write file temporarily
            with open(temp_path, "wb") as f:
                f.write(file["content"])

            ext = os.path.splitext(file["filename"])[1].lower()

            # Load based on file type
            if ext == ".pdf":
                loader = PyPDFLoader(temp_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(temp_path)
            elif ext in [".txt", ".md", ".py", ".js", ".json", ".html", ".css"]:
                # Try multiple encodings
                for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        loader = TextLoader(temp_path, encoding=enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print(f"⚠️  Cannot decode {file['filename']}")
                    continue
            else:
                print(f"⚠️  Unsupported type: {ext} ({file['filename']})")
                continue

            loaded_docs = loader.load()
            
            # Filter out empty documents
            valid_docs = [d for d in loaded_docs if d.page_content.strip()]

            if valid_docs:
                docs.extend(valid_docs)
                print(f"  ✅ Loaded {len(valid_docs)} pages from {file['filename']}")
            else:
                print(f"  ⚠️  No content extracted from {file['filename']}")

        except Exception as e:
            print(f"  ❌ Error processing {file['filename']}: {str(e)[:120]}")
            continue

    if not docs:
        shutil.rmtree(collection_dir, ignore_errors=True)
        raise ValueError("No readable text extracted from uploaded files")

    # Better chunking strategy
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,           # Smaller chunks = more precise matching
        chunk_overlap=150,        # Good overlap to preserve context
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
    )

    chunks = splitter.split_documents(docs)
    
    # Less strict filtering
    chunks = [c for c in chunks if len(c.page_content.strip()) >= 50]

    if not chunks:
        shutil.rmtree(collection_dir, ignore_errors=True)
        raise ValueError("No meaningful chunks after splitting")

    print(f"→ Created {len(chunks)} chunks")

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=collection_dir,
            collection_name="docs"
        )
        
        vectorstore.persist()
        
        print(f"✅ Vector store created → {collection_id}")
        return collection_id
        
    except Exception as e:
        shutil.rmtree(collection_dir, ignore_errors=True)
        raise ValueError(f"Vector store creation failed: {str(e)}")


# ────────────────────────────────────────────────
# FIX 3: Improved query_collection() with better relevance filtering
# ────────────────────────────────────────────────
def query_collection(collection_id: str, question: str, k: int = 5) -> List[Dict]:
    """
    Query a RAG collection with improved similarity matching
    """
    collection_dir = os.path.join(RAG_BASE_DIR, collection_id)

    if not os.path.exists(collection_dir):
        print(f"❌ Collection {collection_id} not found")
        return []

    vectorstore = None
    try:
        vectorstore = Chroma(
            persist_directory=collection_dir,
            embedding_function=embeddings,
            collection_name="docs"
        )

        results = vectorstore.similarity_search_with_score(question, k=k*2)

        if not results:
            print(f"⚠️  No results found for: {question}")
            return []

        contexts = []
        
        for doc, score in results:
            # L2 distance threshold: 0.0-0.5 (excellent), 0.5-1.5 (good), 1.5-3.5 (acceptable)
            if score > 3.5:
                print(f"  Skipping low-quality result (L2 distance: {score:.3f})")
                continue

            source = os.path.basename(doc.metadata.get("source", "unknown"))
            page = doc.metadata.get("page", None)

            # Convert L2 distance to similarity score (0-1)
            similarity = max(0, 1 - (score / 4.0))

            contexts.append({
                "content": doc.page_content.strip(),
                "source": source,
                "page": str(page) if page is not None else "N/A",
                "score": round(float(score), 3),
                "similarity": round(similarity, 3),
                "relevance": "high" if score < 1.0 else "medium" if score < 2.5 else "low"
            })

        contexts.sort(key=lambda x: x["score"])
        final_results = contexts[:k]
        
        print(f"✅ Found {len(final_results)} relevant results (from {len(results)} candidates)")
        return final_results

    except Exception as e:
        print(f"❌ Query failed for collection {collection_id}: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        if vectorstore is not None:
            del vectorstore
        gc.collect()


def delete_collection(collection_id: str) -> bool:
    """Delete a RAG collection"""
    collection_dir = os.path.join(RAG_BASE_DIR, collection_id)
    
    if not os.path.exists(collection_dir):
        return True

    gc.collect()
    time.sleep(0.2)

    for attempt in range(5):
        try:
            shutil.rmtree(collection_dir)
            print(f"✅ Deleted collection: {collection_id}")
            return True
        except PermissionError:
            gc.collect()
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Delete failed (attempt {attempt + 1}): {e}")
            return False

    print(f"⚠️  Could not delete {collection_id} (files locked)")
    return True


def list_collections() -> List[str]:
    """List all available RAG collections"""
    if not os.path.exists(RAG_BASE_DIR):
        return []
    
    return [
        d for d in os.listdir(RAG_BASE_DIR) 
        if os.path.isdir(os.path.join(RAG_BASE_DIR, d))
    ]


def get_collection_info(collection_id: str) -> Dict:
    """Get metadata about a collection"""
    collection_dir = os.path.join(RAG_BASE_DIR, collection_id)
    
    if not os.path.exists(collection_dir):
        return {"exists": False}
    
    try:
        vectorstore = Chroma(
            persist_directory=collection_dir,
            embedding_function=embeddings,
            collection_name="docs"
        )
        
        collection = vectorstore._collection
        count = collection.count()
        
        return {
            "exists": True,
            "collection_id": collection_id,
            "document_count": count,
            "location": collection_dir
        }
        
    except Exception as e:
        return {
            "exists": True,
            "error": str(e)
        }