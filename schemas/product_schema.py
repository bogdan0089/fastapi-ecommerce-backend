from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    price: float = 0.0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class ResponseProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
