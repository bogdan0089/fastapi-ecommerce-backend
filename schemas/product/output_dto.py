
from pydantic import BaseModel, ConfigDict

from core.enum import ProductStatus
from schemas.category.output_dto import CategoryOutputDTO


class ProductOutputDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    color: str
    status: ProductStatus
    image_url: str | None = None
    quantity: int = 0
    description: str | None = None
    category: CategoryOutputDTO | None = None


class ProductPageDTO(BaseModel):
    """One page of the catalogue, plus what the screen needs to draw around it.

    `total` counts every product matching the filters, not the page, so the
    client can size its pager without fetching the rest. `price_ceiling` is the
    dearest product the other filters allow, which is where the price slider ends.
    """

    items: list[ProductOutputDTO]
    total: int
    price_ceiling: float
