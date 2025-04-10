# UI Testing with Playwright

This directory contains end-to-end tests for the IoTSphere UI components using Playwright.

## Setup Instructions

1. **Install Node.js dependencies**

```bash
npm install
```

2. **Install Playwright browsers**

```bash
npx playwright install
```

3. **Run the tests**

```bash
# Run in headless mode
npm run test:e2e

# Run with UI mode for debugging
npm run test:e2e:ui
```

## Test Structure

The tests are organized to validate key user flows:

- Basic navigation and page loading
- Vending machine dashboard display
- Temperature gauge visibility and readability
- Machine selector functionality

## Visual Testing

Screenshots are saved when tests fail, or when explicitly captured in tests, allowing for visual verification of UI components.

## Adding New Tests

When adding new tests, follow these guidelines:

1. Create test files with the `.spec.js` extension
2. Group related tests using `test.describe()`
3. Use meaningful test names that describe the expected behavior
4. Follow the pattern of navigating to a page, interacting with elements, and verifying the result
