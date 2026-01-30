from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.db.database import SessionLocal
from app.db.models import Feedback as FeedbackModel  # We'll create this model

router = APIRouter()

class FeedbackSubmit(BaseModel):
    name: str
    email: str
    rating: int
    message: str

@router.post("/feedback/submit")
async def submit_feedback(feedback: FeedbackSubmit):
    db = SessionLocal()
    try:
        db_feedback = FeedbackModel(
            name=feedback.name,
            email=feedback.email,
            rating=feedback.rating,
            message=feedback.message,
            created_at=datetime.utcnow()
        )
        db.add(db_feedback)
        db.commit()
        return {"message": "Feedback received!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    finally:
        db.close()