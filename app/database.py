from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.logger import log


async_engine = None
AsyncSessionLocal = None


def get_database_url() -> str:
    url = settings.database_url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "sslmode" not in url:
        url += "&sslmode=require" if "?" in url else "?sslmode=require"
    return url


async def init_database():
    global async_engine, AsyncSessionLocal

    database_url = get_database_url()
    log.info(f"Initializing database connection...")

    async_engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    log.info("Database schema initialized")


async def get_session() -> AsyncSession:
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_database():
    global async_engine
    if async_engine:
        await async_engine.dispose()
        log.info("Database connection pool closed")


class Base(DeclarativeBase):
    pass
