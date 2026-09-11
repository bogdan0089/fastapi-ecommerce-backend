from core.redis import redis_client


async def version(namespace: str) -> int:
    """The namespace's current version, 0 until the first invalidate().

    Absence has to read as 0 because Redis INCR on a missing key returns 1 —
    read it as 1 and the first invalidate() would leave every key untouched.
    """
    return int(await redis_client.get(f"cache_version:{namespace}") or 0)

async def key(namespace: str, suffix: str) -> str:
    """Build a cache key stamped with the namespace's current version."""
    return f"{namespace}:v{await version(namespace)}:{suffix}"

async def invalidate(namespace: str) -> None:
    """Retire every cached key of one resource, e.g. invalidate("order").

    Nothing is scanned or deleted: bumping the version makes keys built before
    it unreachable, and they die on their own TTL. Scanning the whole database
    on every write was O(all keys) and blocked Redis for everyone else.
    """
    await redis_client.incr(f"cache_version:{namespace}")