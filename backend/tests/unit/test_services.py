import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import feature_flag as feature_flag_svc
from app.routers.v1.schemas import FeatureCreate
from app.utility.exceptions import (
    DeletingParentFeature,
    DuplicateFeatureNameException,
    SelfParentException,
    FeatureNotFoundException,
    NestedChildException
)

import asyncio
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

# Import your service functions and exceptions
from app.services.feature_flag import (
    delete_feature,
    validate_parent,
    check_feature_name_exists,
    dernomalize_feature_and_children_names,
    create_feature,
    get_feature_details,
    update_feature,
    get_all_features
)
from app.database.models import FeatureFlag
from app.routers.v1.schemas import FeatureCreate, Feature, AllFeaturesList
from app.utility.exceptions import (
    DBIntegrityError,
    DuplicateFeatureNameException,
    FeatureNotFoundException,
    NestedChildException,
    SelfParentException
)
from app.utility.utils import normalize_name, denormalize_name

# ------------------------------------------------------------
# Test class for validate_parent
# ------------------------------------------------------------
class TestValidateParent:
    @pytest.mark.asyncio
    async def test_self_parent_raises_exception(self, monkeypatch):
        # When parent_id equals the current feature id, should raise SelfParentException
        fake_feature = FeatureFlag(id=1, name="feat", is_enabled=True)
        with pytest.raises(SelfParentException):
            await validate_parent(AsyncMock(), 1, db_feature_with_children=fake_feature)

    @pytest.mark.asyncio
    async def test_parent_not_found_raises_exception(self, monkeypatch):
        # If parent_id is provided but get_feature_by_id returns None
        async def fake_get_feature_by_id(db, parent_id, **kwargs):
            return None
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", fake_get_feature_by_id)
        with pytest.raises(FeatureNotFoundException):
            await validate_parent(AsyncMock(), 2)

    @pytest.mark.asyncio
    async def test_parent_with_own_parent_raises_exception(self, monkeypatch):
        # Parent exists but its parent_id is not None => NestedChildException
        fake_parent = FeatureFlag(id=2, name="parent", is_enabled=True, parent_id=1)
        async def fake_get_feature_by_id(db, parent_id, **kwargs):
            return fake_parent
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", fake_get_feature_by_id)
        with pytest.raises(NestedChildException):
            await validate_parent(AsyncMock(), 2)

    @pytest.mark.asyncio
    async def test_current_feature_has_children_raises_exception(self, monkeypatch):
        # Current feature already has children and a parent_id is provided => NestedChildException
        fake_feature = FeatureFlag(id=3, name="child", is_enabled=True, parent_id=2)
        # Simulate that the current feature has children
        fake_feature.children = [FeatureFlag(id=4, name="grandchild", is_enabled=True)]
        async def fake_get_feature_by_id(db, parent_id, **kwargs):
            # Return a valid parent with no parent_id
            return FeatureFlag(id=2, name="parent", is_enabled=True, parent_id=None)
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", fake_get_feature_by_id)
        with pytest.raises(NestedChildException):
            await validate_parent(AsyncMock(), 2, db_feature_with_children=fake_feature)

    @pytest.mark.asyncio
    async def test_validate_parent_success(self, monkeypatch):
        # Valid scenario: parent_id provided, parent exists, and parent's parent_id is None
        fake_parent = FeatureFlag(id=2, name="parent", is_enabled=True, parent_id=None)
        async def fake_get_feature_by_id(db, parent_id, **kwargs):
            return fake_parent
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", fake_get_feature_by_id)
        # Should not raise any exception
        await validate_parent(AsyncMock(), 2)

# ------------------------------------------------------------
# Test class for check_feature_name_exists
# ------------------------------------------------------------
class TestCheckFeatureNameExists:
    @pytest.mark.asyncio
    async def test_feature_not_exists(self, monkeypatch):
        # When get_feature_by_name returns None, expect False
        async def fake_get_feature_by_name(db, name):
            return None
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_name", fake_get_feature_by_name)
        result = await check_feature_name_exists(AsyncMock(), "somefeature")
        assert result is False

    @pytest.mark.asyncio
    async def test_feature_exists(self, monkeypatch):
        # When get_feature_by_name returns a feature, expect True
        fake_feature = FeatureFlag(id=1, name="somefeature", is_enabled=True)
        async def fake_get_feature_by_name(db, name):
            return fake_feature
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_name", fake_get_feature_by_name)
        result = await check_feature_name_exists(AsyncMock(), "somefeature")
        assert result is True

# ------------------------------------------------------------
# Test class for dernomalize_feature_and_children_names
# ------------------------------------------------------------
class TestDernormalizeFeatureAndChildrenNames:
    def test_dernormalize_feature_and_children_names(self, monkeypatch):
        # Create a Feature instance with a child
        feature = Feature(
            id=1,
            name="parent_feature_name",
            is_enabled=True,
            parent_id=None,
            children=[Feature(id=2, name="child_feature_1", is_enabled=False, parent_id=1, children=[])]
        )
        # Call the function to update names
        dernomalize_feature_and_children_names(feature)
        assert feature.name == "Parent Feature Name"
        assert feature.children[0].name == "Child Feature 1"

# ------------------------------------------------------------
# Test class for create_feature
# ------------------------------------------------------------
class TestCreateFeature:
    @pytest.mark.asyncio
    async def test_create_feature_success(self, monkeypatch, db_session: AsyncMock):
        # Prepare a FeatureCreate input
        feature_in = FeatureCreate(name="New Feature", is_enabled=True, parent_id=None)
        normalized_name = "new_feature"

        # Patch check_feature_name_exists to return False (feature does not exist)
        monkeypatch.setattr("app.services.feature_flag.check_feature_name_exists", AsyncMock(return_value=False))
        # Patch validate_parent (assume it passes)
        monkeypatch.setattr("app.services.feature_flag.validate_parent", AsyncMock(return_value=None))
        # Patch add_feature to simulate DB insert (no return value, but updates db_feature with an id)
        async def fake_add_feature(db, db_feature):
            db_feature.id = 1
        monkeypatch.setattr("app.services.feature_flag.add_feature", fake_add_feature)
        # Create a fake db_session that supports commit and refresh
        fake_db_session = db_session  # Assume this is an AsyncMock representing AsyncSession

        # Call create_feature
        result = await create_feature(fake_db_session, feature_in)

        # Check that the returned feature has the normalized name and an id
        assert result.id == 1
        assert result.name == "New Feature"  # denormalization may change it, but for simplicity

    @pytest.mark.asyncio
    async def test_create_feature_duplicate_name(self, monkeypatch, db_session: AsyncMock):
        feature_in = FeatureCreate(name="Duplicate Feature", is_enabled=True, parent_id=None)
        # Patch check_feature_name_exists to return True
        monkeypatch.setattr("app.services.feature_flag.check_feature_name_exists", AsyncMock(return_value=True))
        with pytest.raises(DuplicateFeatureNameException):
            await create_feature(db_session, feature_in)

    @pytest.mark.asyncio
    async def test_create_feature_integrity_error(self, monkeypatch, db_session: AsyncMock):
        feature_in = FeatureCreate(name="Feature", is_enabled=True, parent_id=None)
        monkeypatch.setattr("app.services.feature_flag.check_feature_name_exists", AsyncMock(return_value=False))
        monkeypatch.setattr("app.services.feature_flag.validate_parent", AsyncMock(return_value=None))
        # Simulate IntegrityError by raising it in add_feature
        async def fake_add_feature(db, db_feature):
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("error", None, None)
        monkeypatch.setattr("app.services.feature_flag.add_feature", fake_add_feature)
        with pytest.raises(DBIntegrityError):
            await create_feature(db_session, feature_in)

# ------------------------------------------------------------
# Test class for get_feature_details
# ------------------------------------------------------------
class TestGetFeatureDetails:
    @pytest.mark.asyncio
    async def test_get_feature_details_not_found(self, monkeypatch, db_session: AsyncMock):
        # Patch get_feature_by_id to return None
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=None))
        with pytest.raises(FeatureNotFoundException):
            await get_feature_details(db_session, feature_id=999)

    @pytest.mark.asyncio
    async def test_get_feature_details_success(self, monkeypatch, db_session: AsyncMock):
        # Create a fake db feature with children
        fake_db_feature = FeatureFlag(id=1, name="test", is_enabled=True, parent_id=None)
        fake_db_feature.children = []
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=fake_db_feature))
        result = await get_feature_details(db_session, feature_id=1)
        assert result.id == 1
        assert result.name == "Test"

# ------------------------------------------------------------
# Test class for update_feature
# ------------------------------------------------------------
class TestUpdateFeature:
    @pytest.mark.asyncio
    async def test_update_feature_not_found(self, monkeypatch, db_session: AsyncMock):
        # Patch get_feature_by_id to return None
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=None))
        feature_update = FeatureCreate(name="Updated Feature", is_enabled=False, parent_id=None)
        with pytest.raises(FeatureNotFoundException):
            await update_feature(db_session, feature_id=1, feature_update=feature_update)

    @pytest.mark.asyncio
    async def test_update_feature_duplicate_name(self, monkeypatch, db_session: AsyncMock):
        # Fake existing db_feature
        fake_db_feature = FeatureFlag(id=1, name="old_feature", is_enabled=True, parent_id=None)
        fake_db_feature.children = []
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=fake_db_feature))
        # Patch get_feature_by_name to return an existing feature when new name is provided
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_name", AsyncMock(return_value=FeatureFlag(id=2, name="updated_feature", is_enabled=True)))
        feature_update = FeatureCreate(name="Updated Feature", is_enabled=True, parent_id=None)
        with pytest.raises(DuplicateFeatureNameException):
            await update_feature(db_session, feature_id=1, feature_update=feature_update)

    @pytest.mark.asyncio
    async def test_update_feature_success_without_status_change(self, monkeypatch, db_session: AsyncMock):
        # Fake existing db_feature
        fake_db_feature = FeatureFlag(id=1, name="old_feature", is_enabled=True, parent_id=None)
        fake_db_feature.children = [FeatureFlag(id=2, name="child", is_enabled=False, parent_id=1)]

        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=fake_db_feature))
        # Patch get_feature_by_name to return None (no duplicate)
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_name", AsyncMock(return_value=None))
        # Patch validate_parent to do nothing
        monkeypatch.setattr("app.services.feature_flag.validate_parent", AsyncMock(return_value=None))
        # Simulate successful commit and refresh
        async def fake_commit():
            pass
        monkeypatch.setattr(db_session, "commit", fake_commit)
        async def fake_refresh(feature, opts):
            pass
        monkeypatch.setattr(db_session, "refresh", fake_refresh)
        
        # Create a feature update
        feature_update = FeatureCreate(name="Updated Feature", is_enabled=True, parent_id=None)
        result = await update_feature(db_session, feature_id=1, feature_update=feature_update)
        # Check that the updated feature has new name and status
        assert result.name == "Updated Feature"
        assert result.is_enabled is True
        assert result.children[0].is_enabled is False # no change here
    
    @pytest.mark.asyncio
    async def test_update_feature_success_with_status_chage(self, monkeypatch, db_session: AsyncMock):
        # Fake existing db_feature
        fake_db_feature = FeatureFlag(id=1, name="old_feature", is_enabled=True, parent_id=None)
        fake_db_feature.children = [FeatureFlag(id=2, name="child", is_enabled=True, parent_id=1)]

        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=fake_db_feature))
        # Patch get_feature_by_name to return None (no duplicate)
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_name", AsyncMock(return_value=None))
        # Patch validate_parent to do nothing
        monkeypatch.setattr("app.services.feature_flag.validate_parent", AsyncMock(return_value=None))
        # Simulate successful commit and refresh
        async def fake_commit():
            pass
        monkeypatch.setattr(db_session, "commit", fake_commit)
        async def fake_refresh(feature, opts):
            pass
        monkeypatch.setattr(db_session, "refresh", fake_refresh)
        
        # Create a feature update
        feature_update = FeatureCreate(name="Updated Feature", is_enabled=False, parent_id=None)
        result = await update_feature(db_session, feature_id=1, feature_update=feature_update)
        # Check that the updated feature has new name and status
        assert result.name == "Updated Feature"
        assert result.is_enabled is False
        assert result.children[0].is_enabled is False  # children also gets updated as same

    @pytest.mark.asyncio
    async def test_update_feature_integrity_error(self, monkeypatch, db_session: AsyncMock):
        fake_db_feature = FeatureFlag(id=1, name="old_feature", is_enabled=True, parent_id=None)
        fake_db_feature.children = []
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_id", AsyncMock(return_value=fake_db_feature))
        monkeypatch.setattr("app.services.feature_flag.get_feature_by_name", AsyncMock(return_value=None))
        monkeypatch.setattr("app.services.feature_flag.validate_parent", AsyncMock(return_value=None))
        
        async def fake_commit():
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("error", None, None)
        monkeypatch.setattr(db_session, "commit", fake_commit)
        
        feature_update = FeatureCreate(name="Updated Feature", is_enabled=False, parent_id=None)
        with pytest.raises(DBIntegrityError):
            await update_feature(db_session, feature_id=1, feature_update=feature_update)

# ------------------------------------------------------------
# Test class for get_all_features
# ------------------------------------------------------------
class TestGetAllFeatures:
    @pytest.mark.asyncio
    async def test_get_all_features_empty(self, monkeypatch, db_session: AsyncMock):
        # Patch get_all_db_features to return an empty list
        monkeypatch.setattr("app.services.feature_flag.get_all_db_features", AsyncMock(return_value=[]))
        result = await get_all_features(db_session)
        # Expect an empty features list
        assert result.features == []

    @pytest.mark.asyncio
    async def test_get_all_features_success(self, monkeypatch, db_session: AsyncMock):
        # Create fake db features
        fake_db_feature = FeatureFlag(id=1, name="test_feature", is_enabled=True, parent_id=None)
        fake_db_feature.children = []
        monkeypatch.setattr("app.services.feature_flag.get_all_db_features", AsyncMock(return_value=[fake_db_feature]))
        result = await get_all_features(db_session)
        # Expect a features list with one item
        assert len(result.features) == 1
        assert result.features[0].id == 1
        assert result.features[0].name == "Test Feature"

# ------------------------------------------------------------
# Test class for delete_feature
# ------------------------------------------------------------
class TestDeleteFeature:
    @pytest.mark.asyncio
    async def test_delete_feature_not_exists(self, monkeypatch, db_session: AsyncMock):
        # Patch delete_db_feature to raise FeatureNotFoundException exception
        async def fake_delete_db_feature(db, feature_id):
            raise FeatureNotFoundException()
        monkeypatch.setattr("app.services.feature_flag.delete_db_feature", fake_delete_db_feature)
        with pytest.raises(FeatureNotFoundException):
            await delete_feature(db_session, 1)
    

    @pytest.mark.asyncio
    async def test_delete_feature_parent_feature(self, monkeypatch, db_session: AsyncMock):
        # Patch delete_db_feature to raise IntegrityError exception
        async def fake_delete_db_feature(db, feature_id):
            from sqlalchemy.exc import IntegrityError
            raise IntegrityError("error", None, None)
        monkeypatch.setattr("app.services.feature_flag.delete_db_feature", fake_delete_db_feature)
        with pytest.raises(DeletingParentFeature):
            await delete_feature(db_session, 2)


    @pytest.mark.asyncio
    async def test_delete_feature_success(self, monkeypatch, db_session: AsyncMock):
        # Patch delete_db_feature to return null
        monkeypatch.setattr("app.services.feature_flag.delete_db_feature", AsyncMock(return_value=[]))
        await delete_feature(db_session, 3)
