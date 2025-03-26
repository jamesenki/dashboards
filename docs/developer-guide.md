# IoTSphere Developer Guide

## Introduction

This guide is designed to help new developers get started with the IoTSphere project. It covers development environment setup, coding standards, testing practices, and common development workflows.

## Development Environment Setup

### Prerequisites

- Python 3.9+ (Python 3.10 recommended)
- pip (Python package manager)
- Git
- Node.js 16+ and npm (for frontend tests)
- A code editor (VS Code recommended)

### Initial Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-organization/iotsphere.git
   cd iotsphere
   ```

2. **Set up a Python virtual environment**

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   npm install  # Frontend test dependencies
   ```

4. **Set up pre-commit hooks**

   ```bash
   pre-commit install
   ```

5. **Initialize the database**

   ```bash
   python src/scripts/init_db.py
   ```

## Project Structure

Understanding the project structure is essential for effective development:

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
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── run_tests.py         # Test runner script
```

## Development Workflow

### Running the Application Locally

Start the development server:

```bash
python src/main.py
```

Access the application at http://localhost:8006

### Making Changes

#### Backend Changes

1. Create a new feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes to the Python code
3. Write tests for your changes
4. Run the tests to ensure they pass:
   ```bash
   python run_tests.py
   ```
5. Format your code:
   ```bash
   black src
   isort src
   ```

#### Frontend Changes

1. Modify the HTML templates in `frontend/templates/`
2. Update or create JavaScript in `frontend/static/js/`
3. Add or modify styles in `frontend/static/css/`
4. Test your changes by running the application
5. Run frontend tests:
   ```bash
   npm test
   ```

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if necessary
3. Push your branch to the remote repository
4. Create a pull request with a clear description of your changes
5. Request a code review from a team member

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints when defining functions
- Write docstrings for all modules, classes, and functions
- Keep functions small and focused on a single responsibility
- Use descriptive variable names

Example:

```python
def get_vending_machine_by_id(machine_id: str) -> Optional[VendingMachine]:
    """
    Retrieve a vending machine by its ID.
    
    Args:
        machine_id: The unique identifier of the vending machine
        
    Returns:
        The VendingMachine object if found, None otherwise
    """
    return db.session.query(VendingMachine).filter_by(id=machine_id).first()
```

### JavaScript

- Use ES6+ features where appropriate
- Prefer const over let, and avoid var
- Use descriptive function and variable names
- Add comments for complex logic
- Keep functions small and focused

Example:

```javascript
/**
 * Update the inventory display with the provided data
 * @param {Array} inventoryItems - Array of inventory items
 */
function updateInventoryDisplay(inventoryItems) {
    const container = document.getElementById('inventory-container');
    if (!container) return;
    
    // Clear current inventory
    container.innerHTML = '';
    
    // Handle empty inventory case
    if (!inventoryItems || inventoryItems.length === 0) {
        container.innerHTML = '<div class="no-data-message">No inventory data available</div>';
        return;
    }
    
    // Create inventory items
    inventoryItems.forEach(item => {
        // Implementation details...
    });
}
```

### HTML/CSS

- Use semantic HTML elements
- Follow a consistent naming convention for CSS classes (BEM recommended)
- Ensure all interactive elements are accessible
- Use responsive design principles

## Testing Guidelines

### Backend Testing

All backend code should be covered by tests:

1. **Unit Tests**: For individual functions and classes
2. **Integration Tests**: For API endpoints and service interactions
3. **Functional Tests**: For end-to-end workflows

Example test:

```python
def test_get_vending_machine_by_id():
    # Arrange
    machine_id = "test-123"
    machine = VendingMachine(id=machine_id, name="Test Machine")
    db.session.add(machine)
    db.session.commit()
    
    # Act
    result = get_vending_machine_by_id(machine_id)
    
    # Assert
    assert result is not None
    assert result.id == machine_id
    assert result.name == "Test Machine"
```

### Frontend Testing

Frontend testing focuses on:

1. **Unit Tests**: For JavaScript utility functions
2. **Component Tests**: For UI components
3. **UI Integration Tests**: For user interactions

Example test:

```javascript
describe('updateInventoryDisplay function', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="inventory-container"></div>';
    });
    
    test('should display inventory items correctly', () => {
        // Arrange
        const mockInventory = [
            { name: 'Vanilla', level: 80, max_capacity: 100 }
        ];
        
        // Act
        updateInventoryDisplay(mockInventory);
        
        // Assert
        const container = document.getElementById('inventory-container');
        expect(container.innerHTML).toContain('Vanilla');
        expect(container.innerHTML).toContain('80/100');
    });
    
    test('should handle empty inventory', () => {
        // Act
        updateInventoryDisplay([]);
        
        // Assert
        const container = document.getElementById('inventory-container');
        expect(container.innerHTML).toContain('No inventory data available');
    });
});
```

## Water Heater Dashboard Development

The IoTSphere project uses Test-Driven Development (TDD) for implementing device dashboards, especially the water heater operations and history dashboards. This section provides guidance on extending or modifying these features.

### Dashboard Architecture

The water heater dashboard consists of three main components:

1. **Details Tab**: Basic information and controls
2. **Operations Tab**: Real-time operational monitoring
3. **History Tab**: Historical data analysis

Each component follows a layered architecture:
- **Backend Service**: Processes and prepares data
- **API Endpoint**: Exposes data to frontend
- **Frontend Component**: Renders visualizations and UI

### Test-Driven Development Workflow

When implementing or modifying dashboard features, follow this TDD process:

1. **Red**: Write failing tests first
   ```python
   def test_water_heater_history_service_get_temperature():
       # Arrange
       history_service = WaterHeaterHistoryService()
       heater_id = "test-heater-123"
       days = 7
       
       # Act
       result = await history_service.get_temperature_history(heater_id, days)
       
       # Assert
       assert "labels" in result
       assert "datasets" in result
       assert len(result["labels"]) > 0
   ```

2. **Green**: Implement minimal code to make tests pass
   ```python
   async def get_temperature_history(self, heater_id: str, days: int = 7) -> Dict[str, Any]:
       # Get water heater
       heater = await self.water_heater_service.get_water_heater(heater_id)
       if not heater:
           raise Exception(f"Water heater with ID {heater_id} not found")
            
       # Process readings to create chart data
       # ...implementation code here...
       
       return {
           "labels": timestamp_labels,
           "datasets": [{
               "label": "Temperature (°C)",
               "data": temperature_data,
               # ...other chart configuration...
           }]
       }
   ```

3. **Refactor**: Improve code while maintaining passing tests
   - Enhance error handling
   - Optimize performance
   - Improve code organization

### End-to-End Testing

Always create end-to-end tests to verify consistency across all views:

```python
def test_end_to_end_consistency():
    # Get a water heater ID from the system
    water_heaters = client.get("/api/water-heaters/").json()
    heater_id = water_heaters[0]["id"]
    
    # Test details endpoint
    details = client.get(f"/api/water-heaters/{heater_id}").json()
    
    # Test operations endpoint
    operations = client.get(f"/api/water-heaters/{heater_id}/operations").json()
    
    # Test history endpoint
    history = client.get(f"/api/water-heaters/{heater_id}/history").json()
    
    # Verify consistency across all three views
    assert details["id"] == heater_id
    # Additional assertions...
```

### Real-time vs. Historical Focus

Our dashboard implementation follows these principles:

- **Operations Tab**: Focuses on real-time operational monitoring with status cards, gauges, and asset health metrics
- **History Tab**: Provides historical analysis through time-series charts for temperature, energy usage, and pressure/flow metrics

When extending either tab, maintain this separation of concerns:

1. Operations tab should answer: "What is happening right now?"
2. History tab should answer: "What has happened over time?"

## Debugging Tips

### Backend Debugging

1. Use `print()` statements or Python's `logging` module
2. Set breakpoints in your IDE
3. Use `pdb` for interactive debugging:
   ```python
   import pdb; pdb.set_trace()
   ```

### Frontend Debugging

1. Use `console.log()` statements
2. Leverage browser dev tools (Elements, Network, Console tabs)
3. Set breakpoints in the browser's Sources panel

## Database Management

### Database Migrations

When changing the database schema:

1. Create a migration script:
   ```bash
   python src/scripts/create_migration.py "description_of_changes"
   ```

2. Review the generated migration file in `src/migrations/`

3. Apply the migration:
   ```bash
   python src/scripts/migrate_db.py
   ```

### Database Seeding

Populate the database with test data:

```bash
python src/scripts/seed_db.py
```

## Deployment

### Staging Deployment

Deploy to the staging environment:

```bash
./deploy_staging.sh
```

### Production Deployment

Production deployments are handled through the CI/CD pipeline. Once your code is merged to the main branch, it will be automatically deployed after passing all tests.

## API Documentation

The API is documented using OpenAPI/Swagger. View the API documentation by running the application and navigating to:

```
http://localhost:8006/api/docs
```

## Additional Resources

- [Architecture Overview](./architecture-overview.md)
- [Testing Strategy](../testing-strategy.md)
- [Operations Dashboard](./operations_dashboard.md)
- [Architecture Decision Records](./adr/)

## Getting Help

If you encounter issues or have questions:

1. Check the documentation
2. Review existing GitHub issues
3. Ask in the team Slack channel (#iotsphere-dev)
4. Create a new GitHub issue if needed
