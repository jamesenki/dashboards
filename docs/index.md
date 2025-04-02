# IoTSphere Documentation

Welcome to the IoTSphere documentation. This documentation follows Test-Driven Development principles and provides comprehensive information about the IoTSphere platform architecture, components, and development guides.

## Documentation Structure

### System Architecture
- [Architecture Principles](system-architecture/architecture-principles.md) - Core principles and standards that guide our architecture
- [Architecture Overview](system-architecture/overview.md) - Comprehensive overview of the IoTSphere platform architecture
- [Component Documentation](system-architecture/components/) - Detailed documentation for individual system components:
  - [Monitoring & Alerts](system-architecture/components/monitoring-alerts.md)
  - [Maintenance Predictions](system-architecture/components/maintenance-predictions.md)
  - [Tab Manager](system-architecture/components/tab-manager.md)
- [Sequence Diagrams](system-architecture/sequences.md) - Visual representations of key system interactions
- [Security Plan](system-architecture/security-plan.md) - System security architecture and implementation

### Development Guides
- [Testing Approach](development-guides/testing-approach.md) - Guide to Test-Driven Development in IoTSphere
- [Coding Standards](development-guides/coding-standards.md) - Development standards and best practices

### Specifications
- [API Documentation](specifications/apis/api-documentation.md) - Complete API reference
- [Data Models](specifications/data-models/) - Database schemas and data models
- [Device Specifications](specifications/devices/) - Device-specific documentation
  - [Water Heaters](specifications/devices/water-heaters/)
    - [Residential](specifications/devices/water-heaters/residential.md)
    - [Commercial](specifications/devices/water-heaters/commercial.md)

### Product Features
- [Dashboard Documentation](product/dashboards/) - Documentation for IoTSphere dashboards
- [Feature Documentation](product/features/) - Documentation for IoTSphere features
  - [Water Heater Dashboard](product/features/water-heater-dashboard.md)

### Architecture Decision Records
- [ADR Directory](adr/) - Architecture Decision Records documenting significant design decisions

## Getting Started

To get started with IoTSphere:

1. Review the [Architecture Overview](system-architecture/overview.md) to understand the system's design
2. Explore the [API Documentation](specifications/apis/api-documentation.md) for integration options
3. Learn about our [Testing Approach](development-guides/testing-approach.md) to understand our development methodology

## Contribution Guidelines

When contributing to the IoTSphere documentation:

1. Follow the established folder structure
2. Ensure diagrams are visible on both light and dark backgrounds
3. Adhere to Test-Driven Development principles
4. Update links and references when moving or renaming files
5. Run verification scripts to ensure all documentation is valid

## Diagram Generation

To generate architecture diagrams:

```bash
./docs/scripts/generate_plantuml_diagrams.sh
```
