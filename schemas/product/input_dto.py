from pydantic import BaseModel, Field
from typing import Optional
from core.enum import ProductStatus


class ProductCreateDTO(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(0.0, ge=0)
    color: str = Field(..., min_length=1)
    image_url: Optional[str] = None
    quantity: int = Field(0, ge=0)
    description: Optional[str] = None
    category_id: Optional[int] = None


class ProductUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None


class ProductStatusUpdateDTO(BaseModel):
    status: ProductStatus


class ProductGenerateDescriptionDTO(BaseModel):
    product_name: str = Field(..., min_length=1)


class AiChatDTO(BaseModel):
    message: str = Field(..., min_length=1)
