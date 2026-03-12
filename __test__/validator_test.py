import pytest
from pydantic import ValidationError

from app.components.todos.validator import (
    CreateTodoBody,
    SearchTodosQuery,
    TodoIdParams,
    UpdateTodoBody,
)


def test_create_todo_body_accepts_valid_name():
    result = CreateTodoBody.model_validate({"name": "Buy groceries"})

    assert result.name == "Buy groceries"
    assert result.id is None


def test_create_todo_body_accepts_name_with_optional_id():
    result = CreateTodoBody.model_validate({"name": "Buy groceries", "id": "abc"})

    assert result.name == "Buy groceries"
    assert result.id == "abc"


def test_create_todo_body_rejects_empty_name():
    with pytest.raises(ValidationError, match="Todo must have a name"):
        CreateTodoBody.model_validate({"name": ""})


def test_create_todo_body_rejects_missing_name():
    with pytest.raises(ValidationError):
        CreateTodoBody.model_validate({})


def test_create_todo_body_ignores_unknown_fields():
    result = CreateTodoBody.model_validate({"name": "Test", "extra": True})

    assert result.model_dump(exclude_none=True) == {"name": "Test"}


@pytest.mark.parametrize("status", ["todo", "in progress", "complete"])
def test_update_todo_body_accepts_valid_status(status: str):
    result = UpdateTodoBody.model_validate({"status": status})

    assert result.status.value == status


def test_update_todo_body_rejects_invalid_status():
    with pytest.raises(ValidationError):
        UpdateTodoBody.model_validate({"status": "invalid"})


def test_search_todos_query_accepts_empty_query():
    result = SearchTodosQuery.model_validate({})

    assert result.name is None
    assert result.status is None


def test_todo_id_params_rejects_empty_id():
    with pytest.raises(ValidationError):
        TodoIdParams.model_validate({"id": ""})


def test_todo_id_params_rejects_missing_id():
    with pytest.raises(ValidationError):
        TodoIdParams.model_validate({})
