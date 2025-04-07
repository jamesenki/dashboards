"""
Test script for water heater history API endpoints
Tests the history endpoints to verify they are returning 200 responses instead of 500 errors
"""
import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "http://localhost:8000"
TEST_HEATER_ID = "wh-123"  # Replace with a valid heater ID if needed

async def test_temperature_history():
    """Test the temperature history endpoint"""
    url = f"{BASE_URL}/api/manufacturer/water-heaters/{TEST_HEATER_ID}/history/temperature"
    params = {"days": 7}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            status = response.status
            if status == 200:
                data = await response.json()
                logger.info(f"✅ Temperature history endpoint returned status 200 with data")
                if "datasets" in data and len(data["datasets"]) > 0:
                    logger.info(f"   - Contains {len(data['datasets'][0]['data'])} data points")
            else:
                text = await response.text()
                logger.error(f"❌ Temperature history endpoint failed with status {status}: {text}")
            
            return status

async def test_energy_usage_history():
    """Test the energy usage history endpoint"""
    url = f"{BASE_URL}/api/manufacturer/water-heaters/{TEST_HEATER_ID}/history/energy-usage"
    params = {"days": 7}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            status = response.status
            if status == 200:
                data = await response.json()
                logger.info(f"✅ Energy usage history endpoint returned status 200 with data")
                if "datasets" in data and len(data["datasets"]) > 0:
                    logger.info(f"   - Contains {len(data['datasets'][0]['data'])} data points")
            else:
                text = await response.text()
                logger.error(f"❌ Energy usage history endpoint failed with status {status}: {text}")
            
            return status

async def test_pressure_flow_history():
    """Test the pressure flow history endpoint"""
    url = f"{BASE_URL}/api/manufacturer/water-heaters/{TEST_HEATER_ID}/history/pressure-flow"
    params = {"days": 7}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            status = response.status
            if status == 200:
                data = await response.json()
                logger.info(f"✅ Pressure flow history endpoint returned status 200 with data")
                if "datasets" in data and len(data["datasets"]) > 0:
                    logger.info(f"   - Contains {len(data['datasets'][0]['data'])} data points")
            else:
                text = await response.text()
                logger.error(f"❌ Pressure flow history endpoint failed with status {status}: {text}")
            
            return status

async def test_history_dashboard():
    """Test the complete history dashboard endpoint"""
    url = f"{BASE_URL}/api/manufacturer/water-heaters/{TEST_HEATER_ID}/history/dashboard"
    params = {"days": 7}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            status = response.status
            if status == 200:
                data = await response.json()
                logger.info(f"✅ History dashboard endpoint returned status 200 with data")
                keys = data.keys()
                logger.info(f"   - Dashboard contains sections: {', '.join(keys)}")
            else:
                text = await response.text()
                logger.error(f"❌ History dashboard endpoint failed with status {status}: {text}")
            
            return status

async def run_tests():
    """Run all tests and report results"""
    logger.info("Starting history API endpoint tests...")
    
    results = []
    results.append(("Temperature History", await test_temperature_history()))
    results.append(("Energy Usage History", await test_energy_usage_history()))
    results.append(("Pressure Flow History", await test_pressure_flow_history()))
    results.append(("History Dashboard", await test_history_dashboard()))
    
    # Print summary
    logger.info("\n=== TEST SUMMARY ===")
    all_passed = True
    for name, status in results:
        if status == 200:
            logger.info(f"✅ {name}: PASSED")
        else:
            logger.error(f"❌ {name}: FAILED (Status {status})")
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All history API endpoints are working correctly!")
    else:
        logger.error("\n❌ Some history API endpoints are still failing!")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(run_tests())
