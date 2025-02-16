import pytest
from app.database.models import FeatureFlag
from app.database.operations import (add_feature, delete_db_feature,
                                     get_all_db_features, get_feature_by_id,
                                     get_feature_by_name)
from app.utility.exceptions import FeatureNotFoundException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_feature_by_name_not_found(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(
        text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE")
    )
    await db_session.commit()

    # Test
    result = await get_feature_by_name(db_session, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_feature_by_id_with_children(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(
        text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE")
    )
    await db_session.commit()

    # Prepare test data
    parent = FeatureFlag(id=1, name="parent", is_enabled=True)
    child = FeatureFlag(id=2, name="child", is_enabled=True, parent_id=1)
    db_session.add_all([parent, child])
    await db_session.commit()

    # Test
    result = await get_feature_by_id(db_session, 1, with_children=True)
    assert len(result.children) == 1


@pytest.mark.asyncio
async def test_add_feature(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(
        text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE")
    )
    await db_session.commit()

    # Prepare test data
    feature = FeatureFlag(name="test", is_enabled=True)
    await add_feature(db_session, feature)

    # Verify
    result = await get_feature_by_id(db_session, feature.id)
    assert result.name == "test"


@pytest.mark.asyncio
async def test_get_all_db_features(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(
        text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE")
    )
    await db_session.commit()

    # Prepare test data
    parent = FeatureFlag(name="parent", is_enabled=True)
    child = FeatureFlag(name="child", is_enabled=True, parent=parent)
    db_session.add_all([parent, child])
    await db_session.commit()

    # Test
    result = await get_all_db_features(db_session)
    assert len(result) == 1  # Only parent returned
    assert len(result[0].children) == 1


@pytest.mark.asyncio
async def test_delete_db_feature(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(
        text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE")
    )
    await db_session.commit()

    # Prepare test data
    parent = FeatureFlag(id=1, name="parent", is_enabled=True)
    child = FeatureFlag(id=2, name="child", is_enabled=True, parent=parent)
    db_session.add_all([parent, child])
    await db_session.commit()

    # Test
    with pytest.raises(FeatureNotFoundException):
        await delete_db_feature(db_session, feature_id=3)  # id=3 feature doesn't exists

    with pytest.raises(IntegrityError):
        await delete_db_feature(
            db_session, feature_id=1
        )  # id=1 is a parent, hence can't delete

    await delete_db_feature(db_session, feature_id=2)  # id=2 can be deleted safely
    await delete_db_feature(
        db_session, feature_id=1
    )  # now id=1 is no more parent since id=2 is deleted
