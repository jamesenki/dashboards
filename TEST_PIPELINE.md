# IoTSphere Test Pipeline

This document describes the comprehensive test pipeline for the IoTSphere project, built following Test-Driven Development (TDD) principles.

## Test Pipeline Architecture

The pipeline integrates multiple testing approaches:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing interactions between components
- **BDD Tests**: Behavior-driven tests using Gherkin syntax
- **UI Tests**: Testing the user interface using Playwright
- **E2E Tests**: End-to-end testing of complete workflows

## TDD Principles

This pipeline strictly follows our project's TDD approach:

1. **RED**: Write failing tests first that define expected functionality
2. **GREEN**: Write minimal code to make tests pass
3. **REFACTOR**: Improve code quality while ensuring tests continue to pass

## Running the Pipeline

### Prerequisites

```bash
# Python dependencies
pip install jinja2 pytest pytest-json-report selenium websocket-client requests

# JavaScript dependencies (if not already installed)
npm install -g cucumber playwright
```

### Running All Tests

```bash
python test_runner.py
```

### Running Specific Test Types

```bash
python test_runner.py --types unit integration
```

### Running Tests Sequentially

```bash
python test_runner.py --sequential
```

## Viewing Test Reports

The pipeline generates an HTML report with tabs for each test type. Reports are stored in the `test_reports` directory, with the latest report also available at `test_reports/latest_report.html`.

## Shadow Document Population

Before running tests, populate test shadow documents:

```bash
python populate_shadow_documents.py
```

This creates shadow documents for test devices and generates telemetry data.

## Configuration

Edit `test_config.json` to:

- Modify test commands
- Change test timeouts
- Adjust report settings
- Configure parallel execution

## Next Steps in TDD Workflow

1. **Run Tests** (RED): Run tests to confirm they fail appropriately
2. **Implement Features** (GREEN): Write minimal code to make tests pass
3. **Run Tests Again**: Confirm tests now pass
4. **Refactor**: Improve code quality while maintaining test compliance
5. **Repeat**: Continue with next feature/component

## Shadow Documents and Remaining Tabs

As per our plan, we'll implement the shadow document population first, then use the TDD approach to implement the remaining tabs (operations summary, predictions, history, and AI insights).

Each feature will follow the RED → GREEN → REFACTOR cycle, ensuring we have proper test coverage and clearly defined requirements before implementation.
