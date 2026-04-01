from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from typing import Annotated

from database import get_db
from models import User, Task
from schemas import UserCreate, UserPublic, UserPrivate, UserUpdate, ChangePassword, TaskResponse, Token
from auth import verify_password, hash_password, create_access_token
from config import settings

router = APIRouter()

@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    email_result = db.execute(select(User).where(func.lower(User.email) == user.email.lower()))
    username_result = db.execute(select(User).where(func.lower(User.username) == user.username))

    email_exists = email_result.scalars().first()
    username_exists = username_result.scalars().first()

    if email_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    if username_exists:
        raise HTTPException(status_code=400, detail="Username already in use")

    new_user = User(
        username=user.username,
        email=user.email.lower(),
        password_hash = user.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends], db: Annotated[Session, Depends]):
    # here we use the form data username field to accept either email or username, so the user has a choice
    search_term = form_data.username.lower()
    query = select(User).where(
            or_(
                func.lower(User.email) == search_term,
                func.lower(User.username) == search_term
            )
    )
    result = db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect password or email/username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data = {"sub" : str(user.id)},
        expired_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/all")
def get_all_users(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User))
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users")
    return users


@router.get("/{user_id}", response_model=UserPublic)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.get("/{user_id}/tasks", response_model=list[TaskResponse])
def get_user_tasks(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Task).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = db.execute(select(Task).where(Task.creator_id == user_id))
    tasks = result.scalars().all()

    return tasks


@router.patch("/{user_id}", response_model=UserPrivate)
def update_user(
        user_id: int,
        user_data: UserUpdate,
        db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_data.username is not None and user_data.username.lower() != user.username.lower():
        result = db.execute(select(User).where(User.username == user_data.username))
        existing_username = result.scalars().first()

        if existing_username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    if user_data.email is not None and user_data.email.lower() != user.email.lower():
        result = db.execute(select(User).where(User.email == user_data.email))
        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if user_data.username:
        user_data.username = user_data.username.lower()

    if user_data.email:
        user_data.email = user_data.email.lower()

    update = user_data.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()

