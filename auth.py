import jwt
from datetime import UTC, timedelta, datetime

from argon2 import PasswordHasher
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer

from typing import Annotated
from pwdlib import PasswordHash

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User
from database import get_db
from config import settings


pw_hasher = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")

def hash_password(password: str) -> str:
    return pw_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pw_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict, expired_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expired_delta:
        expire = datetime.now(UTC) + expired_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )

    return encode_jwt


def verify_access_token(token: str) -> bool | str:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=["HS256"],
            option={"require" : ["exp", "sub"]}
        )
    except:
        return False
    else:
        return payload.get("sub")


def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db : Annotated[Session, Depends(get_db)]
):
    user_id = verify_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


current_user = Annotated[User, Depends(get_current_user)]
