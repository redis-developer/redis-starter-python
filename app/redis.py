from typing import Optional

from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry

from app.logger import logger

client: Optional[Redis] = None


def get_client(url: str = "redis://localhost:6379") -> Redis:
    global client

    if client is None:
        logger.info(f"Creating redis client for url: {url}")
        client = Redis.from_url(
            url,
            decode_responses=True,
            retry=Retry(ExponentialBackoff(cap=10, base=1), 25),
            retry_on_error=[ConnectionError, TimeoutError, ConnectionResetError],
            health_check_interval=1,
        )

    return client
