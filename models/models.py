from database.database import Base
from typing import List
from sqlalchemy import ForeignKey, Table, Column, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.enum import SAEnum, TransactionType, OrderStatus


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType, values_callable=lambda x: [e.value for e in x]))
    description: Mapped[str] = mapped_column(nullable=True)
    client: Mapped["Client"] = relationship(back_populates="transactions")
    client_fk: Mapped[int] = mapped_column(ForeignKey("clients.id", name="fk_transaction_client"))


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    age: Mapped[int]
    orders: Mapped[List["Order"]] = relationship(back_populates="client")
    products: Mapped[List["Product"]] = relationship(secondary="client_products", back_populates="clients")
    balance: Mapped[float] = mapped_column(default=0.0)
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="client")
    email: Mapped[str] = mapped_column(nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    
    
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    title: Mapped[str]
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client: Mapped["Client"] = relationship(back_populates="orders")
    products: Mapped[List["Product"]] = relationship(secondary="order_products", back_populates="orders", lazy="selectin")
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, values_callable=lambda x: [e.value for e in x]), 
        default=OrderStatus.create
    )


class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    name: Mapped[str]
    orders: Mapped[List["Order"]] = relationship(secondary="order_products", back_populates="products", lazy="selectin")
    clients: Mapped[List["Client"]] = relationship(secondary="client_products", back_populates="products")
    price: Mapped[float] = mapped_column(default=0.0, nullable=True)


client_products = Table(
    "client_products",
    Base.metadata,
    Column("client_id", ForeignKey("clients.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)


order_products = Table(
    "order_products",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)





