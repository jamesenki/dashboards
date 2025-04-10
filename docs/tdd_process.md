# Test-Driven Development Process for IoTSphere

This document outlines the official Test-Driven Development (TDD) process for the IoTSphere project, ensuring all team members follow consistent practices.

## TDD Lifecycle

TDD follows a "Red-Green-Refactor" cycle that must be strictly followed for all new features and bug fixes:

### 1. RED Phase

The RED phase is when you write a failing test that defines the expected behavior.

**Required Steps:**
1. Begin by writing a failing test (or multiple tests) that define the expected behavior.
2. The test should be as small and focused as possible, testing only a single behavior.
3. Run the test to verify it fails (this proves the test is valid and testing something real).
4. Commit the failing test with the tag `[RED]` in the commit message.

**Example:**
```python
@pytest.mark.red
def test_get_device_shadow_success():
    # Test retrieving a device shadow successfully
    response = client.get(f"/api/shadows/test-device-001")

    # This will fail initially as the endpoint isn't implemented yet
    assert response.status_code == 200
    assert response.json()["device_id"] == "test-device-001"
```

### 2. GREEN Phase

The GREEN phase is when you write the minimal code required to make the test pass.

**Required Steps:**
1. Write the minimal code necessary to make the failing test pass.
2. Don't optimize or refactor yet - focus only on making the test pass.
3. Run the test to verify it now passes.
4. Commit the passing implementation with the tag `[GREEN]` in the commit message.

**Example:**
```python
@router.get("/{device_id}")
async def get_device_shadow(device_id: str, shadow_service: DeviceShadowService = Depends(get_shadow_service)):
    # Minimal implementation to make test pass
    shadow = await shadow_service.get_device_shadow(device_id)
    if not shadow:
        raise HTTPException(status_code=404, detail=f"No shadow document exists for device {device_id}")
    return shadow
```

### 3. REFACTOR Phase

The REFACTOR phase is when you improve the code while ensuring the tests still pass.

**Required Steps:**
1. Clean up the code for readability, maintainability, and performance.
2. Apply design patterns and best practices.
3. Run the tests frequently to ensure they still pass.
4. Commit the refactored code with the tag `[REFACTOR]` in the commit message.

**Example:**
```python
@router.get("/{device_id}", response_model=DeviceShadowResponse)
async def get_device_shadow(
    device_id: str,
    shadow_service: DeviceShadowService = Depends(get_shadow_service)
):
    """
    Retrieve the full shadow document for a device.

    Raises 404 if the device shadow does not exist.
    """
    try:
        shadow = await shadow_service.get_device_shadow(device_id)
        if not shadow:
            raise DeviceShadowNotFoundException(device_id)
        return shadow
    except DeviceShadowNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving device shadow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## BDD Tests in TDD Cycle

BDD (Behavior-Driven Development) tests fit into the TDD cycle as follows:

1. **RED Phase for BDD:**
   - Write feature files with scenarios describing expected behavior
   - Implement step definitions that will fail
   - Mark with `@red` tag

2. **GREEN Phase for BDD:**
   - Implement the minimal functionality to make the scenarios pass
   - Mark passing scenarios with `@green` tag

3. **REFACTOR Phase for BDD:**
   - Improve implementation while keeping scenarios passing
   - Mark refactored scenarios with `@refactored` tag

## Test Structure Guidelines

### Test Isolation

Every test must be completely isolated and able to run independently:

- Use fixtures and mocks to avoid external dependencies
- Reset state between tests
- Never depend on results from other tests
- Use unique test data for each test

### Test Atomicity

Tests should be atomic, focusing on a single behavior:

- One assertion per test (or a minimal set of closely related assertions)
- Test only one feature or behavior per test
- Give tests descriptive names that reflect the behavior being tested

### Test Coverage

All code should have comprehensive test coverage:

- Aim for 90% code coverage at minimum
- Test happy paths, edge cases, and error conditions
- Prioritize testing business-critical paths
- Include performance tests for critical operations

## Test Documentation

All tests should serve as documentation:

- Use descriptive scenario and step names in BDD tests
- Write clear test method names in unit/integration tests
- Include docstrings explaining the purpose and context of each test
- Document any test fixtures and their purpose

## Technical Details

### Python Tests

- Use `pytest` for unit and integration tests
- Use `behave` for Python BDD tests
- Organize tests by domain and type (unit, integration, bdd)

### JavaScript Tests

- Use `jest` for unit tests
- Use `cucumber.js` for BDD tests
- Follow the same RED-GREEN-REFACTOR cycle

## Implementation Order

The recommended implementation order for a new feature is:

1. Write BDD tests to define the high-level business requirements
2. Write integration tests for API contracts
3. Write unit tests for service and domain logic
4. Implement the code following the TDD cycle for each test level

## Continuous Integration

- All RED phase tests must be marked with appropriate tags to prevent CI failures
- CI will run all tests except those tagged with `@red`
- Failed tests block merges to main branches
