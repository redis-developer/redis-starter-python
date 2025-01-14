import asyncio
import re
from datetime import UTC, datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, field_serializer
from pydantic_core import from_json
from redis.asyncio import Redis
from redis.commands.search.document import Document
from redis.commands.search.field import TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ResponseError

from app.logger import logger

TODOS_INDEX = "todos-idx"
TODOS_PREFIX = "todos:"


class TodoStatus(str, Enum):
    todo = "todo"
    in_progress = "in progress"
    complete = "complete"


class Todo(BaseModel):
    name: str
    status: TodoStatus
    created_date: datetime | None = None
    updated_date: datetime | None = None

    @field_serializer("created_date")
    def serialize_created_date(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    @field_serializer("updated_date")
    def serialize_updated_date(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class TodoDocument(BaseModel):
    id: str
    value: Todo


class Todos(BaseModel):
    total: int
    documents: List[TodoDocument]


class TodoStore:
    """Stores todos"""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.INDEX = TODOS_INDEX
        self.PREFIX = TODOS_PREFIX

    async def initialize(self) -> None:
        await self.create_index_if_not_exists()
        return None

    async def have_index(self) -> bool:
        try:
            await self.redis.ft(self.INDEX).info()
        except ResponseError as e:
            if "Unknown index name" in str(e):
                logger.debug(f"Index {self.INDEX} does not exist")
                return False

        logger.debug(f"Index {self.INDEX} already exists")
        return True

    async def create_index_if_not_exists(self) -> None:
        if await self.have_index():
            return None

        logger.debug(f"Creating index {self.INDEX}")

        schema = (
            TextField("$.name", as_name="name"),
            TextField("$.status", as_name="status"),
        )

        try:
            await self.redis.ft(self.INDEX).create_index(
                schema,
                definition=IndexDefinition(
                    prefix=[TODOS_PREFIX], index_type=IndexType.JSON
                ),
            )
        except Exception as e:
            logger.error(f"Error setting up index {self.INDEX}: {e}")
            raise

        logger.debug(f"Index {self.INDEX} created successfully")

        return None

    async def drop_index(self) -> None:
        if not await self.have_index():
            return None

        try:
            await self.redis.ft(self.INDEX).dropindex()
        except Exception as e:
            logger.error(f"Error dropping index ${self.INDEX}: {e}")
            raise

        logger.debug(f"Index {self.INDEX} dropped successfully")

        return None

    def format_id(self, id: str) -> str:
        if re.match(f"^{self.PREFIX}", id):
            return id

        return f"{self.PREFIX}{id}"

    def parse_todo_document(self, todo: Document) -> TodoDocument:
        return TodoDocument(
            id=todo.id,
            value=Todo(**from_json(todo.json, allow_partial=True)),  # type: ignore
        )

    def parse_todo_documents(self, todos: list[Document]) -> list[TodoDocument]:
        todo_docs = []

        for doc in todos:
            todo_docs.append(self.parse_todo_document(doc))

        return todo_docs

    async def all(self) -> Todos:
        try:
            result = await self.redis.ft(self.INDEX).search("*")
            return Todos(
                total=result.total, documents=self.parse_todo_documents(result.docs)
            )
        except Exception as e:
            logger.error(f"Error getting all todos: {e}")
            raise

    async def one(self, id: str) -> Todo:
        id = self.format_id(id)

        try:
            json = await self.redis.json().get(id)
        except Exception as e:
            logger.error(f"Error getting todo ${id}: {e}")
            raise

        return Todo(**json)

    async def search(self, name: str | None, status: TodoStatus | None) -> Todos:
        searches = []

        if name is not None and len(name) > 0:
            searches.append(f"@name:({name})")

        if status is not None and len(status) > 0:
            searches.append(f"@status:{status.value}")

        try:
            result = await self.redis.ft(self.INDEX).search(Query(" ".join(searches)))
            return Todos(
                total=result.total, documents=self.parse_todo_documents(result.docs)
            )
        except Exception as e:
            logger.error(f"Error getting todo {id}: {e}")
            raise

    async def create(self, id: Optional[str], name: Optional[str]) -> TodoDocument:
        dt = datetime.now(UTC)

        if name is None:
            raise Exception("Todo must have a name")

        if id is None:
            id = str(uuid4())

        todo = TodoDocument(
            id=self.format_id(id),
            value=Todo(
                name=name, status=TodoStatus.todo, created_date=dt, updated_date=dt
            ),
        )

        try:
            result = await self.redis.json().set(todo.id, "$", todo.value.model_dump())
        except Exception as e:
            logger.error(f"Error creating todo {todo}: {e}")
            raise

        if not result:
            raise Exception(f"Error creating todo {todo}")

        return todo

    async def update(self, id: str, status: TodoStatus) -> Todo:
        dt = datetime.now(UTC)

        todo = await self.one(id)

        todo.status = status
        todo.updated_date = dt

        try:
            result = await self.redis.json().set(
                self.format_id(id), "$", todo.model_dump()
            )
        except Exception as e:
            logger.error(f"Error updating todo {todo}: {e}")
            raise

        if not result:
            raise Exception(f"Error creating todo {todo}")

        return todo

    async def delete(self, id: str) -> None:
        try:
            await self.redis.json().delete(self.format_id(id))
        except Exception as e:
            logger.error(f"Error deleting todo {id}: {e}")
            raise

        return None

    async def delete_all(self) -> None:
        todos = await self.all()
        coros = []

        try:
            for todo in todos.documents:
                coros.append(self.redis.json().delete(todo.id))
            await asyncio.gather(*coros)
        except Exception as e:
            logger.error(f"Error deleting todos: {e}")
            raise

        return None
