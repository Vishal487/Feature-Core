import os

# from dotenv import load_dotenv
from app.database.models import Base  # Import Base from models
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# load_dotenv()

DEFAULT_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/feature_core"
DATABASE_URL = os.getenv("DATABASE_URL", default=DEFAULT_DB_URL)

print("db_uri: ", DATABASE_URL)

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Create tables (optional, for startup)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
