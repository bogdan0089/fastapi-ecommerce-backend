from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core import DATABASE_URL



async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = sessionmaker(class_=AsyncSession, bind=async_engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_session():
    async with async_session_maker() as session:
        yield session




