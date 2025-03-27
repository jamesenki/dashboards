/**
 * Water Heater Predictions Dashboard Test
 * This test verifies that data loading works properly for the water heater predictions dashboard
 */

// Import mock for testing
require('./water_heater_predictions_mock');


describe('WaterHeaterPredictionsDashboard', function() {
  // Mock DOM elements
  beforeEach(function() {
    // Set up DOM fixtures
    document.body.innerHTML = `
      <div id="test-container">
        <div id="water-heater-predictions-dashboard"></div>
        <div id="lifespan-prediction-card"></div>
        <div id="anomaly-detection-card"></div>
        <div id="usage-patterns-card"></div>
        <div id="multi-factor-card"></div>
      </div>
    `;
    
    // Mock fetch API
    global.fetch = jest.fn();
    
    // Mock successful response
    const mockSuccessResponse = {
      lifespan_estimation: { confidence: 0.9, estimated_remaining_days: 365 },
      anomaly_detection: { 
        confidence: 0.95,
        raw_details: {
          detected_anomalies: [],
          trend_analysis: { temperature: { trend_direction: 'stable' } }
        },
        recommended_actions: []
      },
      usage_patterns: { confidence: 0.8, patterns: [] },
      multi_factor: { 
        confidence: 0.85, 
        health_score: 85,
        component_interactions: []
      }
    };
    
    // Set up fetch mock to return the success response
    global.fetch.mockImplementation(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSuccessResponse)
      })
    );
  });
  
  // Cleanup after tests
  afterEach(function() {
    document.body.innerHTML = '';
    jest.resetAllMocks();
  });
  
  it('should initialize data properly on construction', function() {
    // Create new dashboard instance
    const dashboard = new WaterHeaterPredictionsDashboard('water-heater-predictions-dashboard', 'test-device-id');
    
    // Verify that fetch was called with the correct URL
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/predictions/water-heaters/test-device-id/all'));
    
    // Return the promise for proper async testing
    return new Promise(resolve => {
      // Use setTimeout to allow the dashboard initialization to complete
      setTimeout(() => {
        // Verify dataInitialized flag is true
        expect(dashboard.dataInitialized).toBe(true);
        
        // Verify data objects are populated
        expect(dashboard.lifespanPrediction).not.toBeNull();
        expect(dashboard.anomalyDetection).not.toBeNull();
        expect(dashboard.usagePatterns).not.toBeNull();
        expect(dashboard.multiFactor).not.toBeNull();
        
        resolve();
      }, 200);
    });
  });
  
  it('should set dataInitialized flag when data is loaded', function() {
    // Create new dashboard instance
    const dashboard = new WaterHeaterPredictionsDashboard('water-heater-predictions-dashboard', 'test-device-id');
    
    // Initially the data should not be marked as initialized
    expect(dashboard.dataInitialized).toBe(false);
    
    // Return the promise for proper async testing
    return new Promise(resolve => {
      // Use setTimeout to allow the fetch to complete
      setTimeout(() => {
        // After fetch completes, dataInitialized should be true
        expect(dashboard.dataInitialized).toBe(true);
        resolve();
      }, 200);
    });
  });
  
  it('should retry data loading if initial load fails', function() {
    // Override fetch to fail on first call, succeed on second
    let callCount = 0;
    global.fetch.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.reject(new Error('Network error'));
      } else {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            lifespan_estimation: { confidence: 0.9 }
          })
        });
      }
    });
    
    // Create new dashboard instance
    const dashboard = new WaterHeaterPredictionsDashboard('water-heater-predictions-dashboard', 'test-device-id');
    
    // Return the promise for proper async testing
    return new Promise(resolve => {
      // Wait for retry mechanism to complete
      setTimeout(() => {
        // Verify fetch was called twice (initial + retry)
        expect(fetch).toHaveBeenCalledTimes(2);
        resolve();
      }, 1500);
    });
  });
});
