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
- [Architecture Decision Records](./docs/adr/) - Key technical decisions and their rationales
  - [ADR-001: Angular to Python/JS Migration](./docs/adr/001-angular-to-python-js-migration.md)
  - [ADR-002: Operations Dashboard Real-time Focus](./docs/adr/002-operations-dashboard-realtime-focus.md)
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
4. Run the application:
   ```bash
   python src/main.py
   ```
5. Access the application at `http://localhost:8006` in your browser

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