#!/usr/bin/env python
"""
Test runner script to verify specific functionality without pytest collection issues.
This follows TDD principles by adapting our implementation to work with existing tests.
"""

import os
import sys
import importlib.util
import unittest
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_test_module(file_path):
    """Import a test module from file path"""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_tests_in_module(module):
    """Run all tests found in a module"""
    logger.info(f"Running tests from {module.__name__}")
    
    # Find all test classes
    test_cases = []
    for item_name in dir(module):
        item = getattr(module, item_name)
        if isinstance(item, type) and issubclass(item, unittest.TestCase) and item is not unittest.TestCase:
            test_cases.append(item)
    
    if not test_cases:
        logger.warning(f"No test cases found in {module.__name__}")
        return False
    
    # Create a test suite
    suite = unittest.TestSuite()
    for test_case in test_cases:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def verify_model_monitoring():
    """Verify Model Monitoring functionality"""
    test_files = [
        # Model Monitoring Service Tests
        "src/tests/unit/monitoring/test_model_monitoring_service.py",
        "src/tests/unit/monitoring/test_model_monitoring_service_sync.py",
        # Alert Tests
        "src/tests/unit/monitoring/test_alert_configuration.py",
        "src/tests/unit/monitoring/test_alert_persistence.py",
    ]
    
    success = True
    for file_path in test_files:
        try:
            full_path = os.path.join(os.getcwd(), file_path)
            if not os.path.exists(full_path):
                logger.error(f"File does not exist: {full_path}")
                success = False
                continue
                
            module = import_test_module(full_path)
            if not run_tests_in_module(module):
                success = False
        except Exception as e:
            logger.error(f"Error running tests from {file_path}: {str(e)}")
            success = False
    
    return success

def verify_water_heater():
    """Verify Water Heater functionality"""
    test_files = [
        "src/tests/unit/api/test_water_heater_api.py",
        "src/tests/unit/api/test_water_heater_operations_api.py",
    ]
    
    success = True
    for file_path in test_files:
        try:
            full_path = os.path.join(os.getcwd(), file_path)
            if not os.path.exists(full_path):
                logger.error(f"File does not exist: {full_path}")
                success = False
                continue
                
            module = import_test_module(full_path)
            if not run_tests_in_module(module):
                success = False
        except Exception as e:
            logger.error(f"Error running tests from {file_path}: {str(e)}")
            success = False
    
    return success

def verify_vending_machine():
    """Verify Vending Machine functionality"""
    test_files = [
        "src/tests/unit/api/test_vending_machine_api.py",
        "src/tests/unit/api/test_vending_machine_operrations_api.py",
    ]
    
    success = True
    for file_path in test_files:
        try:
            full_path = os.path.join(os.getcwd(), file_path)
            if not os.path.exists(full_path):
                logger.error(f"File does not exist: {full_path}")
                success = False
                continue
                
            module = import_test_module(full_path)
            if not run_tests_in_module(module):
                success = False
        except Exception as e:
            logger.error(f"Error running tests from {file_path}: {str(e)}")
            success = False
    
    return success

if __name__ == "__main__":
    logger.info("Starting targeted test verification")
    
    monitoring_success = verify_model_monitoring()
    logger.info(f"Model Monitoring tests {'PASSED' if monitoring_success else 'FAILED'}")
    
    water_heater_success = verify_water_heater()
    logger.info(f"Water Heater tests {'PASSED' if water_heater_success else 'FAILED'}")
    
    vending_success = verify_vending_machine()
    logger.info(f"Vending Machine tests {'PASSED' if vending_success else 'FAILED'}")
    
    overall_success = monitoring_success and water_heater_success and vending_success
    
    if overall_success:
        logger.info("✅ All tests passed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed")
        sys.exit(1)
