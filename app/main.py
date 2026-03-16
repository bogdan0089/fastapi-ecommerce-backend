from fastapi import FastAPI
from database.database import async_engine, Base
from router_client import router_client
from router_orders import router_order
from router_products import router_product
from router_transaction import router_transaction

app = FastAPI()

# Асинхронна ініціалізація бази при старті сервера
@app.on_event("startup")
async def init_models():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")

# Підключаємо роутери
app.include_router(router_product)
app.include_router(router_client)
app.include_router(router_order)
app.include_router(router_transaction)