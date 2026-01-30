# backend/app/db/deps.py
from typing import Optional
from uuid import UUID
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.auth.auth_utils import decode_token


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Returns the current logged-in user as a dict with id, email, name.
    Raises 401 if token is missing/invalid/expired.
    """
    if not authorization:
        raise HTTPException(
            status_code=401, 
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization.split(" ", 1)[1]
    
    try:
        payload = decode_token(token)
    except HTTPException:
        # Token is invalid or expired
        raise HTTPException(
            status_code=401, 
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # ✅ FIXED: Query by user ID (from token), not email
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Convert string UUID to UUID object if needed
    if isinstance(user_id, str):
        user_id = UUID(user_id)
    
    # Query by ID (primary key - fast and reliable)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Email not verified"
        )

    # ✅ Return user data with decrypted email
    return {
        "id": str(user.id),
        "email": user.email,  # Uses @property to auto-decrypt
        "name": user.name,
        "provider": user.provider
    }


def get_current_user_optional(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
):
    """
    Returns user dict if authenticated, otherwise returns None (guest user).
    Does not raise exceptions for missing/invalid tokens.
    """
    if not authorization:
        return None  # Guest
        
    if not authorization.lower().startswith("bearer "):
        return None
        
    token = authorization.split(" ", 1)[1]
    
    try:
        payload = decode_token(token)
    except Exception:
        return None
    
    # ✅ FIXED: Query by user ID, not email
    user_id = payload.get("id")
    if not user_id:
        return None
    
    # Convert string UUID to UUID object if needed
    if isinstance(user_id, str):
        try:
            user_id = UUID(user_id)
        except ValueError:
            return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
        
    if not user.is_verified:
        return None
    
    # ✅ Return user data with decrypted email    
    return {
        "id": str(user.id),
        "email": user.email,  # Uses @property to auto-decrypt
        "name": user.name,
        "provider": user.provider
    }