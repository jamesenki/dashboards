"""
Tests for MongoDB shadow storage implementation.

Following TDD principles, these tests define the expected behavior
of the MongoDB shadow storage before implementation.
"""
import asyncio
import os
import uuid
from datetime import datetime

import pytest
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.infrastructure.device_shadow.mongodb_shadow_storage import MongoDBShadowStorage
from src.services.device_shadow import DeviceShadowService

# Skip tests if MongoDB is not available
pytestmark = pytest.mark.skipif(
    os.environ.get("SKIP_MONGODB_TESTS", "false").lower() == "true",
    reason="MongoDB integration tests are disabled",
)

# Test data
TEST_DEVICE_ID = f"test-device-{str(uuid.uuid4())[:8]}"
TEST_SHADOW = {
    "device_id": TEST_DEVICE_ID,
    "reported": {"temperature": 72.5, "status": "ONLINE"},
    "desired": {"temperature": 70.0},
    "version": 1,
    "metadata": {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "last_updated": datetime.utcnow().isoformat() + "Z",
    },
}


@pytest.fixture
async def mongodb_storage():
    """Fixture providing a MongoDB shadow storage instance pointing to test database."""
    # Connection settings - use environment variables or defaults for testing
    mongo_uri = os.environ.get("MONGODB_TEST_URI", "mongodb://localhost:27017/")
    db_name = (
        f"test_iotsphere_{str(uuid.uuid4())[:8]}"  # Use unique DB to avoid conflicts
    )

    # Check if MongoDB is available
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")  # Check connection
    except ConnectionFailure:
        pytest.skip("MongoDB server is not available")

    # Create storage instance
    storage = MongoDBShadowStorage(mongo_uri=mongo_uri, db_name=db_name)
    await storage.initialize()

    yield storage

    # Cleanup after tests
    await storage.drop_collections()
    await storage.close()


@pytest.mark.asyncio
async def test_shadow_exists(mongodb_storage):
    """Test shadow_exists method."""
    # Should return False for non-existent shadow
    assert await mongodb_storage.shadow_exists(TEST_DEVICE_ID) is False

    # Create a shadow and verify it exists
    await mongodb_storage.save_shadow(TEST_DEVICE_ID, TEST_SHADOW)
    assert await mongodb_storage.shadow_exists(TEST_DEVICE_ID) is True


@pytest.mark.asyncio
async def test_get_shadow(mongodb_storage):
    """Test get_shadow method."""
    # Should raise ValueError for non-existent shadow
    with pytest.raises(ValueError):
        await mongodb_storage.get_shadow(TEST_DEVICE_ID)

    # Create a shadow and verify we can get it
    await mongodb_storage.save_shadow(TEST_DEVICE_ID, TEST_SHADOW)
    shadow = await mongodb_storage.get_shadow(TEST_DEVICE_ID)

    # Verify shadow content
    assert shadow["device_id"] == TEST_DEVICE_ID
    assert shadow["reported"]["temperature"] == 72.5
    assert shadow["desired"]["temperature"] == 70.0
    assert shadow["version"] == 1


@pytest.mark.asyncio
async def test_save_shadow(mongodb_storage):
    """Test save_shadow method."""
    # Save shadow and verify it exists
    await mongodb_storage.save_shadow(TEST_DEVICE_ID, TEST_SHADOW)
    assert await mongodb_storage.shadow_exists(TEST_DEVICE_ID) is True

    # Update shadow and verify changes
    updated_shadow = TEST_SHADOW.copy()
    updated_shadow["version"] = 2
    updated_shadow["reported"]["temperature"] = 73.2

    await mongodb_storage.save_shadow(TEST_DEVICE_ID, updated_shadow)

    retrieved_shadow = await mongodb_storage.get_shadow(TEST_DEVICE_ID)
    assert retrieved_shadow["version"] == 2
    assert retrieved_shadow["reported"]["temperature"] == 73.2


@pytest.mark.asyncio
async def test_delete_shadow(mongodb_storage):
    """Test delete_shadow method."""
    # Should return False for non-existent shadow
    assert await mongodb_storage.delete_shadow(TEST_DEVICE_ID) is False

    # Create a shadow, then delete it
    await mongodb_storage.save_shadow(TEST_DEVICE_ID, TEST_SHADOW)
    assert await mongodb_storage.shadow_exists(TEST_DEVICE_ID) is True

    assert await mongodb_storage.delete_shadow(TEST_DEVICE_ID) is True
    assert await mongodb_storage.shadow_exists(TEST_DEVICE_ID) is False


@pytest.mark.asyncio
async def test_get_shadow_history(mongodb_storage):
    """Test get_shadow_history method."""
    # Create initial shadow
    await mongodb_storage.save_shadow(TEST_DEVICE_ID, TEST_SHADOW)

    # Create multiple versions
    for i in range(2, 6):
        updated_shadow = TEST_SHADOW.copy()
        updated_shadow["version"] = i
        updated_shadow["reported"]["temperature"] = 70.0 + i
        updated_shadow["metadata"]["last_updated"] = datetime.utcnow().isoformat() + "Z"

        await mongodb_storage.save_shadow(TEST_DEVICE_ID, updated_shadow)

    # Get history and verify
    history = await mongodb_storage.get_shadow_history(TEST_DEVICE_ID, limit=10)

    assert len(history) == 5  # Original shadow plus 4 updates
    assert history[0]["version"] == 5  # Most recent version first
    assert history[4]["version"] == 1  # Oldest version last


@pytest.mark.asyncio
async def test_integration_with_shadow_service(mongodb_storage):
    """Test integration with DeviceShadowService."""
    shadow_service = DeviceShadowService(storage_provider=mongodb_storage)

    # Create a shadow through the service
    await shadow_service.create_device_shadow(
        device_id=TEST_DEVICE_ID,
        reported_state={"temperature": 72.5, "status": "ONLINE"},
        desired_state={"temperature": 70.0},
    )

    # Verify shadow exists
    shadow = await shadow_service.get_device_shadow(TEST_DEVICE_ID)
    assert shadow["device_id"] == TEST_DEVICE_ID
    assert shadow["reported"]["temperature"] == 72.5

    # Update shadow
    await shadow_service.update_device_shadow(
        device_id=TEST_DEVICE_ID, reported_state={"temperature": 73.2}, version=1
    )

    # Verify update
    updated_shadow = await shadow_service.get_device_shadow(TEST_DEVICE_ID)
    assert updated_shadow["version"] == 2
    assert updated_shadow["reported"]["temperature"] == 73.2

    # Check history
    history = await shadow_service.get_shadow_history(TEST_DEVICE_ID)
    assert len(history) == 2
