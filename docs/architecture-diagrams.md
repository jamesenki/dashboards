# IoTSphere Architecture Diagrams

This document provides information about the architecture diagrams available for the IoTSphere project and how to use them.

## System Architecture Diagram

The main system architecture diagram (`system-architecture.puml`) provides a visual representation of the IoTSphere system components, their interactions, and the key architectural patterns employed in the project. It emphasizes the real-time operational monitoring focus as per the project requirements.

## Viewing the Diagrams

### Option 1: Using Online PlantUML Servers

The quickest way to view the diagrams is to use an online PlantUML server:

1. Copy the content of the `.puml` file you want to view
2. Visit [PlantUML Web Server](https://www.plantuml.com/plantuml/uml/)
3. Paste the content and click "Submit"
4. The server will render the diagram for you to view or download

### Option 2: Using Visual Studio Code with PlantUML Extension

If you're using Visual Studio Code:

1. Install the "PlantUML" extension by jebbs
2. Open the `.puml` file
3. Right-click and select "Preview Current Diagram" or use Alt+D to view the diagram

### Option 3: Using Local PlantUML Installation

For a local installation:

1. Install Java (required for PlantUML)
2. Download the latest PlantUML jar from [PlantUML website](https://plantuml.com/download)
3. Run the diagram generation:
   ```bash
   java -jar plantuml.jar docs/diagrams/system-architecture.puml
   ```
4. This will create a PNG file in the same directory as the `.puml` file

## Key Architecture Components

### Dashboard Architecture

Our dashboard architecture consists of several key components:

#### TabManager System

The TabManager is a core UI component that provides:

- **Component Lifecycle Management**: Handles component activation/deactivation
- **Tab Navigation**: Manages tab switching and visibility
- **Event Propagation**: Provides a publish/subscribe mechanism for cross-component communication
- **Error Recovery**: Implements robust error handling and recovery mechanisms

See the full documentation in `docs/tab-manager.md`.

#### Water Heater Dashboard Modules

The Water Heater dashboard is organized into tabbed modules:

- **Details Tab**: Basic device information and configuration
- **Operations Tab**: Real-time operational monitoring with status cards, gauges, and asset health metrics
- **Predictions Tab**: Predictive analytics with lifespan estimation, anomaly detection, and recommended actions
- **History Tab**: Historical analysis through time-series charts for temperature, energy usage, and pressure metrics

See the detailed documentation in `docs/water-heater-dashboard.md`.

### Real-Time Operational Focus

Our architecture emphasizes real-time operational monitoring rather than historical analytics, as highlighted in ADR-002. Key components include:

- **Real-time Operations API**: Provides current status of devices with minimal latency
- **Operational Dashboard**: Displays status cards, temperature/energy gauges, and cycle tracking
- **Predictions Dashboard**: Provides forward-looking analytics with action recommendations
- **PostgreSQL with TimescaleDB**: Efficiently stores and retrieves time-series data, with graceful degradation if TimescaleDB is not available

### Test-Driven Development Workflow

The TDD workflow is integrated into our development process for all new features, especially for machine learning components:

1. **Red Phase**: Write failing tests that define expected functionality
2. **Green Phase**: Implement the minimum code required to pass tests
3. **Refactor Phase**: Improve code quality while keeping tests passing

The `scripts/tdd_workflow.py` script helps automate this process.

### Database Architecture

As documented in ADR-003, we've implemented a PostgreSQL database with optional TimescaleDB integration:

- PostgreSQL provides reliable relational storage with JSON support
- TimescaleDB extension optimizes time-series data handling for telemetry readings
- The application is designed to work with or without TimescaleDB

## Diagram Maintenance

When making significant architectural changes, please update the relevant diagrams to keep documentation in sync with the implementation. Follow these guidelines:

1. Edit the `.puml` files in the `docs/diagrams/` directory
2. Generate updated diagram images
3. Link to these diagrams from relevant documentation

## Reference

- [PlantUML Documentation](https://plantuml.com/guide)
- [C4 Model for Software Architecture](https://c4model.com/)
