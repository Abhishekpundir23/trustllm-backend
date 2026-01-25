from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserKeysUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        # Return True/False if they have a key
        has_openai=bool(current_user.openai_key),
        has_anthropic=bool(current_user.anthropic_key),
        has_gemini=bool(current_user.gemini_key)
    )

@router.put("/me/keys")
def update_api_keys(
    keys: UserKeysUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if keys.openai_key is not None:
        current_user.openai_key = keys.openai_key
    if keys.anthropic_key is not None:
        current_user.anthropic_key = keys.anthropic_key
    if keys.gemini_key is not None:
        current_user.gemini_key = keys.gemini_key
    
    db.commit()
    db.refresh(current_user)
    return {"status": "success", "message": "API Keys updated"}