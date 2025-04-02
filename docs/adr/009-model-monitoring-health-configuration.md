# ADR-009: Model Monitoring Health Status and Configuration Management

## Status

Accepted (April 2025)

## Context

The IoTSphere platform's model monitoring system requires a robust configuration management approach to track model health, display appropriate status indicators, and manage alert configurations. During implementation, we encountered several challenges:

1. **Health Status Display**: Models were showing "Unknown" status on the Models page despite having valid health data.
2. **Model Version Management**: Only certain models were appearing in dropdown menus for monitoring.
3. **Alert Configuration**: Alert rules needed to be properly configured for different model types.
4. **Data Structure Consistency**: Frontend and backend had different expectations about data structure.

These issues impacted the usability of the monitoring dashboard and undermined confidence in the system's ability to accurately track model health.

## Decision

We've implemented a comprehensive model health and configuration management system following these principles:

1. **Model Version and Health Tables**:
   - Created dedicated `model_versions` table to track all versions for each model
   - Implemented `model_health` table to store detailed health status information
   - Established `model_health_reference` for quick lookup of the latest health status
   - Created database views (`model_health_view` and `model_display_view`) for simplified queries

2. **Health Status Representation**:
   - Standardized health status values: `GREEN`, `YELLOW`, `RED` (matching frontend expectations)
   - Placed health status values in both the model object and its metrics dictionary
   - Set appropriate default values when health status is unavailable

3. **Configuration Scripts**:
   - Created database initialization scripts to ensure consistent setup
   - Developed utilities to populate model versions and alert rules
   - Implemented scripts to update health status formats when needed

4. **Frontend-Backend Integration**:
   - Modified API responses to match frontend expectations exactly
   - Ensured all required fields exist in the appropriate structure
   - Added fallback values when real data is unavailable

5. **Alert System**:
   - Created model-type specific alert templates (water heater models, energy models, etc.)
   - Set appropriate thresholds based on the model's purpose and metrics
   - Integrated alert status with overall health determination

## Rationale

### TDD Compliance
- Following the project's established commitment to Test-Driven Development
- Modifying implementation code to pass tests rather than changing tests
- Ensuring test coverage for configuration management functionality

### Data Layer Consistency
- Maintaining a single source of truth for model status
- Creating a normalized database schema that separates concerns
- Using database views to simplify common queries

### Tailored Configurations
- Recognizing that different model types have different requirements
- Providing sensible defaults while allowing customization
- Ensuring model-specific alert rules reflect domain knowledge

### Frontend-Backend Contract
- Respecting the established API contract expected by the frontend
- Ensuring backward compatibility for existing interfaces
- Providing defensive fallbacks for missing data

### Maintainability and Extensibility
- Creating scripts for consistent database initialization
- Documenting the configuration approach for future developers
- Establishing patterns that can be extended to new model types

## Implementation Details

The implementation follows these key patterns:

1. **Database Schema**:
   ```sql
   CREATE TABLE model_versions (
       id TEXT PRIMARY KEY,
       model_id TEXT NOT NULL,
       version TEXT NOT NULL,
       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
       UNIQUE(model_id, version)
   );
   
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

2. **API Response Structure**:
   ```json
   {
     "id": "water-heater-model-1",
     "name": "Water Heater Predictive Model",
     "versions": ["1.0", "1.1"],
     "metrics": {
       "accuracy": 0.92,
       "drift_score": 0.03,
       "health_status": "GREEN"
     },
     "health_status": "GREEN",
     "alert_count": 2,
     "tags": ["production"]
   }
   ```

3. **Model Type-Specific Alert Templates**:
   - Water heater models: accuracy, drift, latency
   - Energy forecasting models: accuracy, consumption patterns
   - Anomaly detection models: precision, recall, F1 score
   - Maintenance prediction models: accuracy, false positives

## Consequences

### Positive
- Consistent health status display across all models
- Proper population of all dropdown menus
- Model-specific alert configurations
- Reliable representation of model health
- Maintainable configuration approach

### Negative
- Increased database complexity with more tables and relationships
- Need for additional initialization scripts
- Some duplication of data (health status in multiple locations)

### Neutral
- Frontend code unchanged, backend adapted to match its expectations

## Future Considerations

1. **Configuration UI**: Develop a UI for managing configurations without scripting
2. **Health Status History**: Track changes in health status over time
3. **Automated Health Checks**: Schedule regular health assessments
4. **Alert Thresholds Tuning**: Use historical data to optimize thresholds
5. **Documentation Generation**: Auto-generate configuration documentation

## References

- ADR-007: Model Monitoring Dashboard with PDF/CSV Export Functionality
- ADR-008: Model Monitoring Alerts Implementation
