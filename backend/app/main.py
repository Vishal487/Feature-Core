from fastapi import FastAPI
from app.database.session import engine, get_db
from app.database.models import FeatureFlag
from app.routers.v1 import feature_flag


app = FastAPI()

# Include routers
app.include_router(feature_flag.router, prefix="/features", tags=["features"])

# Create tables (for development only)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(FeatureFlag.metadata.create_all)