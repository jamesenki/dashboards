"""
Integration tests for tag management API endpoints.
These tests verify that all tag management operations (CRUD) work correctly.
"""

import json
import unittest
import uuid

from fastapi.testclient import TestClient

# Import the main application
from src.main import app


class TestTagManagement(unittest.TestCase):
    """Test tag management endpoints including create, read, update, and delete operations."""

    @classmethod
    def setUpClass(cls):
        """Set up the test client."""
        cls.client = TestClient(app)

    def setUp(self):
        """Create a test tag that can be used by individual tests."""
        # Create a test tag for use in tests
        self.test_tag_data = {"name": f"test-tag-{uuid.uuid4()}", "color": "blue"}
        response = self.client.post("/api/monitoring/tags", json=self.test_tag_data)
        self.test_tag = response.json()
        self.test_tag_id = self.test_tag.get("id")

    def tearDown(self):
        """Clean up by attempting to delete the test tag if it exists."""
        try:
            self.client.delete(f"/api/monitoring/tags/{self.test_tag_id}")
        except:
            # It's okay if this fails, e.g., if the tag was already deleted in a test
            pass

    def test_get_all_tags(self):
        """Test that all tags can be retrieved."""
        response = self.client.get("/api/monitoring/tags")

        # Check response is successful
        self.assertEqual(response.status_code, 200)

        # Check response is a list
        tags = response.json()
        self.assertIsInstance(tags, list)

        # Check that our test tag is in the list
        tag_ids = [tag.get("id") for tag in tags]
        self.assertIn(self.test_tag_id, tag_ids)

    def test_create_tag(self):
        """Test creating a new tag."""
        # Prepare new tag data
        new_tag_data = {"name": f"new-test-tag-{uuid.uuid4()}", "color": "red"}

        # Create the tag
        response = self.client.post("/api/monitoring/tags", json=new_tag_data)

        # Check response is successful
        self.assertEqual(response.status_code, 201)

        # Check the returned tag has the expected properties
        created_tag = response.json()
        self.assertEqual(created_tag.get("status"), "success")
        self.assertEqual(created_tag.get("name"), new_tag_data["name"])
        self.assertEqual(created_tag.get("color"), new_tag_data["color"])

        # Clean up: delete the created tag
        self.client.delete(f"/api/monitoring/tags/{created_tag.get('id')}")

    def test_update_tag(self):
        """Test updating an existing tag."""
        # Prepare update data
        update_data = {"name": f"updated-tag-{uuid.uuid4()}", "color": "green"}

        # Update the tag
        response = self.client.put(
            f"/api/monitoring/tags/{self.test_tag_id}", json=update_data
        )

        # Check response is successful
        self.assertEqual(response.status_code, 200)

        # Check the returned tag has the updated properties
        updated_tag = response.json()
        self.assertEqual(updated_tag.get("status"), "success")
        self.assertEqual(updated_tag.get("name"), update_data["name"])
        self.assertEqual(updated_tag.get("color"), update_data["color"])

        # Verify the update was persisted by getting the tag
        response = self.client.get("/api/monitoring/tags")
        tags = response.json()

        # Find our updated tag
        updated_tags = [tag for tag in tags if tag.get("id") == self.test_tag_id]
        self.assertEqual(len(updated_tags), 1)

        # Check it has the updated properties
        if updated_tags:
            tag = updated_tags[0]
            self.assertEqual(tag.get("name"), update_data["name"])
            self.assertEqual(tag.get("color"), update_data["color"])

    def test_delete_tag(self):
        """Test deleting a tag."""
        # Create a tag specifically for deletion
        delete_tag_data = {"name": f"delete-test-tag-{uuid.uuid4()}", "color": "purple"}
        response = self.client.post("/api/monitoring/tags", json=delete_tag_data)
        delete_tag = response.json()
        delete_tag_id = delete_tag.get("id")

        # Delete the tag
        response = self.client.delete(f"/api/monitoring/tags/{delete_tag_id}")

        # Check response is successful
        self.assertEqual(response.status_code, 200)

        # Check the deletion was successful
        delete_result = response.json()
        self.assertEqual(delete_result.get("status"), "success")

        # Verify the tag is no longer in the list
        response = self.client.get("/api/monitoring/tags")
        tags = response.json()
        tag_ids = [tag.get("id") for tag in tags]
        self.assertNotIn(delete_tag_id, tag_ids)

    def test_create_tag_validation(self):
        """Test validation when creating a tag with missing required fields."""
        # Try to create a tag without a name
        invalid_tag_data = {
            "color": "blue"
            # name is missing
        }

        response = self.client.post("/api/monitoring/tags", json=invalid_tag_data)

        # Check validation failure
        self.assertEqual(response.status_code, 400)

        # Check error message
        error = response.json()
        self.assertIn("detail", error)
        self.assertIn("required", error["detail"].lower())


if __name__ == "__main__":
    unittest.main()
