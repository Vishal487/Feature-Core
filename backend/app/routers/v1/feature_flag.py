from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import FeatureFlag
from app.routers.v1.schemas import FeatureCreate, Feature
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.utility.utils import normalize_name, denormalize_name

router = APIRouter()



async def validate_parent(db: AsyncSession, parent_id: int, current_feature_id: int = None):
    # Rule 1: A feature can't be its own parent
    if parent_id and parent_id == current_feature_id:
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


# async def get_children(db: AsyncSession, parent_id: int):
#     result = await db.execute(select(FeatureFlag).filter(FeatureFlag.parent_id == parent_id))
#     return result.scalars().all()


@router.post("/", response_model=Feature)
async def create_feature(feature: FeatureCreate, db: AsyncSession = Depends(get_db)):
    # Normalize the feature name
    normalized_name = normalize_name(feature.name)

    # Check if a feature with the same name already exists
    existing_feature = await db.execute(
        select(FeatureFlag).filter(FeatureFlag.name == normalized_name)
    )
    if existing_feature.scalar():
        raise HTTPException(
            status_code=409,
            detail="Feature with this name already exists"
        )

    # Validate parent rules
    await validate_parent(db, feature.parent_id)
    
    # Create feature with normalized name
    db_feature = FeatureFlag(
        name=normalized_name,
        is_enabled=feature.is_enabled,
        parent_id=feature.parent_id
    )
    # add to db
    db.add(db_feature)
    await db.commit()

    # Refresh the feature to load relationships (eagerly load children)
    # this is to load refresh the 'db_feature' object. So it is required to fetch the latest from db
    # This is required to fetch the auto-generated fields, for eg. 'id' and 'children'. So if not required, we can skip.
    await db.refresh(db_feature, ["children"])
    
    # Convert SQLAlchemy model to Pydantic model
    feature_response = Feature.model_validate(db_feature)
    
    # Denormalize names for response
    feature_response.name = denormalize_name(db_feature.name)
    for child in feature_response.children:
        child.name = denormalize_name(child.name)
    
    return feature_response

@router.get("/{feature_id}", response_model=Feature)
async def get_feature_details(feature_id: int, db: AsyncSession = Depends(get_db)):
    # Fetch existing feature with children eagerly loaded
    result = await db.execute(
        select(FeatureFlag)
        .options(selectinload(FeatureFlag.children).selectinload(FeatureFlag.children))  # Load nested children
        .filter(FeatureFlag.id == feature_id)
    )
    db_feature = result.scalar()
    
    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Convert SQLAlchemy model to Pydantic model
    feature_response = Feature.model_validate(db_feature)
    
    # Denormalize names for response
    feature_response.name = denormalize_name(db_feature.name)
    for child in feature_response.children:
        child.name = denormalize_name(child.name)
    
    return feature_response

@router.put("/{feature_id}", response_model=Feature)
async def update_feature(
    feature_id: int, 
    feature_update: FeatureCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Fetch existing feature with children eagerly loaded
    result = await db.execute(
        select(FeatureFlag)
        .options(selectinload(FeatureFlag.children).selectinload(FeatureFlag.children))  # Load nested children
        .filter(FeatureFlag.id == feature_id)
    )
    db_feature = result.scalar()
    
    if not db_feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Check if a feature with the same name already exists, if name is being updated
    new_normalized_name = normalize_name(feature_update.name)
    if new_normalized_name != db_feature.name:
        existing_feature = await db.execute(
            select(FeatureFlag).filter(FeatureFlag.name == new_normalized_name)
        )
        if existing_feature.scalar():
            raise HTTPException(
                status_code=409,
                detail="Feature with this name already exists"
            )

    # Validate parent rules (include current_feature_id to check self-parenting)
    await validate_parent(db, feature_update.parent_id, current_feature_id=feature_id)

    # Update fields
    for key, value in feature_update.model_dump().items():
        setattr(db_feature, key, value)
    db_feature.name = new_normalized_name

    # update children status same as parent status
    for child in db_feature.children:
        child: Feature
        child.is_enabled = db_feature.is_enabled
    
    await db.commit()
    
    # Refresh the feature to load relationships (eagerly load children)
    await db.refresh(db_feature, ["children"])
    
    # Convert SQLAlchemy model to Pydantic model
    feature_response = Feature.model_validate(db_feature)
    
    # Denormalize names for response
    feature_response.name = denormalize_name(db_feature.name)
    for child in feature_response.children:
        child.name = denormalize_name(child.name)
    
    return feature_response