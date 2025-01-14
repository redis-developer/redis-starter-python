from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.redis as redis
from app.components.todos.router import router as todos_router


app = FastAPI()
app.include_router(router=todos_router, prefix="/api/todos")
