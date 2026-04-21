from typing import Annotated
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from core.exceptions import (
ClientNotFoundError,
InsufficientPermissionsError,
TooManyRequests
)
from database.unit_of_work import UnitOfWork
from models.models import Client
from services.auth_service import AuthService
from core.enum import Role
from core.redis import redis_client


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


async def rate_limit(request: Request):
    ip = request.client.host
    limit = f"rate_limit:{ip}"
    if int(await redis_client.get(limit) or 0) > 5:
        raise TooManyRequests()
    else:
        await redis_client.incr(limit)
        await redis_client.expire(limit, 60)



RateLimit = Annotated[None, Depends(rate_limit)]