from datetime import datetime, timedelta, timezone
from core.config import settings
import jwt
from schemas.schemas import ClientCreate, TokenResponse
from database.unit_of_work import UnitOfWork
from utils.hash import hash_password, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from core.exceptions import ClientNotFoundError, TokenExpiredError, TokenInvalidError, VerifyPasswordError, ClientAlreadyError


class AuthService:

    @staticmethod
    def create_access_token(user_id: int):
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)
    
    @staticmethod
    def decode_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise ClientNotFoundError()
            return int(user_id)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError:
            raise TokenInvalidError()
        
    @staticmethod
    def create_refresh_token(client_id: int):
        payload = {
            "sub": str(client_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        }
        return jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)
    

    @staticmethod
    def refresh_token(token: str):
        client_id = AuthService.decode_token(token)
        new_access_token = AuthService.create_access_token(client_id)
        return new_access_token
        
    @staticmethod
    async def register_client(data: ClientCreate):
        async with UnitOfWork() as uow:
            existing_client = await uow.client.get_client_email(data.email)
            if existing_client:
                raise ClientAlreadyError(email=data.email)
            hashed = hash_password(data.password)
            client = await uow.client.create_client(
                name=data.name,
                email=data.email,
                balance=data.balance,
                age=data.age,
                hashed_password=hashed
            )
            return client
        
    @staticmethod
    async def client_login(data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.username)
            if client is None:
                raise ClientNotFoundError(data.username)
            if not verify_password(data.password, client.hashed_password):
                raise VerifyPasswordError()
            token = AuthService.create_access_token(client.id)
            refresh_token = AuthService.create_refresh_token(client.id)
            return TokenResponse(
                access_token=token,
                refresh_token=refresh_token,
                token_type="bearer",
                client_id=client.id,
                email=client.email,
                age=client.age,
                name=client.name
            )
            
        
                


            
            
