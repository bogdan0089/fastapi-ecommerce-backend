import redis.asyncio as aioredis


redis_client = aioredis.from_url("redis://redis:6379")