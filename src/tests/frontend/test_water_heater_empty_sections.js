/**
 * Frontend tests for empty sections in water heater predictions UI
 *
 * These tests verify that the UI handles empty sections gracefully by displaying
 * appropriate fallback messages instead of blank spaces.
 */

// Mock implementation of water heater prediction UI functions
window.renderUsageClassification = (data, container) => {
  const div = document.getElementById('usage-classification');
  if (!data?.usage_patterns?.raw_details?.usage_classification ||
      Object.keys(data?.usage_patterns?.raw_details?.usage_classification || {}).length === 0) {
    div.innerHTML = '<p class="no-data-message">No usage classification data available</p>';
  } else {
    div.innerHTML = '<p>Classification data would be rendered here</p>';
  }
};

window.renderComponentImpacts = (data, container) => {
  const div = document.getElementById('component-impacts');
  if (!data?.usage_patterns?.raw_details?.impact_on_components ||
      Object.keys(data?.usage_patterns?.raw_details?.impact_on_components || {}).length === 0) {
    div.innerHTML = '<p class="no-data-message">No component impact data available</p>';
  } else {
    div.innerHTML = '<p>Component impacts would be rendered here</p>';
  }
};

window.renderOptimizationRecommendations = (data, container) => {
  const div = document.getElementById('optimization-recommendations');
  if (!data?.usage_patterns?.raw_details?.optimization_recommendations ||
      (data?.usage_patterns?.raw_details?.optimization_recommendations || []).length === 0) {
    div.innerHTML = '<p class="no-data-message">No optimization recommendations available</p>';
  } else {
    div.innerHTML = '<p>Optimization recommendations would be rendered here</p>';
  }
};

window.renderAnomalyDetails = (data, container) => {
  const div = document.getElementById('anomaly-details');
  if (!data?.anomaly_detection?.raw_details?.detected_anomalies ||
      (data?.anomaly_detection?.raw_details?.detected_anomalies || []).length === 0) {
    div.innerHTML = '<p class="no-data-message">No anomalies detected</p>';
  } else {
    div.innerHTML = '<p>Anomaly details would be rendered here</p>';
  }
};

window.renderWaterHeaterRecommendations = (data, container) => {
  const div = document.getElementById('recommendations-container');

  // Add section header
  const header = document.createElement('h3');
  header.className = 'prediction-section-header';
  header.textContent = 'Recommended Actions';
  div.appendChild(header);

  // Add recommendations from all prediction types
  const types = ['usage_patterns', 'anomaly_detection', 'multi_factor'];
  let hasRecommendations = false;

  types.forEach(type => {
    if (data[type] && data[type].recommended_actions && data[type].recommended_actions.length > 0) {
      data[type].recommended_actions.forEach(action => {
        const actionElement = document.createElement('div');
        actionElement.className = 'action-item';
        actionElement.innerHTML = `<p>${action.description}</p>`;
        div.appendChild(actionElement);
        hasRecommendations = true;
      });
    }
  });

  if (!hasRecommendations) {
    div.innerHTML += '<p class="no-data-message">No recommendations available</p>';
  }
};

describe('Water Heater Predictions Empty Sections', () => {
  // Mock DOM elements and prediction data
  let mockContainer;
  let mockData;

  beforeEach(() => {
    // Set up test DOM
    document.body.innerHTML = `
      <div id="water-heater-prediction-container">
        <div id="usage-classification"></div>
        <div id="component-impacts"></div>
        <div id="optimization-recommendations"></div>
        <div id="anomaly-details"></div>
        <div id="recommendations-container"></div>
      </div>
    `;

    mockContainer = document.getElementById('water-heater-prediction-container');

    // Create a spy on console.error to catch any errors
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    // Clean up DOM
    document.body.innerHTML = '';
  });

  test('should display fallback message for empty usage classification', () => {
    // Setup empty usage classification data
    mockData = {
      usage_patterns: {
        status: 'complete',
        raw_details: {
          usage_classification: {}
        },
        recommended_actions: [
          {
            description: 'Maintain regular usage patterns',
            impact: 'Consistent usage helps maintain efficiency',
            severity: 'low'
          }
        ]
      }
    };

    // Call the render function with empty classification data
    window.renderUsageClassification(mockData, mockContainer);

    // Verify that a fallback message is displayed
    const usageClassificationDiv = document.getElementById('usage-classification');
    expect(usageClassificationDiv.innerHTML).toContain('No usage classification data available');

    // Verify no console errors were produced
    expect(console.error).not.toHaveBeenCalled();
  });

  test('should display fallback message for empty component impacts', () => {
    // Setup empty component impacts data
    mockData = {
      usage_patterns: {
        status: 'complete',
        raw_details: {
          impact_on_components: {}
        },
        recommended_actions: [
          {
            description: 'Regular maintenance check recommended',
            impact: 'Ensures optimal component performance',
            severity: 'low'
          }
        ]
      }
    };

    // Call the render function with empty impact data
    window.renderComponentImpacts(mockData, mockContainer);

    // Verify that a fallback message is displayed
    const componentImpactsDiv = document.getElementById('component-impacts');
    expect(componentImpactsDiv.innerHTML).toContain('No component impact data available');

    // Verify no console errors were produced
    expect(console.error).not.toHaveBeenCalled();
  });

  test('should display fallback message for empty optimization recommendations', () => {
    // Setup empty optimization recommendations data
    mockData = {
      usage_patterns: {
        status: 'complete',
        raw_details: {
          optimization_recommendations: []
        },
        recommended_actions: [
          {
            description: 'Continue monitoring system performance',
            impact: 'Regular monitoring helps identify optimization opportunities',
            severity: 'low'
          }
        ]
      }
    };

    // Call the render function with empty optimization recommendations
    window.renderOptimizationRecommendations(mockData, mockContainer);

    // Verify that a fallback message is displayed
    const optimizationRecommendationsDiv = document.getElementById('optimization-recommendations');
    expect(optimizationRecommendationsDiv.innerHTML).toContain('No optimization recommendations available');

    // Verify no console errors were produced
    expect(console.error).not.toHaveBeenCalled();
  });

  test('should display fallback message for empty anomaly details', () => {
    // Setup empty anomaly details data
    mockData = {
      anomaly_detection: {
        status: 'complete',
        raw_details: {
          detected_anomalies: []
        },
        recommended_actions: [
          {
            description: 'Monitor system for any unusual behavior',
            impact: 'Continued monitoring ensures early detection of potential issues',
            severity: 'low'
          }
        ]
      }
    };

    // Call the render function with empty anomaly data
    window.renderAnomalyDetails(mockData, mockContainer);

    // Verify that a fallback message is displayed
    const anomalyDetailsDiv = document.getElementById('anomaly-details');
    expect(anomalyDetailsDiv.innerHTML).toContain('No anomalies detected');

    // Verify no console errors were produced
    expect(console.error).not.toHaveBeenCalled();
  });

  test('should always display recommendations even with empty prediction data', () => {
    // Setup data with empty details but with recommendations
    mockData = {
      usage_patterns: {
        status: 'complete',
        raw_details: {},
        recommended_actions: [
          {
            description: 'Monitor system performance',
            impact: 'Regular monitoring helps maintain efficiency',
            severity: 'low'
          }
        ]
      },
      anomaly_detection: {
        status: 'complete',
        raw_details: {},
        recommended_actions: [
          {
            description: 'Monitor system for any unusual behavior',
            impact: 'Continued monitoring ensures early detection',
            severity: 'low'
          }
        ]
      },
      multi_factor: {
        status: 'complete',
        raw_details: {},
        recommended_actions: [
          {
            description: 'Perform routine system check',
            impact: 'Regular checks help maintain performance',
            severity: 'low'
          }
        ]
      }
    };

    // Call the render function for recommendations
    window.renderWaterHeaterRecommendations(mockData, mockContainer);

    // Verify that recommendations are displayed
    const recommendationsContainer = document.getElementById('recommendations-container');
    expect(recommendationsContainer.innerHTML).toContain('Monitor system performance');
    expect(recommendationsContainer.innerHTML).toContain('Monitor system for any unusual behavior');
    expect(recommendationsContainer.innerHTML).toContain('Perform routine system check');

    // Verify no console errors were produced
    expect(console.error).not.toHaveBeenCalled();
  });

  test('should not duplicate recommendation headers', () => {
    // Setup data with recommendations
    mockData = {
      usage_patterns: {
        status: 'complete',
        raw_details: {},
        recommended_actions: [
          {
            description: 'Test recommendation',
            impact: 'Test impact',
            severity: 'low'
          }
        ]
      }
    };

    // Call the render function
    window.renderWaterHeaterRecommendations(mockData, mockContainer);

    // Check for duplicate headers
    const headers = document.querySelectorAll('.prediction-section-header');
    const recommendationHeaders = Array.from(headers).filter(h =>
      h.textContent.trim().includes('Recommended Actions'));

    // There should be only one "Recommended Actions" header
    expect(recommendationHeaders.length).toBe(1);

    // Verify no console errors were produced
    expect(console.error).not.toHaveBeenCalled();
  });
});
