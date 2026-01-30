from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.db.deps import get_current_user
from app.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


class RetentionPolicyUpdate(BaseModel):
    policy: str

    def model_post_init(self, __context) -> None:
        if self.policy not in ["30days", "90days", "forever"]:
            raise ValueError("policy must be one of: '30days', '90days', 'forever'")


@router.get("/retention-policy")
async def get_retention_policy(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the current user's retention policy.
    Returns "forever" if not set.
    """
    # Extract user_id from the dict returned by get_current_user
    user_id = current_user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"policy": user.retention_policy or "forever"}


@router.post("/retention-policy")
async def set_retention_policy(
    payload: RetentionPolicyUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's retention policy.
    Allowed values: "30days", "90days", "forever"
    """
    # Extract user_id from the dict returned by get_current_user
    user_id = current_user.get("id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update the retention policy
    user.retention_policy = payload.policy
    db.commit()
    db.refresh(user)
    
    logger.info(f"Updated retention policy for user {user_id} to {payload.policy}")
    
    return {
        "message": "Retention policy updated successfully",
        "policy": user.retention_policy
    }