# TDD-Based End-to-End Testing for IoTSphere

This directory contains our end-to-end tests structured according to the Test-Driven Development principles and Clean Architecture. These tests validate complete user journeys through the application, focusing on business outcomes rather than implementation details.

## Directory Structure

- **journeys/** - Contains test files organized by user journey
- **page-objects/** - Page object models that abstract UI interaction details
- **fixtures/** - Test data and system state fixtures
- **helpers/** - Utility functions for testing

## TDD Approach

Our E2E tests follow the Red-Green-Refactor cycle:

1. **RED Phase (@red)**: Create a failing test that defines the expected behavior
2. **GREEN Phase (@green)**: Implement the minimal code to make the test pass
3. **REFACTOR Phase (@refactor)**: Improve both test and implementation while keeping tests passing

Each test file uses the appropriate tag to indicate its current TDD phase.

## Creating New E2E Tests

Follow these guidelines when creating new E2E tests:

1. **Focus on critical user journeys** that deliver high business value
2. **Write tests from the user's perspective**, interacting with the system as a real user would
3. **Respect architectural boundaries**, avoiding direct access to internal system components
4. **Verify business outcomes**, not implementation details
5. **Document the business purpose** of each test in its description

## Running Tests

```bash
# Run all e2e tests
npm run test:e2e

# Run only RED phase tests
npm run test:e2e -- --tags=@red

# Run only GREEN phase tests
npm run test:e2e -- --tags=@green

# Run only REFACTOR phase tests
npm run test:e2e -- --tags=@refactor

# Run tests for a specific journey
npm run test:e2e -- --spec="journeys/water_heater_monitoring.spec.js"
```

## Example User Journey

A typical user journey test will follow this pattern:

```javascript
// @red - This test defines the expected behavior for water heater monitoring

describe('Water Heater Monitoring Journey', () => {
  it('allows a facility manager to detect and respond to an abnormal temperature', () => {
    // Arrange: Prepare the system for the test
    cy.fixture('users/facility_manager.json').as('user');
    cy.login('@user');

    // Act: Execute the user journey steps
    cy.visit('/dashboard');
    cy.findWaterHeaterWithIssue().click();
    cy.selectOperationsTab();
    cy.adjustTemperature(125);

    // Assert: Verify the business outcome
    cy.verifyTemperatureAdjustmentSent();
    cy.verifyStatusUpdated('Adjustment in progress');
  });
});
```

## Maintenance

- Review E2E test coverage quarterly
- Remove tests that no longer validate critical user journeys
- Update tests when user journeys change, not when implementation details change

Remember: E2E tests are the most expensive to maintain, so keep them focused on what truly matters for business value.
