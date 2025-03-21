from app.database.session import get_db
from app.routers.v1.schemas import AllFeaturesList, Feature, FeatureCreate
from app.services import feature_flag as feature_flag_svc
from app.utility.exceptions import (DeletingParentFeature,
                                    DuplicateFeatureNameException,
                                    FeatureNotFoundException,
                                    NameLengthLimitException,
                                    NestedChildException, SelfParentException)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/features", tags=["feature"])


# Common function to handle exceptions
def handle_exceptions(exception):
    exception_map = {
        DuplicateFeatureNameException: (409, "Feature with this name already exists"),
        SelfParentException: (400, "Feature cannot be its own parent"),
        FeatureNotFoundException: (404, "Feature or parent feature not found"),
        NestedChildException: (400, "Only one-level relationships allowed)"),
    }
    status_code, detail = exception_map.get(
        type(exception), (500, "Internal server error")
    )
    raise HTTPException(status_code=status_code, detail=detail)


@router.post("/", response_model=Feature)
async def create_feature(feature: FeatureCreate, db: AsyncSession = Depends(get_db)):
    try:
        feature_response = await feature_flag_svc.create_feature(db, feature)
        return feature_response
    except NameLengthLimitException:
        raise HTTPException(status_code=400, detail="Feature name is not within limit")
    except DuplicateFeatureNameException:
        raise HTTPException(
            status_code=409, detail="Feature with this name already exists"
        )
    except SelfParentException:
        raise HTTPException(status_code=400, detail="Feature cannot be its own parent")
    except FeatureNotFoundException:
        raise HTTPException(status_code=404, detail="Parent not found")
    except NestedChildException:
        raise HTTPException(
            status_code=400,
            detail="Parent already has a parent (only one-level relationships allowed)",
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
    feature_id: int, feature_update: FeatureCreate, db: AsyncSession = Depends(get_db)
):
    try:
        return await feature_flag_svc.update_feature(db, feature_id, feature_update)
    except NameLengthLimitException:
        raise HTTPException(status_code=400, detail="Feature name is not within limit")
    except DuplicateFeatureNameException:
        raise HTTPException(
            status_code=409, detail="Feature with this name already exists"
        )
    except SelfParentException:
        raise HTTPException(status_code=400, detail="Feature cannot be its own parent")
    except FeatureNotFoundException:
        raise HTTPException(status_code=404, detail="Feature or Parent not found")
    except NestedChildException:
        raise HTTPException(
            status_code=400,
            detail="Parent or current feature is a parent (only one-level relationships allowed)",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=AllFeaturesList)
async def get_all_features(db: AsyncSession = Depends(get_db)):
    try:
        return await feature_flag_svc.get_all_features(db)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{feature_id}")
async def delete_feature(feature_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await feature_flag_svc.delete_feature(db, feature_id)
    except FeatureNotFoundException:
        raise HTTPException(status_code=404, detail="Feature not found")
    except DeletingParentFeature:
        raise HTTPException(status_code=400, detail="Parent feature can't be deleted")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
