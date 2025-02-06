import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import FeatureFlag
from app.database.operations import (
    get_feature_by_name,
    get_feature_by_id,
    add_feature,
    get_all_db_features
)

@pytest.mark.asyncio
async def test_get_feature_by_name_not_found(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE"))
    await db_session.commit()

    # Test
    result = await get_feature_by_name(db_session, "nonexistent")
    assert result is None

@pytest.mark.asyncio
async def test_get_feature_by_id_with_children(db_session: AsyncSession):
    # Clear the database
    await db_session.execute(text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE"))
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
    await db_session.execute(text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE"))
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
    await db_session.execute(text("TRUNCATE TABLE feature_flags RESTART IDENTITY CASCADE"))
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
    