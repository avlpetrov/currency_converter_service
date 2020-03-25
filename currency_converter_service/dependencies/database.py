import aioredis


async def create_connection_pool(uri: str) -> aioredis.Redis:
    pool = await aioredis.create_redis_pool(uri)

    return pool
