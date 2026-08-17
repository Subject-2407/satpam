from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import Token, authenticate_user, create_access_token

router = APIRouter(tags=["auth"])


@router.post("/api/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 password flow. Gunakan email sebagai username.

    Seed users (demo only):
    - reporter@satpam.test / reporter123
    - analyst@satpam.test  / analyst123
    - supervisor@satpam.test / supervisor123
    - admin@satpam.test    / admin123
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password tidak valid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    return Token(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        user_id=user["id"],
    )
