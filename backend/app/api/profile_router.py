from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from PIL import Image
import io

from app.db.database import get_db
from app.db.deps import get_current_user
from app.db.models import User

router = APIRouter(prefix="/profile", tags=["profile"])

# Create uploads directory
UPLOAD_DIR = Path("uploads/profile_pictures")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and update user profile picture
    """
    try:
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Read file content
        contents = await file.read()
        
        # Validate file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 5MB"
            )

        # Validate it's a real image
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Reopen image for processing (verify() closes it)
        image = Image.open(io.BytesIO(contents))
        
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize image to max 400x400 while maintaining aspect ratio
        max_size = (400, 400)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Generate unique filename
        filename = f"{uuid.uuid4()}.jpg"
        filepath = UPLOAD_DIR / filename

        # Save optimized image
        image.save(filepath, "JPEG", quality=85, optimize=True)

        # Get user from database
        user_id = current_user["id"]
        if isinstance(user_id, str):
            from uuid import UUID
            user_id = UUID(user_id)

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete old profile picture if exists and it's not a default/external URL
        if user.picture and user.picture.startswith("/uploads/"):
            old_path = Path(user.picture.lstrip("/"))
            if old_path.exists():
                old_path.unlink()

        # Update user profile picture
        picture_url = f"/uploads/profile_pictures/{filename}"
        user.picture = picture_url
        db.commit()
        db.refresh(user)

        return {
            "message": "Profile picture updated successfully",
            "picture_url": picture_url,
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "picture": user.picture,
                "provider": user.provider,
                "is_verified": user.is_verified,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload profile picture: {str(e)}"
        )


@router.delete("/delete-picture")
async def delete_profile_picture(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user profile picture and reset to initial
    """
    try:
        user_id = current_user["id"]
        if isinstance(user_id, str):
            from uuid import UUID
            user_id = UUID(user_id)

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Delete file if it's a local upload
        if user.picture and user.picture.startswith("/uploads/"):
            old_path = Path(user.picture.lstrip("/"))
            if old_path.exists():
                old_path.unlink()

        # Reset picture to None
        user.picture = None
        db.commit()
        db.refresh(user)

        return {
            "message": "Profile picture deleted successfully",
            "user": {
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "picture": None,
                "provider": user.provider,
                "is_verified": user.is_verified,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete profile picture: {str(e)}"
        )