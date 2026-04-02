from fastapi import FastAPI
from database.database import async_engine, Base
from app.router_client import router_client
from app.router_orders import router_order
from app.router_products import router_product
from app.router_transaction import router_transaction
from app.router_auth import router_auth


app = FastAPI()


app.include_router(router_product)
app.include_router(router_client)
app.include_router(router_order)
app.include_router(router_transaction)
app.include_router(router_auth)