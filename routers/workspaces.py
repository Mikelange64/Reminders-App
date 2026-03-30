from fastapi import APIRouter, Depends, status, HTTPException

from typing import Annotated

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload, joinedload

from database import get_db
from models import User, Task, Workspace
from schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, TaskResponse
)

router = APIRouter()

@router.post("/{user_id}", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
        user_id: int,
        workspace: WorkspaceCreate,
        db: Annotated[Session, Depends(get_db)]
):
    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    due_date = workspace.due_date if workspace.due_date else None

    new_workspace = Workspace(
        title=workspace.title,
        description=workspace.description,
        max_number=workspace.max_number,
        due_date=workspace.due_date,
    )

    new_workspace.members.append(user)
    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)

    return new_workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
            select(Workspace)
            .options(selectinload(Workspace.members))
            .where(Workspace.id == workspace_id)
    )
    workspace = result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    return workspace


@router.get("/tasks/{workspace_id}", response_model=list[TaskResponse])
def get_tasks(workspace_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
            select(Workspace)
            .options(selectinload(Workspace.tasks))
            .where(Workspace.id == workspace_id)
    )
    workspace = result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    return workspace.tasks

@router.patch("/add-user/{workspace_id}/{user_id}", response_model=WorkspaceResponse)
def add_user(workspace_id: int, user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
            select(Workspace)
            .options(joinedload(Workspace.members))
            .where(Workspace.id == workspace_id)
    )
    workspace = result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user in workspace.members:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already in this workspace")

    workspace.members.append(user)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace_partial(
        workspace_id: int,
        user_id: int,
        workspace_data: WorkspaceUpdate,
        db: Annotated[Session, Depends(get_db)]
):
    workspace_result = db.execute(
            select(Workspace)
            .options(selectinload(Workspace.members))
            .where(Workspace.id == workspace_id)
    )
    workspace = workspace_result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user not in workspace.members:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized to update this workspace")

    update = workspace_data.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(workspace, field, value)

    db.commit()
    db.refresh(workspace)
    return workspace


@router.put("/{workspace_id}/{user_id}", response_model=WorkspaceResponse)
def update_workspace_full(
        workspace_id: int,
        user_id: int,
        workspace_data: WorkspaceCreate,
        db: Annotated[Session, Depends(get_db)]
):
    workspace_result = db.execute(
            select(Workspace)
            .options(joinedload(Workspace.members))
            .where(Workspace.id == workspace_id)
    )
    workspace = workspace_result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user not in workspace.members:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authorized to update this task")

    workspace.title = workspace_data.title
    workspace.description = workspace_data.description
    workspace.max_number = workspace_data.max_number
    workspace.due_date = workspace_data.due_date

    db.commit()
    db.refresh(workspace)
    return workspace



@router.delete("/{workspace_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: int, user_id: int, db: Annotated[Session, Depends(get_db)]):
    workspace_result = db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = workspace_result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user not in workspace.members:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized to update this task")

