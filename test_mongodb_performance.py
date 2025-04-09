#!/usr/bin/env python3
"""
MongoDB Performance Test Script

This script tests the performance of both the original and optimized MongoDB storage implementations
to demonstrate the performance improvements with time series collections and connection pooling.
"""
import asyncio
import logging
import os
import statistics
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to Python path
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def run_performance_test():
    """Run comparative performance tests for MongoDB storage implementations"""

    # Save original environment variables
    original_storage_type = os.environ.get("SHADOW_STORAGE_TYPE")
    original_optimized = os.environ.get("USE_OPTIMIZED_MONGODB")

    try:
        # Test Setup
        device_id = "wh-001"  # Test device
        test_iterations = 10  # Number of test iterations

        # ----- Test Standard MongoDB Implementation -----
        os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
        os.environ["USE_OPTIMIZED_MONGODB"] = "false"

        logger.info("🔍 Testing standard MongoDB implementation...")
        from src.infrastructure.device_shadow.mongodb_shadow_storage import (
            MongoDBShadowStorage,
        )

        standard_storage = MongoDBShadowStorage(
            mongo_uri=os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
            db_name=os.environ.get("MONGODB_DB_NAME", "iotsphere"),
        )
        await standard_storage.initialize()

        # Test 1: Shadow Document Retrieval
        standard_get_times = []
        for i in range(test_iterations):
            start_time = time.time()
            shadow = await standard_storage.get_shadow(device_id)
            end_time = time.time()
            standard_get_times.append((end_time - start_time) * 1000)  # Convert to ms

        # Test 2: History Retrieval (last 24 hours)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        standard_history_times = []
        for i in range(test_iterations):
            perf_start = time.time()
            # Standard implementation only takes device_id and limit
            history = await standard_storage.get_shadow_history(device_id, limit=100)
            perf_end = time.time()
            standard_history_times.append(
                (perf_end - perf_start) * 1000
            )  # Convert to ms

        await standard_storage.close()

        # ----- Test Optimized MongoDB Implementation -----
        os.environ["SHADOW_STORAGE_TYPE"] = "mongodb"
        os.environ["USE_OPTIMIZED_MONGODB"] = "true"

        logger.info("🔍 Testing optimized MongoDB implementation...")
        from src.infrastructure.device_shadow.optimized_mongodb_storage import (
            OptimizedMongoDBShadowStorage,
        )

        optimized_storage = OptimizedMongoDBShadowStorage(
            mongo_uri=os.environ.get("MONGODB_URI", "mongodb://localhost:27017/"),
            db_name=os.environ.get("MONGODB_DB_NAME", "iotsphere"),
            pool_size=int(os.environ.get("MONGODB_POOL_SIZE", "20")),
        )
        await optimized_storage.initialize()

        # Test 1: Shadow Document Retrieval
        optimized_get_times = []
        for i in range(test_iterations):
            start_time = time.time()
            shadow = await optimized_storage.get_shadow(device_id)
            end_time = time.time()
            optimized_get_times.append((end_time - start_time) * 1000)  # Convert to ms

        # Test 2: History Retrieval (last 24 hours)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        optimized_history_times = []
        for i in range(test_iterations):
            perf_start = time.time()
            # Optimized implementation takes start_time and end_time parameters
            history = await optimized_storage.get_shadow_history(
                device_id, limit=100, start_time=start_time, end_time=end_time
            )
            perf_end = time.time()
            optimized_history_times.append(
                (perf_end - perf_start) * 1000
            )  # Convert to ms

        await optimized_storage.close()

        # ----- Display Results -----
        logger.info("\n📊 PERFORMANCE TEST RESULTS")
        logger.info("=" * 50)

        # Shadow Document Retrieval
        std_avg = statistics.mean(standard_get_times)
        opt_avg = statistics.mean(optimized_get_times)
        improvement = ((std_avg - opt_avg) / std_avg) * 100 if std_avg > 0 else 0

        logger.info("\n🔹 Shadow Document Retrieval (ms)")
        logger.info(
            f"  Standard Implementation:  Avg: {std_avg:.2f}ms, Min: {min(standard_get_times):.2f}ms, Max: {max(standard_get_times):.2f}ms"
        )
        logger.info(
            f"  Optimized Implementation: Avg: {opt_avg:.2f}ms, Min: {min(optimized_get_times):.2f}ms, Max: {max(optimized_get_times):.2f}ms"
        )
        logger.info(f"  Performance Improvement:  {improvement:.1f}%")

        # History Retrieval
        std_avg = statistics.mean(standard_history_times)
        opt_avg = statistics.mean(optimized_history_times)
        improvement = ((std_avg - opt_avg) / std_avg) * 100 if std_avg > 0 else 0

        logger.info("\n🔹 24h History Retrieval (ms)")
        logger.info(
            f"  Standard Implementation:  Avg: {std_avg:.2f}ms, Min: {min(standard_history_times):.2f}ms, Max: {max(standard_history_times):.2f}ms"
        )
        logger.info(
            f"  Optimized Implementation: Avg: {opt_avg:.2f}ms, Min: {min(optimized_history_times):.2f}ms, Max: {max(optimized_history_times):.2f}ms"
        )
        logger.info(f"  Performance Improvement:  {improvement:.1f}%")

        logger.info("\n🔹 Key Optimizations")
        logger.info("  ✅ Time Series Collections for temporal data")
        logger.info("  ✅ Connection Pooling (pool size: 20)")
        logger.info("  ✅ Shadow Document Caching")
        logger.info("  ✅ Separate Storage of History Data")

    finally:
        # Restore original environment variables
        if original_storage_type:
            os.environ["SHADOW_STORAGE_TYPE"] = original_storage_type
        if original_optimized:
            os.environ["USE_OPTIMIZED_MONGODB"] = original_optimized


if __name__ == "__main__":
    asyncio.run(run_performance_test())
