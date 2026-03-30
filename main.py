from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from starlette.exceptions import HTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session


from typing import Annotated

from database import engine, get_db, Base
from models import User, Task
from routers import users, tasks, workspaces


Base.metadata.create_all(bind=engine)
app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="templates"), name="static")
app.mount("/media", StaticFiles(directory="templates"), name="static")

app.include_router(users.router, prefix="/api/user", tags=["user"])
app.include_router(tasks.router, prefix="/api/task", tags=["task"])
app.include_router(workspaces.router, prefix="/api/workspaces", tags=["workspaces"])


@app.get("/{user_id}", include_in_schema=False)
def home(request: Request, user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = db.execute(select(Task).where(Task.user_id == user.id, Task.is_completed == False))
    pending_tasks = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="pending.html",
        context={"pending_tasks": pending_tasks, "title" : "Home"},
    )




# ======================================================================================================================
# EXCEPTION HANDLER
# ======================================================================================================================

@app.exception_handler(HTTPException)
def general_exception_handler(request: Request, exc: HTTPException):

    message = exc.detail if exc.detail else "An error occurred, please try again"

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message" : message}
        )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "status_code" : exc.status_code,
            "message"     : message,
            "title" : exc.status_code
        },
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"message": exc.errors()}
        )

    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context = {
            "status_code" : status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title"       : status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message"     : "Invalid request, please check your input and try again",
        }
    )

