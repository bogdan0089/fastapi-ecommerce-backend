from pydantic import BaseModel, ConfigDict
from core.enum import TransactionType


class TransactionOutputDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    type: TransactionType
    description: str
    client_fk: int
