from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from core.enum import Role
from typing import Optional


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: int

    @field_validator("password")
    @classmethod
    def validate_password(cls, p: str) -> str:
        if len(p) < 8:
            raise ValueError("Password must be at least 8 characters")
        return p
            
    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class ClientUpdate(BaseModel):
    name: str
    age: int
    address: Optional[str] = None


class ResponseClient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    age: int
    balance: float
    role: Role
    address: Optional[str] = None 

class ClientOrdersCount(BaseModel):
    client_id: int
    orders_count: int


class OperationsRequest(BaseModel):
    amount: float
