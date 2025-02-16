import random
import uuid

from locust import HttpUser, SequentialTaskSet, task


def get_unique_feature_name(prefix="feature"):
    """Generates a unique feature name using UUID."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# Pre-populate features for read-heavy load testing
def prepopulate_features(client, count=20):
    """Creates multiple features before the test for GET requests"""
    feature_ids = []
    for i in range(count):
        feat_name = get_unique_feature_name()
        response = client.post(
            "/api/v1/features/",
            json={"name": feat_name, "is_enabled": True},
            name="Create feature",
        )
        if response.status_code == 200:
            feature_ids.append(response.json().get("id"))
    return feature_ids


# Simulating a typical user journey (Create → Update → Delete)
class FeatureLifecycle(SequentialTaskSet):
    feature_id = None

    @task
    def test_flow(self):
        """Step 1: Create feature"""
        self.unique_name = get_unique_feature_name()
        response = self.client.post(
            "/api/v1/features/",
            json={"name": self.unique_name, "is_enabled": True},
            name="Create feature",
        )
        if response.status_code == 200:
            self.feature_id = response.json().get("id")
        else:
            print(f"Feature creation failed: {response.text}")

    @task
    def update_feature(self):
        """Step 2: Update the created feature"""
        if self.feature_id:
            new_name = get_unique_feature_name("updated")
            self.client.put(
                f"/api/v1/features/{self.feature_id}",
                json={"name": new_name, "is_enabled": False},
                name="Update feature",
            )
        else:
            print("Feature id is None")

    @task
    def delete_feature(self):
        """Step 3: Delete the created feature"""
        if self.feature_id:
            self.client.delete(
                f"/api/v1/features/{self.feature_id}", name="Delete feature"
            )
            self.feature_id = None  # Prevent multiple deletions
        else:
            print("Feature id is None")


# Read-only user to stress test the GET API
class ReadUser(HttpUser):
    # wait_time = between(1, 3)
    feature_ids = []

    def on_start(self):
        """Prepopulate database with features for read tests"""
        self.feature_ids = prepopulate_features(self.client, count=50)

    @task(5)  # More frequent reads
    def get_all_features(self):
        """Get all features"""
        self.client.get("/api/v1/features", name="Get all features")

    @task(2)
    def get_random_feature(self):
        """Get a random feature"""
        if self.feature_ids:
            random_id = random.choice(self.feature_ids)
            self.client.get(f"/api/v1/features/{random_id}", name="Get feature")


# Full CRUD User
class FeatureCoreUser(HttpUser):
    # wait_time = between(1, 3)
    tasks = [FeatureLifecycle]  # Simulate Create → Update → Delete
