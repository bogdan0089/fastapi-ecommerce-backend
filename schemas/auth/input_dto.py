from pydantic import BaseModel, EmailStr
from core.enum import Role


class RefreshRequestDTO(BaseModel):
    refresh_token: str


class ChangePasswordDTO(BaseModel):
    old_password: str
    new_password: str


class ChangeRoleDTO(BaseModel):
    role: Role


class ResetPasswordDTO(BaseModel):
    reset_token: str
    new_password: str


class ForgotPasswordDTO(BaseModel):
    email: EmailStr
