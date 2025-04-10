# Integration Testing Framework

This directory contains integration tests that validate the interactions between different components of the IoTSphere system. These tests bridge the gap between unit tests and end-to-end tests, following our Clean Architecture principles and TDD approach.

## Structure

Integration tests are organized by the interface boundaries they test:

```
integration/
├── README.md                   # This file
├── api/                        # Tests for API layer integration with use cases
├── adapters/                   # Tests for adapter implementations
├── data_access/                # Tests for repository implementations with real databases
├── device_communication/       # Tests for device communication layer
└── utils/                      # Common testing utilities and fixtures
```

## TDD Approach

Integration tests follow the same Red-Green-Refactor cycle as our other tests:

1. **RED Phase**: Write failing tests that define expected integration behavior
2. **GREEN Phase**: Implement the minimal integration code to make tests pass
3. **REFACTOR Phase**: Improve the implementation while maintaining passing tests

Test files are tagged with TDD phase tags (`@red`, `@green`, `@refactor`) to indicate their current phase.

## Testing Strategy

Our integration tests focus on:

- **Clean Architecture Boundaries**: Testing interactions across architectural layers
- **Component Interaction**: Verifying different components work together correctly
- **External Dependencies**: Testing integration with databases, message queues, etc.
- **Real Subsystems**: Using real (not mocked) subsystems where practical

## Running Integration Tests

Integration tests can be run using pytest:

```bash
# Run all integration tests
pytest src/tests/integration

# Run tests for a specific component
pytest src/tests/integration/api

# Run tests in a specific phase
pytest src/tests/integration -m red
```

## Test Data Management

Integration tests use:

- **Test Fixtures**: For setting up and tearing down test environments
- **Real Databases**: Tests may use real databases with isolated test schemas
- **Containerization**: Docker containers for external dependencies

## Key Principles

1. **Independence**: Tests should be independent and not rely on other tests
2. **Realistic Data**: Tests should use realistic data scenarios
3. **Focused Scope**: Each test should validate a specific integration point
4. **Performance**: Tests should run reasonably quickly to support TDD workflow
5. **Clean Setup/Teardown**: Tests must clean up any resources they create
