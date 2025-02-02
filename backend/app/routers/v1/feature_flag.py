from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import FeatureFlag
from app.routers.v1.schemas import AllFeaturesList, FeatureCreate, Feature
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.utility.utils import normalize_name, denormalize_name
from app.services import feature_flag as feature_flag_svc
from app.utility.exceptions import DuplicateFeatureNameException, FeatureNotFoundException, NestedChildException, SelfParentException

router = APIRouter()


@router.post("/", response_model=Feature)
async def create_feature(feature: FeatureCreate, db: AsyncSession = Depends(get_db)):
    try:
        feature_response = await feature_flag_svc.create_feature(db, feature)
        return feature_response
    except DuplicateFeatureNameException:
        raise HTTPException(
                status_code=409,
                detail="Feature with this name already exists"
            )
    except SelfParentException:
        raise HTTPException(status_code=400, detail="Feature cannot be its own parent")
    except FeatureNotFoundException:
        raise HTTPException(status_code=404, detail="Parent not found")
    except NestedChildException:
        raise HTTPException(
                status_code=400,
                detail="Parent already has a parent (only one-level relationships allowed)"
            )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{feature_id}", response_model=Feature)
async def get_feature_details(feature_id: int, db: AsyncSession = Depends(get_db)):
    # Fetch feature with children eagerly loaded
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
    try:
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
        await feature_flag_svc.validate_parent(db, feature_update.parent_id, current_feature_id=feature_id)

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
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid parent-child relationship (self parenting)"
        )


@router.get("", response_model=AllFeaturesList)
async def get_all_features(db: AsyncSession = Depends(get_db)):
    # fetch all the parent features only, i.e. parent_id == null
    # because we will anyway get all the children (because of use of selectinload)
    # two advantages:
    #   1. no duplicates. Child will only appear at 2nd level
    #   2. we will get the child in nested manner which will be helpful

    result = await db.execute(
        select(FeatureFlag)
        .options(selectinload(FeatureFlag.children).selectinload(FeatureFlag.children))  # Load nested children
        .filter(FeatureFlag.parent_id == None)
    )
    all_db_features = result.scalars()

    # Convert SQLAlchemy model to Pydantic model
    # Denormalize names in the same loop
    all_features_response = AllFeaturesList(features=[])
    for db_feature in all_db_features:
        feature_response = Feature.model_validate(db_feature)

        # denormalize name for feature_response
        feature_response.name = denormalize_name(db_feature.name)
        for child in feature_response.children:
            child.name = denormalize_name(child.name)
        
        # add to the final response
        all_features_response.features.append(feature_response)


    return all_features_response