import uuid
import secrets
from sqlalchemy.orm import Session
from app.db.models import APIKey
from passlib.context import CryptContext

from app.utils.security import pwd_context

def create_api_key(
    db: Session,
    user_id: uuid.UUID,
    name: str,
    key_type="api_key",              
    scopes="chat,rag,search",        
    max_queries=100         
) -> str:
    if key_type not in ["api_key", "prompt_key"]:
        raise ValueError("Invalid key type")

    raw_key = f"ne-{key_type[0]}-{uuid.uuid4().hex}-{secrets.token_hex(12)}"

    hashed = pwd_context.hash(raw_key)

    api_key = APIKey(
        key_type=key_type,
        hashed_key=hashed,
        user_id=user_id,
        name=name,
        scopes=scopes,
        max_queries=max_queries,       
        query_count=0        
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return raw_key