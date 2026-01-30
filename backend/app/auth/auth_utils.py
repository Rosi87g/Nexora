# app/auth_utils.py
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests

from app.utils.security import pwd_context

SECRET_KEY = os.getenv("SECRET_KEY", "octopus-secret")
ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = int(os.getenv("ACCESS_EXPIRE_MINUTES", "1440"))

BACKEND_PUBLIC_URL = os.getenv(
    "BACKEND_PUBLIC_URL", "http://127.0.0.1:8000"
)

# ---------------- PASSWORD AUTH ----------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain[:72], hashed)

def create_token(data: dict, expires_minutes: int = ACCESS_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ---------------- GOOGLE OAUTH ----------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

async def verify_google_token(token: str):
    """Verify Google ID token and return user info"""
    try:
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
        
        # Extract user info
        return {
            "google_id": idinfo["sub"],  # Google's unique user ID
            "email": idinfo["email"],
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture", ""),
            "email_verified": idinfo.get("email_verified", False)
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google token verification failed: {str(e)}")

async def exchange_google_code_for_token(code: str) -> str:
    """Exchange Google authorization code for ID token"""
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = f"{BACKEND_PUBLIC_URL}/auth/google/callback"
        
        if not all([google_client_id, google_client_secret]):
            raise HTTPException(status_code=500, detail="Google OAuth credentials missing")
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": google_client_id,
                    "client_secret": google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code": code,
                },
                timeout=30.0
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to exchange Google code: {token_response.text}"
                )
            
            token_data = token_response.json()
            return token_data["id_token"]
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error with Google: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to exchange Google code: {str(e)}")