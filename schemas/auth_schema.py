from pydantic import BaseModel
from core.enum import Role


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    client_id: int
    email: str
    age: int
    name: str

class RefreshResponse(BaseModel):
    access_token: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class ChangeRole(BaseModel):
    role: Role

class ResetPassword(BaseModel):
    reset_token: str
    new_password: str

class ForgotPassword(BaseModel):
    email: str
