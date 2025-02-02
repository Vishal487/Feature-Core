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


async def validate_parent(db: AsyncSession, parent_id: int, current_feature_id: int = None):
    # Rule 1: A feature can't be its own parent
    if parent_id and parent_id == current_feature_id:
        raise SelfParentException()
    
    # Rule 2: Parent must exist (if provided)
    if parent_id is not None:
        parent = await db.get(FeatureFlag, parent_id)
        if not parent:
            raise FeatureNotFoundException()
        
        # Rule 3: Parent must not have its own parent (no nested relationships)
        if parent.parent_id is not None:
            raise NestedChildException()

async def check_feature_name_exists(db: AsyncSession, name: str):
    # Check if a feature with the same name already exists
    existing_feature = await db.execute(
        select(FeatureFlag).filter(FeatureFlag.name == name)
    )
    if existing_feature.scalar():
        return True
    return False

def dernomalize_feature_and_children_names(feature: Feature):
    # Denormalize names for response
    feature.name = denormalize_name(feature.name)
    for child in feature.children:
        child.name = denormalize_name(child.name)

async def create_feature(db: AsyncSession, feature: FeatureCreate):
    try:
        # Normalize the feature name
        normalized_name = normalize_name(feature.name)

        # Check if a feature with the same name already exists
        if await check_feature_name_exists(db, normalized_name):
            raise DuplicateFeatureNameException()
        
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
        dernomalize_feature_and_children_names(feature_response)
        
        return feature_response
    except IntegrityError as e:
        await db.rollback()
        raise DBIntegrityError()