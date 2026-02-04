from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from . import models, schemas
from .database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = int(payload.get("sub"))
        role: str = str(payload.get("role"))
        if user_id is None or role is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(models.User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


from fastapi import Request

async def get_current_user_from_token(
    request: Request, db: Session = Depends(get_db)
) -> models.User:
    token = request.cookies.get("access_token")
    if token:
        # Simple "Bearer <token>" split or just token
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
    else:
        # Fallback to header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    try:
        # VULNERABILITY: JWT None Algorithm & Weak Secret
        # We allow "none" algorithm which is a classic JWT vulnerability.
        # This typically involves removing the signature and changing 'alg' to 'none'.
        
        # Check if algorithm is 'none' in the header first if we were being really realistic
        # but here we just allow it in the decode call.
        
        # We also use a weak secret key (from settings, but usually it's hardcoded "secret")
        
        # PyJWT requires 'algorithms' list. We add 'none'.
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm, "none", "HS256"],
            options={"verify_signature": False} if token.split('.')[2] == "" else {}
        )
        user_id: int = int(payload.get("sub"))
        role: str = str(payload.get("role"))
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(models.User, user_id)
    if user is None:
        raise credentials_exception
    return user

def require_role(*roles: str):
    """Dependency factory to enforce role-based access."""

    def dependency(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


