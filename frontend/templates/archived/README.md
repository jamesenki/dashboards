# Archived Templates

This directory contains templates that have been archived during the IoTSphere refactoring process. These templates are kept for historical reference but should not be used in production.

## Archival Date
April 10, 2025

## Archived Templates

### water_heater_details.html
This template has been replaced by the more modular approach in `/frontend/templates/water-heater/detail.html` which better follows Clean Architecture principles by:
- Using template inheritance with base layouts
- Better separation of concerns
- More modular component structure
- Improved maintainability

### water_heater_details.production.html
A production variant of the water heater details template. Also replaced by the new modular templating system.

## Architectural Decision
This change aligns with our Clean Architecture implementation by:
1. Enforcing proper separation of concerns between UI and business logic
2. Improving maintainability through template inheritance
3. Following the interface adapters layer principles by creating clear boundaries

## Test-Driven Development Impact
The debug version (`water_heater_details_debug.html`) has been kept outside the archive as it contains essential testing utilities needed for our TDD workflow. According to our TDD approach, testing tools are necessary to validate behavior before implementation.

## Related Templates
Current active templates:
- `/frontend/templates/water-heater/detail.html` - New version following Clean Architecture
- `/frontend/templates/water_heater_details_debug.html` - Debug version maintained for TDD purposes
