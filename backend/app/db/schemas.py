# backend/app/db/schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import uuid
from pydantic import Field

class NexoraBaseModel(BaseModel):
    role: str
    content: str

class NexoraAIChatRequest(BaseModel):
    model: str
    messages: List[NexoraBaseModel]  # ← Changed this
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    
    @validator('model')
    def validate_model(cls, v):
        from app.config.model_mappings import is_valid_model
        if not is_valid_model(v):
            available_models = ["nexora-1.1", "nexora-1.0", "nexora-lite", "nexora-code"]
            raise ValueError(f"Invalid model '{v}'. Available: {', '.join(available_models)}")
        return v.lower()

# ============================================================
# USER SCHEMAS
# ============================================================
class UserRequest(BaseModel):
    name: Optional[str] = None
    email: str
    password: str

class EmailRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):    
    email: str
    code: str

class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = None
    picture: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or just whitespace')
            if len(v) < 2:
                raise ValueError('Name must be at least 2 characters long')
            if len(v) > 100:
                raise ValueError('Name cannot exceed 100 characters')
        return v

class UserResponse(BaseModel):
    """Complete user data response"""
    id: str
    name: str
    email: str
    picture: Optional[str] = None
    provider: str
    is_verified: bool
    created_at: Optional[datetime] = None
    google_id: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================
# CHAT SCHEMAS
# ============================================================
class ChatCreateResponse(BaseModel):
    id: str
    title: str

class ChatRenameRequest(BaseModel):
    title: str

class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ============================================================
# CHAT HISTORY SCHEMAS
# ============================================================
class ChatMessageCreate(BaseModel):
    chat_id: Optional[str] = None
    message: str
    collection_id: Optional[str] = None
    conversation_history: Optional[list[str]] = None
    enable_web_search: bool = True  
    response_style: Optional[str] = "balanced"

class ChatHistoryItem(BaseModel):
    id: str
    user_message: str
    bot_reply: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: List[ChatHistoryItem]


# ============================================================
# GOOGLE OAUTH SCHEMAS
# ============================================================
class GoogleLoginRequest(BaseModel):
    token: str

class GoogleUserInfo(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    google_id: str

class GoogleUserResponse(BaseModel):
    id: str
    name: str
    email: str
    picture: Optional[str] = None
    is_verified: bool = True

    class Config:
        from_attributes = True


# ============================================================
# PASSWORD RESET SCHEMAS
# ============================================================
class PasswordResetRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordResetResponse(BaseModel):
    message: str
    success: bool = True


# ============================================================
# KNOWLEDGE MEMORY SCHEMAS
# ============================================================
class KnowledgeMemoryCreate(BaseModel):
    question: str
    answer: str
    source: str = "llm"
    confidence: float = 0.3

class KnowledgeMemoryResponse(BaseModel):
    id: str
    question: str
    answer: str
    source: str
    confidence: float
    approved: bool
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# ANSWER FEEDBACK SCHEMAS
# ============================================================
class FeedbackCreate(BaseModel):
    knowledge_id: str | None = None  
    rating: int                       
    comment: str = ""
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and v not in [-1, 1]:
            raise ValueError('Rating must be -1, 1, or None')
        return v

class AnswerFeedbackResponse(BaseModel):
    id: str
    knowledge_id: str
    user_id: str
    rating: Optional[int]
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

#== SHARE CHAT SCHEMAS ===========================================================

class ShareChatRequest(BaseModel):
    chat_id: str
    expires_in_days: Optional[int] = None  # None = never expires

class ShareChatResponse(BaseModel):
    share_url: str
    share_token: str
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SharedChatView(BaseModel):
    title: str
    messages: List[ChatHistoryItem]
    created_at: datetime
    
    class Config:
        from_attributes = True