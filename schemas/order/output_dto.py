from pydantic import BaseModel, ConfigDict
from core.enum import OrderStatus


class OrderOutputDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    client_id: int
    status: OrderStatus
