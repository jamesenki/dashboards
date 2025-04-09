"""
Unit tests for shadow document functionality
Following TDD principles - these tests define expected behavior
"""
import os
import sys

import pytest

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


# This test should fail initially (RED phase)
def test_shadow_document_exists():
    """Test that a shadow document exists for a device"""
    from src.services.device_shadow import get_device_shadow

    # Get shadow for a test device
    device_id = "wh-test-001"
    shadow = get_device_shadow(device_id)

    # Shadow should exist and have required fields
    assert shadow is not None, "Shadow document should exist"
    assert "state" in shadow, "Shadow should have state field"
    assert "reported" in shadow["state"], "Shadow should have reported state"
    assert (
        "temperature" in shadow["state"]["reported"]
    ), "Shadow should have temperature in reported state"


# This test defines temperature history requirements
def test_temperature_history_available():
    """Test that temperature history is available for a device"""
    from src.services.telemetry import get_temperature_history

    # Get temperature history for test device
    device_id = "wh-test-001"
    history = get_temperature_history(device_id, days=7)

    # History should exist and have data points
    assert history is not None, "Temperature history should exist"
    assert len(history) > 0, "Temperature history should have data points"
    assert "timestamp" in history[0], "Temperature data should have timestamp"
    assert "value" in history[0], "Temperature data should have value"
