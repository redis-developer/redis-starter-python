import os

from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis = Redis.from_url(
    redis_url,
    decode_responses=True,
    retry=Retry(ExponentialBackoff(cap=10, base=1), 25),
    retry_on_error=[ConnectionError, TimeoutError, ConnectionResetError],
    health_check_interval=1,
)
