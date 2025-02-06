import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app  # Assuming your FastAPI app is initialized in main.py
from app.services import feature_flag as feature_flag_svc
from app.utility.exceptions import (
    DuplicateFeatureNameException, FeatureNotFoundException
)
from app.routers.v1.schemas import FeatureCreate, Feature, AllFeaturesList


# Test client
client = TestClient(app)

class TestCreateFeature:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        self.mock_create_feature = mocker.patch.object(feature_flag_svc, "create_feature", new_callable=AsyncMock)

    @pytest.mark.asyncio
    async def test_create_feature_success(self):
        feature_data = FeatureCreate(name="TestFeature", is_enabled=True)
        response_feature = Feature(id=1, **feature_data.model_dump())
        self.mock_create_feature.return_value = response_feature

        response = client.post("/features/", json=feature_data.model_dump())
        assert response.status_code == 200
        assert response.json()["name"] == "TestFeature"

    @pytest.mark.asyncio
    async def test_create_feature_duplicate_name(self):
        self.mock_create_feature.side_effect = DuplicateFeatureNameException()
        response = client.post("/features/", json={"name": "DuplicateFeature", "is_enabled": True})
        assert response.status_code == 409
        assert response.json()["detail"] == "Feature with this name already exists"

class TestGetFeatureDetails:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        self.mock_get_feature_details = mocker.patch.object(feature_flag_svc, "get_feature_details", new_callable=AsyncMock)

    @pytest.mark.asyncio
    async def test_get_feature_success(self):
        feature = Feature(id=1, name="TestFeature", is_enabled=True, children=[])
        self.mock_get_feature_details.return_value = feature

        response = client.get("/features/1")
        assert response.status_code == 200
        assert response.json()["name"] == "TestFeature"

    @pytest.mark.asyncio
    async def test_get_feature_not_found(self):
        self.mock_get_feature_details.side_effect = FeatureNotFoundException()
        response = client.get("/features/99")
        assert response.status_code == 404
        assert response.json()["detail"] == "Feature not found"

class TestUpdateFeature:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        self.mock_update_feature = mocker.patch.object(feature_flag_svc, "update_feature", new_callable=AsyncMock)

    @pytest.mark.asyncio
    async def test_update_feature_success(self):
        feature_update = FeatureCreate(name="UpdatedFeature", is_enabled=True)
        updated_feature = Feature(id=1, **feature_update.model_dump())
        self.mock_update_feature.return_value = updated_feature

        response = client.put("/features/1", json=feature_update.model_dump())
        assert response.status_code == 200
        assert response.json()["name"] == "UpdatedFeature"

    @pytest.mark.asyncio
    async def test_update_feature_duplicate_name(self):
        self.mock_update_feature.side_effect = DuplicateFeatureNameException()
        response = client.put("/features/1", json={"name": "DuplicateFeature", "is_enabled": True})
        assert response.status_code == 409
        assert response.json()["detail"] == "Feature with this name already exists"

class TestGetAllFeatures:
    @pytest.fixture(autouse=True)
    def setup_method(self, mocker):
        self.mock_get_all_features = mocker.patch.object(feature_flag_svc, "get_all_features", new_callable=AsyncMock)

    @pytest.mark.asyncio
    async def test_get_all_features_success(self):
        all_features = AllFeaturesList(features=[])
        self.mock_get_all_features.return_value = all_features

        response = client.get("/features")
        assert response.status_code == 200
        assert response.json()["features"] == []
