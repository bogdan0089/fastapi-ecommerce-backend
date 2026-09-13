
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.validators import Password


class ClientCreateDTO(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: Password
    age: int = Field(..., gt=0)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class ClientUpdateDTO(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., gt=0)
    address: str | None = None


class ClientBalanceOperationDTO(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
