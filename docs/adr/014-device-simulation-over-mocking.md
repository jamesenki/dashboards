# 14. Device Simulation Framework Over Mocking

Date: 2025-04-06

## Status

Accepted

## Context

Testing and developing an IoT platform requires representative device data. Our previous approach relied heavily on mock data providers and mock APIs, which created several limitations:

1. Mocks often simplified real-world behavior, leading to gaps in testing
2. Mock data was disconnected from actual device protocols and behaviors
3. User interfaces didn't clearly indicate when they were displaying mock data
4. Development and production environments had significant differences
5. Testing focused on simplified interfaces rather than realistic interactions

The BDD tests require validation of complex device behavior and interactions, which demand more realistic device data and interactions.

## Decision

We will implement a comprehensive device simulation framework instead of simple mocking:

1. **Device Simulator Framework**:
   - Creates software-simulated devices that mimic real device behavior
   - Connects to the system using the same protocols as real devices (MQTT, HTTP, etc.)
   - Generates realistic telemetry based on device type models
   - Responds to commands like real devices would

2. **Simulation Manager**:
   - Coordinates fleets of simulated devices
   - Configures device behavior characteristics
   - Creates testing scenarios with predictable outcomes
   - Supports load testing with many simultaneous devices

3. **Simulation Indicators**:
   - Clear visual indicators in UI when displaying simulated data
   - API response headers indicating simulation source
   - Log entries that clearly identify simulated interactions
   - Documentation of simulated vs. real behavior

4. **Database Population**:
   - Simulators will populate the actual production database types
   - Simulated data will follow the same schemas and formats as real data
   - Historical simulation runs can be preserved for regression testing

## Consequences

### Positive

1. **More Realistic Testing**: Tests will interact with a closer approximation of real devices
2. **Better Developer Experience**: Working with simulated devices in development is similar to production
3. **Enhanced Test Coverage**: Simulators can generate edge cases and fault conditions difficult to reproduce with real devices
4. **Improved Transparency**: Clear indication of simulated data prevents confusion
5. **Production-Like Data**: Databases contain realistic data structures and volumes

### Negative

1. **Higher Development Effort**: Creating realistic simulators requires more work than simple mocks
2. **Increased Complexity**: Simulator frameworks are more complex to maintain than mocks
3. **Additional Runtime Resources**: Running simulators requires more computational resources
4. **Potential for Over-Engineering**: Risk of building overly complex simulators that don't add proportional value

### Mitigations

1. We will develop the simulator framework incrementally, starting with the most critical features
2. For simpler components, traditional mocks may still be appropriate
3. Containerization will make efficient use of resources when running simulators
4. Clear documentation will explain simulator capabilities and limitations

## Compliance with TDD Principles

This decision strongly supports our TDD approach by:

1. Enabling tests that define realistic expected behavior based on device interactions
2. Supporting comprehensive behavior verification rather than implementation details
3. Allowing tests to drive the development of actual device integration code
4. Creating a testing environment that closely mirrors production

Our approach follows the TDD principle that tests define the expected behaviors and requirements, and our implementation will make those tests pass using the same interfaces and protocols as real devices would use.

## Alternative Options Considered

1. **Traditional Mocking Framework**:
   - Pros: Simpler implementation, lower resource requirements
   - Cons: Less realistic behavior, disconnected from real protocols
   - Rejected because: Cannot adequately test the full system behavior

2. **Hardware Device Test Lab**:
   - Pros: Testing with actual physical devices provides highest realism
   - Cons: Extremely expensive, limited scale, difficult to automate
   - Rejected because: Not practical for continuous integration and most development needs

3. **Third-Party IoT Simulation Service**:
   - Pros: Potentially more sophisticated simulation without building from scratch
   - Cons: External dependency, less customization, potential costs
   - Rejected because: Need deeper integration with our specific platform architecture
