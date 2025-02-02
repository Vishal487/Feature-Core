from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import FeatureFlag
from app.routers.v1.schemas import AllFeaturesList, FeatureCreate, Feature
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.utility.utils import normalize_name, denormalize_name
from app.utility.exceptions import DBIntegrityError, DuplicateFeatureNameException, FeatureNotFoundException, NestedChildException, SelfParentException



async def get_feature_by_name(db: AsyncSession, name: str):
    feature = await db.execute(
        select(FeatureFlag).filter(FeatureFlag.name == name)
    )
    return feature.scalar()

async def get_feature_by_id(db: AsyncSession, id: int):
    feature = await db.execute(
        select(FeatureFlag).filter(FeatureFlag.id == id)
    )
    return feature.scalar()

async def add_feature(db: AsyncSession, db_feature: FeatureFlag):
    # add to db
    db.add(db_feature)
    await db.commit()

    # Refresh the feature to load relationships (eagerly load children)
    # this is to refresh the 'db_feature' object. So it is required to fetch the latest from db.
    # This is required to fetch the auto-generated fields, for eg. 'id' and 'children'. So if not required, we can skip.
    await db.refresh(db_feature, ["children"])
