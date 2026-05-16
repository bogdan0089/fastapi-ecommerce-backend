from pydantic import BaseModel, ConfigDict
from typing import Optional
from core.enum import ProductStatus
from schemas.category.output_dto import CategoryOutputDTO


class ProductOutputDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    color: str
    status: ProductStatus
    image_url: Optional[str] = None
    quantity: int = 0
    description: Optional[str] = None
    category: Optional[CategoryOutputDTO] = None
