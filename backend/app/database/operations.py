from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import FeatureFlag
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

async def get_feature_by_name(db: AsyncSession, name: str):
    feature = await db.execute(
        select(FeatureFlag).filter(FeatureFlag.name == name)
    )
    return feature.scalar()

async def get_feature_by_id(db: AsyncSession, feature_id: int, with_children: bool = False):
    if with_children:
        feature = await db.execute(
            select(FeatureFlag)
            .options(selectinload(FeatureFlag.children).selectinload(FeatureFlag.children))  # Load nested children
            .filter(FeatureFlag.id == feature_id)
        )
    else:
        feature = await db.execute(
            select(FeatureFlag).filter(FeatureFlag.id == feature_id)
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

async def get_all_db_features(db: AsyncSession, flatten: bool = False):
    if flatten:
        result = await db.execute(select(FeatureFlag))
    else:
        result = await db.execute(
            select(FeatureFlag)
            .options(selectinload(FeatureFlag.children).selectinload(FeatureFlag.children))  # Load nested children
            .filter(FeatureFlag.parent_id == None)
        )

    return result.scalars()

