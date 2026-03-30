from typing import List

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime


class Base(BaseModel):
    pass


# ======================================================================================================================
# USERS SCHEMAS
# ======================================================================================================================

class UserBase(Base):
    username : str   = Field(min_length=5, max_length=50)
    email : EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password : str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id         : int
    username   : str
    image_path : str | None = None


class UserPrivate(UserPublic):
    email : EmailStr


class UserUpdate(UserBase):
    username   : str | None = Field(default=None, min_length=5, max_length=50)
    email      : EmailStr | None = Field(default=None,  max_length=120)
    image_path : str | None = None


class ChangePassword(BaseModel):
    old_password : str
    new_password : str


# ======================================================================================================================
# TASK SCHEMAS
# ======================================================================================================================

class TaskBase(BaseModel):
    title     : str = Field(min_length=1, max_length=100)
    content   : str = Field(min_length=1, max_length=300)
    workspace_id : int | None = None
    is_public : bool = Field(default=False)
    due_date  : datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id           : int
    creator_id   : int
    workspace_id : int | None
    date_created : datetime
    due_date     : datetime | None
    is_completed : bool


class TaskUpdate(TaskBase):
    content      : str | None = Field(default=None, min_length=1, max_length=300)
    workspace_id : int | None = None
    is_completed : bool | None = None
    is_public    : bool | None = None
    due_date     : datetime | None = None


class TaskMove(BaseModel):
    workspace_id : int | None


# ======================================================================================================================
# WORKSPACE SCHEMAS
# ======================================================================================================================


class WorkspaceBase(BaseModel):
    title       : str = Field(min_length=1, max_length=50)
    description : str = Field(min_length=1, max_length=500)
    max_number  : int | None = None
    due_date    : datetime | None = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceResponse(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)

    id           : int
    title        : str
    description  : str
    max_number   : int
    members      : list[UserPublic]
    date_created : datetime
    due_date     : datetime | None


class WorkspaceUpdate(WorkspaceBase):
    title        : str | None = Field(min_length=1, max_length=50, default=None)
    description  : str | None = Field(min_length=1, max_length=500, default=None)
    max_number   : int | None = None
    due_date     : datetime | None = None
    is_completed : bool | None = None