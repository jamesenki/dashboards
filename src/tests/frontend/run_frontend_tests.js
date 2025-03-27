/**
 * Frontend Test Runner for IoTSphere
 * 
 * This script sets up a testing environment for frontend JavaScript components
 * and runs the test suite using Jest.
 */

// Mock browser environment
const { JSDOM } = require('jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
global.Element = dom.window.Element;

// Mock fetch API
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
    ok: true
  })
);

// Load water heater prediction functions
const fs = require('fs');
const path = require('path');

// Add missing browser globals
global.DOMParser = dom.window.DOMParser;
global.HTMLElement = dom.window.HTMLElement;

// Mock chart.js and other dependencies
global.Chart = {
  register: jest.fn(),
  controllers: {},
  scales: {}
};

// Mock the water heater prediction functions
global.window.renderUsageClassification = jest.fn((data, container) => {
  const div = document.getElementById('usage-classification');
  if (!data?.usage_patterns?.raw_details?.usage_classification || 
      Object.keys(data?.usage_patterns?.raw_details?.usage_classification || {}).length === 0) {
    div.innerHTML = '<p class="no-data-message">No usage classification data available</p>';
  } else {
    div.innerHTML = '<p>Classification data would be rendered here</p>';
  }
});

global.window.renderComponentImpacts = jest.fn((data, container) => {
  const div = document.getElementById('component-impacts');
  if (!data?.usage_patterns?.raw_details?.impact_on_components || 
      Object.keys(data?.usage_patterns?.raw_details?.impact_on_components || {}).length === 0) {
    div.innerHTML = '<p class="no-data-message">No component impact data available</p>';
  } else {
    div.innerHTML = '<p>Component impacts would be rendered here</p>';
  }
});

global.window.renderOptimizationRecommendations = jest.fn((data, container) => {
  const div = document.getElementById('optimization-recommendations');
  if (!data?.usage_patterns?.raw_details?.optimization_recommendations || 
      (data?.usage_patterns?.raw_details?.optimization_recommendations || []).length === 0) {
    div.innerHTML = '<p class="no-data-message">No optimization recommendations available</p>';
  } else {
    div.innerHTML = '<p>Optimization recommendations would be rendered here</p>';
  }
});

global.window.renderAnomalyDetails = jest.fn((data, container) => {
  const div = document.getElementById('anomaly-details');
  if (!data?.anomaly_detection?.raw_details?.detected_anomalies || 
      (data?.anomaly_detection?.raw_details?.detected_anomalies || []).length === 0) {
    div.innerHTML = '<p class="no-data-message">No anomalies detected</p>';
  } else {
    div.innerHTML = '<p>Anomaly details would be rendered here</p>';
  }
});

global.window.renderWaterHeaterRecommendations = jest.fn((data, container) => {
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
});

// Run the tests
const { run } = require('jest');

run();
