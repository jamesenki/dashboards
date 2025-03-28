# Model Monitoring Dashboard Tests

## Overview
This directory contains tests for the model monitoring dashboard functionality of IoTSphere, following Test-Driven Development (TDD) principles. These tests define the expected behavior of the model monitoring components before implementation.

## Components Tested

### 1. Model Monitoring Service
The `test_model_monitoring_service.py` file tests the core functionality for tracking and analyzing model performance metrics:

- Recording model performance metrics
- Retrieving metric history 
- Creating alert rules for metric thresholds
- Checking for triggered alerts
- Calculating model drift between versions
- Generating performance summaries and reports

### 2. Monitoring Dashboard API
The `test_monitoring_dashboard_api.py` file tests the REST API endpoints that expose the monitoring functionality:

- Retrieving model information
- Accessing performance metrics
- Creating and managing alert rules
- Calculating drift between model versions
- Exporting performance reports

## Test Design Principles

All tests follow these TDD principles:

1. **Red**: Tests are written first to define the expected behavior
2. **Green**: Implementation is written to make the tests pass
3. **Refactor**: Code is improved while ensuring tests continue to pass

## Key Test Scenarios

- **Metric Tracking**: Tests verify that model metrics are correctly recorded and retrieved
- **Historical Analysis**: Tests ensure the system can analyze performance trends over time
- **Alert System**: Tests validate that alerts are triggered when metrics cross thresholds
- **Model Drift Detection**: Tests confirm the system can detect and quantify model drift
- **Reporting**: Tests verify that the system can generate useful performance reports

## Running the Tests

```bash
# Run all monitoring tests
python -m pytest src/tests/unit/monitoring/

# Run specific test file
python -m pytest src/tests/unit/monitoring/test_model_monitoring_service.py -v

# Run specific test case
python -m pytest src/tests/unit/monitoring/test_model_monitoring_service.py::TestModelMonitoringService::test_record_model_metrics -v
```

## Implementation Requirements

Based on these tests, we need to implement:

1. `src/monitoring/metrics.py` - Data models for performance metrics
2. `src/monitoring/alerts.py` - Alert rule definitions and alert processing
3. `src/monitoring/model_monitoring_service.py` - Core service for monitoring functionality
4. `src/monitoring/dashboard_api.py` - FastAPI endpoints for the dashboard