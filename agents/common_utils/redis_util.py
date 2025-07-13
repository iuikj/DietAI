from redis.asyncio import Redis as AsyncRedis
from shared.config.settings import get_settings

settings = get_settings()


async def get_redis_client():
    return await AsyncRedis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True,
        password=settings.redis_password)

