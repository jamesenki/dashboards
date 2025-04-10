import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.web.routes import get_water_heater_detail


class TestLazyTabManager(unittest.TestCase):
    """
    Test the lazy-loading tab management for the water heater details page.
    Following TDD principles, these tests define the expected behavior
    for the improved tab management system.
    """

    def setUp(self):
        """Set up test environment."""
        self.mock_request = MagicMock()
        self.device_id = "test-device-id"

    @patch(
        "src.services.configurable_water_heater_service.ConfigurableWaterHeaterService"
    )
    async def test_details_page_loads_minimal_data_initially(self, mock_service_class):
        """Test that details page loads with minimal data initially."""
        # Mock the service to return a minimal water heater object
        mock_service = mock_service_class.return_value
        mock_service.get_water_heater.return_value = {
            "id": self.device_id,
            "name": "Test Water Heater",
            "manufacturer": "TestMfg",
            "model": "TestModel",
        }

        # Get the rendered template response
        response = await get_water_heater_detail(self.mock_request, self.device_id)

        # Verify only the basic data was fetched
        mock_service.get_water_heater.assert_called_once_with(self.device_id)

        # Verify response contains lazy-loading attributes
        context = response.context
        self.assertEqual(context["heater_id"], self.device_id)
        self.assertTrue("lazy_load_enabled" in context)
        self.assertTrue(context["lazy_load_enabled"])

    @patch(
        "src.services.configurable_water_heater_service.ConfigurableWaterHeaterService"
    )
    async def test_error_isolation_per_tab(self, mock_service_class):
        """Test that errors in one tab don't affect others."""
        # Mock the service to return a water heater object
        mock_service = mock_service_class.return_value
        mock_service.get_water_heater.return_value = {
            "id": self.device_id,
            "name": "Test Water Heater",
        }

        # Get the rendered template response
        response = await get_water_heater_detail(self.mock_request, self.device_id)

        # Verify error isolation flags are set
        context = response.context
        self.assertTrue("isolate_tab_errors" in context)
        self.assertTrue(context["isolate_tab_errors"])

    def test_tab_manager_handles_missing_data_gracefully(self):
        """Test that the tab manager handles missing data gracefully."""
        # This test will be implemented properly once we have the client-side
        # JavaScript tests in place, as this behavior is primarily in the frontend.
        pass


if __name__ == "__main__":
    unittest.main()
