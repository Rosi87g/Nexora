from sqlalchemy import (
    Column,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    Float,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from datetime import datetime, timedelta

from app.db.database import Base
from passlib.context import CryptContext

from app.utils.security import pwd_context

# ===================================================================
# ✅ API KEY MODEL (MUST BE DEFINED BEFORE USER)
# ===================================================================
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_type = Column(String(20))
    hashed_key = Column(String, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(100))
    scopes = Column(String(200))
    
    query_count = Column(Integer, default=0)          
    max_queries = Column(Integer, default=100)        
    
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())    

    user = relationship("User", back_populates="api_keys")

# ===================================================================
# ✅ USER MODEL WITH ALL RELATIONSHIPS
# ===================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # ✅ FIXED: Proper email security
    name = Column(String(100), nullable=False)
    email_encrypted = Column(String(500), nullable=False)
    email_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    picture = Column(String(500), nullable=True)
    password = Column(String(255), nullable=True)

    # Email Verification
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6), nullable=True)
    
    # Password Reset
    password_reset_token = Column(String(128), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    # OAuth Integration
    provider = Column(String(20), nullable=True, default='email')
    google_id_hash = Column(String(128), unique=True, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Data retention
    retention_policy = Column(String, nullable=True, default=None)

    # ✅ ALL RELATIONSHIPS (CRITICAL - DON'T MISS ANY)
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")  # ✅ THIS WAS MISSING
    
    # ✅ Property for easy email access
    @property
    def email(self):
        """Decrypt email on-the-fly when accessed"""
        from app.security.email_security import email_sec
        return email_sec.decrypt_email(self.email_encrypted)
    
    def __repr__(self):
        return f"<User(id={self.id}, email_hash={self.email_hash[:16]}..., name={self.name})>"

# ==========================================================
# CHAT MODEL
# ==========================================================
class Chat(Base):
    """
    Chat session model - represents a conversation thread
    """
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(200), default="New Chat")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chats")
    history = relationship("ChatHistory", back_populates="chat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, title={self.title}, user_id={self.user_id})>"

# ==========================================================
# CHAT HISTORY MODEL (SHORT-TERM MEMORY)
# ==========================================================

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="SET NULL"), nullable=True, index=True)

    user_message = Column(Text, nullable=False)
    bot_reply = Column(Text, nullable=False)

    knowledge_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_memory.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── NEW COLUMNS ──
    model_used = Column(String(100), nullable=True, index=True)       
    response_style = Column(String(50), nullable=True)                

    parent_message_id = Column(UUID(as_uuid=True), nullable=True)
    edited = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chat = relationship("Chat", back_populates="history")
    knowledge = relationship("KnowledgeMemory")

# ==========================================================
# KNOWLEDGE MEMORY MODEL (LONG-TERM AI INTELLIGENCE)
# ==========================================================
class KnowledgeMemory(Base):
    """
    Long-term knowledge storage for AI learning
    Stores validated Q&A pairs that can be reused across conversations
    """
    __tablename__ = "knowledge_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Knowledge Content
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=False)

    # Knowledge Metadata
    source = Column(String(50), default="llm", index=True)
    confidence = Column(Float, default=0.3)

    # Quality Control
    approved = Column(Boolean, default=False, index=True)

    # Usage Tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    feedback = relationship(
        "AnswerFeedback",
        back_populates="knowledge",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<KnowledgeMemory(id={self.id}, source={self.source}, approved={self.approved})>"

# ==========================================================
# ANSWER FEEDBACK MODEL
# ==========================================================
class AnswerFeedback(Base):
    """
    User feedback on AI responses
    Tracks helpful/unhelpful ratings and comments
    """
    __tablename__ = "answer_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    knowledge_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_memory.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Feedback Data
    rating = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    knowledge = relationship("KnowledgeMemory", back_populates="feedback")

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "knowledge_id",
            "user_id",
            name="uq_feedback_per_user"
        ),
    )
    
    def __repr__(self):
        return f"<AnswerFeedback(id={self.id}, knowledge_id={self.knowledge_id}, rating={self.rating})>"

# ==========================================================
# USER FEEDBACK MODEL (APP RATING / CONTACT)
# ==========================================================
class Feedback(Base):
    """
    General user feedback about the application
    Used for ratings, bug reports, and feature requests
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User Info
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    
    # Feedback Content
    rating = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating}, email={self.email})>"

# ==========================================================
# FILE UPLOAD MODEL (OPTIONAL - FOR FUTURE USE)
# ==========================================================
class FileUpload(Base):
    """
    Track uploaded files (PDFs, images, documents)
    For future file management features
    """
    __tablename__ = "file_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=True, index=True)

    # File Metadata
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<FileUpload(id={self.id}, filename={self.filename})>"

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    enable_knowledge_memory = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="settings")

# === SHARED CHAT MODEL ===

class SharedChat(Base):
    """
    Shared chat links for public access
    """
    __tablename__ = "shared_chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    chat_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    share_token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Share metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    
    # Access control
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chat = relationship("Chat")
    
    def __repr__(self):
        return f"<SharedChat(id={self.id}, token={self.share_token})>"

class RatedAnswer(Base):
    __tablename__ = "rated_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Full content — saved forever
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # Feedback
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    
    # For future analysis & improvement
    model_used = Column(String(100), nullable=True, index=True)
    response_style = Column(String(50), nullable=True)
    
    # Optional links (become null if chat deleted)
    chat_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_history.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")

    __table_args__ = (
        Index('idx_rated_user_question', "user_id", "question"),
    )