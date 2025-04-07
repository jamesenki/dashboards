#!/usr/bin/env python
"""
UI Data Validation Script

This script:
1. Connects to the PostgreSQL database to count water heaters
2. Makes an API request to the water heaters endpoint
3. Opens a web browser to check the UI elements
4. Validates that the number of water heaters matches across all layers

Usage:
    python ui_data_validation.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import asyncpg
import httpx

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Get environment variables
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def count_db_water_heaters():
    """Count water heaters in the PostgreSQL database."""
    print("Connecting to PostgreSQL database...")

    # Get DB settings from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "iotsphere")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")

    # Create PostgreSQL connection
    conn = await asyncpg.connect(
        host=db_host, port=db_port, user=db_user, password=db_password, database=db_name
    )

    try:
        # Count water heaters in the database
        water_heater_count = await conn.fetchval("SELECT COUNT(*) FROM water_heaters")
        manufacturers = await conn.fetch(
            "SELECT manufacturer, COUNT(*) FROM water_heaters GROUP BY manufacturer"
        )

        print(f"Database contains {water_heater_count} water heaters")
        print("Manufacturers in database:")
        for row in manufacturers:
            print(f"  - {row['manufacturer']}: {row['count']} water heater(s)")

        return water_heater_count, manufacturers
    finally:
        await conn.close()


async def count_api_water_heaters():
    """Count water heaters returned by the API."""
    print("\nChecking API response...")
    base_url = "http://localhost:8006"  # Default API port

    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.get("/api/manufacturer/water-heaters/")

        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return 0, []

        water_heaters = response.json()
        water_heater_count = len(water_heaters)

        # Count by manufacturer
        manufacturer_counts = {}
        for wh in water_heaters:
            manufacturer = wh.get("manufacturer", "Unknown")
            manufacturer_counts[manufacturer] = (
                manufacturer_counts.get(manufacturer, 0) + 1
            )

        print(f"API returns {water_heater_count} water heaters")
        print("Manufacturers in API response:")
        for manufacturer, count in manufacturer_counts.items():
            print(f"  - {manufacturer}: {count} water heater(s)")

        return water_heater_count, manufacturer_counts


def count_ui_water_heaters() -> Tuple[int, Dict[str, int]]:
    """Count water heaters displayed in the UI using Puppeteer."""
    print("\nChecking UI display with Puppeteer...")

    # Path to the Puppeteer script
    puppeteer_script_path = os.path.join(
        project_root, "src/scripts/puppeteer_count_water_heaters.js"
    )

    # Create the Puppeteer script if it doesn't exist
    if not os.path.exists(puppeteer_script_path):
        with open(puppeteer_script_path, "w") as f:
            f.write(
                """
 const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Navigate to the water heaters page
    console.log('Navigating to water heaters page...');
    await page.goto('http://localhost:8006/water-heaters', { waitUntil: 'networkidle0' });

    // Wait for the water heater cards to load
    await page.waitForSelector('.heater-card', { timeout: 10000 });

    // Take a screenshot for verification
    await page.screenshot({ path: 'ui_validation_screenshot.png' });
    console.log('Screenshot saved to: ui_validation_screenshot.png');

    // Count the water heater cards
    const waterHeaterCount = await page.evaluate(() => {
      const cards = document.querySelectorAll('.heater-card');
      return cards.length;
    });

    // Extract manufacturer information from each card
    const manufacturerCounts = await page.evaluate(() => {
      const manufacturers = {};
      const cards = document.querySelectorAll('.heater-card');

      cards.forEach(card => {
        let manufacturer = 'Unknown';
        const manufacturerElement = card.querySelector('.manufacturer');

        if (manufacturerElement) {
          manufacturer = manufacturerElement.textContent.trim();
        }

        manufacturers[manufacturer] = (manufacturers[manufacturer] || 0) + 1;
      });

      return manufacturers;
    });

    // Output the results as JSON
    const results = {
      waterHeaterCount,
      manufacturerCounts
    };

    console.log(JSON.stringify(results));
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
            """
            )

    # Check if Node.js and Puppeteer are installed
    try:
        # Run the Puppeteer script
        result = subprocess.run(
            ["node", puppeteer_script_path], capture_output=True, text=True, check=True
        )

        # Parse the JSON output
        output_lines = result.stdout.strip().split("\n")
        json_line = next((line for line in output_lines if line.startswith("{")), None)

        if not json_line:
            print("Error: Could not find JSON output from Puppeteer script")
            print(f"Script output: {result.stdout}")
            return 0, {}, []

        data = json.loads(json_line)
        water_heater_count = data.get("waterHeaterCount", 0)
        manufacturer_counts = data.get("manufacturerCounts", {})
        heater_details = data.get("heaterDetails", [])
        empty_state_text = data.get("emptyStatePresent")
        page_content_summary = data.get("pageContentSummary", "")

        print(f"UI displays {water_heater_count} water heaters")

        # If we have an empty state message, display it
        if empty_state_text:
            print(f"\nEmpty state message found: '{empty_state_text}'")

        # Show page content summary if no water heaters found
        if water_heater_count == 0:
            print("\nPage content summary:")
            print(f"{page_content_summary[:200]}...")

        print("Manufacturers in UI:")
        for manufacturer, count in manufacturer_counts.items():
            print(f"  - {manufacturer}: {count} water heater(s)")

        # Print detailed information about the first few water heaters
        if heater_details:
            print("\nSample water heaters in UI:")
            for i, heater in enumerate(heater_details[:3]):
                print(
                    f"  {i+1}. ID: {heater['id']}, Name: {heater.get('name', 'Unknown')}, Manufacturer: {heater.get('manufacturer', 'Unknown')}"
                )

            # Check for duplicate IDs
            id_counts = {}
            for heater in heater_details:
                hid = heater["id"]
                id_counts[hid] = id_counts.get(hid, 0) + 1

            # Report duplicates if found
            duplicates = {hid: count for hid, count in id_counts.items() if count > 1}
            if duplicates:
                print("\nDUPLICATE WATER HEATERS DETECTED:")
                print(
                    f"Found {len(duplicates)} water heaters appearing multiple times in the UI"
                )
                for hid, count in duplicates.items():
                    print(f"  - ID: {hid} appears {count} times")

        # Return additional heater details for complete validation
        return water_heater_count, manufacturer_counts, heater_details
    except subprocess.CalledProcessError as e:
        print(f"Error running Puppeteer script: {e}")
        print(f"Stderr: {e.stderr}")
        return 0, {}, []
    except Exception as e:
        print(f"Error: {e}")
        return 0, {}, []


async def main():
    """Run the validation tests."""
    print("=========================================")
    print("IoTSphere UI Data Validation")
    print("=========================================")

    # Count water heaters in the database
    db_count, db_manufacturers = await count_db_water_heaters()

    # Count water heaters in the API response
    api_count, api_manufacturers = await count_api_water_heaters()

    # Count water heaters in the UI
    ui_count, ui_manufacturers, ui_heater_details = count_ui_water_heaters()

    # Validate counts
    print("\n=========================================")
    print("Validation Results")
    print("=========================================")
    db_api_match = db_count == api_count
    api_ui_match = api_count == ui_count

    print(
        f"Database count ({db_count}) matches API count ({api_count}): {db_api_match}"
    )
    print(f"API count ({api_count}) matches UI count ({ui_count}): {api_ui_match}")

    if db_api_match and api_ui_match:
        print("\n✅ VALIDATION PASSED: All counts match!")
        print(
            "The UI is correctly displaying only the water heaters from the database."
        )
    else:
        print("\n❌ VALIDATION FAILED: Counts don't match!")
        print(
            "The UI may be displaying mock water heaters or missing some database entries."
        )

    print("\nManufacturer comparison:")
    # Extract just string manufacturer names from db_manufacturers to avoid Record objects
    db_manufacturer_names = [
        m["manufacturer"]
        for m in db_manufacturers
        if isinstance(m["manufacturer"], str)
    ]

    # Get unique manufacturer names across all sources, but only use string values
    all_manufacturers = set()
    all_manufacturers.update(db_manufacturer_names)
    all_manufacturers.update(api_manufacturers.keys())
    all_manufacturers.update(ui_manufacturers.keys())

    for manufacturer in all_manufacturers:
        db_mfr_count = next(
            (m["count"] for m in db_manufacturers if m["manufacturer"] == manufacturer),
            0,
        )
        api_mfr_count = api_manufacturers.get(manufacturer, 0)
        ui_mfr_count = ui_manufacturers.get(manufacturer, 0)

        match = db_mfr_count == api_mfr_count == ui_mfr_count
        status = "✅" if match else "❌"

        print(
            f"{status} {manufacturer}: DB={db_mfr_count}, API={api_mfr_count}, UI={ui_mfr_count}"
        )


if __name__ == "__main__":
    asyncio.run(main())
