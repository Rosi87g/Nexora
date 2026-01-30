# app/utils.py (No changes needed)
import random
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db.models import User, ChatHistory
from app.auth.auth_utils import hash_password, verify_password, create_token
from app.utils.emailer import send_verification_code


def generate_code(n=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(n))


def signup(db: Session, name: str, email: str, password: str):
    email = email.lower().strip()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    code = generate_code()
    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        verification_code=code
    )

    db.add(user)
    db.commit()
    send_verification_code(email, code)

    return {"message": "Verification code sent"}


def verify_code(db: Session, email: str, code: str):
    email = email.lower().strip()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid code")

    user.is_verified = True
    user.verification_code = None
    db.commit()

    token = create_token({"email": user.email})
    return {"token": token}


def resend_code(db: Session, email: str):
    email = email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = generate_code()
    user.verification_code = code
    db.commit()

    send_verification_code(email, code)
    return {"message": "Verification code resent"}


def get_chat_history(db: Session, user_id: int):
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

def login(db: Session, email: str, password: str):
    email = email.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    token = create_token({"email": user.email})

    return {"token": token}