# app/api/settings.py (or add to your existing routes file)

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ResponseStyleUpdate(BaseModel):
    response_style: Literal["concise", "balanced", "detailed"]


class ResponseStyleResponse(BaseModel):
    response_style: str
    message: str


@router.get("/response-style", response_model=ResponseStyleResponse)
async def get_response_style(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the user's current response style preference.
    """
    # If you have a user preferences table:
    # user_prefs = db.query(UserPreferences).filter(
    #     UserPreferences.user_id == current_user.id
    # ).first()
    
    # For now, return default if not stored in DB
    # You can store this in user table or separate preferences table
    response_style = getattr(current_user, 'response_style', 'balanced')
    
    return ResponseStyleResponse(
        response_style=response_style,
        message="Response style retrieved successfully"
    )


@router.patch("/response-style", response_model=ResponseStyleResponse)
async def update_response_style(
    style_update: ResponseStyleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the user's response style preference.
    """
    try:
        # Update user's response style preference
        # If you have a user preferences table:
        # user_prefs = db.query(UserPreferences).filter(
        #     UserPreferences.user_id == current_user.id
        # ).first()
        # 
        # if not user_prefs:
        #     user_prefs = UserPreferences(user_id=current_user.id)
        #     db.add(user_prefs)
        # 
        # user_prefs.response_style = style_update.response_style
        
        # For now, if storing directly in user table:
        current_user.response_style = style_update.response_style
        
        db.commit()
        db.refresh(current_user)
        
        return ResponseStyleResponse(
            response_style=style_update.response_style,
            message=f"Response style updated to {style_update.response_style}"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update response style: {str(e)}"
        )


# Add this to your chat endpoint (in chat routes file)

from app.core.response_style import get_response_style_config

@router.post("/chat")
async def send_chat_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    """
    # Get user's response style preference
    response_style = getattr(current_user, 'response_style', 'balanced')
    
    # If user included style in request, use that instead
    if hasattr(message, 'response_style') and message.response_style:
        response_style = message.response_style
    
    # Generate response with the user's preferred style
    response = await generate_chat_response(
        question=message.content,
        user_id=str(current_user.id),
        chat_id=message.chat_id,
        contexts=message.contexts or [],
        enable_web_search=message.enable_web_search,
        response_style=response_style  # Pass the style here
    )
    
    return {
        "response": response,
        "response_style": response_style,
        "timestamp": datetime.now().isoformat()
    }


# Database migration to add response_style column to User table
# Create a new migration file:

"""
# migration file: add_response_style_to_users.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add response_style column to users table
    op.add_column('users', 
        sa.Column('response_style', 
                  sa.String(20), 
                  nullable=False, 
                  server_default='balanced')
    )

def downgrade():
    op.drop_column('users', 'response_style')
"""


# Or if using a separate UserPreferences table:

"""
# migration file: create_user_preferences_table.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('response_style', sa.String(20), nullable=False, server_default='balanced'),
        sa.Column('theme', sa.String(20), nullable=False, server_default='dark'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'])

def downgrade():
    op.drop_table('user_preferences')
"""