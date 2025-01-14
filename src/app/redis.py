import os

from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry

clients: dict[str, Redis] = {}


def get_client(url: str | None = None) -> Redis:
    redis_url = (
        url
        if url is not None
        else os.environ.get("REDIS_URL", "redis://localhost:6379")
    )

    if redis_url in clients:
        return clients[redis_url]

    clients[redis_url] = Redis.from_url(
        redis_url,
        decode_responses=True,
        retry=Retry(ExponentialBackoff(cap=10, base=1), 25),
        retry_on_error=[ConnectionError, TimeoutError, ConnectionResetError],
        health_check_interval=1,
    )

    return clients[redis_url]
