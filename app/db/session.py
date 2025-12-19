from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.security.vault_client import vault_client, get_db_credentials
from sqlalchemy.exc import OperationalError, DBAPIError
import asyncio

_engine_lock = asyncio.Lock()
engine = None
AsyncSessionLocal = None


async def init_db_engine():
    global engine, AsyncSessionLocal

    async with _engine_lock:
        if engine is not None:
            return

        creds = await get_db_credentials()

        db_url = (
            f"postgresql+asyncpg://{creds['username']}:"
            f"{creds['password']}@db:5432/synapse"
        )

        engine = create_async_engine(
            db_url,
            pool_pre_ping=True,
            future=True,
            echo=False,
        )

        AsyncSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

async def get_async_session():
    """Dependency injected into FastAPI routes."""
    global AsyncSessionLocal

    if AsyncSessionLocal is None:
        await init_db_engine()

    try:
        async with AsyncSessionLocal() as session:
            yield session

    except (OperationalError, DBAPIError) as exc:
        # Likely expired / revoked Vault DB credentials
        await reset_db_engine()
        raise exc


async def reset_db_engine():
    global engine, AsyncSessionLocal

    async with _engine_lock:
        if engine is not None:
            await engine.dispose()
            engine = None
            AsyncSessionLocal = None

        await init_db_engine()