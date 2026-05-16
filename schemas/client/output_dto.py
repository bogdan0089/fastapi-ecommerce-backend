from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from core.enum import Role


class ClientOutputDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    age: int
    balance: float
    role: Role
    address: Optional[str] = None


class ClientOrdersCountDTO(BaseModel):
    client_id: int
    orders_count: int
