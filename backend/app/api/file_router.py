# app/api/file_router.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Header
from typing import List 
from app.db.deps import get_current_user_optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import io
import os
import requests
import time
import uuid

# === NEW: RAG IMPORTS ===
from app.core.rag import create_collection

router = APIRouter()

# 🔥 FIXED: Use fast text model instead of moondream (10x faster, no timeout)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
LLM_MODEL = os.getenv("OCTO_LLM_MODEL_GENERATE", "gemma3:4b")  # 🔥 CHANGED: Was "moondream"

def extract_text_from_file(content: bytes, ext: str, filename: str) -> str:
    """Extract text from various file formats"""
    texts = []
    
    try:
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                txt = page.extract_text() or ""
                if txt.strip():
                    texts.append(txt)
        
        elif ext in ["docx", "doc"]:
            doc = Document(io.BytesIO(content))
            texts.extend([p.text for p in doc.paragraphs if p.text.strip()])
        
        elif ext in ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]:
            try:
                img = Image.open(io.BytesIO(content)).convert("RGB")
                ocr_text = pytesseract.image_to_string(img, lang="eng")
                if ocr_text.strip():
                    texts.append(ocr_text.strip())
                else:
                    texts.append("[Image with no readable text detected]")
            except Exception as e:
                texts.append(f"[Could not process image: {str(e)}]")
        
        elif ext in ["txt", "md", "py", "js", "json", "html", "css", "java", "cpp", "c", "go", "rs", "rb", "php"]:
            try:
                texts.append(content.decode("utf-8", errors="ignore"))
            except Exception:
                texts.append(content.decode("latin-1", errors="ignore"))
        
        else:
            raise HTTPException(400, f"Unsupported file type: .{ext}")
        
        if not texts:
            raise HTTPException(400, "No text could be extracted from the file")
        
        return "\n\n".join(texts)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error extracting text: {str(e)}")


def analyze_with_ollama(content: str, filename: str, query: str = None) -> str:    
    
    try:
        # 🔥 FIXED: Reduced from 7000 to 4000 (prevents 90s timeout)
        truncated_content = content[:4000]
        
        if query and query.strip():
            # Strong prompt for specific questions
            prompt = f"""You are an expert document analyst. Carefully read the content from "{filename}" and answer the user's question accurately.

INSTRUCTIONS:
- Answer ONLY based on the actual content below.
- If the information is not present, say "Not mentioned in the document."
- Quote relevant parts when possible.
- Extract exact names, dates, numbers, etc.

Document Content:
{truncated_content}

Question: {query}

Answer directly and clearly:"""
        else:
            # Strong general summary prompt
            prompt = f"""Provide a comprehensive summary of the document "{filename}".

Document Content:
{truncated_content}

Include:
- Main topic and purpose
- All key information (names, dates, numbers, sections)
- Important details, conclusions, and structure
- Any tables, lists, or standout points

Be accurate, thorough, and well-organized."""

        # Optimized for speed and quality on llama3.2:3b + CPU
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": -1,
                    "num_ctx": 8192,
                    "top_k": 30,
                    "top_p": 0.8,
                    "repeat_penalty": 1.05,
                }
            },
            timeout=90
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.status_code} {response.text}")
        
        result = response.json()
        return result.get("response", "No response from AI").strip()
        
    except requests.exceptions.Timeout:
        return f"Analysis took too long (timeout), but '{filename}' was uploaded and saved. You can ask follow-up questions!"
    
    except Exception as e:
        return f"File '{filename}' processed successfully, but AI analysis failed ({str(e)[:80]}).\n\nThe content is saved — ask me specific questions about it!"


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    query: str = Form(None),
    chat_id: str = Form(None),  # NEW: Optional chat_id parameter
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Upload file, save to disk + DB, extract text, analyze with Ollama,
    and embed content into vector database for future retrieval.
    Files persist after server restart.
    """
    
    # Get user ID from token (fallback to guest)
    user_id = "guest"
    user_name = "Guest"
    
    if authorization and authorization.startswith("Bearer "):
        try:
            from app.auth.auth_utils import decode_token
            payload = decode_token(authorization.replace("Bearer ", ""))
            if payload and payload.get("id"):
                user_id = str(payload["id"])
                user_name = payload.get("name", "User")
        except Exception:
            pass
    
    # Get file info
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    content = await file.read()
    
    if len(content) > max_size:
        raise HTTPException(400, "File too large. Maximum size is 10MB.")
    
    if len(content) == 0:
        raise HTTPException(400, "File is empty")
    
    # === STEP 1: Save file permanently on disk ===
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # === STEP 2: Extract text from file ===
    try:
        extracted_text = extract_text_from_file(content, ext, filename)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(400, "Could not extract any text from the file")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error processing file: {str(e)}")
    
    # === STEP 3: Process (analyze + save to DB + embed) ===
    try:
        # Analyze with Ollama
        ai_analysis = analyze_with_ollama(extracted_text, filename, query)
        
        # Save to database
        from app.db.models import FileUpload, Chat
        
        effective_chat_id = chat_id
        if user_id != "guest" and not effective_chat_id:
            new_chat = Chat(
                user_id=user_id,
                title=filename[:60] + ("..." if len(filename) > 60 else "")
            )
            db.add(new_chat)
            db.flush()
            effective_chat_id = new_chat.id
        
        file_record = FileUpload(
            user_id=user_id if user_id != "guest" else None,
            chat_id=effective_chat_id,
            filename=filename,
            file_path=file_path,
            file_type=ext,
            file_size=len(content)
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        # === IMPROVED EMBEDDING BLOCK - with overlap & better filtering ===
        try:
            from app.data_processing.embed_dataset import embed_new_content
            
            start_time = time.time()
            
            # Better chunking with small overlap
            chunk_size = 850
            overlap = 120
            chunks = []
            i = 0
            while i < len(extracted_text):
                end = min(i + chunk_size, len(extracted_text))
                chunks.append(extracted_text[i:end])
                i += chunk_size - overlap
            
            # Filter short/empty chunks
            chunks = [c.strip() for c in chunks if len(c.strip()) >= 70]
            chunks = chunks[:60]  # reasonable upper limit per file
            
            if chunks:
                enriched = [f"[Uploaded file: {filename}] {c}" for c in chunks]
                added_count = embed_new_content(enriched, source=filename)
                embed_time = time.time() - start_time
                print(f"Embedded {added_count} chunks from '{filename}' in {embed_time:.2f}s")
            else:
                print(f"No suitable chunks from '{filename}'")
                
        except Exception as e:
            print(f"Embedding failed (non-critical): {str(e)}")
        
        # Success response
        return {
            "status": "success",
            "file": filename,
            "file_id": str(file_record.id),
            "chat_id": str(effective_chat_id) if effective_chat_id else None,
            "message": ai_analysis,
            "answer": ai_analysis,
            "text_length": len(extracted_text),
            "chunks_embedded": len(chunks) if 'chunks' in locals() else 0,
            "has_query": bool(query and query.strip())
        }
    
    except Exception as e:
        # Fallback: file is saved, but processing failed
        preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
        
        return {
            "status": "partial_success",
            "file": filename,
            "message": f"""File '{filename}' uploaded and saved to disk!

**Content Preview:**
{preview}

**File Info:**
- Length: {len(extracted_text):,} characters
- Type: {ext.upper()}

Processing failed: {str(e)[:100]}

The file is permanently saved. You can ask questions about it later!""",
            "answer": f"File uploaded: {filename}\n\nPreview:\n{preview}",
            "text_length": len(extracted_text),
            "error": str(e)
        }


# === NEW RAG UPLOAD ENDPOINT ===
@router.post("/upload-rag")
async def upload_for_rag(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """Upload multiple files for RAG — returns collection_id for document Q&A"""
    if len(files) == 0:
        raise HTTPException(400, "No files provided")
    
    collections = []
    for file in files:  # Process one by one
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(400, f"Empty file: {file.filename}")
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(400, f"File too large: {file.filename} (max 10MB)")
        
        try:
            collection_id = create_collection([{
                "filename": file.filename,
                "content": content
            }])
            collections.append({
                "filename": file.filename,
                "collection_id": collection_id
            })
        except Exception as e:
            raise HTTPException(500, f"Failed to process {file.filename}: {str(e)}")
    
    return {
        "status": "success",
        "collections": collections,
        "message": "Documents processed one by one. Use each collection_id for queries.",
        "example": "Try: 'What is the main topic?' or 'Summarize page 2'"
    }


@router.post("/analyze-text")
async def analyze_text_endpoint(
    text: str = Form(...),
    question: str = Form(None),
    authorization: str = Header(None),
):
    """
    Analyze raw text with llama3.2:3b
    """
    
    if not text or not text.strip():
        raise HTTPException(400, "No text provided")
    
    try:
        truncated_text = text[:4000]  # 🔥 Same fix: reduced context
        
        if question and question.strip():
            prompt = f"""Answer the question based only on the provided text.

Text:
{truncated_text}

Question: {question}

Answer accurately and directly:"""
        else:
            prompt = f"""Summarize the text clearly:

{truncated_text}

Include key points and important details."""

        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": -1,
                    "num_ctx": 8192,
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception("Ollama API error")
        
        result = response.json()
        answer = result.get("response", "No response generated")
        
        return {
            "status": "success",
            "answer": answer
        }
    
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")