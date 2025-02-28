from typing import AsyncIterator, Never

from fastapi import APIRouter, FastAPI
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel

from app.components.todos.store import Todo, TodoDocument, Todos, TodoStatus, TodoStore
from app.redis import get_client

todos_store: TodoStore | None = None


def get_todos() -> TodoStore:
    global todos_store

    return todos_store if todos_store is not None else TodoStore(get_client())


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[Never]:
    # before
    todos = get_todos()
    await todos.initialize()
    yield  # type: ignore
    # after
    return


router = APIRouter(lifespan=lifespan)


@router.get("/", tags=["todos"])
async def all() -> Todos:
    """Gets all todos"""
    todos = get_todos()
    return await todos.all()


@router.get("/search", tags=["todos"])
async def search(name: str | None = None, status: TodoStatus | None = None) -> Todos:
    """Searches for todos by name and/or status"""
    todos = get_todos()
    return await todos.search(name, status)


@router.get("/{id}", tags=["todos"])
async def one(id: str) -> Todo:
    """Gets a todo by id"""
    todos = get_todos()
    return await todos.one(id)


class CreateTodo(BaseModel):
    id: str | None = None
    name: str


@router.post("/", tags=["todos"])
async def create(todo: CreateTodo) -> TodoDocument:
    """Creates a todo"""
    todos = get_todos()
    return await todos.create(todo.id, todo.name)


class UpdateTodo(BaseModel):
    status: TodoStatus


@router.patch("/{id}", tags=["todos"])
async def update(id: str, todo: UpdateTodo) -> Todo:
    """Updates a todo's status"""
    todos = get_todos()
    return await todos.update(id, todo.status)


@router.delete("/{id}", tags=["todos"])
async def delete(id: str) -> None:
    """Deletes a todo"""
    todos = get_todos()
    return await todos.delete(id)
