from fastapi import APIRouter, HTTPException, status, Depends

from typing import Annotated

from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload


from database import get_db
from models import Task, User, Workspace
from schemas import (
    TaskCreate, TaskResponse, TaskUpdate, TaskMove,
    UserCreate, UserPublic, UserPrivate, UserUpdate
)

router = APIRouter()

@router.post("/{user_id}", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(user_id: int, task: TaskCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_task = Task(
        title=task.title,
        content=task.content,
        creator_id=user.id,
        workspace_id=task.workspace_id,
        is_public=task.is_public,
        due_date=task.due_date,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task


@router.patch("/{task_id}/{user_id}", response_model=TaskResponse)
def update_task_partial(task_id: int, user_id: int, task_data: TaskUpdate, db :Annotated[Session, Depends(get_db)]):
    task_result = db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id != task.creator_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized to update this task")

    update = task_data.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.patch("{task_id}/{user_id}/{workspace_id}/", response_model=TaskResponse)
def move_task(task_id: int, user_id: int, workspace_id: int, task_data: TaskMove, db :Annotated[Session, Depends(get_db)]):
    task_result = db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    workspace_result = db.execute(
        select(Workspace)
        .options(joinedload(Workspace.members))
        .where(Workspace.id == workspace_id)
    )
    workspace = workspace_result.scalars().first()

    if not workspace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    is_creator = user.id == task.creator_id
    is_member = user in workspace.members

    if not is_member and not is_creator:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User not authorized to move task")

    if not is_member:
        workspace.members.append(user)

    task.workspace_id = task_data.workspace_id

    db.commit()
    db.refresh(workspace)
    db.refresh(task)

    return task


@router.put("/{task_id}/{user_id}", response_model=TaskResponse)
def update_task_full(task_id: int, user_id: int, task_data: TaskCreate, db:Annotated[Session, Depends(get_db)]):
    task_result = db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user.id != task.creator_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized to update this task")

    task.title = task_data.title
    task.content = task_data.content
    task.creator_id = user.id
    task.workspace_id = task_data.workspace_id
    task.is_public = task_data.is_public
    task.due_date = task_data.due_date

    db.commit()
    db.refresh(task, attribute_names=['creator'])
    return task


@router.delete("/{task_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, user_id: int, db:Annotated[Session, Depends(get_db)]):
    task_result = db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    user_result = db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id != task.creator_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized to delete this task")

    db.delete(task)
    db.commit()
