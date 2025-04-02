# ADR-010: Water Heater Configuration Management

## Status

Accepted

## Context

The IoTSphere application needs to manage water heater devices with a configuration system similar to the existing model monitoring configuration. This includes:

1. Making data sources configurable (mock vs. database)
2. Supporting health status configuration for water heaters
3. Implementing alert rule management
4. Following Test-Driven Development (TDD) principles

The current water heater implementation uses hard-coded data sources and lacks configuration options for health status and alerts, making it difficult to customize behavior without code changes.

## Decision

We will implement a configurable repository pattern for water heaters with the following components:

1. **Repository Interface**: Define a `WaterHeaterRepository` interface with all required operations
2. **Mock Implementation**: Create a `MockWaterHeaterRepository` for testing and development
3. **SQLite Implementation**: Develop a `SQLiteWaterHeaterRepository` for production use
4. **Configurable Service**: Build a `ConfigurableWaterHeaterService` that chooses the appropriate repository based on configuration
5. **Configuration Management**: Add database tables and methods for health status configuration and alert rules

The implementation will strictly follow Test-Driven Development by:
- Writing tests first to define the expected behavior
- Implementing code to satisfy the tests
- Refactoring while maintaining test coverage

## Consequences

### Advantages

1. **Configurability**: Water heater behavior can be modified through configuration rather than code changes
2. **Testability**: Mock implementations facilitate easier testing of dependent components
3. **Consistency**: The approach aligns with the existing model monitoring configuration design
4. **Maintainability**: Clear separation of concerns between repositories, services, and API endpoints
5. **Documentation**: Tests provide living documentation of expected behavior

### Disadvantages

1. **Complexity**: Introduces more abstraction layers and interfaces
2. **Learning Curve**: Team members need to understand the repository pattern and configuration system
3. **Migration**: Existing code may need updates to use the new configurable approach

## Implementation Details

### Repository Interface

```python
class WaterHeaterRepository(ABC):
    @abstractmethod
    async def get_water_heaters(self) -> List[WaterHeater]:
        pass

    @abstractmethod
    async def get_water_heater(self, device_id: str) -> Optional[WaterHeater]:
        pass

    # Additional methods...

    @abstractmethod
    async def get_health_configuration(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def set_health_configuration(self, config: Dict[str, Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        pass
```

### Configuration Database Schema

The database schema includes tables for:

1. **water_heaters**: Core water heater data
2. **water_heater_readings**: Temperature and other readings
3. **water_heater_diagnostic_codes**: Error and diagnostic information
4. **water_heater_health_config**: Health status thresholds and configuration
5. **water_heater_alert_rules**: Rules for generating alerts

### Environment Configuration

The implementation uses environment variables to toggle between repositories:

```python
use_mock_data = os.environ.get("USE_MOCK_DATA", "True").lower() in ["true", "1", "yes"]
```

## References

- ADR-009: Model Monitoring Health Configuration
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Test-Driven Development](https://www.agilealliance.org/glossary/tdd/)
