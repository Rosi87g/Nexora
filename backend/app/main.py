# backend/app/main.py
import random
import secrets
import os
from pathlib import Path
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import Depends

import base64
from cryptography.fernet import Fernet

from passlib.context import CryptContext

from app.api.profile_router import router as profile_router

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.feedback import router as feedback_router
from app.api.chat_router import router as chat_router
from app.api.file_router import router as file_router

from app.db.database import Base, engine, get_db
from app.db.schemas import (
    UserRequest, 
    VerifyCodeRequest, 
    EmailRequest, 
    ResetPasswordRequest,
    UpdateProfileRequest,
    UserResponse
)
from app.db.deps import get_current_user
from app.db.models import User

from app.auth.auth_utils import hash_password, verify_password, create_token
from app.utils.emailer import send_verification_code, send_password_reset_email
from app.security.email_security import email_sec
from app.data_processing.learning_system import learning_system  # This forces it to initialize

from app.tools.code_execution import (
    execute_python_with_output,
    execute_javascript_code,
    safe_execute_code
)

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

from app.api.user_router import router as user_router
from app.api.api_keys import router as api_keys_router

from app.utils.security import pwd_context

from app.dependencies.api_key_dep import get_current_api_key
from app.db.models import APIKey

from dotenv import load_dotenv
load_dotenv()

limiter = Limiter(key_func=get_remote_address)

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY missing in .env")
fernet = Fernet(ENCRYPTION_KEY.encode())

app = FastAPI(title="AI 1.0 - Nexora", version="1.0.0")

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded (100 queries per hour per key). Try again later."}
    )
)

app.add_middleware(SlowAPIMiddleware)

# =============================================================
# 🔹 ENV CONFIG
# =============================================================
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
DEMO_SECRET = os.getenv("DEMO_SECRET", "octopus-demo")

BASE_DIR = Path(__file__).resolve().parent.parent   # backend/
UPLOADS_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "dist"

if UPLOADS_DIR.exists():
    app.mount(
        "/uploads",
        StaticFiles(directory=str(UPLOADS_DIR)),
        name="uploads"
    )

app.include_router(feedback_router)
app.include_router(user_router)
app.include_router(profile_router, prefix="/api", tags=["profile"])
app.include_router(chat_router, tags=["chat"])
app.include_router(api_keys_router, prefix="/api_keys", tags=["api-keys"])
app.include_router(file_router, prefix="/files", tags=["files"])

# =============================================================
# CORS
# =============================================================
origins = [
    FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://one-0-yjls.onrender.com",
    "https://*.trycloudflare.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https://.*",
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.on_event("startup")
async def startup_init():
    from app.core.vector import get_sentence_transformer
    from app.data_processing.embed_dataset import load_or_build_db

    print("🔥 Warming up embedding model...")
    get_sentence_transformer()

    print("📦 Loading Nexora vector database...")
    load_or_build_db()

    print("✅ Model & Vector DB initialized (once)")

# =============================================================
# 🔐 DEMO PROTECTION (SINGLE, CORRECT)
# =============================================================
#@app.middleware("http")
#async def demo_protection(request: Request, call_next):

    # Preflight
#    if request.method == "OPTIONS":
#        return Response(
#            status_code=200,
#            headers={
#                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
#                "Access-Control-Allow-Credentials": "true",
#                "Access-Control-Allow-Headers": "*",
#                "Access-Control-Allow-Methods": "*",
#            },
#        )

    # ✅ UPDATED: Add code execution routes to public paths (OPTIONAL - remove if you want to protect it)
    # Public paths
#    if request.url.path.startswith((
#        "/auth/",
#        "/assets/",
#        "/docs",
#        "/openapi.json",
#        "/redoc",
#        "/vite.svg",
#        "/favicon.ico",
#        "/api/execute",  # ✅ NEW: Allow code execution endpoints (remove this line if you want them protected)
#    )):
#        return await call_next(request)

#    demo_key = request.headers.get("x-demo-key") or request.cookies.get("demo_key")

#    if demo_key != DEMO_SECRET:
#        return JSONResponse(
#            status_code=401,
#            content={"detail": "Unauthorized - Demo key required"},
#        )

#    return await call_next(request)

# =============================================================
# 🔧 FORCE CORS HEADERS (SAFE)
# =============================================================
@app.middleware("http")
async def force_cors_headers(request: Request, call_next):
    response = await call_next(request)

    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"

    return response


# =============================================================
# DATABASE
# =============================================================
Base.metadata.create_all(bind=engine)


# =============================================================
# ✅ NEW: CODE EXECUTION API
# =============================================================

from pydantic import BaseModel

class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"  # "python" or "javascript"
    timeout: int = 10

@app.post("/api/execute-code")
async def execute_code_endpoint(request: CodeExecutionRequest):
    """
    Execute Python or JavaScript code safely
    
    Example:
    ```json
    {
        "code": "print('Hello, World!')",
        "language": "python",
        "timeout": 10
    }
    ```
    """
    try:
        if request.language == "python":
            result = execute_python_with_output(request.code, timeout=request.timeout)
        elif request.language == "javascript":
            result = execute_javascript_code(request.code, timeout=request.timeout)
        else:
            raise HTTPException(400, "Unsupported language. Use 'python' or 'javascript'")
        
        return {
            "success": result['success'],
            "output": result['output'],
            "error": result.get('error'),
            "plot": result.get('plot'),  # Base64 image if matplotlib was used
            "language": request.language
        }
    except Exception as e:
        raise HTTPException(500, f"Execution failed: {str(e)}")


@app.post("/api/execute-safe")
async def execute_safe_endpoint(request: CodeExecutionRequest):
    """
    Execute Python code in restricted sandbox (legacy safe mode)
    Limited builtins, no external libraries
    """
    if request.language != "python":
        raise HTTPException(400, "Safe execution only supports Python")
    
    try:
        output = safe_execute_code(request.code)
        return {
            "success": True,
            "output": output,
            "language": "python"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "language": "python"
        }


# =============================================================
# AUTH ROUTES
# =============================================================

@app.post("/auth/signup")
def signup(user: UserRequest, db: Session = Depends(get_db)):
    """
    User signup with email encryption and verification
    """
    # Clean and normalize email
    email = user.email.lower().strip()
    
    # ✅ FIXED: Use SHA-256 hash for lookup (deterministic)
    email_hash = email_sec.hash_email(email)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email_hash == email_hash).first()
    if existing_user:
        raise HTTPException(400, "Email already exists")
    
    # Generate 6-digit verification code
    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    
    # ✅ FIXED: Prepare email for storage (encrypt + hash)
    email_data = email_sec.prepare_email_for_storage(email)
    
    # ✅ FIXED: Create user with proper fields
    new_user = User(
        name=user.name if user.name else "User",  # Provide default if None
        email_encrypted=email_data['email_encrypted'],
        email_hash=email_data['email_hash'],
        password=hash_password(user.password),
        verification_code=code,
        provider="email",
        is_verified=False,
    )
    
    # Save to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # ✅ Send verification email (plain text email)
    try:
        send_verification_code(email, code)
    except Exception as e:
        # Roll back if email fails
        db.delete(new_user)
        db.commit()
        raise HTTPException(500, f"Failed to send verification email: {str(e)}")
    
    return {
        "message": "Verification code sent to your email",
        "email": email  # Safe to return - user just entered it
    }


# ============================================================
# ✅ FIXED: RESEND CODE
# ============================================================
@app.post("/auth/resend")
def resend_code(data: EmailRequest, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    
    # ✅ FIXED: Hash email for lookup
    email_hash = email_sec.hash_email(email)
    user = db.query(User).filter(User.email_hash == email_hash).first()
    
    if not user:
        raise HTTPException(404, "User not found")
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Generate new code
    code = "".join(str(random.randint(0, 9)) for _ in range(6))
    user.verification_code = code
    db.commit()
    
    # ✅ FIXED: Decrypt email for sending
    decrypted_email = email_sec.decrypt_email(user.email_encrypted)
    send_verification_code(decrypted_email, code)
    
    return {"message": "Verification code resent"}


# ============================================================
# ✅ FIXED: VERIFY CODE
# ============================================================
@app.post("/auth/verify-code")
def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    email = data.email.lower().strip()
    
    # ✅ FIXED: Hash email for lookup
    email_hash = email_sec.hash_email(email)
    user = db.query(User).filter(User.email_hash == email_hash).first()
    
    if not user or user.verification_code != data.code:
        raise HTTPException(400, "Invalid verification code")
    
    # Mark as verified
    user.is_verified = True
    user.verification_code = None
    db.commit()
    
    # ✅ FIXED: Decrypt email for token
    decrypted_email = email_sec.decrypt_email(user.email_encrypted)
    token = create_token({
        "id": str(user.id),
        "email": decrypted_email,
        "name": user.name,
        "provider": user.provider,
    })
    
    return {
        "message": "Email verified successfully",
        "token": token
    }


# ============================================================
# ✅ FIXED: LOGIN
# ============================================================
@app.post("/auth/login")
def login(user: UserRequest, db: Session = Depends(get_db)):
    email = user.email.lower().strip()
    
    # ✅ FIXED: Hash email for lookup
    email_hash = email_sec.hash_email(email)
    db_user = db.query(User).filter(User.email_hash == email_hash).first()
    
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(401, "Invalid credentials")
    
    if not db_user.is_verified:
        raise HTTPException(403, "Email not verified")
    
    # ✅ FIXED: Decrypt email for token
    decrypted_email = email_sec.decrypt_email(db_user.email_encrypted)
    token = create_token({
        "id": str(db_user.id),
        "email": decrypted_email,
        "name": db_user.name,
        "provider": db_user.provider,
    })
    
    return {"token": token}


# ============================================================
# ✅ FIXED: FORGOT PASSWORD
# ============================================================
@app.post("/auth/forgot-password")
def forgot_password(data: EmailRequest, db: Session = Depends(get_db)):
    from datetime import timezone
    
    email = data.email.lower().strip()
    email_hash = email_sec.hash_email(email)
    user = db.query(User).filter(User.email_hash == email_hash).first()
    
    if not user:
        return {"message": "If the email exists, a reset link was sent"}
    
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(minutes=10)  # ✅ 10 minutes
    db.commit()
    
    decrypted_email = email_sec.decrypt_email(user.email_encrypted)
    
    try:
        send_password_reset_email(decrypted_email, token, FRONTEND_URL)
    except Exception as e:
        print(f"Failed to send password reset email: {str(e)}")
    
    return {"message": "If the email exists, a reset link was sent", "expires_in_minutes": 10}


@app.post("/auth/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    from datetime import timezone
    
    user = db.query(User).filter(User.password_reset_token == data.token).first()
    current_time = datetime.now(timezone.utc)
    
    if not user or not user.password_reset_expires:
        raise HTTPException(400, "Invalid or expired token")
    
    if user.password_reset_expires < current_time:
        expired_minutes = int((current_time - user.password_reset_expires).total_seconds() / 60)
        raise HTTPException(400, f"Token has expired {expired_minutes} minutes ago. Please request a new password reset.")
    
    if data.password != data.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    
    if len(data.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters long")
    
    user.password = hash_password(data.password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    
    return {"message": "Password reset successful.", "success": True}


# ============================================================
# ✅ FIXED: GET CURRENT USER
# ============================================================
@app.get("/auth/me")
def me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = UUID(current_user["id"]) if isinstance(current_user["id"], str) else current_user["id"]
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # ✅ FIXED: Use the property (auto-decrypts)
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,  # ✅ Uses @property to auto-decrypt
        "picture": user.picture,
        "provider": user.provider or "email",
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

@app.patch("/auth/update-profile")
def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    Currently supports: name, picture
    """
    user_id = current_user["id"]
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated = False
    
    if data.name is not None:
        if not data.name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        user.name = data.name.strip()
        updated = True
    
    # Add picture update support
    if data.picture is not None:
        user.picture = data.picture
        updated = True
    
    if updated:
        db.commit()
        db.refresh(user)
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": fernet.decrypt(base64.b64decode(user._email_encrypted)).decode('utf-8'),
            "picture": user.picture,  # Include picture in response
            "provider": user.provider,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    }


# =============================================================
# STATIC FILES
# =============================================================
if STATIC_DIR.exists() and (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")


@app.get("/vite.svg")
async def vite_svg():
    path = STATIC_DIR / "vite.svg"
    if path.exists():
        return FileResponse(path)
    return Response(status_code=204)


@app.get("/favicon.ico")
async def favicon():
    path = STATIC_DIR / "favicon.ico"
    if path.exists():
        return FileResponse(path)
    return Response(status_code=204)


# =============================================================
# SPA FALLBACK
# =============================================================
@app.get("/")
async def root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"status": "Nexora backend running"}


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    # Serve index.html UNLESS it's an API-like path
    if not full_path.startswith(("api/", "api_keys/", "debug/", "auth/", "chat/", "files/", "shared/", "uploads/")):
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
    
    # Important: if it's an API path but no route matched → real 404
    raise HTTPException(status_code=404, detail="Not Found")