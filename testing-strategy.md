# IoTSphere Refactor Testing Strategy

## Overview

This document outlines the testing strategy for the refactored IoTSphere application, which has transitioned from an Angular frontend to a Python backend with a lightweight JavaScript/HTML frontend. The new architecture requires a modified approach to testing to ensure functionality, performance, and reliability.

## Current Test Coverage

### Backend Tests
- ✅ **Unit Tests** for API endpoints, models, and services
- ✅ **Integration Tests** for the water heater component
- ❌ **No E2E tests** connecting frontend to backend

### Frontend Tests
- ❌ **No JavaScript unit tests**
- ❌ **No UI integration tests**
- ❌ **No visual regression tests**

## Testing Approach

### 1. Backend Testing (Existing)

The current backend tests using pytest provide good coverage of the Python components:

- **Unit Tests**: Testing individual API endpoints, models, and service functions
- **Integration Tests**: Testing the flow between different backend components

### 2. Frontend Testing (New)

For the new JavaScript frontend, we'll implement:

- **Unit Tests with Jest**:
  - Test individual JavaScript functions
  - Test UI component rendering
  - Mock API responses

- **UI Integration Tests with Playwright**:
  - Test browser interactions
  - Verify DOM elements and their states
  - Test forms and user inputs

### 3. End-to-End Testing

E2E tests will ensure the full application functions correctly:

- **Full-Stack Tests with Playwright**:
  - Test complete user flows
  - Verify data flows correctly between frontend and backend
  - Test navigation between pages
  - Validate visual elements match design specifications

### 4. Visual Regression Testing

To ensure consistent UI:

- Capture screenshots of key components
- Compare screenshots with baseline images
- Alert when visual differences are detected

## Test Organization

```
/src/tests/
├── unit/                # Backend unit tests
│   ├── api/             # API endpoint tests
│   ├── models/          # Data model tests
│   └── services/        # Business logic tests
├── integration/         # Backend integration tests
└── e2e/                 # End-to-end tests
    ├── tests/           # Playwright test files
    └── fixtures/        # Test data and utilities
```

## Implementation Plan

### Phase 1: Frontend Unit Testing
- Set up Jest for JavaScript testing
- Create unit tests for utility functions
- Create unit tests for dashboard components

### Phase 2: UI Integration Testing
- Implement Playwright tests for key user flows:
  - Dashboard navigation
  - Vending machine selection and display
  - Form submissions
  - Data visualization components

### Phase 3: End-to-End Testing
- Create E2E tests for critical features:
  - User authentication
  - Device management
  - Data visualization
  - Alert systems

### Phase 4: CI/CD Integration
- Integrate tests with CI/CD pipeline
- Set up automatic test runs on code changes
- Implement reporting and alerts

## Running Tests

Execute tests using the npm scripts defined in `package.json`:

```bash
# Run backend tests
python -m pytest

# Run JavaScript unit tests
npm run test:unit

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI mode
npm run test:e2e:ui

# Generate test coverage report
npm run test:coverage
```
