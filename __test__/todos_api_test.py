import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ResponseError

from app.components.todos.store import TODOS_INDEX, TODOS_PREFIX, reset_todos_store
from app.config import get_settings
from app.main import app
from app.redis import get_sync_client

settings = get_settings()
redis = get_sync_client()


def _reset_redis_state() -> None:
    todo_keys = redis.keys(f"{TODOS_PREFIX}*")

    if len(todo_keys) > 0:
        redis.delete(*todo_keys)

    redis.delete(settings.log_stream_key)

    try:
        redis.ft(TODOS_INDEX).dropindex()
    except ResponseError as exc:
        if "Unknown index name" not in str(exc) and "no such index" not in str(exc):
            raise


@pytest.fixture(autouse=True)
def reset_todos():
    reset_todos_store()
    _reset_redis_state()
    yield
    reset_todos_store()
    _reset_redis_state()


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_crud_for_single_todo(client: TestClient):
    create_response = client.post("/api/todos", json={"name": "Take out the trash"})
    create_result = create_response.json()
    todo_id = create_result["id"]
    created_todo = create_result["value"]

    assert create_response.status_code == 200
    assert created_todo["name"] == "Take out the trash"
    assert created_todo["status"] == "todo"
    assert "createdDate" in created_todo
    assert "updatedDate" in created_todo

    read_response = client.get(f"/api/todos/{todo_id}")
    read_result = read_response.json()

    assert read_response.status_code == 200
    assert read_result["name"] == created_todo["name"]
    assert read_result["status"] == created_todo["status"]

    update_response = client.patch(
        f"/api/todos/{todo_id}",
        json={"status": "complete"},
    )
    update_result = update_response.json()

    assert update_response.status_code == 200
    assert update_result["name"] == read_result["name"]
    assert update_result["status"] == "complete"
    assert update_result["updatedDate"] > update_result["createdDate"]
    assert update_result["updatedDate"] > read_result["updatedDate"]

    delete_response = client.delete(f"/api/todos/{todo_id}")

    assert delete_response.status_code == 200
    assert delete_response.text == ""


def test_create_and_read_multiple_todos(client: TestClient):
    todo_names = [
        "Take out the trash",
        "Vacuum downstairs",
        "Fold the laundry",
    ]

    for name in todo_names:
        response = client.post("/api/todos", json={"name": name})
        assert response.status_code == 200

    all_todos_response = client.get("/api/todos")
    all_todos = all_todos_response.json()

    assert all_todos_response.status_code == 200
    assert all_todos["total"] == len(todo_names)

    for todo in all_todos["documents"]:
        assert todo["value"]["name"] in todo_names


def test_search_by_name_and_status(client: TestClient):
    client.post("/api/todos", json={"name": "Buy groceries"})
    second = client.post("/api/todos", json={"name": "Clean kitchen"}).json()
    client.patch(f"/api/todos/{second['id']}", json={"status": "complete"})

    search_by_name = client.get("/api/todos/search", params={"name": "Buy"}).json()
    search_by_status = client.get(
        "/api/todos/search",
        params={"status": "complete"},
    ).json()

    assert search_by_name["total"] == 1
    assert search_by_name["documents"][0]["value"]["name"] == "Buy groceries"
    assert search_by_status["total"] == 1
    assert search_by_status["documents"][0]["value"]["status"] == "complete"


def test_missing_todo_returns_not_found(client: TestClient):
    response = client.get("/api/todos/missing")

    assert response.status_code == 404
    assert response.json() == {"status": 404, "message": "Not Found"}


def test_invalid_create_returns_client_error(client: TestClient):
    response = client.post("/api/todos", json={"name": ""})

    assert response.status_code == 400
    assert response.json() == {"status": 400, "message": "Todo must have a name"}


def test_invalid_update_returns_validation_error(client: TestClient):
    response = client.patch("/api/todos/x", json={"status": "invalid"})

    assert response.status_code == 400
    assert response.json()["status"] == 400
    assert (
        "Input should be 'todo', 'in progress' or 'complete'"
        in response.json()["message"]
    )


def test_request_logging_writes_to_redis_stream(client: TestClient):
    response = client.get("/api/todos")

    assert response.status_code == 200
    assert redis.xlen(settings.log_stream_key) >= 1
