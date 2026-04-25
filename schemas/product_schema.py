from pydantic import BaseModel, ConfigDict
from typing import Optional
from core.enum import ProductStatus


class ProductCreate(BaseModel):
    name: str
    price: float = 0.0
    color: str
    image_url: str | None = None
    quantity: int = 0


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class UpdateProductStatus(BaseModel):
    status: ProductStatus
                        

class ResponseProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    color: str
    status: ProductStatus
    image_url: str | None = None
    quantity: int = 0
