"""
Test for temperature chart rendering - simplified version without Selenium
"""
import unittest

import requests
from bs4 import BeautifulSoup


class TemperatureChartTest(unittest.TestCase):
    """Test that temperature charts render properly without duplication"""

    def setUp(self):
        """Setup for each test"""
        self.base_url = "http://localhost:8006"

    def test_details_page_html_structure(self):
        """Test that the details page HTML has proper chart container structure"""
        # Get the details page
        url = f"{self.base_url}/water-heaters/wh-001"
        print(f"\nFetching {url}...")
        response = requests.get(url)

        self.assertEqual(
            response.status_code,
            200,
            f"Failed to load details page, got status {response.status_code}",
        )

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for chart containers
        print("Checking for chart containers...")
        chart_containers = soup.select(
            '.temperature-history-chart, [data-chart="temperature-history"], #temperature-chart'
        )

        # Print all chart containers found for debugging
        for i, container in enumerate(chart_containers):
            container_id = container.get("id") or "unnamed"
            container_class = container.get("class") or "no-class"
            print(f"  Container {i+1}: id='{container_id}', class='{container_class}'")

        # Test for excessive duplicate containers
        self.assertLessEqual(
            len(chart_containers),
            2,
            f"Found {len(chart_containers)} chart containers, should have at most 2 (one in details, one in history tab)",
        )

        # Check for any chart-error or error-message elements
        error_elements = soup.select(".chart-error, .error-message")
        for i, error in enumerate(error_elements):
            print(f"  Error {i+1}: {error.text}")

        self.assertEqual(
            len(error_elements), 0, f"Found {len(error_elements)} error messages"
        )


if __name__ == "__main__":
    unittest.main()
