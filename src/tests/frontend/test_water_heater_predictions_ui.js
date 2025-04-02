/**
 * Frontend UI tests for the water heater predictions dashboard
 *
 * These tests verify that the UI components correctly handle various data scenarios,
 * including empty sections, missing data, and proper formatting of recommended actions.
 */

describe('Water Heater Predictions UI Tests', function() {
  // Mock DOM elements
  let predictionsUI;

  beforeEach(function() {
    // Set up test DOM
    document.body.innerHTML = `
      <div id="anomaly-detection-card"></div>
      <div id="anomaly-loading"></div>
      <div id="anomaly-error"></div>
      <div id="anomaly-summary"></div>
      <div id="anomaly-recommendations"></div>

      <div id="usage-patterns-card"></div>
      <div id="usage-loading"></div>
      <div id="usage-error"></div>
      <div id="usage-summary"></div>
      <div id="usage-classification"></div>
      <div id="component-impacts-list"></div>
      <div id="optimization-recommendations-list"></div>
      <div id="usage-recommendations"></div>

      <div id="multi-factor-card"></div>
      <div id="multi-factor-loading"></div>
      <div id="multi-factor-error"></div>
      <div id="multi-factor-score"></div>
      <div id="multi-factor-gauge"></div>
      <div id="multi-factor-summary"></div>
      <div id="combined-factors-list"></div>
      <div id="environmental-impact-text"></div>
      <div id="component-interactions-list"></div>
      <div id="overall-evaluation-text"></div>
      <div id="multi-factor-recommendations"></div>

      <div id="lifespan-prediction-card"></div>
      <div id="lifespan-loading"></div>
      <div id="lifespan-error"></div>
      <div id="lifespan-gauge"></div>
      <div id="lifespan-percentage"></div>
      <div id="lifespan-summary"></div>
      <div id="lifespan-actions-list"></div>
    `;

    // Create a new instance of the UI controller
    predictionsUI = new WaterHeaterPredictionsDashboard('device-123');

    // Mock the fetch API
    global.fetch = jest.fn();
  });

  afterEach(function() {
    jest.resetAllMocks();
  });

  /**
   * Test handling of empty or missing data in the Usage Pattern component
   */
  test('Usage Pattern UI handles empty or missing data sections', function() {
    // Mock usage pattern data with empty component impacts and optimization recommendations
    const emptyUsageData = {
      device_id: 'device-123',
      prediction_type: 'usage_pattern',
      confidence: 0.85,
      predicted_value: 0.7,
      recommended_actions: [],
      raw_details: {
        usage_classification: 'normal',
        impact_on_components: {},
        optimization_recommendations: []
      }
    };

    // Set the data and render
    predictionsUI.usagePatterns = emptyUsageData;
    predictionsUI.usageCardElement = document.getElementById('usage-patterns-card');
    predictionsUI.renderUsagePatterns();

    // Verify component impacts shows no-data message
    const impactsList = document.getElementById('component-impacts-list');
    expect(impactsList.innerHTML).toContain('No significant component impacts');

    // Verify optimization recommendations shows no-data message
    const optimizationsList = document.getElementById('optimization-recommendations-list');
    expect(optimizationsList.innerHTML).toContain('No optimization recommendations needed');

    // Verify recommendations section shows no-data message
    const recommendationsList = document.getElementById('usage-recommendations');
    expect(recommendationsList.innerHTML).toContain('No specific actions recommended');
  });

  /**
   * Test that all recommendation sections display correctly with both data and no data
   */
  test('Recommendation sections display correctly across all prediction types', function() {
    // Test with empty recommendations
    const testNoRecommendations = function(containerId, predictionType, data) {
      const container = document.getElementById(containerId);
      predictionsUI.renderRecommendedActions(predictionType, [], container);
      expect(container.innerHTML).toBe('');
    };

    // Test with recommendations
    const testWithRecommendations = function(containerId, predictionType, recommendations) {
      const container = document.getElementById(containerId);
      predictionsUI.renderRecommendedActions(predictionType, recommendations, container);
      expect(container.children.length).toBeGreaterThan(0);
      expect(container.innerHTML).toContain(recommendations[0].description);
    };

    // Sample recommendation
    const sampleRecommendation = {
      action_id: 'test-action-123',
      description: 'Test Recommendation',
      impact: 'This is a test impact description',
      severity: 'LOW',
      expected_benefit: 'Test benefit',
      due_date: new Date(2025, 3, 15),
      estimated_cost: 50.00,
      estimated_duration: '1 hour'
    };

    // Test all recommendation containers
    testNoRecommendations('anomaly-recommendations', 'anomaly', []);
    testNoRecommendations('usage-recommendations', 'usage', []);
    testNoRecommendations('multi-factor-recommendations', 'multi-factor', []);
    testNoRecommendations('lifespan-actions-list', 'lifespan', []);

    testWithRecommendations('anomaly-recommendations', 'anomaly', [sampleRecommendation]);
    testWithRecommendations('usage-recommendations', 'usage', [sampleRecommendation]);
    testWithRecommendations('multi-factor-recommendations', 'multi-factor', [sampleRecommendation]);
    testWithRecommendations('lifespan-actions-list', 'lifespan', [sampleRecommendation]);
  });

  /**
   * Test handling of null or undefined values in recommendations
   */
  test('Recommendation rendering handles null or undefined values', function() {
    // Sample recommendation with missing values
    const incompleteRecommendation = {
      action_id: 'incomplete-action',
      description: null,
      impact: undefined,
      severity: null,
      expected_benefit: '',
      due_date: null,
      estimated_cost: null,
      estimated_duration: undefined
    };

    // Render the incomplete recommendation
    const container = document.getElementById('anomaly-recommendations');
    predictionsUI.renderRecommendedActions('anomaly', [incompleteRecommendation], container);

    // Verify fallback values are displayed
    expect(container.innerHTML).toContain('No description available');
    expect(container.innerHTML).toContain('No impact description available');
    expect(container.innerHTML).toContain('Not specified');
  });
});
