from redis.asyncio import Redis
from redis.commands.search.field import TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.exceptions import ResponseError

from app.logger import logger

TODOS_INDEX = "todos-idx"
TODOS_PREFIX = "todos:"


class Todos:
    """Stores todos"""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def initialize(self) -> None:
        await self.create_index_if_not_exists()
        return None

    async def have_index(self) -> bool:
        try:
            await self.redis.ft(TODOS_INDEX).info()  # type: ignore
        except ResponseError as e:
            if "Unknown index name" not in str(e):
                logger.info(f"Index {TODOS_INDEX} already exists")
                raise

        return True

    async def create_index_if_not_exists(self) -> None:
        try:
            if await self.have_index():
                return None

            logger.debug(f"Creating index {TODOS_INDEX}")

            schema = (
                TextField("$.name", as_name="name"),
                TextField("$.status", as_name="status"),
            )

            await self.redis.ft(TODOS_INDEX).create_index(  # type: ignore
                schema,
                definition=IndexDefinition(  # type: ignore
                    prefix=[TODOS_PREFIX], index_type=IndexType.JSON
                ),
            )

            logger.debug(f"Index {TODOS_INDEX} created successfully")
        except Exception as e:
            logger.error(f"Error setting up index {TODOS_INDEX}: {e}")
            raise

        return None
