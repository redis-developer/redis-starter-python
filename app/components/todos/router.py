from typing import AsyncIterator, Never
from fastapi import APIRouter, FastAPI
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel

from app.redis import redis
from app.components.todos.store import Todo, TodoDocument, TodoStatus, TodoStore, Todos

todos = TodoStore(redis)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[Never]:
    # before
    await todos.initialize()
    yield  # type: ignore
    # after
    return

router = APIRouter(lifespan=lifespan)

@router.get("/", tags=["todos"])
async def all() -> Todos:
    return await todos.all()

@router.get("/search", tags=["todos"])
async def search(name: str | None = None, status: TodoStatus | None = None) -> Todos:
    return await todos.search(name, status)

@router.get("/{id}", tags=["todos"])
async def one(id: str) -> Todo:
    return await todos.one(id)

class CreateTodo(BaseModel):
    id: str | None = None
    name: str

@router.post("/", tags=["todos"])
async def create(todo: CreateTodo) -> TodoDocument:
    return await todos.create(todo.id, todo.name)

class UpdateTodo(BaseModel):
    status: TodoStatus

@router.patch("/{id}", tags=["todos"])
async def update(id: str, todo: UpdateTodo) -> Todo:
    return await todos.update(id, todo.status)

@router.delete("/{id}", tags=["todos"])
async def delete(id: str) -> None:
    return await todos.delete(id)
