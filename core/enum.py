from enum import Enum


class OrderStatus(Enum):
    create = "create"
    completed = "completed"
    cancelled = "cancelled"

class ProductStatus(Enum):
    pending = "pending"
    accept = "accept"
    rejected = "rejected"

class TransactionType(Enum):
    deposit = "deposit"
    withdraw = "withdraw"
    refund = "refund"
    purchase = "purchase"

class Role(Enum):
    superadmin = "superadmin"
    moderator = "moderator"
    client = "client"
