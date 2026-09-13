import asyncio

from utils import cache


class VersionRedis:
    """Keeps versions in memory, so a bump is visible to the next key build.

    FakeRedis in conftest answers None to everything, which would let these
    tests pass no matter what invalidate() did.
    """

    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    async def get(self, key):
        value = self.store.get(key)
        return None if value is None else str(value).encode()

    async def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

def test_key_is_stable_until_invalidated(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    first = asyncio.run(cache.key("order", "list:limit=10"))
    assert first == asyncio.run(cache.key("order", "list:limit=10"))

def test_invalidate_changes_the_key(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    before = asyncio.run(cache.key("order", "list:limit=10"))
    asyncio.run(cache.invalidate("order"))
    assert asyncio.run(cache.key("order", "list:limit=10")) != before

def test_second_invalidate_changes_the_key_again(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    asyncio.run(cache.invalidate("order"))
    after_first = asyncio.run(cache.key("order", "list:limit=10"))
    asyncio.run(cache.invalidate("order"))
    assert asyncio.run(cache.key("order", "list:limit=10")) != after_first

def test_version_starts_at_zero(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    assert asyncio.run(cache.version("order")) == 0

def test_version_counts_invalidations(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    asyncio.run(cache.invalidate("order"))
    asyncio.run(cache.invalidate("order"))
    assert asyncio.run(cache.version("order")) == 2

def test_version_is_per_namespace(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    asyncio.run(cache.invalidate("order"))
    assert asyncio.run(cache.version("product")) == 0

def test_invalidate_leaves_other_resources_alone(monkeypatch):
    monkeypatch.setattr(cache, "redis_client", VersionRedis())
    product_key = asyncio.run(cache.key("product", "list:limit=10"))
    asyncio.run(cache.invalidate("order"))
    assert asyncio.run(cache.key("product", "list:limit=10")) == product_key
