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
    try:
        return await feature_flag_svc.get_feature_details(db, feature_id)
    except FeatureNotFoundException:
        raise HTTPException(status_code=404, detail="Feature not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.put("/{feature_id}", response_model=Feature)
async def update_feature(
    feature_id: int, 
    feature_update: FeatureCreate, 
    db: AsyncSession = Depends(get_db)
):
    try:
        return await feature_flag_svc.update_feature(db, feature_id, feature_update)
    except DuplicateFeatureNameException:
        raise HTTPException(status_code=409, detail="Feature with this name already exists")
    except SelfParentException:
        raise HTTPException(status_code=400, detail="Feature cannot be its own parent")
    except FeatureNotFoundException:
        raise HTTPException(status_code=404, detail="Feature or Parent not found")
    except NestedChildException:
        raise HTTPException(status_code=400, detail="Parent or current feature is a parent (only one-level relationships allowed)")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

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