"""
Test script to verify model monitoring functionality with new environment-based configuration.
"""
import os
import sys
import asyncio
from datetime import datetime
from pprint import pprint

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

# Import required components
from src.monitoring.model_monitoring_service import ModelMonitoringService
from src.monitoring.metrics import MetricType


async def test_model_monitoring():
    print("\n===== Testing Model Monitoring Service =====\n")
    
    # Create the service using our environment-based configuration
    monitoring_service = ModelMonitoringService()
    
    # Test: Record model metrics
    print("\n----- Recording Model Metrics -----")
    model_id = "test-water-heater-model-1"
    model_version = "1.0.0"
    metrics = {
        "accuracy": 0.92,
        "precision": 0.91,
        "recall": 0.89,
        "f1_score": 0.90,
        "drift_score": 0.05
    }
    
    # This is an async method that needs to be awaited
    metric_id = await monitoring_service._record_model_metrics_async(model_id, model_version, metrics)
    print(f"Recorded metrics with ID: {metric_id}")
    
    # Test: Get model list
    print("\n----- Getting Model List -----")
    models = await monitoring_service.get_models()
    print(f"Found {len(models)} models")
    if models:
        print("Sample model:")
        pprint(models[0])
    
    # Test: Get metrics for a model
    print("\n----- Getting Model Metrics -----")
    metrics_data, is_mock = await monitoring_service.get_latest_metrics(model_id, model_version)
    print(f"Retrieved metrics for model (is_mock={is_mock})")
    if metrics_data:
        print("Latest metrics:")
        pprint(metrics_data)
    
    # Test: Create and get alert rules
    print("\n----- Testing Alert Rules -----")
    try:
        rule_id, is_mock = await monitoring_service.create_alert_rule(
            model_id=model_id,
            metric_name="accuracy",
            threshold=0.90,
            condition="BELOW",
            severity="WARNING"
        )
        print(f"Created alert rule with ID: {rule_id} (is_mock={is_mock})")
        
        rules, is_mock = await monitoring_service.get_alert_rules(model_id)
        print(f"Retrieved {len(rules)} alert rules (is_mock={is_mock})")
        if rules:
            print("Sample rule:")
            pprint(rules[0])
        
        # Test: Check for alerts
        print("\n----- Checking for Alerts -----")
        alert_events, is_mock = await monitoring_service.get_triggered_alerts(model_id)
        print(f"Found {len(alert_events)} triggered alerts (is_mock={is_mock})")
    except Exception as e:
        print(f"Error in alert tests: {e}")
    
    # Test: Check configuration source
    print("\n----- Configuration Source -----")
    print(f"Using mock data: {monitoring_service.using_mock_data}")
    print(f"Drift threshold: {monitoring_service.drift_threshold}")
    print(f"Accuracy threshold: {monitoring_service.accuracy_threshold}")
    print(f"Metrics retention days: {monitoring_service.metrics_retention_days}")
    
    print("\n===== Test Completed =====")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_model_monitoring())
