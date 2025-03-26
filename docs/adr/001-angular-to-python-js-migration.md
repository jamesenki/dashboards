# ADR 001: Migration from Angular to Python/JavaScript Architecture

## Status

Accepted

## Context

The original IoTSphere application was built using Angular on the frontend with a complex component architecture. This implementation had several challenges:

1. **Dependency Management**: Angular's extensive dependency tree became difficult to maintain and secure over time.
2. **Security Vulnerabilities**: Regular security updates in the Angular ecosystem required frequent maintenance.
3. **Customer Customization**: Customers found it difficult to customize the Angular application without specialized knowledge.
4. **Frontend-Backend Coupling**: The Angular frontend contained significant business logic that should ideally be in the backend.

## Decision

We decided to refactor the application architecture from an Angular frontend to a Python backend with a lightweight JavaScript/HTML frontend.

Key aspects of this decision:

1. Move business logic to the Python backend
2. Create simple HTML templates with minimal JavaScript for UI interactions
3. Implement a REST API for communication between frontend and backend
4. Use standard JavaScript (no framework) for frontend interactions

## Consequences

### Positive

1. **Better Separation of Concerns**: Business logic is now centralized in the backend.
2. **Simplified Dependency Management**: Fewer frontend dependencies and better control over versions.
3. **Improved Customization**: HTML/CSS templates are easier for customers to customize.
4. **Enhanced Security**: Reduced attack surface with fewer frontend dependencies.
5. **Developer Flexibility**: Backend developers can focus on Python, while frontend work requires only standard HTML/JS/CSS knowledge.

### Negative

1. **Feature Reimplementation**: Certain Angular features needed reimplementation in vanilla JavaScript.
2. **Loss of Angular Tooling**: Loss of Angular's built-in tooling for development and testing.
3. **Manual DOM Manipulation**: More manual DOM manipulation required compared to Angular's declarative approach.

### Mitigations

1. Implemented a compact JavaScript utility library to handle common tasks
2. Created a standardized pattern for server-side rendering with client-side enhancements
3. Established clear API contracts to maintain frontend-backend separation
4. Added comprehensive testing to ensure functionality parity with the original Angular application

## Implementation Notes

The implementation was carried out in phases:

1. First, we developed the Python backend with a complete REST API
2. Next, we created HTML templates matching the original Angular UI
3. Then, we implemented JavaScript for dynamic functionality
4. Finally, we added comprehensive testing for both frontend and backend

## Related Documentation

- [Architecture Overview](../architecture-overview.md)
- [Operations Dashboard](../operations_dashboard.md)
