# ADR-011: Model Monitoring Environment-Based Configuration

## Status

Accepted

## Context

Previously, the IoTSphere project implemented an environment-based configuration system for the Water Heater service (ADR-010), which allowed for different settings based on the execution environment (development, staging, production) and provided a robust fallback mechanism when database connections fail.

However, the Model Monitoring service was still using a mix of hardcoded settings and environment variables, creating inconsistencies in how configuration was managed across services. This made it difficult to:

1. Apply different monitoring thresholds and settings across environments
2. Maintain consistent behavior when database connections fail
3. Properly test the monitoring service with different configurations
4. Update settings without code changes

## Decision

We will update the Model Monitoring service to follow the same environment-based configuration pattern implemented for the Water Heater service. This includes:

1. **YAML Configuration Files**:
   - Use the central `config.yaml`, `development.yaml`, and `production.yaml` files
   - Define environment-specific monitoring settings (thresholds, retention periods, etc.)

2. **Consistent Data Source Configuration**:
   - Use `services.monitoring.use_mock_data` to control database usage
   - Support `services.monitoring.fallback_to_mock` for controlling fallback behavior

3. **Environment-Specific Thresholds**:
   - Different drift and accuracy thresholds for development vs. production
   - Environment-specific alert configuration and notification settings

4. **Loading Configuration Through ConfigurationService**:
   - Use the established `config` module to retrieve settings
   - Respect the application environment hierarchy

## Consequences

### Advantages

1. **Consistency**: The Model Monitoring service now follows the same configuration pattern as other services
2. **Environment-Awareness**: Model health thresholds and alert settings can be tuned per environment
3. **Robustness**: Proper fallback behavior when database connections fail
4. **Maintainability**: Configuration changes without code modifications
5. **Testability**: Easier testing with different configuration profiles

### Disadvantages

1. **Migration Effort**: Required modifying existing Model Monitoring service code
2. **Backward Compatibility**: Needed to maintain support for legacy environment variable settings
3. **Learning Curve**: Developers must understand the configuration hierarchy

## Implementation Details

### Configuration Structure

```yaml
services:
  monitoring:
    use_mock_data: false
    fallback_to_mock: true
    metrics_retention_days: 90
    model_health:
      drift_threshold: 0.15
      accuracy_threshold: 0.85
    alerts:
      enabled: true
      check_interval: 300
      notification_channels:
        email: true
        slack: false
        webhook: false
```

### Repository and Service Modifications

1. **ModelMetricsRepository**:
   - Updated to load settings from configuration service
   - Added configurable fallback mechanism
   - Maintained backward compatibility with environment variables

2. **ModelMonitoringService**:
   - Modified to use configuration for thresholds and settings
   - Environment-specific alert configuration
   - Proper initialization with fallback support

### Documentation and Testing

1. Updated documentation to reflect the new configuration approach
2. Enhanced tests to verify behavior with different configurations
3. Added sample configuration examples for various environments
