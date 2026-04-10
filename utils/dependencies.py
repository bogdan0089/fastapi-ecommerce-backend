from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from core.exceptions import ClientNotFoundError
from database.unit_of_work import UnitOfWork
from models.models import Client
from services.auth_service import AuthService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/client_login")


async def get_current_client(token: str = Depends(oauth2_scheme)) -> Client:
    client_id = AuthService.decode_token(token)
    async with UnitOfWork() as uow:
        client = await uow.client.get_client(client_id)
        if client is None:
            raise ClientNotFoundError(client_id)
        return client


CurrentClient = Annotated[Client, Depends(get_current_client)]
