from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Never, Union

from fastapi import FastAPI

import app.redis as redis
from app.todos import Todos

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
client = redis.get_client(redis_url)
todos = Todos(client)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[Never]:
    # before
    await todos.initialize()
    yield  # type: ignore
    # after
    return


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root() -> bool:
    return await todos.have_index()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None) -> Any:
    return {"item_id": item_id, "q": q}
