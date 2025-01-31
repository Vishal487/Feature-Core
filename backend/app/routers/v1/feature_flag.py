from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import FeatureFlag
from app.routers.v1.schemas import FeatureCreate, Feature
from sqlalchemy.future import select

router = APIRouter()



async def validate_parent(db: AsyncSession, parent_id: int, current_feature_id: int = None):
    # Rule 1: A feature can't be its own parent
    if parent_id == current_feature_id:
        raise HTTPException(status_code=400, detail="Feature cannot be its own parent")
    
    # Rule 2: Parent must exist (if provided)
    if parent_id is not None:
        parent = await db.get(FeatureFlag, parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent not found")
        
        # Rule 3: Parent must not have its own parent (no nested relationships)
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Parent already has a parent (only one-level relationships allowed)"
            )


async def get_children(db: AsyncSession, parent_id: int):
    result = await db.execute(select(FeatureFlag).filter(FeatureFlag.parent_id == parent_id))
    return result.scalars().all()


@router.post("/", response_model=Feature)
async def create_feature(feature: FeatureCreate, db: AsyncSession = Depends(get_db)):
    # Validate parent rules
    await validate_parent(db, feature.parent_id)
    
    # Create feature
    db_feature = FeatureFlag(**feature.model_dump())
    db.add(db_feature)
    await db.commit()
    await db.refresh(db_feature)
    return db_feature

@router.get("/{feature_id}", response_model=Feature)
async def read_feature(feature_id: int, db: AsyncSession = Depends(get_db)):
    feature = await db.get(FeatureFlag, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Get children recursively
    feature.children = await get_children(db, feature_id)
    return feature

@router.put("/{feature_id}", response_model=Feature)
async def update_feature(
    feature_id: int, 
    feature_update: FeatureCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Fetch existing feature
    db_feature = await db.get(FeatureFlag, feature_id)
    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Validate parent rules (include current_feature_id to check self-parenting)
    await validate_parent(db, feature_update.parent_id, current_feature_id=feature_id)

    # Update fields
    for key, value in feature_update.model_dump().items():
        setattr(db_feature, key, value)
    
    await db.commit()
    await db.refresh(db_feature)
    return db_feature