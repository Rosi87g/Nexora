from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.utils.api_key_utils import create_api_key
from app.db.database import get_db
from app.auth.dependencies import get_current_user
from app.db.models import APIKey

from sqlalchemy import and_

router = APIRouter(prefix="/api_keys", tags=["api-keys"])


@router.post("/create")
def create_key(
    name: str,                                      # ← ONLY this is required (query param)
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key.
    
    Only ?name=... is required.
    All other settings are fixed:
    - key_type: "api_key"
    - scopes: "chat,rag,search"
    - max_queries: 100 (lifetime limit)
    """
    if not name or not name.strip():
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'name' is required and cannot be empty"
        )

    cleaned_name = name.strip()

    raw_key = create_api_key(
        db=db,
        user_id=current_user.id,
        name=cleaned_name,
        key_type="api_key",           # ← fixed
        scopes="chat,rag,search",     # ← fixed
        max_queries=100               # ← fixed - 100 requests lifetime
    )

    return {
        "api_key": raw_key,
        "type": "api_key",
        "scopes": "chat,rag,search",
        "max_queries": 100,
        "warning": "Copy this key now — you will never see it again!"
    }


@router.get("/my-keys")
def list_my_keys(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all API keys created by the current user
    """
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    
    return [{
        "id": k.id,
        "name": k.name,
        "type": k.key_type,
        "scopes": k.scopes,
        "query_count": k.query_count,
        "max_queries": k.max_queries,
        "last_used": k.last_used.isoformat() if k.last_used else None,
        "created_at": k.created_at.isoformat() if k.created_at else None
    } for k in keys]

@router.delete("/{key_id}")
def revoke_key(
    key_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke (delete) a specific API key by its ID.
    - Only the owner can revoke their own key
    - After revocation, the key will no longer work
    """
    api_key = db.query(APIKey).filter(
        and_(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found or you do not own this key"
        )

    try:
        db.delete(api_key)
        db.commit()
        return {
            "success": True,
            "message": "API key revoked successfully",
            "revoked_key_id": key_id,
            "name": api_key.name
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to revoke API key"
        )