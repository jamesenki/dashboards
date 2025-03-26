# ADR 002: Operations Dashboard Realignment to Real-Time Monitoring

## Status

Accepted

## Context

During the refactoring process from Angular to a Python/JavaScript architecture, we identified a significant architectural mismatch between our implementation of the Operations Dashboard and the original Angular version:

1. **Original Angular Implementation**:
   - Focused on real-time operational monitoring
   - Featured status cards (Machine Status, POD Code, Cup Detect, etc.)
   - Included gauge charts (Asset Health, Freezer Temperature, Dispense Force, Cycle time)
   - Provided inventory tracking
   - Emphasized real-time operational metrics

2. **Our Initial Refactored Implementation**:
   - Focused on historical analytics and reporting
   - Emphasized sales data and performance metrics
   - Included usage patterns analysis
   - Displayed maintenance history records
   - Featured refill tracking
   - Showed temperature trends over time

This misalignment meant that users would lose critical real-time operational visibility when migrating to our refactored version.

## Decision

We decided to realign our Operations Dashboard implementation to match the real-time operational focus of the original Angular application, while maintaining the Python backend architecture.

Key aspects of this decision:

1. Create new models that match the expected frontend data structure for real-time operations
2. Update our services to provide real-time operational data instead of historical analytics
3. Implement real-time gauge visualizations and status cards
4. Maintain consistent data formats between frontend and backend
5. Ensure property naming conventions are consistent and handle fallbacks for backward compatibility

## Consequences

### Positive

1. **Feature Parity**: Users maintain the same operational visibility they had in the Angular version
2. **Real-Time Decision Making**: Operators can make timely decisions based on current operational status
3. **Consistent User Experience**: The transition between Angular and refactored versions is seamless for users
4. **More Useful for Day-to-Day Operations**: Real-time data is more valuable for daily operations than historical analytics

### Negative

1. **Delayed Analytics Features**: Historical analytics implementation is postponed
2. **Additional Development Effort**: Required reimplementation of real-time components
3. **Data Format Complexity**: Need to handle multiple property naming conventions for backward compatibility

### Mitigations

1. Added property name fallbacks in frontend rendering to handle inconsistent data formats
2. Implemented comprehensive tests to verify data transformation correctness
3. Created flexible UI components that can adapt to different property naming patterns
4. Documented the operational dashboard architecture for future maintenance

## Implementation Details

1. **Data Model Alignment**:
   - Created `VendingMachineOperationsData` model for real-time metrics
   - Implemented sub-models for specific metrics (temperature, pressure, cycle time)
   - Added inventory tracking models with consistent property names

2. **UI Components**:
   - Implemented gauge visualizations for key metrics
   - Created status cards for operational states
   - Added inventory visualization with level indicators
   - Ensured responsive design across device sizes

3. **Data Transformation**:
   - Implemented data normalization in both frontend and backend
   - Added graceful fallbacks for missing or malformed data
   - Ensured consistent data formats between API and UI

4. **Property Name Compatibility**:
   - Added fallback property name handling in UI (e.g., `level` or `current_level`)
   - Standardized property names in backend to prevent future inconsistencies

## Related Documentation

- [Operations Dashboard Documentation](../operations_dashboard.md)
- [Testing Strategy](../../testing-strategy.md)
