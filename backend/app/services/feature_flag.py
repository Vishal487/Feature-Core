from app.database.models import FeatureFlag
from app.database.operations import (add_feature, delete_db_feature,
                                     get_all_db_features, get_feature_by_id,
                                     get_feature_by_name)
from app.routers.v1.schemas import AllFeaturesList, Feature, FeatureCreate
from app.services.constants import (FEATURE_NAME_LOWER_LIMIT,
                                    FEATURE_NAME_UPPER_LIMIT)
from app.utility.exceptions import (DBIntegrityError, DeletingParentFeature,
                                    DuplicateFeatureNameException,
                                    FeatureNotFoundException,
                                    NameLengthLimitException,
                                    NestedChildException, SelfParentException)
from app.utility.utils import denormalize_name, normalize_name
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


async def validate_parent(
    db: AsyncSession, parent_id: int, db_feature_with_children: FeatureFlag = None
):
    # Rule 1: A feature can't be its own parent
    if (
        parent_id
        and db_feature_with_children
        and parent_id == db_feature_with_children.id
    ):
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
        if feature.name:
            feature.name = feature.name.strip()
        if (not feature.name) or (
            len(feature.name) < FEATURE_NAME_LOWER_LIMIT
            or len(feature.name) > FEATURE_NAME_UPPER_LIMIT
        ):
            raise NameLengthLimitException()

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
            parent_id=feature.parent_id,
        )
        await add_feature(db, db_feature)

        # Convert SQLAlchemy model to Pydantic model
        feature_response = Feature.model_validate(db_feature)

        # Denormalize names for response
        dernomalize_feature_and_children_names(feature_response)

        return feature_response
    except IntegrityError:
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


async def update_feature(
    db: AsyncSession, feature_id: int, feature_update: FeatureCreate
):
    try:
        if feature_update.name:
            feature_update.name = feature_update.name.strip()
        if (not feature_update.name) or (
            len(feature_update.name) < FEATURE_NAME_LOWER_LIMIT
            or len(feature_update.name) > FEATURE_NAME_UPPER_LIMIT
        ):
            raise NameLengthLimitException()

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
        await validate_parent(
            db, feature_update.parent_id, db_feature_with_children=db_feature
        )

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
    except IntegrityError:
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
    all_features_response.features.sort(key=lambda feat: feat.name)
    # sort children
    for feature in all_features_response.features:
        if feature.children:
            feature.children.sort(key=lambda feat: feat.name)

    return all_features_response


async def delete_feature(db: AsyncSession, feature_id: int):
    # check if feature exists
    # db_feature = await get_feature_by_id(db, feature_id, with_children=True)
    # if not db_feature:
    #     raise FeatureNotFoundException()

    # check if feature has some children
    # if db_feature.children:
    #     raise DeletingParentFeature()

    # Just one db call now

    # now delete
    try:
        await delete_db_feature(db, feature_id)
    except IntegrityError:
        # will be raised when we try to delete a parent feature (because of foreign contraint on the same table)
        raise DeletingParentFeature()
