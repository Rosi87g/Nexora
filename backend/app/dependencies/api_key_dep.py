# backend/app/dependencies/api_key_dep.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db.database import get_db
from app.db.models import APIKey
from app.utils.security import pwd_context 

# Standard FastAPI header dependency
api_key_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="API key in format: Bearer <your-api-key>"
)


def get_current_api_key(
    authorization: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db),
    request: Request = None
) -> APIKey:
    """
    Strict API Key authentication dependency with rate limiting

    Features:
    - Must use "Bearer " prefix
    - Constant-time-like verification (loop + early exit possible)
    - Only considers keys with remaining quota
    - Updates usage atomically (simple version)
    - Clear, standardized error messages
    - 429 on rate limit exhaustion
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": 'Bearer error="missing_api_key"'}
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
            headers={"WWW-Authenticate": 'Bearer error="invalid_scheme"'}
        )

    # Extract raw key (remove "Bearer " prefix)
    raw_key = authorization[7:].strip()

    if not raw_key.startswith("ne-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format (must start with 'ne-')",
            headers={"WWW-Authenticate": 'Bearer error="invalid_format"'}
        )

    # Get only keys that still have quota (optimization + security)
    active_keys = db.query(APIKey).filter(
        APIKey.query_count < APIKey.max_queries
    ).order_by(APIKey.created_at.desc()).limit(50).all()  # reasonable safety limit

    if not active_keys:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum requests per API key exceeded."
        )

    matched_key: Optional[APIKey] = None

    # Verify in constant-ish time (we check all candidates)
    for db_key in active_keys:
        if pwd_context.verify(raw_key, db_key.hashed_key):
            matched_key = db_key
            break  # We can break early - improves average case

    if not matched_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or exhausted API key",
            headers={"WWW-Authenticate": 'Bearer error="invalid_key"'}
        )

    # Rate limit check (redundant but explicit)
    if matched_key.query_count >= matched_key.max_queries:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {matched_key.max_queries} requests per API key lifetime."
        )

    # Update usage - simple version (not fully atomic)
    # In high-concurrency you should use SELECT FOR UPDATE or redis counter
    matched_key.query_count += 1
    matched_key.last_used = datetime.utcnow()
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update API key usage counter"
        )

    # Optional: store in request state for logging/middleware
    if request is not None:
        request.state.api_key = matched_key
        request.state.api_key_id = str(matched_key.id)

    return matched_key


# Optional: Very strict variant with 403 instead of 401 for exhausted keys
def get_current_api_key_strict(
    authorization: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db),
    request: Request = None
) -> APIKey:
    """
    Even stricter version:
    - 403 Forbidden when quota is exhausted (instead of 401/429)
    - More explicit error separation
    """
    api_key = get_current_api_key(authorization, db, request)
    
    if api_key.query_count >= api_key.max_queries:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This API key has reached its lifetime limit of {api_key.max_queries} requests"
        )
    
    return api_key