#!/usr/bin/env python3
"""
Performance Testing Script for IoTSphere
Measures startup time and response times for critical operations
"""
import asyncio
import time
import sys
import os
import requests
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8006"
ENDPOINTS = [
    "/",
    "/dashboard",
    "/water-heaters",
    "/api/water-heaters",
    "/api/shadow-documents/status"
]
TIMEOUT = 5  # seconds
RETRY_COUNT = 3
CONCURRENCY = 3

async def measure_startup_time():
    """Measure how long it takes for the server to start responding"""
    logger.info("Measuring server startup time...")
    start_time = time.time()
    max_wait = 30  # seconds
    
    while (time.time() - start_time) < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                elapsed = time.time() - start_time
                logger.info(f"Server responded after {elapsed:.2f} seconds")
                return elapsed
        except requests.exceptions.RequestException:
            await asyncio.sleep(0.5)
    
    logger.error(f"Server did not respond within {max_wait} seconds")
    return max_wait

async def test_endpoint(endpoint):
    """Test response time for a specific endpoint"""
    url = f"{BASE_URL}{endpoint}"
    logger.info(f"Testing endpoint: {url}")
    
    total_time = 0
    success_count = 0
    
    for i in range(RETRY_COUNT):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=TIMEOUT)
            elapsed = time.time() - start_time
            
            status = response.status_code
            success = 200 <= status < 300
            
            if success:
                success_count += 1
                total_time += elapsed
                
            logger.info(f"  Attempt {i+1}: status={status}, time={elapsed:.2f}s, success={success}")
            
            # Check for specific MongoDB-related errors in response
            if "MongoDB" in response.text or "mongo" in response.text.lower():
                if "error" in response.text.lower() or "failed" in response.text.lower():
                    logger.warning(f"MongoDB error detected in response: {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            logger.warning(f"  Attempt {i+1}: Request timed out after {TIMEOUT}s")
        except requests.exceptions.RequestException as e:
            logger.warning(f"  Attempt {i+1}: Request failed: {str(e)}")
    
    if success_count > 0:
        avg_time = total_time / success_count
        logger.info(f"  Average response time: {avg_time:.2f}s (success rate: {success_count}/{RETRY_COUNT})")
        return avg_time
    else:
        logger.error(f"  All requests failed for {endpoint}")
        return None

async def analyze_mongodb_connection():
    """Specifically analyze MongoDB connection time"""
    logger.info("Analyzing MongoDB connection performance...")
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/diagnostics/mongo-connection", timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            logger.info(f"MongoDB connection test completed in {elapsed:.2f}s")
            logger.info(f"Response: {response.text}")
            return elapsed
        else:
            logger.error(f"MongoDB connection test failed with status {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"MongoDB connection test failed: {str(e)}")
        return None

async def main():
    """Run performance tests"""
    logger.info("Starting IoTSphere performance test")
    
    # Measure startup time
    startup_time = await measure_startup_time()
    
    # Test MongoDB connection specifically
    mongo_time = await analyze_mongodb_connection()
    
    # Test endpoints concurrently
    logger.info(f"Testing {len(ENDPOINTS)} endpoints with concurrency={CONCURRENCY}")
    
    tasks = []
    for endpoint in ENDPOINTS:
        tasks.append(test_endpoint(endpoint))
    
    # Run up to CONCURRENCY tasks at a time
    results = []
    for i in range(0, len(tasks), CONCURRENCY):
        batch = tasks[i:i+CONCURRENCY]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)
    
    # Calculate overall statistics
    successful_times = [t for t in results if t is not None]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        max_time = max(successful_times)
        min_time = min(successful_times)
        
        logger.info("\nPerformance Summary:")
        logger.info(f"Server startup time: {startup_time:.2f}s")
        if mongo_time:
            logger.info(f"MongoDB connection time: {mongo_time:.2f}s")
        logger.info(f"Average response time: {avg_time:.2f}s")
        logger.info(f"Min response time: {min_time:.2f}s")
        logger.info(f"Max response time: {max_time:.2f}s")
        logger.info(f"Success rate: {len(successful_times)}/{len(results)} endpoints")
    else:
        logger.error("All endpoint tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
