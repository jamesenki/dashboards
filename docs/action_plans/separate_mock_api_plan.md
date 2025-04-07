# Action Plan: Separate Mock API Architecture

## Overview
This action plan outlines the steps for implementing a clear separation between the real database API and mock data API in the IoTSphere application. Instead of using mock data as a fallback within the same API endpoints, we will create separate and explicit endpoints for mock data.

## Architecture Change
```
Current:
UI → API Endpoint → Service → Repository (DB or Mock)

Proposed:
UI → Real API Endpoint → Database Repository
 ↘→ Mock API Endpoint → Mock Repository
```

## Implementation Tasks

### Phase 1: Backend API Separation

- [ ] **Create API Interface Definition**
  - [ ] Define common interface/contract for both real and mock APIs
  - [ ] Document required endpoints and response formats
  - [ ] Create OpenAPI specification for both APIs

- [ ] **Implement Separate API Routers**
  - [ ] Create `/api/db/water-heaters/*` routes for database operations
  - [ ] Create `/api/mock/water-heaters/*` routes for mock data
  - [ ] Implement health check endpoints for both APIs
  - [ ] Add metadata to API responses indicating data source

- [ ] **Refactor Repository Layer**
  - [ ] Update SQLiteWaterHeaterRepository to ensure database schema matches model
  - [ ] Create database migration scripts for required schema changes
  - [ ] Enhance MockWaterHeaterRepository to fully implement the repository interface
  - [ ] Add proper error handling in both repositories

- [ ] **Implement Shared Base Classes (Mitigation for API Duplication)**
  - [ ] Create base router class with common endpoint logic
  - [ ] Implement shared request/response validation
  - [ ] Extract common functionality to utility classes

### Phase 2: API Synchronization (Mitigation for API Drift)

- [ ] **Create API Parity Tests**
  - [ ] Implement tests to verify both APIs return same structure
  - [ ] Create test fixtures for comparing API responses
  - [ ] Add tests for edge cases and error scenarios

- [ ] **Implement API Version Control**
  - [ ] Add version headers to all API responses
  - [ ] Create documentation detailing API versions
  - [ ] Implement version compatibility checks

- [ ] **Setup Automated Consistency Monitoring**
  - [ ] Create CI/CD pipeline to verify API parity
  - [ ] Implement alerts for API drift
  - [ ] Add documentation for maintaining API consistency

### Phase 3: Frontend Integration

- [ ] **Create Frontend Service Layer (Mitigation for Frontend Complexity)**
  - [ ] Implement `WaterHeaterService` to abstract API selection
  - [ ] Add configuration options for API preference
  - [ ] Create error handling for API fallback scenarios

- [ ] **Enhance UI for Data Source Transparency**
  - [ ] Add visual indicators showing data source (mock vs real)
  - [ ] Implement user-controlled toggle between sources
  - [ ] Add tooltips explaining data source implications

- [ ] **Update Angular Components**
  - [ ] Modify water heater components to use new service layer
  - [ ] Update API path references throughout the codebase
  - [ ] Add loading states during API fallback scenarios

### Phase 4: Testing and Documentation

- [ ] **Update Integration Tests**
  - [ ] Create separate test suites for real and mock APIs
  - [ ] Remove xfail tests that were handling mixed implementation
  - [ ] Add end-to-end tests for fallback scenarios

- [ ] **Enhance Documentation**
  - [ ] Update API documentation to reflect new endpoints
  - [ ] Create developer guide for working with separate APIs
  - [ ] Add notes on testing strategy with separated concerns

- [ ] **Create Monitoring Dashboard**
  - [ ] Implement visual indicators for API health
  - [ ] Create metrics for API usage (mock vs real)
  - [ ] Add logging for API fallback scenarios

## Timeline and Resources

**Estimated Timeline:**
- Phase 1: 1-2 weeks
- Phase 2: 1 week
- Phase 3: 1-2 weeks
- Phase 4: 1 week

**Required Resources:**
- Backend Developer: 1-2 full-time
- Frontend Developer: 1 full-time
- QA Engineer: Part-time during testing phases
- DevOps: Support for CI/CD pipeline updates

## Risk Assessment

**Potential Risks:**
1. **Migration Complexity:** Existing code relying on current API structure may break
   - Mitigation: Phase the rollout with compatibility layer during transition

2. **Performance Impact:** Additional API layer might introduce latency
   - Mitigation: Implement caching strategies where appropriate

3. **Development Timeline:** Large architecture change may impact other features
   - Mitigation: Implement changes incrementally with continuous integration

## Success Criteria
- Clear separation between real and mock data sources
- Improved transparency for users about data source
- Elimination of xfail tests related to mixed implementations
- Proper error handling and fallback mechanisms
- Comprehensive documentation and monitoring

## Approval and Sign-off

- [ ] Architecture review completed
- [ ] Resource allocation approved
- [ ] Timeline agreed upon
- [ ] Success criteria accepted

## Notes
This architecture change aligns with the IoTSphere project's Test-Driven Development approach by creating clearer test expectations and making it easier to test each component in isolation.
