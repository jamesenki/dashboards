# Integration Testing with TDD and Clean Architecture

This directory contains integration tests that follow Test-Driven Development (TDD) principles and respect Clean Architecture boundaries. Integration tests validate interactions between different components of the IoTSphere system.

## Clean Architecture Testing Boundaries

Our integration tests are organized according to the Clean Architecture layer boundaries they test:

```
integration-tdd/
├── api_to_usecase/         # Tests integration between API and Use Case layers
├── usecase_to_entity/      # Tests integration between Use Cases and Entities
├── usecase_to_gateway/     # Tests integration between Use Cases and Gateway interfaces
├── gateway_to_external/    # Tests integration between Gateways and external systems
└── utils/                  # Common test utilities and fixtures
```

This organization ensures that:
1. Tests validate specific architectural boundary interactions
2. Tests respect dependency rules of Clean Architecture
3. Layer responsibilities are clearly maintained

## TDD Approach

All integration tests follow the Red-Green-Refactor cycle:

1. **Red Phase** (`@pytest.mark.red`):
   - Write failing tests that define expected behavior
   - Tests validate the interaction contract between layers
   - Tests are expected to fail initially

2. **Green Phase** (`@pytest.mark.green`):
   - Implement minimal code to make tests pass
   - Tests validate the basic functionality works
   - All tests should pass in this phase

3. **Refactor Phase** (`@pytest.mark.refactor`):
   - Improve implementation while maintaining passing tests
   - Tests validate that refactoring preserves behavior
   - Tests ensure code quality improvements don't break functionality

## Test File Structure

Each test file follows a consistent pattern:

```python
"""
Integration test for [specific boundary/feature].
Tests the interaction between [Layer A] and [Layer B].
"""
import pytest

# Test fixtures and setup
@pytest.fixture
def test_dependency():
    # Setup test dependencies
    pass

# Red Phase Tests
@pytest.mark.red
def test_expected_behavior_definition():
    # Test defining expected behavior before implementation
    pass

# Green Phase Tests
@pytest.mark.green
def test_minimal_implementation():
    # Test validating minimal implementation works
    pass

# Refactor Phase Tests
@pytest.mark.refactor
def test_improved_implementation():
    # Test ensuring refactored code maintains behavior
    pass
```

## Running Tests

Tests can be run by TDD phase:

```bash
# Run all integration tests
pytest src/tests/integration-tdd

# Run only RED phase tests
pytest src/tests/integration-tdd -m red

# Run only GREEN phase tests
pytest src/tests/integration-tdd -m green

# Run only REFACTOR phase tests
pytest src/tests/integration-tdd -m refactor

# Run tests for a specific boundary
pytest src/tests/integration-tdd/api_to_usecase
```

## Test Isolation

Integration tests follow these isolation principles:

1. **Mocking at Boundaries**: Mock adjacent layers not under test
2. **Test Doubles**: Use test doubles (stubs, spies) at architectural boundaries
3. **In-Memory Repositories**: Use in-memory implementations of repositories
4. **Test-Specific Fixtures**: Create test-specific fixtures that don't rely on external systems
5. **Clean Setup/Teardown**: Tests clean up after themselves and don't leave residual state

## Business Value Focus

Integration tests focus on validating critical business requirements:

1. Each test maps to a specific user journey or business rule
2. Tests document expected behavior at architectural boundaries
3. Tests validate business rules are enforced consistently across layers

## Integration vs. Unit vs. E2E Tests

| Test Type | Purpose | Scope | Mocking |
|-----------|---------|-------|---------|
| Unit | Test single component | Single class/function | Heavy mocking |
| Integration | Test components working together | Boundary between layers | Selective mocking |
| E2E | Test complete user journey | Multiple systems | Minimal mocking |

We maintain a ratio of approximately 70:20:10 for unit:integration:e2e tests.
