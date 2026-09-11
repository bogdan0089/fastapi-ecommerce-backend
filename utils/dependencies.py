from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.security import OAuth2PasswordBearer

from core.enum import Role
from core.exceptions import ClientNotFoundError, InsufficientPermissionsError, TooManyRequests
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client
from services.auth_service import AuthService

MAX_PAGE_SIZE = 200

# Without a ceiling, ?limit=1000000 on any public list endpoint loads a million
# rows into ORM objects and serialises them. A negative offset reaches Postgres
# and fails there as a 500 instead of a 422.
Limit = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]
Offset = Annotated[int, Query(ge=0)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/client_login")

async def get_current_client(token: str = Depends(oauth2_scheme)) -> Client:
    client_id = AuthService.decode_token(token)
    async with UnitOfWork() as uow:
        client = await uow.client.get_client(client_id)
        if client is None:
            raise ClientNotFoundError(client_id)
        return client

CurrentClient = Annotated[Client, Depends(get_current_client)]

async def get_current_admin(client: Client = Depends(get_current_client)) -> Client:
    if client.role == Role.superadmin:
        return client
    else:
        raise InsufficientPermissionsError(
            required_role=Role.superadmin.value,
            client_role=client.role.value
        )

CurrentAdmin = Annotated[Client, Depends(get_current_admin)]

async def get_current_moderator(client: Client = Depends(get_current_client)) -> Client:
    if client.role in (Role.superadmin, Role.moderator):
        return client
    else:
        raise InsufficientPermissionsError(
            required_role=f"{Role.moderator.value} or {Role.superadmin.value}",
            client_role=client.role.value
        )
    
CurrentModerator = Annotated[Client, Depends(get_current_moderator)]

RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60

def client_ip(request: Request) -> str:
    """The caller's address, or the proxy's if it did not forward one.

    Behind nginx every request comes from the proxy, so without this the limit
    would be shared by everyone: six requests from anybody would lock out all.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

async def rate_limit(request: Request):
    key = f"rate_limit:{client_ip(request)}"
    used = await redis_client.incr(key)
    if used == 1:
        await redis_client.expire(key, RATE_LIMIT_WINDOW_SECONDS)
    if used > RATE_LIMIT_REQUESTS:
        raise TooManyRequests()

RateLimit = Annotated[None, Depends(rate_limit)]