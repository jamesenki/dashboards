# IoTSphere Testing Guide

This document provides guidelines for writing and running tests for the IoTSphere application following Test-Driven Development (TDD) principles.

## Test-Driven Development (TDD) Principles

All development in IoTSphere follows these TDD principles:

1. **RED Phase**: Write failing tests first that define expected functionality
   - Tests should be atomic, focused on a single behavior
   - Tests should be independent and repeatable
   - Run tests to verify they fail (proving they're valid tests)

2. **GREEN Phase**: Write minimal code to make tests pass
   - Implement just enough functionality to pass the test
   - Don't optimize or refactor yet
   - Run tests to verify they pass

3. **REFACTOR Phase**: Improve code quality while ensuring tests still pass
   - Clean up code for readability and maintainability
   - Apply design patterns and best practices
   - Run tests again to ensure they still pass

## Testing Structure

The IoTSphere application uses a comprehensive testing strategy with multiple levels of tests:

```
src/tests/
├── bdd/               # Behavior-Driven Development tests
│   ├── features/      # Feature specifications in Gherkin syntax
│   ├── steps/         # Step implementations for BDD tests
│   └── environment.py # BDD test environment configuration
├── e2e/               # End-to-end tests with Playwright
│   └── tests/         # Test files for UI testing
├── integration/       # Integration tests
│   ├── api/           # API integration tests
│   └── database/      # Database integration tests
├── unit/              # Unit tests
│   ├── api/           # API tests
│   ├── models/        # Model tests
│   └── services/      # Service tests
├── test_helpers.py    # Helper utilities for testing
└── README.md          # This file
```

In addition, frontend BDD tests are located in:

```
features/
├── *.feature          # Feature specifications in Gherkin syntax
└── step_definitions/  # JavaScript step implementations for frontend BDD tests
```

## Running Tests

### BDD Tests

BDD tests use behave and can be run with:

```bash
cd src/tests/bdd
behave
```

You can run specific features or scenarios using tags:

```bash
# Run all API tests
behave --tags=@api

# Run all WebSocket tests
behave --tags=@websocket

# Run specific feature file
behave features/device_shadow_service.feature
```

### Python Unit and Integration Tests

Python tests use pytest and can be run with:

```bash
# Run all tests
python -m pytest

# Run specific test category
python -m pytest src/tests/unit/
python -m pytest src/tests/integration/

# Run with coverage report
python -m pytest --cov=src
```

### UI Tests with Playwright

UI tests use Playwright and can be run with:

```bash
npm test
```

These tests interact with a running instance of the application, so make sure the backend server is running on port 8000 before executing the tests.

### JavaScript BDD Tests

Frontend BDD tests use Cucumber.js and can be run with:

```bash
npx cucumber-js
```

### Backend Tests with pytest

Backend tests use pytest and can be run with:

```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest src/tests/unit/api/direct_patch_test_vending_machine.py

# Run with verbose output
python -m pytest -v

# Disable asyncio plugin (if causing issues)
python -m pytest -p no:asyncio
```

## Writing Backend API Tests

### Direct Patching Approach (Recommended)

The most effective way to test API endpoints is to directly patch the service methods they call. This approach ensures proper isolation between tests and prevents real service calls.

Example:

```python
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app

@patch('src.services.vending_machine.VendingMachineService.get_all_vending_machines')
def test_get_all_vending_machines(mock_get_all, test_client):
    # Configure the mock
    mock_get_all.return_value = [your_test_data]

    # Create a test client
    client = TestClient(app)

    # Make request
    response = client.get("/api/vending-machines")

    # Check response
    assert response.status_code == 200

    # Verify mock was called
    mock_get_all.assert_called_once()
```

See `src/tests/unit/api/direct_patch_test_vending_machine.py` for complete examples of this approach.

### Testing Multiple Dependencies

When an endpoint requires multiple service methods, you can stack patch decorators:

```python
@patch('src.services.vending_machine.VendingMachineService.method1')
@patch('src.services.vending_machine.VendingMachineService.method2')
def test_endpoint(mock_method2, mock_method1, test_client):
    # Note: mocks are injected in reverse order of decorators
    # Configure mocks...
    # Test implementation...
```

## Best Practices

1. **Test in Isolation**: Use mocks to isolate the component being tested.
2. **One Assert Per Behavior**: Each test should focus on verifying one specific behavior.
3. **Descriptive Test Names**: Use descriptive names that explain what the test is checking.
4. **Test Both Success and Error Cases**: Test both the happy path and error conditions.
5. **Avoid Test Dependencies**: Each test should be independent and not rely on other tests.

## Troubleshooting

### Common Issues

- **Asyncio Plugin Errors**: If you encounter errors related to the asyncio plugin, disable it with `-p no:asyncio`.
- **Mock Not Being Called**: Ensure you're patching the correct path to the method being called.
- **Test Data Not Being Used**: Verify the mock is configured correctly with `return_value` or `side_effect`.

### Debugging Tips

- Use pytest's `-v` flag for verbose output showing which tests pass/fail.
- Add print statements in tests for debugging complex issues.
- Use `breakpoint()` to pause execution for interactive debugging.
