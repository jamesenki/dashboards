# IoTSphere Architecture Overview

## Introduction

IoTSphere is built on a modern, maintainable architecture that separates backend data processing from frontend presentation. This document provides a comprehensive overview of the system architecture, component interactions, and design patterns using the C4 model approach.

> **Note:** This document includes Mermaid diagrams that should render automatically in modern Markdown viewers, including Windsurf.

![Model Monitoring Dashboard](IoTSphere-Refactor/docs/images/mermaid/system_context.svg)

The frontend architecture follows a modular, component-based approach that facilitates Test-Driven Development:

1. **Core Module**: Provides application initialization and centralized control
2. **API Client**: Abstracts backend communication with standardized interfaces
3. **Tab Manager**: Manages component lifecycle and navigation
4. **Event Bus**: Implements pub/sub pattern for loose coupling between components
5. **Dashboard Modules**: Implement specific functionality as self-contained units

This architecture supports TDD through:

- **Component Isolation**: Each component can be tested independently
- **Dependency Injection**: Services and utilities can be mocked for testing
- **Event-Based Communication**: Components interact through well-defined interfaces
- **Clear Responsibilities**: Each component has a single, well-defined purpose

## Key Design Patterns

### Backend

1. **Repository Pattern**: Abstracts data access logic with configurable implementations (e.g., MockWaterHeaterRepository and SQLiteWaterHeaterRepository)
2. **Service Layer Pattern**: Centralizes business logic in services with configurable data sources
3. **Factory Pattern**: Creates complex objects
4. **Dependency Injection**: Makes services and dependencies more testable
5. **Configuration Management Pattern**: Externalizes configuration to allow behavior changes without code modification

### Frontend

1. **Module Pattern**: Organizes JavaScript code
2. **Observer Pattern**: Enables event-driven UI updates
3. **Template Pattern**: Standardizes UI component rendering

## Communication Flow

Following our Test-Driven Development principles, we've created comprehensive sequence diagrams that define expected behaviors for key system interactions. These diagrams serve as both documentation and specifications that drive our implementation.

### Sequence Diagrams

We maintain detailed sequence diagrams for all critical system flows in the [Sequence Diagrams](./sequence-diagrams.md) document, including:

1. **Device Data Flow**: Shows how IoT devices send telemetry data to the platform
   - Successful device data transmission
   - Authentication failure handling
   - Malformed data handling

2. **User Dashboard Flow**: Illustrates user interactions with the monitoring dashboard
   - Successful dashboard data retrieval
   - Authentication failure recovery
   - Database connectivity error handling

3. **Model Monitoring Alert Flow**: Documents the alert lifecycle
   - Alert rule creation
   - Alert triggering
   - Notification failure recovery

These diagrams are critical to our TDD approach as they define expected behaviors that our code must satisfy, allowing us to write effective tests before implementation.

## Authentication & Authorization

IoTSphere uses JWT (JSON Web Tokens) for authentication:

1. **Authentication Flow**:
   - User submits credentials
   - Server validates credentials and issues a JWT
   - JWT is stored client-side
   - JWT is sent with subsequent requests

2. **Authorization Model**:
   - Role-based access control (RBAC)
   - Multiple user roles (Admin, Operator, Viewer)
   - Feature-based permissions

## Data Models

See [Data Models Documentation](./data-models.md) for detailed information.

## Scalability Considerations

IoTSphere is designed with scalability in mind:

1. **Horizontal Scaling**:
   - Stateless backend allows multiple server instances
   - Database connection pooling

2. **Performance Optimization**:
   - Data caching
   - Optimized database queries
   - Browser caching for static assets

## Deployment Architecture

### Production Deployment

### Development Deployment

## Security Considerations

1. **Data Protection**:
   - TLS for all communications
   - Password hashing
   - Input validation and sanitization

2. **Application Security**:
   - CSRF protection
   - XSS prevention
   - Regular dependency updates

## Monitoring & Logging

1. **Application Monitoring**:
   - Performance metrics
   - Error tracking
   - User activity logs

2. **System Monitoring**:
   - Server health
   - Database performance
   - Network metrics

## Device Dashboards

### Water Heater Dashboard

The Water Heater Dashboard follows a tabbed interface pattern with three main views:

1. **Details Tab**: Displays basic water heater information including current temperature, target temperature, mode, and status. Provides controls for adjusting settings.

2. **Operations Tab**: Focused on real-time operational monitoring with:
   - Status cards showing current operational state
   - Asset health indicators
   - Gauge visualizations for temperature, pressure, flow rate, and energy usage
   - Real-time operational metrics

3. **History Tab**: Provides historical analytics through time-series charts:
   - Temperature history (actual vs. target)
   - Energy usage patterns
   - Pressure and flow rate trends
   - Customizable time ranges (7, 14, or 30 days)

#### Architecture Implementation

- **Backend**: Separate services handle device details, operations data, and historical metrics
- **APIs**: RESTful endpoints for each dashboard component (details, operations, history)
- **Frontend**: JavaScript modules leverage Chart.js for data visualization
- **Testing**: End-to-end tests verify data consistency across all three views

## Model Monitoring Dashboard

The Model Monitoring Dashboard provides comprehensive tools for tracking ML model performance and health over time. The dashboard follows a tabbed interface pattern with specialized views:

1. **Models Tab**: Displays all deployed models with filtering options for both active and archived models. Shows key performance indicators and model metadata.

2. **Performance Tab**: Focuses on ML model performance metrics:
   - Accuracy, precision, recall, and F1 scores over time
   - Performance trend visualizations
   - Threshold configuration for acceptable performance
   - Comparison between models

3. **Drift Tab**: Monitors data and concept drift to identify when models need retraining:
   - Feature drift visualization and metrics
   - Distribution comparisons between training and production data
   - Statistical measures of drift (PSI, JSI)
   - Drift alerts and thresholds

4. **Alerts Tab**: Centralized view of all model-related alerts:
   - Severity-based alert categorization (critical, high, medium, low)
   - Alert filtering by model, metric, and status
   - Alert management workflow (acknowledge, resolve)
   - Historical alert patterns

5. **Reports Tab**: Generates comprehensive model monitoring reports:
   - Template-based report generation (performance, drift, alerts)
   - Customizable date ranges and models
   - Export functionality for PDF and CSV formats
   - Visual representations of key metrics

### Export Functionality Architecture

The report export system uses a server-side generation approach for reliability and consistency:

- **Backend**: 
  - FastAPI endpoints (`/reports/export/pdf` and `/reports/export/csv`) handle export requests
  - ReportLab library generates professionally formatted PDF reports with charts and tables
  - Python's CSV module creates structured data exports
  - Mock data generation during development follows TDD principles

- **Frontend**:
  - JavaScript functions initiate export requests via fetch API
  - Proper MIME types and Content-Disposition headers enable browser download
  - UI provides clear feedback during export process

- **Testing**:
  - Integration tests verify API endpoints for exports
  - Unit tests confirm client-side export functions
  - Test-driven development approach ensures functionality meets requirements

### Architecture Implementation

- **Backend**: Dashboard API module handles data aggregation and export generation
- **APIs**: RESTful endpoints for model metrics, alerts, and exports
- **Frontend**: JavaScript modules integrate with backend services
- **Testing**: End-to-end tests verify model monitoring functionality

### Model Monitoring System Architecture

### Monitoring Container Architecture

### Monitoring Components

### Alert Flow Sequence

- **APIs**: RESTful endpoints for each monitoring component with standardized response formats
- **Frontend**: JavaScript modules use Chart.js for interactive visualizations
- **Testing**: Comprehensive test suite validates both frontend and backend components
- **Design**: Dark theme UI with minimalist, clean interface following IoTSphere design principles

## Conclusion

This architecture provides a solid foundation for IoTSphere's current functionality while allowing for future growth and enhancements. The separation of concerns and modular design facilitate maintainability and scalability.

## Viewing PlantUML Diagrams

The architecture diagrams in this document are written in PlantUML, which allows for version-controllable diagrams as code. This approach aligns with our Test-Driven Development principles by providing living documentation that evolves alongside our code.

### Setup Requirements

1. **Install the required tools**:
   ```bash
   # macOS (using Homebrew)
   brew install graphviz plantuml
   
   # Linux (Ubuntu/Debian)
   sudo apt-get install graphviz plantuml
   
   # Windows
   # Download and install from https://graphviz.org/download/ and https://plantuml.com/download
   ```

2. **Visual Studio Code extensions**:
   - Install the "PlantUML" extension by jebbs
   - Install the "Markdown Preview Enhanced" extension
   
3. **Configure VS Code settings**:
   Add the following to your settings.json (Preferences > Settings > Edit in settings.json):
   ```json
   {
       "plantuml.render": "PlantUMLServer",
       "plantuml.server": "https://www.plantuml.com/plantuml",
       "markdown-preview-enhanced.enablePlantUMLServer": true
   }
   ```

### Viewing the Diagrams

- Right-click on this Markdown file and select "Markdown Preview Enhanced: Open Preview"
- The PlantUML diagrams will be rendered automatically within the preview
- Alternatively, you can preview specific diagrams by right-clicking within a PlantUML code block and selecting "Preview Current Diagram"

### Editing Diagrams

The PlantUML diagrams are embedded directly in this Markdown file as code blocks with the `plantuml` language identifier. To edit a diagram:

1. Find the diagram's code block (enclosed in \`\`\`plantuml markers)
2. Edit the diagram code
3. Preview to verify your changes

This approach follows our Test-Driven Development principles by:

- Ensuring diagrams accurately represent the implemented system behavior
- Providing a way to "test" diagram changes visually before committing
- Maintaining documentation as a living artifact that changes with the codebase
- Supporting code reviews of architectural changes
