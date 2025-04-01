"""
Verification script to test the API endpoints directly.
This will help confirm that our fixes are working correctly.
"""
import asyncio
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8006"

async def main():
    logger.info("=== Starting API Verification ===")
    
    # Test the monitoring dashboard endpoints
    models_url = f"{BASE_URL}/api/monitoring/models"
    try:
        models_response = requests.get(models_url)
        logger.info(f"Models endpoint returned status: {models_response.status_code}")
        
        if models_response.status_code == 200:
            # Parse the response appropriately based on its actual format
            models_data = models_response.json()
            logger.info(f"Response type: {type(models_data)}")
            
            # Check if it's a dictionary with 'models' key or a list directly
            if isinstance(models_data, dict) and 'models' in models_data:
                model_count = len(models_data.get("models", []))
                is_mock = models_data.get("is_mock_data", True)
                models_list = models_data.get("models", [])
                logger.info(f"Models returned: {model_count}, is_mock: {is_mock}")
            elif isinstance(models_data, list):
                # Handle case where response is a list directly
                models_list = models_data
                model_count = len(models_list)
                is_mock = False  # Assume real data if not specified
                logger.info(f"Models returned (list format): {model_count}")
            else:
                logger.error(f"Unexpected response format: {models_data}")
                return
            
            if model_count > 0:
                # Get the first model for testing based on the response format
                if isinstance(models_data, dict) and 'models' in models_data:
                    test_model = models_data["models"][0]
                else:
                    test_model = models_list[0]
                
                # Handle different model object structures
                if isinstance(test_model, dict):
                    model_id = test_model.get("id", "test-model-1")
                    # Try different possible keys for version
                    if "versions" in test_model and isinstance(test_model["versions"], list) and test_model["versions"]:
                        model_version = test_model["versions"][0]
                    elif "version" in test_model:
                        model_version = test_model["version"]
                    else:
                        model_version = "1.0"  # Default version if not found
                else:
                    # If model is not a dict, use default values
                    model_id = "test-model-1"
                    model_version = "1.0"
                
                logger.info(f"Testing with model_id: {model_id}, version: {model_version}")
                
                # Test the alert rules endpoint
                rules_url = f"{BASE_URL}/api/monitoring/models/{model_id}/versions/{model_version}/alerts/rules"
                rules_response = requests.get(rules_url)
                logger.info(f"Alert rules endpoint returned status: {rules_response.status_code}")
                
                if rules_response.status_code == 200:
                    rules_data = rules_response.json()
                    rules = rules_data.get("rules", [])
                    is_mock_rules = rules_data.get("is_mock_data", True)
                    
                    logger.info(f"Rules count: {len(rules)}, is_mock: {is_mock_rules}")
                    logger.info(f"Rules data structure type: {type(rules)}")
                    
                    if len(rules) > 0:
                        logger.info(f"Sample rule: {json.dumps(rules[0], indent=2)}")
                    else:
                        logger.info("No rules returned (empty array)")
                
                # Test the alerts endpoint
                alerts_url = f"{BASE_URL}/api/monitoring/models/{model_id}/versions/{model_version}/alerts"
                alerts_response = requests.get(alerts_url)
                logger.info(f"Alerts endpoint returned status: {alerts_response.status_code}")
                
                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    alerts = alerts_data.get("alerts", [])
                    is_mock_alerts = alerts_data.get("is_mock_data", True)
                    
                    logger.info(f"Alerts count: {len(alerts)}, is_mock: {is_mock_alerts}")
                    logger.info(f"Alerts data structure type: {type(alerts)}")
                    
                    if len(alerts) > 0:
                        logger.info(f"Sample alert: {json.dumps(alerts[0], indent=2)}")
                    else:
                        logger.info("No alerts returned (empty array)")
            else:
                logger.warning("No models returned to test with")
        else:
            logger.error(f"Failed to get models: {models_response.text}")
            
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
    
    logger.info("=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(main())
