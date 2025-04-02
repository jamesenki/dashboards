# IoTSphere Application

IoTSphere is an IoT monitoring platform for tracking and managing various devices including plant equipment, vending machines (Polar Delight), electric motorcycles/vehicles, and smart water heaters. This repository contains the refactored version using a Python backend with a lightweight JavaScript/HTML frontend.

## Project Overview

This refactored version addresses issues with Angular's dependency management and security vulnerabilities by adopting a more maintainable architecture with these benefits:

1. Better separation between backend data processing and frontend presentation
2. Easier frontend customization for customers
3. More explicit control over dependencies
4. Leveraging Python's strengths for data processing

## Documentation Guide

This README provides high-level information about the project. For detailed documentation, please refer to the following resources:

### Design & Architecture
- [Architecture Overview](./docs/architecture-overview.md) - High-level system architecture and component interaction
- [Database Configuration](./docs/database_configuration.md) - PostgreSQL and TimescaleDB integration details
- [Predictions Plan](./docs/predictionsplan.md) - Machine learning features for water heater monitoring
- [Monitoring & Alerts Architecture](./docs/monitoring-alerts-architecture.md) - ML model monitoring and alerts system

### Architecture Decision Records
- [ADR-001: Angular to Python/JS Migration](./docs/adr/001-angular-to-python-js-migration.md) - Rationale for platform migration
- [ADR-002: Operations Dashboard Real-time Focus](./docs/adr/002-operations-dashboard-realtime-focus.md) - Focus on operational metrics
- [ADR-003: PostgreSQL with TimescaleDB](./docs/adr/003-postgresql-timescaledb-database-choice.md) - Database architecture decisions
- [ADR-004: ML Approach for Lifespan Estimation](./docs/adr/004-ml-approach-for-lifespan-estimation.md) - Machine learning implementation approach
- [Data Models](./docs/data-models.md) - Database schema and model relationships

### Features & Implementation
- [Operations Dashboard](./docs/operations_dashboard.md) - Real-time operational monitoring and analytics
- [API Documentation](./docs/api-documentation.md) - REST API endpoints and usage

### Developer Resources
- [Developer Guide](./docs/developer-guide.md) - Getting started for developers
- [Testing Strategy](./testing-strategy.md) - Test coverage and implementation
- [Coding Standards](./docs/coding-standards.md) - Coding conventions and best practices
- [Contributing Guide](./docs/contributing.md) - Guidelines for contributing to the project

## Project Structure

```
IoTSphere-Refactor/
├── src/                  # Backend Python code
│   ├── api/              # API endpoints
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── utils/            # Utility functions
│   ├── web/              # Web server configuration
│   └── tests/            # Test files
│       ├── unit/         # Unit tests
│       └── integration/  # Integration tests
├── frontend/            # Frontend assets
│   ├── static/           # CSS, JS, images
│   ├── templates/        # HTML templates
│   └── tests/            # Frontend tests
└── run_tests.py         # Test runner script
```

## Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Node.js 16+ and npm (for frontend tests)

### Installation

1. Clone the repository
2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend test dependencies:
   ```bash
   npm install
   ```

### Database Setup

#### Option 1: Using Docker (Recommended)

The easiest way to get started is using Docker Compose, which will set up PostgreSQL with TimescaleDB automatically:

```bash
# Start PostgreSQL and Redis services
docker-compose up -d postgres redis

# Check that services are running
docker-compose ps
```

#### Option 2: Manual PostgreSQL Setup

If you prefer a local PostgreSQL installation:

1. Install PostgreSQL 14:
   ```bash
   # On macOS with Homebrew
   brew install postgresql@14
   brew services start postgresql@14
   ```

2. Create the database and user:
   ```bash
   createdb iotsphere
   psql -c "CREATE USER iotsphere WITH ENCRYPTED PASSWORD 'iotsphere';"
   psql -c "GRANT ALL PRIVILEGES ON DATABASE iotsphere TO iotsphere;"
   ```

3. (Optional) Install TimescaleDB extension:
   ```bash
   # On macOS with Homebrew
   brew install timescaledb
   /opt/homebrew/bin/timescaledb-tune --quiet --yes
   brew services restart postgresql@14
   psql iotsphere -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
   ```

> **Note:** The application is designed to work with or without TimescaleDB. If TimescaleDB is not available, the application will gracefully fall back to standard PostgreSQL tables.

### Running the Application

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8006 --reload
```

Access the application at `http://localhost:8006` in your browser

### Test-Driven Development Workflow

This project follows Test-Driven Development (TDD) principles with the Red-Green-Refactor cycle:

#### Using the TDD Workflow Script

The TDD workflow helper script streamlines development of new features:

```bash
# Start a new feature with failing tests (Red phase)
python scripts/tdd_workflow.py red water_heater_prediction

# Run tests after implementing the feature (Green phase)
python scripts/tdd_workflow.py green water_heater_prediction

# Verify tests still pass after refactoring (Refactor phase)
python scripts/tdd_workflow.py refactor water_heater_prediction

# Or run the entire guided TDD cycle
python scripts/tdd_workflow.py cycle water_heater_prediction
```

#### Manual TDD Process

1. **Red Phase**: Write failing tests that define the expected behavior
   ```bash
   # Run tests and verify they fail
   pytest src/tests -v -m tdd_red
   ```

2. **Green Phase**: Write the minimum code needed to make tests pass
   ```bash
   # Run tests and verify they pass
   pytest src/tests -v -m "tdd_red or tdd_green"
   ```

3. **Refactor Phase**: Improve code quality while keeping tests passing
   ```bash
   # Run all tests to ensure nothing broke during refactoring
   pytest src/tests -v
   ```

## Key Features

### Remote Monitoring
- Real-time device status monitoring
- Customizable dashboards for different device types
- Alerting system for critical events

### Operations Management
- Remote operations control for compatible devices
- Scheduling and automation capabilities
- Maintenance tracking and planning

### Analytics
- Historical performance data visualization
- Usage pattern analysis
- Predictive maintenance indicators

### Administration
- User and role management
- Customer account management
- White-labeling capabilities

## Technology Stack

### Backend
- **Python**: Core application logic
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database interactions
- **JWT**: Authentication mechanism

### Frontend
- **HTML/CSS/JavaScript**: Core UI components
- **Bootstrap**: UI framework
- **Chart.js**: Data visualization
- **Fetch API**: AJAX requests

### Testing
- **pytest**: Backend testing
- **Jest**: Frontend unit testing
- **Playwright**: E2E and UI testing

## Testing

IoTSphere has a comprehensive test suite covering both backend and frontend components. See our [Testing Strategy](./testing-strategy.md) for details.

### Running Backend Tests

```bash
# Run all backend tests
python run_tests.py

# Run with coverage reporting
python run_tests.py --coverage

# Run specific test types
python run_tests.py --unit
python run_tests.py --integration
```

### Running Frontend Tests

```bash
# Run all frontend tests
npm test

# Run with coverage
npm run test:coverage

# Run UI/E2E tests
npm run test:e2e
```

## Contributing

Please read our [Contributing Guide](./docs/contributing.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is proprietary software. All rights reserved.

## Support

For support, please contact the development team at dev-support@iotsphere.example.com.

This creates an HTML report in the `coverage_report` directory.

## Device Types

IoTSphere currently supports the following device types:

- Smart Water Heaters
- Plant Equipment (coming soon)
- Vending Machines - Polar Delight (coming soon)
- Electric Vehicles (coming soon)

## License

This project is proprietary software. All rights reserved.
# Test comment for pre-commit hook
