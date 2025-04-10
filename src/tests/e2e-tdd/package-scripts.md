# Package.json Scripts for TDD-Based E2E Testing

Add these scripts to your project's package.json file to integrate the TDD-based E2E testing workflow:

```json
{
  "scripts": {
    "test:e2e:tdd": "cypress open --config-file src/tests/e2e-tdd/ci-config.js",
    "test:e2e:tdd:red": "cypress run --config-file src/tests/e2e-tdd/ci-config.js --project red",
    "test:e2e:tdd:green": "cypress run --config-file src/tests/e2e-tdd/ci-config.js --project green",
    "test:e2e:tdd:refactor": "cypress run --config-file src/tests/e2e-tdd/ci-config.js --project refactor",
    "test:e2e:tdd:ci": "cypress run --config-file src/tests/e2e-tdd/ci-config.js --project $TDD_PHASE",
    "test:e2e:tdd:report": "cypress run --config-file src/tests/e2e-tdd/ci-config.js --reporter junit"
  }
}
```

## Usage in Development Workflow

These scripts ensure our E2E tests follow the TDD principles:

1. **Start with RED phase**:
   ```bash
   npm run test:e2e:tdd:red
   ```
   This runs all tests tagged with `@red` and expects them to fail, validating our test definitions.

2. **Move to GREEN phase** after implementing minimal functionality:
   ```bash
   npm run test:e2e:tdd:green
   ```
   This runs all tests tagged with `@green` and expects them to pass.

3. **Continue to REFACTOR phase** to improve implementation:
   ```bash
   npm run test:e2e:tdd:refactor
   ```
   This runs all tests tagged with `@refactor` with additional code quality checks.

## CI/CD Integration

In your CI/CD pipeline, you can use the `test:e2e:tdd:ci` script with the appropriate environment variable:

```yaml
# Example GitHub Actions workflow step
- name: Run E2E Tests (RED phase)
  env:
    TDD_PHASE: red
  run: npm run test:e2e:tdd:ci

# Later in your pipeline after implementation
- name: Run E2E Tests (GREEN phase)
  env:
    TDD_PHASE: green
  run: npm run test:e2e:tdd:ci
```

## Reporting

For CI/CD environments where you need detailed reports:

```bash
npm run test:e2e:tdd:report
```

This generates JUnit reports that can be consumed by CI systems like Jenkins, GitHub Actions, or CircleCI.
