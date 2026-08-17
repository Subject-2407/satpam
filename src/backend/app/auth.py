from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt as _bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


class Role:
    PUBLIC_REPORTER = "public_reporter"
    ANALYST = "analyst"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


# Seed users — passwords hashed at import time, NOT hardcoded plaintext.
# Default plaintext passwords are intentionally weak for demo only.
def _hash(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


SEED_USERS: dict[str, dict] = {
    "reporter@satpam.test": {
        "id": "user-reporter-001",
        "name": "Pelapor Demo",
        "email": "reporter@satpam.test",
        "role": Role.PUBLIC_REPORTER,
        "hashed_password": _hash("reporter123"),
        "status": "active",
    },
    "analyst@satpam.test": {
        "id": "user-analyst-001",
        "name": "Analis Demo",
        "email": "analyst@satpam.test",
        "role": Role.ANALYST,
        "hashed_password": _hash("analyst123"),
        "status": "active",
    },
    "supervisor@satpam.test": {
        "id": "user-supervisor-001",
        "name": "Supervisor Demo",
        "email": "supervisor@satpam.test",
        "role": Role.SUPERVISOR,
        "hashed_password": _hash("supervisor123"),
        "status": "active",
    },
    "admin@satpam.test": {
        "id": "user-admin-001",
        "name": "Admin Demo",
        "email": "admin@satpam.test",
        "role": Role.ADMIN,
        "hashed_password": _hash("admin123"),
        "status": "active",
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = SEED_USERS.get(email)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kadaluarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str | None = payload.get("sub")
        if email is None:
            raise exc
    except JWTError:
        raise exc

    user = SEED_USERS.get(email)
    if user is None:
        raise exc
    return user


def require_roles(*roles: str):
    """Factory that returns a FastAPI dependency enforcing the given roles."""

    def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user['role']}' tidak memiliki akses ke endpoint ini",
            )
        return current_user

    return checker
