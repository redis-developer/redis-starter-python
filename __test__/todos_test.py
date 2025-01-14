import asyncio
import pytest
from app.redis import redis
from app.components.todos.store import TodoStatus, TodoStore

todos = TodoStore(redis)

@pytest.fixture(autouse=True)
async def run_around_each():
    await todos.initialize()
    yield
    await todos.delete_all()
    await todos.drop_index()

async def test_crud_for_single_todo():
    created_todo = await todos.create(None, "Take out the trash")
    todo_id = created_todo.id

    assert created_todo.value.name == "Take out the trash"
    assert created_todo.value.status == "todo"

    read_todo = await todos.one(todo_id)

    assert created_todo.value.name == read_todo.name
    assert created_todo.value.status == read_todo.status

    updated_todo = await todos.update(todo_id, TodoStatus.in_progress)

    assert updated_todo.name == read_todo.name
    assert updated_todo.status == TodoStatus.in_progress
    assert updated_todo.updated_date > updated_todo.created_date
    assert updated_todo.updated_date > read_todo.updated_date

    await todos.delete(todo_id)


async def test_crud_for_multiple_todos():
    all_todo_names = [
      "Take out the trash",
      "Vacuum downstairs",
      "Fold the laundry",
    ]

    coros = []

    for todo in all_todo_names:
        coros.append(todos.create(None, todo))
    await asyncio.gather(*coros)

    all_todos = await todos.all()

    assert all_todos.total == 3

    for todo in all_todos.documents:
        assert todo.value.name in all_todo_names
