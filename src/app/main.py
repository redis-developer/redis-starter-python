from fastapi import FastAPI

from app.components.todos.router import router as todos_router

app = FastAPI()
app.include_router(router=todos_router, prefix="/api/todos")
