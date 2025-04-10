# Test-Driven Development Approach for IoTSphere

## Introduction

The IoTSphere project follows Test-Driven Development (TDD) principles for all new features and enhancements. This document outlines our testing philosophy, approach, and best practices to ensure high-quality, maintainable code.

## TDD Cycle

All development in IoTSphere follows the classic TDD cycle:

### 1. RED Phase

- Write failing tests first that define expected functionality
- Tests should clearly specify requirements before any implementation
- Run tests to verify they fail (RED)

### 2. GREEN Phase

- Write minimal code to make tests pass
- Focus on functionality, not optimization
- Run tests to verify they pass (GREEN)

### 3. REFACTOR Phase

- Improve code quality while maintaining passing tests
- Apply design patterns and best practices
- Ensure all tests still pass after refactoring

## Key Principles

1. **Tests Drive Development**: We always change the code to pass the tests, not the other way around. Tests define the expected behaviors and requirements.

2. **Meaningful Tests**: Tests should verify behavior, not implementation details, and provide clear failure messages.

3. **Comprehensive Coverage**: Aim for high test coverage, focusing on critical paths and edge cases.

4. **Fast Execution**: Tests should run quickly to provide immediate feedback.

5. **Independent Tests**: Tests should not depend on each other or external services.

## Testing Levels

### Unit Testing

- Tests individual components in isolation
- Mocks or stubs dependencies
- Focuses on single responsibility
- Written using Jest and Jasmine frameworks

### Integration Testing

- Tests interaction between components
- Verifies correct communication between services
- May use test doubles for external systems
- Implemented with a combination of Jasmine and custom test harnesses

### Behavior-Driven Development (BDD) Testing

- Bridges the gap between business requirements and technical implementation
- Uses Gherkin syntax (Given-When-Then) for test scenarios
- Implemented with both JavaScript and Python frameworks
- Provides executable specifications of system behavior

### End-to-End Testing

- Tests complete user flows
- Verifies system behavior from user perspective
- Runs against a test environment similar to production
- Follows the 70:20:10 ratio (unit:integration:e2e) guidance

## Best Practices

1. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification phases.

2. **Test Naming**: Use descriptive names that explain the scenario and expected outcome.

3. **Test Data**: Use meaningful test data that represents real-world scenarios.

4. **Boundary Testing**: Test edge cases and boundary conditions.

5. **Behavior Focus**: Test what the code should do, not how it does it.

6. **Continuous Integration**: Run tests automatically on code changes.

7. **TDD Phase Tagging**: Mark tests with appropriate phase tags (@red, @green, @refactor) to track progress.

8. **Test Coverage Reporting**: Generate combined reports to monitor implementation progress across test types.

## Test Reporting Infrastructure

IoTSphere implements a comprehensive test reporting system to track implementation progress across different test types and TDD phases:

### Combined Test Report Generator

The `combined-test-report.js` script integrates results from multiple testing frameworks to provide a unified view of implementation status:

- Aggregates results from JavaScript and Python BDD tests
- Tracks test counts across RED, GREEN, and REFACTOR phases
- Generates HTML reports with progress visualizations
- Calculates overall implementation completion percentages

### Python BDD Reporting

The `python-bdd-report-v3.js` script analyzes Python BDD implementations:

- Parses Python step definitions to identify TDD phases
- Detects @given, @when, and @then decorators in implementation files
- Identifies RED, GREEN, or REFACTOR phase markers in implementation
- Generates focused reports on Python BDD test status

### Report Generation and Usage

Reports can be generated using the following commands:

```bash
# Generate combined test report
node scripts/combined-test-report.js

# Generate Python BDD specific report
node scripts/python-bdd-report-v3.js
```

Reports are saved to the `test-reports` directory and provide critical feedback for the TDD workflow, helping teams identify which components need implementation (RED), which have been implemented (GREEN), and which are being improved (REFACTOR).

## Implementation Examples

### Angular Component Testing

```typescript
describe('DeviceStatusComponent', () => {
  // RED: Define the test before implementation
  it('should display device health status as "Critical" when health score < 30', () => {
    // Arrange
    const testDevice = { id: '123', healthScore: 25 };
    component.device = testDevice;

    // Act
    fixture.detectChanges();

    // Assert
    const statusElement = fixture.nativeElement.querySelector('.status-indicator');
    expect(statusElement.textContent).toContain('Critical');
    expect(statusElement.classList).toContain('critical');
  });
});
```

### BDD Testing with Python

```python
# Feature file (device_shadow_service.feature)
Feature: Device Shadow Service

  @red  # Initially marked as RED phase
  Scenario: Retrieve device shadow
    Given a device with ID "test-device-001" exists in the system
    When a client requests the shadow state for device "test-device-001"
    Then the response should be successful
    And the shadow document should contain "reported" and "desired" sections

# Step implementation (steps/device_shadow_steps.py)
from behave import given, when, then

@given('a device with ID "{device_id}" exists in the system')
def step_impl(context, device_id):
    # Implementation that creates a test device in the system
    context.device_id = device_id
    context.device_service.create_test_device(device_id)

@when('a client requests the shadow state for device "{device_id}"')
def step_impl(context, device_id):
    # GREEN PHASE - Implementation that retrieves the shadow
    context.response = context.shadow_service.get_shadow(device_id)
```

### API Service Testing

```typescript
describe('DeviceService', () => {
  // RED: Define the test before implementation
  it('should retry failed device connection attempts up to 3 times', () => {
    // Arrange
    const deviceId = '123';
    const errorResponse = new HttpErrorResponse({ status: 503 });
    httpClientSpy.post.and.returnValues(
      throwError(errorResponse),
      throwError(errorResponse),
      throwError(errorResponse),
      of({ success: true })
    );

    // Act
    service.connectDevice(deviceId).subscribe(
      response => expect(response.success).toBeTrue(),
      error => fail('should not error out')
    );

    // Assert
    expect(httpClientSpy.post.calls.count()).toBe(4); // Initial + 3 retries
  });
});
```

## Benefits of Our TDD Approach

1. **Clear Requirements**: Tests serve as executable specifications
2. **High Test Coverage**: By definition, all code has tests
3. **More Modular, Maintainable Code**: TDD encourages better design
4. **Confidence in Changes**: Tests catch regressions early
5. **Living Documentation**: Tests document expected behavior

## Conclusion

Test-Driven Development is fundamental to the IoTSphere development process. By following the RED-GREEN-REFACTOR cycle and adhering to these principles, we ensure that our codebase remains maintainable, reliable, and adaptable to changing requirements.
