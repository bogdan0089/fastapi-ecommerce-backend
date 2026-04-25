from sqlalchemy import Column, Enum as SAEnum, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.enum import OrderStatus, TransactionType, Role, ProductStatus
from database.database import Base


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        SAEnum(TransactionType, values_callable=lambda x: [e.value for e in x])
    )
    description: Mapped[str | None] = mapped_column(nullable=True)
    client_fk: Mapped[int] = mapped_column(ForeignKey("clients.id", name="fk_transaction_client"))
    client: Mapped["Client"] = relationship(back_populates="transactions")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    age: Mapped[int]
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    balance: Mapped[float] = mapped_column(default=0.0)
    orders: Mapped[list["Order"]] = relationship(back_populates="client")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="client")
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    address: Mapped[str] = mapped_column(nullable=True)
    role: Mapped[Role] = mapped_column(SAEnum(Role, values_callable=lambda x: [e.value for e in x]),
        default=Role.client,
    )
    products: Mapped[list["Product"]] = relationship(
        secondary="client_products", back_populates="clients"
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.create,
    )
    client: Mapped["Client"] = relationship(back_populates="orders")
    order_products: Mapped[list["OrderProduct"]] = relationship(
        back_populates="order", lazy="selectin"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float] = mapped_column(default=0.0)
    color: Mapped[str]
    status: Mapped[ProductStatus] = mapped_column(
        SAEnum(ProductStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProductStatus.pending
    )
    image_url: Mapped[str | None] = mapped_column(nullable=True)
    quantity: Mapped[int] = mapped_column(default=0)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    category: Mapped["Category | None"] = relationship(back_populates="products")
    order_products: Mapped[list["OrderProduct"]] = relationship(
        back_populates="product"
    )
    clients: Mapped[list["Client"]] = relationship(
        secondary="client_products", back_populates="products"
    )


class OrderProduct(Base):
    __tablename__ = "order_products"
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(default=1)
    order: Mapped["Order"] = relationship(back_populates="order_products")
    product: Mapped["Product"] = relationship(back_populates="order_products", lazy="selectin")



class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    products: Mapped[list["Product"]] = relationship(back_populates="category")



client_products = Table(
    "client_products",
    Base.metadata,
    Column("client_id", ForeignKey("clients.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)
