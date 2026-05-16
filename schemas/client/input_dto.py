from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional


class ClientCreateDTO(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str
    age: int = Field(..., gt=0)

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


class ClientUpdateDTO(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., gt=0)
    address: Optional[str] = None


class ClientBalanceOperationDTO(BaseModel):
    amount: float = Field(..., gt=0)
