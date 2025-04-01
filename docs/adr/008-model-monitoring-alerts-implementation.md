# ADR-008: Model Monitoring Alerts Implementation

## Status

Accepted (April 2025)

## Context

The IoTSphere platform requires a robust monitoring system that can track machine learning model performance, detect anomalies, and alert stakeholders to potential issues. This functionality is critical for ensuring model performance remains within expected parameters and that stakeholders are promptly notified of issues requiring attention.

Initial implementation of the monitoring alerts system had several issues:
- Alerts created in the database weren't displaying in the Recent Alerts section
- The `/api/monitoring/alerts` endpoint was returning empty arrays instead of actual alert data
- Frontend routes for monitoring pages were returning 404 errors
- The system was using mock data instead of real database information even when explicitly configured not to

## Decision

We have implemented a comprehensive monitoring alerts system following Test-Driven Development (TDD) principles:

1. **Data Source Configuration**: 
   - Explicit support for both mock and real data sources
   - Environment variable `USE_MOCK_DATA=False` to use real database data

2. **Database Schema**:
   - Direct SQLite connection for reliable data retrieval
   - Schema includes `models`, `alert_rules`, and `alert_events` tables

3. **API Response Format**:
   - Formatted API responses to match frontend expectations
   - Added required fields: model_name, version, status
   - Standardized field naming

4. **Web Routing**:
   - Fixed routes for `/monitoring` and `/monitoring/alerts`
   - Proper template rendering with Jinja2

5. **Testing Approach**:
   - End-to-end tests to verify the complete alert workflow
   - Selenium-based frontend testing to validate JavaScript rendering

## Consequences

### Positive Consequences

- The monitoring system now correctly displays all alerts in the frontend
- New models appear in the model filter dropdown
- All models and alerts are retrieved from the database when `USE_MOCK_DATA=False`
- End-to-end tests validate the full alert flow from creation to display
- The system adheres to TDD principles by adapting code to match expected behaviors
- Improved developer experience with comprehensive documentation

### Negative Consequences

- Adds complexity to manage both mock and real data sources
- Requires maintaining compatibility with existing frontend expectations
- End-to-end testing includes some steps that only pass when manually verified

## Alternatives Considered

1. **Changing Frontend Expectations**: We could have modified the frontend JavaScript to match our backend API format, but this would violate our TDD principle of adapting implementations to match tests and expected behaviors, not vice versa.

2. **Creating a New API Version**: We considered implementing a new version of the API with improved formats, but maintaining backward compatibility would be more complex than adapting our current implementation.

## References

- [Monitoring & Alerts Architecture](../monitoring-alerts-architecture.md)
- [API Documentation](../api-documentation.md) - See Model Monitoring API section
- [Architecture Overview](../architecture-overview.md)
