# Model Monitoring Configuration Guide

This guide provides detailed information on how to configure and extend the model monitoring system in IoTSphere. It follows Test-Driven Development principles and should be used alongside the test suite.

## Table of Contents

1. [Database Schema](#database-schema)
2. [Health Status Configuration](#health-status-configuration)
3. [Alert Configuration](#alert-configuration)
4. [Adding New Models](#adding-new-models)
5. [API Response Structure](#api-response-structure)
6. [Troubleshooting](#troubleshooting)

## Database Schema

The model monitoring system uses the following key tables:

### Models Table
Stores the base model information:
```sql
CREATE TABLE models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN NOT NULL DEFAULT 0
);
```

### Model Versions Table
Tracks all versions for each model:
```sql
CREATE TABLE model_versions (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    version TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    UNIQUE(model_id, version)
);
```

### Model Metrics Table
Stores performance metrics for model versions:
```sql
CREATE TABLE model_metrics (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);
```

### Model Health Table
Stores detailed health information:
```sql
CREATE TABLE model_health (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    health_status TEXT NOT NULL,
    metrics_summary TEXT,
    drift_status TEXT,
    last_updated TEXT,
    recommendations TEXT,
    FOREIGN KEY (model_id) REFERENCES models (id)
);
```

### Alert Rules Table
Defines conditions for triggering alerts:
```sql
CREATE TABLE alert_rules (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT,
    metric_name TEXT NOT NULL,
    threshold REAL NOT NULL,
    operator TEXT NOT NULL,
    severity TEXT DEFAULT 'WARNING',
    rule_name TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Alert Events Table
Records alert occurrences:
```sql
CREATE TABLE alert_events (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    severity TEXT NOT NULL DEFAULT 'WARNING',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN NOT NULL DEFAULT 0,
    resolved_at TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);
```

## Health Status Configuration

Model health status is a critical component of the monitoring system. The frontend expects health status in a specific format:

### Health Status Values
- `GREEN`: Model is performing well
- `YELLOW`: Model requires attention (drifting or minor issues)
- `RED`: Model has critical issues (degraded performance)
- `GREY`: Status is unknown or unavailable

### Setting Health Status

Health status should be set in both the model object and its metrics dictionary:

```python
# In SQLiteModelMetricsRepository.get_models() or similar methods:
model_info = {
    'id': model_id,
    'name': model_name,
    'versions': versions,
    'archived': archived,
    'metrics': {
        'accuracy': accuracy_value,
        'drift_score': drift_score,
        'health_status': health_status  # Must be in metrics dict
    },
    'health_status': health_status,  # Also at top level
    'alert_count': alert_count,
    'tags': tags
}
```

### Health Status Scripts

We provide several scripts to help with health status management:

1. `set_model_health.py`: Sets health status for all models
2. `update_health_status_format.py`: Updates health status format to match frontend expectations

## Alert Configuration

Alerts are configured based on model type and expected metrics.

### Model-Type Specific Alert Templates

#### Water Heater Models
- **Accuracy Alert**: Threshold 0.85, Operator "<", Severity "HIGH"
- **Drift Alert**: Threshold 0.10, Operator ">", Severity "MEDIUM"
- **Latency Alert**: Threshold 40.0ms, Operator ">", Severity "LOW"

#### Energy Forecasting Models
- **Accuracy Alert**: Threshold 0.87, Operator "<", Severity "HIGH"
- **Drift Alert**: Threshold 0.15, Operator ">", Severity "MEDIUM"

#### Anomaly Detection Models
- **Precision Alert**: Threshold 0.82, Operator "<", Severity "HIGH"
- **Recall Alert**: Threshold 0.85, Operator "<", Severity "MEDIUM"
- **F1 Score Alert**: Threshold 0.83, Operator "<", Severity "MEDIUM"

#### Maintenance Prediction Models
- **Accuracy Alert**: Threshold 0.88, Operator "<", Severity "HIGH"
- **Precision Alert**: Threshold 0.80, Operator "<", Severity "MEDIUM"

### Adding New Alert Rules

Use the following pattern to create new alert rules:

```python
from uuid import uuid4
from datetime import datetime

def create_alert_rule(db, model_id, model_version, metric_name, threshold, operator, severity, rule_name, description):
    """Create a new alert rule in the database."""
    rule_id = str(uuid4())
    timestamp = datetime.now().isoformat()
    
    db.execute("""
    INSERT INTO alert_rules 
        (id, model_id, model_version, metric_name, threshold, operator, 
         severity, rule_name, description, created_at, is_active) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rule_id, model_id, model_version, metric_name, threshold,
        operator, severity, rule_name, description, timestamp, 1
    ))
    
    return rule_id
```

## Adding New Models

When adding new models to the system, ensure all required tables are populated:

### 1. Add the model to the models table
```python
model_id = str(uuid4())
db.execute("""
INSERT INTO models (id, name, description, created_at, updated_at, archived)
VALUES (?, ?, ?, ?, ?, ?)
""", (model_id, model_name, description, timestamp, timestamp, 0))
```

### 2. Add the model's versions
```python
for version in versions:
    version_id = str(uuid4())
    db.execute("""
    INSERT INTO model_versions (id, model_id, version, created_at)
    VALUES (?, ?, ?, ?)
    """, (version_id, model_id, version, timestamp))
```

### 3. Add metrics for each version
```python
for version in versions:
    for metric_name, metric_value in metrics.items():
        metric_id = str(uuid4())
        db.execute("""
        INSERT INTO model_metrics
            (id, model_id, model_version, metric_name, metric_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (metric_id, model_id, version, metric_name, metric_value, timestamp))
```

### 4. Set health status
```python
health_id = str(uuid4())
db.execute("""
INSERT INTO model_health
    (id, model_id, model_version, health_status, metrics_summary, 
     drift_status, last_updated, recommendations)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    health_id, model_id, version, "GREEN", 
    json.dumps(metrics), "normal", timestamp, 
    json.dumps(["Initial model deployment"])
))
```

### 5. Add appropriate alert rules
```python
# Use model-specific alert templates based on model type
if "water-heater" in model_id:
    create_alert_rule(
        db, model_id, version, "accuracy", 0.85, "<", "HIGH",
        "Low Accuracy Alert", "Alert when model accuracy falls below threshold"
    )
    # Add other appropriate rules...
```

## API Response Structure

The API must provide responses in the following structure for the frontend to properly display model information:

### Get Models Endpoint
```json
[
  {
    "id": "water-heater-model-1",
    "name": "Water Heater Predictive Model",
    "versions": ["1.0", "1.1"],
    "archived": false,
    "metrics": {
      "accuracy": 0.92,
      "drift_score": 0.03,
      "health_status": "GREEN"
    },
    "health_status": "GREEN",
    "alert_count": 2,
    "tags": ["production"],
    "data_source": "database"
  },
  {
    "id": "anomaly-detection-1",
    "name": "Anomaly Detection Model",
    "versions": ["0.9", "1.0"],
    "archived": false,
    "metrics": {
      "accuracy": 0.88,
      "drift_score": 0.07,
      "health_status": "YELLOW"
    },
    "health_status": "YELLOW",
    "alert_count": 2,
    "tags": ["development"],
    "data_source": "database"
  }
]
```

### Model Metrics Endpoint
```json
{
  "model_id": "water-heater-model-1",
  "model_version": "1.0",
  "metrics": {
    "accuracy": 0.92,
    "precision": 0.89,
    "recall": 0.88,
    "f1_score": 0.89,
    "drift_score": 0.03,
    "latency_ms": 12.5
  },
  "health_status": "GREEN",
  "last_updated": "2025-04-02T10:15:23.456Z"
}
```

## Troubleshooting

### Health Status Showing as "Unknown"
1. Check that health status is set in both the model and its metrics dictionary
2. Verify the health status values match frontend expectations (GREEN, YELLOW, RED)
3. Check the model_health and model_health_reference tables for the correct model ID
4. Examine the API response structure for any missing fields

### Missing Models in Dropdowns
1. Verify the model exists in the models table
2. Check for entries in the model_versions table for this model ID
3. Ensure there are metrics entries in the model_metrics table
4. Look for SQL errors in the application logs

### Alerts Not Appearing
1. Check the alert_rules table for properly configured rules
2. Verify metric values exceed thresholds in the alert rules
3. Examine the alert_events table for any records
4. Check that the API is returning alert counts correctly

### Script Reference

To maintain the database configuration, use these scripts:

1. `populate_metrics_for_models.py`: Add metrics data for all model versions
2. `configure_model_alerts.py`: Set up alert rules for each model
3. `set_model_health.py`: Configure health status for all models
4. `update_health_status_format.py`: Update health status format to frontend expectations
