import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"mysql+aiomysql://"
    f"{os.getenv('MYSQL_USER', 'root')}:"
    f"{os.getenv('MYSQL_PASSWORD', '')}@"
    f"{os.getenv('MYSQL_HOST', 'localhost')}:"
    f"{os.getenv('MYSQL_PORT', '3306')}/"
    f"{os.getenv('MYSQL_DB', 'system_design_db')}"
    f"?charset=utf8mb4"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session