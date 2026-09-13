import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from kombu.exceptions import OperationalError

from celery_app import send_reset_password_email, send_verification_email
from core.config import settings
from core.exceptions import (
    ClientAlreadyError,
    ClientNotFoundError,
    EmailNotVerifiedError,
    EmailQueueError,
    TokenExpiredError,
    TokenInvalidError,
    VerifyPasswordError,
)
from core.redis import redis_client
from database.unit_of_work import UnitOfWork
from models.models import Client
from schemas.auth.input_dto import ChangePasswordDTO, ChangeRoleDTO, ForgotPasswordDTO, ResetPasswordDTO
from schemas.auth.output_dto import TokenOutputDTO
from schemas.client.input_dto import ClientCreateDTO
from utils.hash import hash_password, verify_password
from utils.logger import get_logger

logger = get_logger(__name__)

class AuthService:

    @staticmethod
    def create_access_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, settings.SECRET_KEY, settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(client_id: int) -> str:
        payload = {
            "sub": str(client_id),
            "exp": datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
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
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalidError() from exc

    @staticmethod
    def refresh_token(token: str) -> str:
        client_id = AuthService.decode_token(token)
        return AuthService.create_access_token(client_id)

    @staticmethod
    async def _queue_verification_email(client_id: int, email: str) -> bool:
        token = str(uuid.uuid4())
        await redis_client.set(f"verify:{token}", client_id, ex=86400)
        try:
            send_verification_email.delay(email, token)
        except OperationalError:
            logger.error(
                "verification_email_not_queued",
                extra={"extra_fields": {"client_id": client_id, "email": email}},
            )
            return False
        return True

    @staticmethod
    async def register_client(data: ClientCreateDTO) -> dict[str, str]:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.email)
            if client:
                raise ClientAlreadyError(email=data.email)
            hashed = hash_password(data.password)
            client = await uow.client.create_client(
                data,
                hashed
            )
        queued = await AuthService._queue_verification_email(client.id, client.email)
        logger.info("client_registered", extra={"extra_fields": {"client_id": client.id, "email": data.email}})
        if queued:
            return {"message": "Registration successful. Check your email to verify account."}
        return {
            "message": "Registration successful, but the verification email could not be sent. "
                       "Use resend verification to try again."
        }

    @staticmethod
    async def resend_verification(data: ForgotPasswordDTO) -> dict[str, str]:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.email)
            if not client:
                raise ClientNotFoundError(email=data.email)
            if client.is_verified:
                return {"message": "This email is already verified. You can log in."}
            client_id, email = client.id, client.email
        queued = await AuthService._queue_verification_email(client_id, email)
        if queued:
            return {"message": "Verification email sent. Check your inbox."}
        raise EmailQueueError()

    @staticmethod
    async def client_login(data: OAuth2PasswordRequestForm = Depends()) -> TokenOutputDTO:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.username)
            if not client:
                logger.warning("login_failed_not_found", extra={"extra_fields": {"email": data.username}})
                raise ClientNotFoundError(email=data.username)
            if not client.is_verified:
                logger.warning("login_blocked_not_verified", extra={"extra_fields": {"client_id": client.id}})
                raise EmailNotVerifiedError()
            if not verify_password(data.password, client.hashed_password):
                logger.warning("login_failed_wrong_password", extra={"extra_fields": {"client_id": client.id}})
                raise VerifyPasswordError()
            token = AuthService.create_access_token(client.id)
            refresh_token = AuthService.create_refresh_token(client.id)
            logger.info("client_login", extra={"extra_fields": {"client_id": client.id}})
            return TokenOutputDTO(
                access_token=token,
                refresh_token=refresh_token,
                token_type="bearer",
                client_id=client.id,
                email=client.email,
                age=client.age,
                name=client.name
            )

    @staticmethod
    async def change_password(data: ChangePasswordDTO, current_client: Client) -> dict:
        if not verify_password(data.old_password, current_client.hashed_password):
            raise VerifyPasswordError()
        new_hashed = hash_password(data.new_password)
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(current_client.id)
            if not client:
                raise ClientNotFoundError(current_client.id)
            client.hashed_password = new_hashed
        logger.info("password_changed", extra={"extra_fields": {"client_id": current_client.id}})
        return {"message": "Password changed successfully."}

    @staticmethod
    async def change_role(client_id: int, data: ChangeRoleDTO) -> Client:
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            changed = await uow.client.change_role(client, data)
        logger.info("role_changed", extra={"extra_fields": {"client_id": client_id, "role": data.role.value}})
        return changed

    @staticmethod
    async def verify_email(token: str) -> dict:
        raw = await redis_client.get(f"verify:{token}")
        if not raw:
            raise TokenInvalidError()
        client_id = int(raw)
        async with UnitOfWork() as uow:
            client = await uow.client.get_client(client_id)
            if not client:
                raise ClientNotFoundError(client_id)
            client.is_verified = True
        await redis_client.delete(f"verify:{token}")
        logger.info("email_verified", extra={"extra_fields": {"client_id": client_id}})
        return {
            "message": "Email verified successfully"
        }

    @staticmethod
    async def forgot_password(data: ForgotPasswordDTO):
        async with UnitOfWork() as uow:
            client = await uow.client.get_client_email(data.email)
            if not client:
                raise ClientNotFoundError(email=data.email)
            reset_token = str(uuid.uuid4())
        await redis_client.set(f"reset_token:{reset_token}", client.id, ex=86400)
        send_reset_password_email.delay(client.email, reset_token)
        logger.info("forgot_password_requested", extra={"extra_fields": {"email": data.email}})
        return {
            "message": "Password reset email sent"
        }

    @staticmethod
    async def reset_password(data: ResetPasswordDTO):
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
        logger.info("password_reset", extra={"extra_fields": {"client_id": client_id}})
        return {
            "message": "Password is reset"
        }
