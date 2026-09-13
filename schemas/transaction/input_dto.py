from decimal import Decimal

from pydantic import BaseModel, Field

from core.enum import TransactionType


class TransactionCreateDTO(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    type: TransactionType
    description: str
    client_fk: int


class PaymentRequestDTO(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
