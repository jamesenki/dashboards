# IoTSphere Testing Guide

This document provides guidelines for writing and running tests for the IoTSphere application.

## Setting Up the Test Environment

The IoTSphere application uses pytest for both the UI and backend tests. The tests are organized in the following directory structure:

```
src/tests/
├── e2e/               # End-to-end tests with Playwright
│   └── tests/         # Test files for UI testing
├── unit/              # Unit tests
│   ├── api/           # API tests
│   ├── models/        # Model tests
│   └── services/      # Service tests
├── test_helpers.py    # Helper utilities for testing
└── README.md          # This file
```

## Running Tests

### UI Tests with Playwright

UI tests use Playwright and can be run with:

```bash
npm test
```

These tests interact with a running instance of the application, so make sure the backend server is running on port 8006 before executing the tests.

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
