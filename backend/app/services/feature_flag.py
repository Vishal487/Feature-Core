from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import FeatureFlag
from app.routers.v1.schemas import AllFeaturesList, FeatureCreate, Feature
from sqlalchemy.exc import IntegrityError

from app.utility.utils import normalize_name, denormalize_name
from app.utility.exceptions import DBIntegrityError, DuplicateFeatureNameException, FeatureNotFoundException, NestedChildException, SelfParentException
from app.database.operations import add_feature, get_feature_by_id, get_feature_by_name, get_all_db_features


async def validate_parent(db: AsyncSession, parent_id: int, db_feature_with_children: FeatureFlag = None):
    # Rule 1: A feature can't be its own parent
    if parent_id and db_feature_with_children and parent_id == db_feature_with_children.id:
        raise SelfParentException()
    
    # Rule 2: Parent must exist (if provided)
    if parent_id is not None:
        parent = await get_feature_by_id(db, parent_id)
        if not parent:
            raise FeatureNotFoundException()
        
        # Rule 3: Parent must not have its own parent (no nested relationships)
        if parent.parent_id is not None:
            raise NestedChildException()
    
    # Rule 4: current feature should not be a parent of any other feature. Basically it shouldn't have any child
    if parent_id and db_feature_with_children and db_feature_with_children.children:
        raise NestedChildException()

async def check_feature_name_exists(db: AsyncSession, name: str):
    # Check if a feature with the same name already exists
    existing_feature = await get_feature_by_name(db, name)
    if existing_feature:
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
        await add_feature(db, db_feature)

        # Convert SQLAlchemy model to Pydantic model
        feature_response = Feature.model_validate(db_feature)
        
        # Denormalize names for response
        dernomalize_feature_and_children_names(feature_response)
        
        return feature_response
    except IntegrityError as e:
        await db.rollback()
        raise DBIntegrityError()

async def get_feature_details(db: AsyncSession, feature_id: int):
    db_feature = await get_feature_by_id(db, feature_id, with_children=True)
    if not db_feature:
        raise FeatureNotFoundException()
    
    # Convert SQLAlchemy model to Pydantic model
    feature_response = Feature.model_validate(db_feature)

    # Denormalize names for response
    dernomalize_feature_and_children_names(feature_response)
    
    return feature_response

async def update_feature(db: AsyncSession, feature_id: int, feature_update: FeatureCreate):
    try:   
        db_feature = await get_feature_by_id(db, feature_id, with_children=True)
        if not db_feature:
            raise FeatureNotFoundException()
        
        # Check if a feature with the same name already exists, if name is being updated
        # TODO: see if we can combine this with above db query
        new_normalized_name = normalize_name(feature_update.name)
        if new_normalized_name != db_feature.name:
            existing_feature = await get_feature_by_name(db, new_normalized_name)
            if existing_feature:
                raise DuplicateFeatureNameException()
        
        # Validate parent rules (include current_feature_id to check self-parenting)
        await validate_parent(db, feature_update.parent_id, db_feature_with_children=db_feature)

        # update children status same as parent status iff (<=>) parent status is being modified
        # we need to do it before updating the db_feature object with feature_update
        if db_feature.is_enabled != feature_update.is_enabled:
            for child in db_feature.children:
                child: Feature
                child.is_enabled = feature_update.is_enabled

        # Update fields
        for key, value in feature_update.model_dump().items():
            setattr(db_feature, key, value)
        db_feature.name = new_normalized_name
        
        await db.commit()
        
        # Refresh the feature to load relationships (eagerly load children)
        await db.refresh(db_feature, ["children"])
        
        # Convert SQLAlchemy model to Pydantic model
        feature_response = Feature.model_validate(db_feature)

        # Denormalize names for response
        dernomalize_feature_and_children_names(feature_response)
        
        return feature_response    
    except IntegrityError as e:
        await db.rollback()
        raise DBIntegrityError()

async def get_all_features(db: AsyncSession):
    # fetch all the parent features only, i.e. parent_id == null
    # because we will anyway get all the children (because of use of selectinload)
    # two advantages:
    #   1. no duplicates. Child will only appear at 2nd level
    #   2. we will get the child in nested manner which will be helpful

    all_db_features = await get_all_db_features(db)

    # Convert SQLAlchemy model to Pydantic model
    # Denormalize names in the same loop
    all_features_response = AllFeaturesList(features=[])
    for db_feature in all_db_features:
        feature_response = Feature.model_validate(db_feature)

        # denormalize name for feature_response
        dernomalize_feature_and_children_names(feature_response)

        # add to the final response
        all_features_response.features.append(feature_response)
    
    # sort by name
    all_features_response.features.sort(key = lambda feat: feat.name)
    # sort children
    for feature in all_features_response.features:
        if feature.children:
            feature.children.sort(key = lambda feat: feat.name)

    return all_features_response
