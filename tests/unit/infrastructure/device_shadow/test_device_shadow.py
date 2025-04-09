#!/usr/bin/env python3
"""
Unit tests for device shadow service
"""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to path for imports
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
)

# Import the module to test
from src.infrastructure.device_shadow.init_shadow_store import (
    DeviceShadowService,
    setup_redis_shadow,
)


class TestDeviceShadow(unittest.TestCase):
    """Test suite for device shadow service"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_redis = MagicMock()
        self.shadow_service = DeviceShadowService(redis_client=self.mock_redis)

        # Sample device data for tests
        self.device_id = "test-device-001"
        self.reported_state = {
            "temperature": 72.5,
            "mode": "auto",
            "power": "on",
            "lastReportTime": "2025-04-06T09:45:00Z",
        }
        self.desired_state = {
            "temperature": 74.0,
            "mode": "auto",
            "power": "on",
            "requestTime": "2025-04-06T09:44:00Z",
        }

    def test_get_device_shadow(self):
        """Test getting a device shadow"""
        # Setup mocks
        self.mock_redis.pipeline.return_value = self.mock_redis
        self.mock_redis.execute.return_value = [
            json.dumps(self.reported_state),
            json.dumps(self.desired_state),
            json.dumps({"manufacturer": "Test"}),
            "1",  # Simulated flag
        ]
        self.mock_redis.sismember.return_value = True  # Device is connected

        # Call method
        shadow = self.shadow_service.get_device_shadow(self.device_id)

        # Verify results
        self.assertEqual(shadow["device_id"], self.device_id)
        self.assertEqual(shadow["reported"], self.reported_state)
        self.assertEqual(shadow["desired"], self.desired_state)
        self.assertTrue(shadow["simulated"])
        self.assertTrue(shadow["connected"])

        # Verify Redis calls
        self.mock_redis.pipeline.assert_called_once()
        self.mock_redis.execute.assert_called_once()
        self.mock_redis.sismember.assert_called_once()

    def test_update_reported_state(self):
        """Test updating reported state"""
        # Setup mock
        self.mock_redis.get.return_value = json.dumps({"temperature": 70.0})

        # New state to update
        new_state = {"temperature": 72.5, "mode": "auto"}

        # Call method
        result = self.shadow_service.update_reported_state(self.device_id, new_state)

        # Verify result contains merged state
        self.assertEqual(result["temperature"], 72.5)
        self.assertEqual(result["mode"], "auto")

        # Verify Redis calls
        self.mock_redis.get.assert_called_once()
        self.mock_redis.set.assert_called()

    def test_update_desired_state(self):
        """Test updating desired state"""
        # Setup mock
        self.mock_redis.get.return_value = json.dumps({"temperature": 70.0})

        # New state to update
        new_state = {"temperature": 74.0, "mode": "auto"}

        # Call method
        result = self.shadow_service.update_desired_state(self.device_id, new_state)

        # Verify result contains merged state
        self.assertEqual(result["temperature"], 74.0)
        self.assertEqual(result["mode"], "auto")

        # Verify Redis calls
        self.mock_redis.get.assert_called_once()
        self.mock_redis.set.assert_called_once()

    def test_set_device_simulated(self):
        """Test marking a device as simulated"""
        # Call method
        self.shadow_service.set_device_simulated(self.device_id, True)

        # Verify Redis call
        self.mock_redis.set.assert_called_once()
        call_args = self.mock_redis.set.call_args[0]
        self.assertIn(self.device_id, call_args[0])
        self.assertEqual(call_args[1], "1")

    def test_set_device_connected(self):
        """Test marking a device as connected/disconnected"""
        # Test connecting
        self.shadow_service.set_device_connected(self.device_id, True)
        self.mock_redis.sadd.assert_called_once()

        # Test disconnecting
        self.shadow_service.set_device_connected(self.device_id, False)
        self.mock_redis.srem.assert_called_once()

    @patch("src.infrastructure.device_shadow.init_shadow_store.redis.Redis")
    def test_setup_redis_shadow(self, mock_redis_class):
        """Test Redis shadow setup"""
        # Setup mock
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Call function
        result = setup_redis_shadow()

        # Verify results
        self.assertTrue(result)
        mock_redis.ping.assert_called_once()
        mock_redis.set.assert_called()


if __name__ == "__main__":
    unittest.main()
