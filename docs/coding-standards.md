# IoTSphere Coding Standards

## Overview

This document outlines the coding standards and style guidelines for the IoTSphere project. Consistent coding practices improve readability, maintainability, and collaboration across the development team.

## General Principles

1. **Readability**: Code should be easy to read and understand
2. **Simplicity**: Prefer simple, straightforward solutions over complex ones
3. **Consistency**: Follow established patterns and practices
4. **Documentation**: Document code where necessary, especially public APIs
5. **Testability**: Write code that is testable and has appropriate test coverage

## Python Standards

### Style Guide

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style with these specifics:

- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (as per Black formatter)
- Use snake_case for function and variable names
- Use CamelCase for class names
- Use UPPER_CASE for constants

### Code Organization

- Each module should have a clear, single responsibility
- Organize imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Separate import groups with a blank line
- Sort imports alphabetically within each group

```python
# Standard library
import json
import os
from datetime import datetime

# Third-party
import flask
from sqlalchemy import Column, Integer, String

# Local application
from src.models.base import Base
from src.utils.validators import validate_email
```

### Type Annotations

Use type hints for function parameters and return values:

```python
def get_user_by_id(user_id: str) -> Optional[User]:
    """Retrieve a user by their ID."""
    return User.query.filter_by(id=user_id).first()
```

### Docstrings

Use Google-style docstrings for functions, classes, and modules:

```python
def calculate_average_temperature(readings: List[float]) -> float:
    """
    Calculate the average temperature from a list of readings.
    
    Args:
        readings: A list of temperature readings in Celsius
        
    Returns:
        The average temperature
        
    Raises:
        ValueError: If the readings list is empty
    """
    if not readings:
        raise ValueError("Cannot calculate average of empty readings list")
    return sum(readings) / len(readings)
```

### Error Handling

- Use specific exception types instead of catching all exceptions
- Only catch exceptions you can actually handle
- Re-raise exceptions with context when appropriate

```python
try:
    user_data = fetch_user_data(user_id)
except ConnectionError:
    logger.warning(f"Network error when fetching data for user {user_id}")
    return None
except ValueError as e:
    logger.error(f"Invalid data format for user {user_id}: {str(e)}")
    raise
```

## JavaScript Standards

### Style Guide

- Use ES6+ syntax where appropriate
- Use 2 spaces for indentation (no tabs)
- Maximum line length of 100 characters
- Use camelCase for function and variable names
- Use PascalCase for class names and component names
- Use semicolons at the end of statements

### Code Organization

- Organize code into logical modules
- Keep functions small and focused on a single responsibility
- Use meaningful names for functions and variables

### Comments

Add comments for complex logic, but aim for self-documenting code:

```javascript
/**
 * Calculate percentage and determine status class for inventory items
 * @param {number} current - Current inventory level
 * @param {number} max - Maximum inventory capacity
 * @returns {Object} Status information including percentage and class
 */
function getInventoryStatus(current, max) {
  // Ensure values are valid numbers and calculate percentage
  const value = Number(current) || 0;
  const capacity = Number(max) || 100;
  const percentage = Math.max(0, Math.min(100, (value / capacity) * 100));
  
  // Determine status based on percentage thresholds
  let statusClass = 'inventory-status-ok';
  let statusText = 'OK';
  
  if (percentage <= 20) {
    statusClass = 'inventory-status-critical';
    statusText = 'Critical';
  } else if (percentage <= 50) {
    statusClass = 'inventory-status-low';
    statusText = 'Low';
  }
  
  return { percentage, statusClass, statusText };
}
```

### Error Handling

- Use try/catch blocks for error handling
- Provide meaningful error messages
- Log errors appropriately

```javascript
async function fetchMachineData(machineId) {
  try {
    const response = await fetch(`/api/machines/${machineId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch machine data: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching data for machine ${machineId}:`, error);
    showErrorNotification('Failed to load machine data. Please try again.');
    return null;
  }
}
```

## HTML/CSS Standards

### HTML

- Use HTML5 semantic elements where appropriate
- Use lowercase for HTML element names and attributes
- Use double quotes for attribute values
- Ensure proper nesting of elements
- Include appropriate ARIA attributes for accessibility

```html
<section class="dashboard-panel">
  <h2 class="panel-title">Operations Summary</h2>
  <div class="panel-content" aria-live="polite">
    <div class="status-card" role="status">
      <span class="status-indicator online"></span>
      <span class="status-label">Machine Status: Online</span>
    </div>
  </div>
</section>
```

### CSS

- Use BEM (Block, Element, Modifier) naming convention
- Keep selectors as simple as possible
- Use CSS variables for common values
- Organize CSS by component
- Include comments for complex sections

```css
/* Operations Dashboard - Status Cards */
.status-card {
  display: flex;
  align-items: center;
  padding: var(--spacing-medium);
  background-color: var(--color-background-card);
  border-radius: var(--border-radius-standard);
  margin-bottom: var(--spacing-small);
}

.status-card__indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: var(--spacing-small);
}

.status-card__indicator--online {
  background-color: var(--color-status-online);
}

.status-card__indicator--offline {
  background-color: var(--color-status-offline);
}

.status-card__label {
  font-weight: 500;
  color: var(--color-text-primary);
}
```

## SQL Standards

- Use uppercase for SQL keywords
- Use singular names for tables
- Use snake_case for column and table names
- Include appropriate indexes
- Use full column names in queries (not `SELECT *`)

```sql
-- Good
SELECT user_id, username, email 
FROM user 
WHERE status = 'active' 
ORDER BY created_at DESC;

-- Avoid
SELECT * 
FROM users 
WHERE status = 'active';
```

## Testing Standards

### Test Organization

- Group tests by functionality
- Name test functions clearly to describe what they're testing
- Organize tests with Arrange-Act-Assert pattern

### Python Tests

```python
def test_get_vending_machine_by_id_returns_correct_machine():
    # Arrange
    machine_id = "test-123"
    expected_machine = VendingMachine(id=machine_id, name="Test Machine")
    db.session.add(expected_machine)
    db.session.commit()
    
    # Act
    result = get_vending_machine_by_id(machine_id)
    
    # Assert
    assert result is not None
    assert result.id == machine_id
    assert result.name == "Test Machine"
```

### JavaScript Tests

```javascript
describe('updateInventoryDisplay', () => {
  beforeEach(() => {
    // Set up DOM for testing
    document.body.innerHTML = '<div id="inventory-container"></div>';
  });
  
  test('displays inventory items with correct format', () => {
    // Arrange
    const inventoryItems = [
      { name: 'Vanilla', level: 80, max_capacity: 100 }
    ];
    
    // Act
    updateInventoryDisplay(inventoryItems);
    
    // Assert
    const container = document.getElementById('inventory-container');
    expect(container.innerHTML).toContain('Vanilla');
    expect(container.innerHTML).toContain('80/100');
  });
});
```

## Code Review Guidelines

### What to Look For

1. **Functionality**: Does the code work as expected?
2. **Correctness**: Is the logic correct?
3. **Style**: Does the code follow our style guidelines?
4. **Performance**: Are there any performance concerns?
5. **Security**: Are there any security vulnerabilities?
6. **Testability**: Is the code testable and are tests included?
7. **Maintainability**: Will the code be easy to maintain?

### Review Process

1. Be respectful and constructive in comments
2. Focus on the code, not the person
3. Explain the reasoning behind suggestions
4. Provide examples when possible
5. Categorize comments (e.g., "Blocker", "Suggestion", "Question")

### Sample Review Comment

```
[Suggestion] Consider using a more descriptive variable name than 'data' here. 
Perhaps 'operationsData' or 'machineMetrics' would better convey its purpose.
```

## Documentation Standards

### Code Documentation

- Document all public APIs, classes, and functions
- Keep documentation up-to-date with code changes
- Include examples where helpful

### Project Documentation

- Store documentation in the `docs/` directory
- Write documentation in Markdown format
- Maintain a consistent structure across documentation files
- Include diagrams where appropriate (using PlantUML or Mermaid)

## Version Control Practices

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features or enhancements
- `bugfix/*`: Bug fixes
- `release/*`: Release preparation
- `hotfix/*`: Urgent production fixes

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks

Example:
```
feat(operations): add real-time inventory tracking

Implement real-time inventory tracking on the operations dashboard with 
visual indicators for inventory levels and automatic updating.

Closes #123
```

## Enforcement

These standards are enforced through:

1. **Pre-commit hooks**: Automatically check and fix style issues
2. **CI/CD pipeline**: Run linters and tests on each commit
3. **Code reviews**: Manual verification by team members
4. **Pair programming**: Knowledge sharing and adherence to standards

## Tools

Use these tools to help maintain coding standards:

- **Python**: Black (formatter), isort (import sorting), flake8 (linter), mypy (type checking)
- **JavaScript**: ESLint (linter), Prettier (formatter)
- **HTML/CSS**: HTMLHint, Stylelint
- **SQL**: SQLFluff

## Conclusion

Adhering to these coding standards will help ensure that the IoTSphere codebase remains clean, maintainable, and consistent. The goal is to make development more efficient and collaboration more effective, not to create unnecessary constraints.
