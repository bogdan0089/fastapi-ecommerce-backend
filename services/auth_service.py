from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from core.config import settings
from core.exceptions import (
    ClientAlreadyError,
    ClientNotFoundError,
    TokenExpiredError,
    TokenInvalidError,
    VerifyPasswordError,
)
from database.unit_of_work import UnitOfWork
from models.models import Client
from schemas.auth_schema import ChangePassword, TokenResponse, ChangeRole, ForgotPassword, ResetPassword
from schemas.client_schema import ClientCreate
from utils.hash import hash_password, verify_password
import uuid
from core.redis import redis_client
from services.email_service import EmailService


class AuthService:

    @staticmethod
    def create_access_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(client_id: int) -> str:
        payload = {
            "sub": str(client_id),
            "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }
        return jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> int:
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
    def refresh_token(token: str) -> str:
        client_id = AuthService.decode_token(token)
        return AuthService.create_access_token(client_id)

    @staticmethod
    async def register_client(data: ClientCreate) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.email)
            if client:
                raise ClientAlreadyError(email=data.email)
            hashed = hash_password(data.password)
            client = await uow.client.create_client(
                data,
                hashed
            )
            token = str(uuid.uuid4())
        await redis_client.set(f"verify:{token}", client.id, ex=86400)
        await EmailService.send_verification_email(client.email, token)
        return client

    @staticmethod
    async def client_login(data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.username)
            if not client:
                raise ClientNotFoundError(email=data.username)
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
                name=client.name,
            )

    @staticmethod
    async def change_password(data: ChangePassword, current_client: Client) -> dict:
        if not verify_password(data.old_password, current_client.hashed_password):
            raise VerifyPasswordError()
        new_hashed = hash_password(data.new_password)
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(current_client.id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            client.hashed_password = new_hashed
            return {"message": "Password changed successfully."}
        
    @staticmethod
    async def change_role(client_id: int, data: ChangeRole) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            changed = await uow.client.change_role(client, data)
            return changed
        
    @staticmethod
    async def verify_email(token: str) -> dict:
        raw = await redis_client.get((f"verify:{token}"))
        if not raw:
            raise TokenInvalidError()
        client_id = int(raw)
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            client.is_verified = True
        await redis_client.delete(f"verify:{token}")
        return {
            "message": "Email verified successfully"
        }
            
    @staticmethod
    async def forgot_password(data: ForgotPassword):
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.email)
            if not client:
                raise ClientNotFoundError(email=data.email)
            reset_token = str(uuid.uuid4())
        await redis_client.set(f"reset_token:{reset_token}", client.id, ex=86400)
        await EmailService.send_reset_password_email(client.email, reset_token)
        return {
            "message": "Password reset email sent"
        }

    @staticmethod
    async def reset_password(data: ResetPassword):
        raw = await redis_client.get(f"reset_token:{data.reset_token}")
        if not raw:
            raise TokenInvalidError()
        client_id = int(raw)
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            hashed = hash_password(data.new_password)
            client.hashed_password = hashed
        await redis_client.delete(f"reset_token:{data.reset_token}")
        return {
            "message": "Password is reset"
        }
