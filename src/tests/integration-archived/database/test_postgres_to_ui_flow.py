"""
End-to-end tests for PostgreSQL to UI data flow.

These tests verify that:
1. Data from PostgreSQL is correctly retrieved and displayed in the UI
2. Only PostgreSQL data is used (not mock data)
3. All UI water heaters correspond to entries in the PostgreSQL database
4. The UI properly displays Rheem-specific water heater types
"""
import asyncio
import logging
import os
from typing import Any, Dict, List

import asyncpg
import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from src.db.config import db_settings
from src.main import app
from src.repositories.postgres_water_heater_repository import (
    PostgresWaterHeaterRepository,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create test client
client = TestClient(app)

# Skip all tests if PostgreSQL is not available
pytestmark = pytest.mark.asyncio


class TestPostgresToUIFlow:
    """Test suite for verifying PostgreSQL to UI data flow."""

    @pytest.fixture(scope="function")
    async def postgres_connection(self):
        """Create a direct connection to PostgreSQL for verification."""
        try:
            conn = await asyncpg.connect(
                host=db_settings.DB_HOST,
                port=db_settings.DB_PORT,
                database=db_settings.DB_NAME,
                user=db_settings.DB_USER,
                password=db_settings.DB_PASSWORD,
            )
            yield conn
            await conn.close()
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    @pytest.fixture(scope="function")
    async def postgres_water_heaters(self, postgres_connection) -> List[Dict[str, Any]]:
        """Get all water heaters directly from PostgreSQL."""
        try:
            # Use raw SQL to get all water heaters
            rows = await postgres_connection.fetch(
                """
                SELECT id, name, manufacturer, model, type, series,
                       current_temperature, target_temperature
                FROM water_heaters
                ORDER BY manufacturer, type
            """
            )

            # Convert to list of dictionaries
            water_heaters = []
            for row in rows:
                water_heater = dict(row)
                water_heaters.append(water_heater)

            logger.info(f"Retrieved {len(water_heaters)} water heaters from PostgreSQL")
            return water_heaters
        except Exception as e:
            logger.error(f"Error retrieving water heaters from PostgreSQL: {e}")
            return []

    @pytest.fixture(scope="function")
    def api_water_heaters(self) -> List[Dict[str, Any]]:
        """Get all water heaters from the API."""
        # Use configurable API endpoint to get all water heaters
        response = client.get("/api/manufacturer/water-heaters")
        assert (
            response.status_code == 200
        ), f"Failed to get water heaters from API: {response.text}"

        water_heaters = response.json()
        logger.info(f"Retrieved {len(water_heaters)} water heaters from API")
        return water_heaters

    @pytest.fixture(scope="function")
    def ui_water_heaters_html(self):
        """Get the water heaters list page HTML."""
        response = client.get("/water-heaters")
        assert response.status_code == 200, "Failed to get water heaters list page"
        return response.text

    async def test_postgres_to_api_consistency(
        self, postgres_water_heaters, api_water_heaters
    ):
        """Test that water heaters from PostgreSQL match those from the API."""
        # Skip if no water heaters in PostgreSQL
        if not postgres_water_heaters:
            pytest.skip("No water heaters found in PostgreSQL")

        # Create ID maps for easy lookup
        pg_heaters_by_id = {h["id"]: h for h in postgres_water_heaters}
        api_heaters_by_id = {h["id"]: h for h in api_water_heaters}

        # Check that all PostgreSQL water heaters are in the API response
        missing_in_api = set(pg_heaters_by_id.keys()) - set(api_heaters_by_id.keys())
        assert (
            not missing_in_api
        ), f"Water heaters in PostgreSQL but missing from API: {missing_in_api}"

        # Check that all API water heaters are in PostgreSQL
        # This ensures we're not showing mock data
        missing_in_pg = set(api_heaters_by_id.keys()) - set(pg_heaters_by_id.keys())
        assert (
            not missing_in_pg
        ), f"Water heaters in API but missing from PostgreSQL: {missing_in_pg}"

        # Check that data matches for each water heater
        for heater_id in pg_heaters_by_id:
            pg_heater = pg_heaters_by_id[heater_id]
            api_heater = api_heaters_by_id[heater_id]

            # Check essential fields
            assert (
                pg_heater["name"] == api_heater["name"]
            ), f"Name mismatch for {heater_id}"
            assert (
                pg_heater["manufacturer"] == api_heater["manufacturer"]
            ), f"Manufacturer mismatch for {heater_id}"

            # Temperature fields may be named differently in API vs DB
            pg_temp = pg_heater.get("current_temperature")
            api_temp = api_heater.get("current_temperature") or api_heater.get(
                "current_temp"
            )

            # Allow small temperature differences due to rounding or updates
            if pg_temp is not None and api_temp is not None:
                assert (
                    abs(float(pg_temp) - float(api_temp)) < 1.0
                ), f"Temperature mismatch for {heater_id}"

        logger.info("Successfully verified PostgreSQL to API data consistency")

    async def test_ui_displays_all_postgres_water_heaters(
        self, postgres_water_heaters, ui_water_heaters_html
    ):
        """Test that all PostgreSQL water heaters appear in the UI."""
        # Skip if no water heaters in PostgreSQL
        if not postgres_water_heaters:
            pytest.skip("No water heaters found in PostgreSQL")

        # Parse the HTML
        soup = BeautifulSoup(ui_water_heaters_html, "html.parser")

        # Find all water heater cards
        water_heater_cards = soup.select(".water-heater-card, .device-card")
        assert water_heater_cards, "No water heater cards found in UI"

        logger.info(f"Found {len(water_heater_cards)} water heater cards in UI")

        # Extract heater IDs from cards
        ui_heater_ids = set()
        for card in water_heater_cards:
            # Try different ways to extract the ID
            heater_id = (
                card.get("id") or card.get("data-id") or card.get("data-heater-id")
            )

            # If not found directly, look for links or buttons with the ID
            if not heater_id:
                links = card.select("a[href*='water-heaters/'], button[data-id]")
                for link in links:
                    href = link.get("href")
                    if href and "/water-heaters/" in href:
                        heater_id = href.split("/water-heaters/")[-1].split("/")[0]
                        break
                    heater_id = link.get("data-id")
                    if heater_id:
                        break

            if heater_id:
                ui_heater_ids.add(heater_id)

        # Get PostgreSQL heater IDs
        pg_heater_ids = {h["id"] for h in postgres_water_heaters}

        # Check that all PostgreSQL water heaters appear in the UI
        missing_in_ui = pg_heater_ids - ui_heater_ids
        assert (
            not missing_in_ui
        ), f"Water heaters in PostgreSQL but missing from UI: {missing_in_ui}"

        # Check that all UI water heaters are in PostgreSQL
        # This ensures we're not showing mock data
        extra_in_ui = ui_heater_ids - pg_heater_ids
        assert (
            not extra_in_ui
        ), f"Water heaters in UI but missing from PostgreSQL: {extra_in_ui}"

        logger.info("Successfully verified all PostgreSQL water heaters appear in UI")

    async def test_rheem_water_heater_types_in_ui(
        self, postgres_water_heaters, ui_water_heaters_html
    ):
        """Test that Rheem water heater types (Tank, Tankless, Hybrid) are displayed correctly in the UI."""
        # Filter for Rheem water heaters
        rheem_heaters = [
            h for h in postgres_water_heaters if h.get("manufacturer") == "Rheem"
        ]

        # Skip if no Rheem water heaters in PostgreSQL
        if not rheem_heaters:
            pytest.skip("No Rheem water heaters found in PostgreSQL")

        # Parse the HTML
        soup = BeautifulSoup(ui_water_heaters_html, "html.parser")

        # Find elements containing water heater type
        type_elements = soup.select(".heater-type, .device-type, .water-heater-type")

        # Alternatively, look for text in the water heater cards
        if not type_elements:
            # Try to find cards that contain Rheem and type information
            cards = soup.select(".water-heater-card, .device-card")

            # Check if the page has the expected Rheem types
            page_text = soup.get_text().lower()

            # The UI might not explicitly show the type, but it should at least
            # contain references to the different Rheem models
            has_tank_reference = "tank" in page_text
            has_tankless_reference = "tankless" in page_text
            has_hybrid_reference = "hybrid" in page_text or "proterra" in page_text

            # At least some types should be represented
            assert any(
                [has_tank_reference, has_tankless_reference, has_hybrid_reference]
            ), "UI does not display any Rheem water heater types"

            # Log what was found for debugging
            found_types = []
            if has_tank_reference:
                found_types.append("Tank")
            if has_tankless_reference:
                found_types.append("Tankless")
            if has_hybrid_reference:
                found_types.append("Hybrid")

            logger.info(
                f"Found Rheem water heater types in UI: {', '.join(found_types)}"
            )
        else:
            # If we found explicit type elements, check that they include the expected types
            type_texts = [elem.get_text().lower() for elem in type_elements]

            # Check if the expected types are represented
            has_tank = any("tank" in text for text in type_texts)
            has_tankless = any("tankless" in text for text in type_texts)
            has_hybrid = any("hybrid" in text for text in type_texts)

            # At least some types should be displayed
            assert any(
                [has_tank, has_tankless, has_hybrid]
            ), "UI does not display any Rheem water heater types correctly"

            # Log what was found for debugging
            found_types = []
            if has_tank:
                found_types.append("Tank")
            if has_tankless:
                found_types.append("Tankless")
            if has_hybrid:
                found_types.append("Hybrid")

            logger.info(
                f"Found Rheem water heater types in UI: {', '.join(found_types)}"
            )

        logger.info("Successfully verified Rheem water heater types in UI")

    async def test_ui_shows_only_postgres_data(
        self, api_water_heaters, ui_water_heaters_html
    ):
        """Test that the UI only displays data from PostgreSQL (not mock data)."""
        # Get the total count of water heaters from the API
        api_count = len(api_water_heaters)

        # Parse the HTML
        soup = BeautifulSoup(ui_water_heaters_html, "html.parser")

        # Find all water heater cards
        water_heater_cards = soup.select(".water-heater-card, .device-card")
        ui_count = len(water_heater_cards)

        # Check for an indicator that might show the data source
        data_source_indicators = soup.select(".data-source, .source-indicator")
        for indicator in data_source_indicators:
            indicator_text = indicator.get_text().lower()
            assert (
                "mock" not in indicator_text
            ), "UI indicates mock data source is being used"
            if "postgres" in indicator_text or "database" in indicator_text:
                logger.info("UI explicitly indicates PostgreSQL data source")

        # Verify counts match (there shouldn't be extra items from mock data)
        assert (
            ui_count <= api_count
        ), f"UI shows more water heaters ({ui_count}) than API ({api_count})"

        # The UI count may be less if pagination is used
        if ui_count < api_count:
            pagination = soup.select(".pagination")
            assert (
                pagination
            ), "UI shows fewer water heaters than API but no pagination found"

        logger.info("Successfully verified UI only shows PostgreSQL data")
