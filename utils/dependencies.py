from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from database.unit_of_work import UnitOfWork
from services.auth_service import AuthService
from core.exceptions import ClientNotFoundError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_client(token: str = Depends(oauth2_scheme)):
    client_id = AuthService.decode_token(token)
    async with UnitOfWork() as uow:
        client = await uow.client.get_client(client_id)
        if client is None:
            raise ClientNotFoundError(client_id)
        return client