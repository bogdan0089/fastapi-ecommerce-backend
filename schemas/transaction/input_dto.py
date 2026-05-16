from pydantic import BaseModel, Field
from core.enum import TransactionType


class TransactionCreateDTO(BaseModel):
    amount: float = Field(..., gt=0)
    type: TransactionType
    description: str
    client_fk: int


class PaymentRequestDTO(BaseModel):
    amount: float = Field(..., gt=0)
