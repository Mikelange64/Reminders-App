from __future__ import annotations

from datetime import datetime, UTC
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

user_workspace = Table(
    "user_workspace",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("workspace_id", Integer, ForeignKey("workspace.id"), primary_key=True),
)


class User(Base) :
    __tablename__ = 'user'

    id            : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username      : Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email         : Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash : Mapped[str] = mapped_column(String(100), nullable=False)
    image_path    : Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)

    created_tasks : Mapped[list[Task]] = relationship(
        "Task",
        back_populates="creator",
    )
    workspaces : Mapped[list[Workspace]] = relationship(
        secondary=user_workspace,
        back_populates="members"
    )

    @property
    def get_image_path(self):
        if not self.image_path:
            return "/static/defaults/default_profile_picture.jpg"
        return f"/media/profile_pics/{self.image_path}"


class Task(Base) :
    __tablename__ = "task"

    id           : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title        : Mapped[str] = mapped_column(String(50), nullable=False)
    content      : Mapped[str] = mapped_column(Text, nullable=False)
    is_completed : Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_public    : Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    creator_id   : Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user.id'),
        nullable=False,
        index=True
    )
    workspace_id : Mapped[int] = mapped_column(
        Integer,
        ForeignKey('workspace.id'),
        nullable=True,
        index=True
    )

    creator : Mapped["User"] = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    workspace : Mapped["Worskspace"] = relationship("Workspace", foreign_keys=[workspace_id], back_populates="tasks")

    date_created : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default = lambda : datetime.now(UTC)
    )
    due_date   : Mapped[datetime] = mapped_column( DateTime(timezone=True), nullable=True )

    @property
    def _days_remaining(self):
        if self.due_date is None:
            return None
        return (self.due_date - self.date_created).days


class Workspace(Base):
    __tablename__ = "workspace"

    id          : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title       : Mapped[str] = mapped_column(String(50), nullable=False)
    description : Mapped[str] = mapped_column(Text, nullable=False)
    max_number  : Mapped[int] = mapped_column(Integer, default=None)

    members : Mapped[list[User]] = relationship(
        secondary=user_workspace,
        back_populates="workspaces"
    )
    tasks   : Mapped[list[Task]] = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")

    date_created : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default = lambda : datetime.now(UTC),
    )
    due_date : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    @property
    def default_due_date(self):
        dates = [t.due_date for t in self.tasks if t.due_date is not None]
        return max(dates) if dates else None