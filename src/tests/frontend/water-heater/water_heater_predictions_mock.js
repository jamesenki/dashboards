/**
 * Mock for the WaterHeaterPredictionsDashboard class
 * This allows us to test the dashboard functionality without loading the entire DOM
 */

// Import actual class implementation from the frontend
window.WaterHeaterPredictionsDashboard = class WaterHeaterPredictionsDashboard {
  constructor(containerId, deviceId) {
    this.container = document.getElementById(containerId);
    this.deviceId = deviceId;
    
    // Fetch status for each prediction type
    this.fetchingLifespan = false;
    this.fetchingAnomaly = false;
    this.fetchingUsage = false;
    this.fetchingMultiFactor = false;
    
    // Rendering state items for all prediction types
    this.lifespanPrediction = null;
    this.anomalyDetection = null;
    this.usagePatterns = null;
    this.multiFactor = null;
    
    // Data loaded flags - set to false initially
    this.dataInitialized = false;
    
    // Set up a proper load sequence with retries
    console.log(`Initializing water heater predictions dashboard for device: ${this.deviceId}`);
    
    // Start data loading immediately
    this.initializeData();
  }
  
  initializeData() {
    console.log('Starting data initialization sequence');
    this.fetchPredictionData();
    
    // Set up a retry mechanism in case the first load fails
    setTimeout(() => {
      if (!this.dataInitialized) {
        console.warn('Data not initialized after first attempt, retrying...');
        this.fetchPredictionData();
      }
    }, 1000);
  }
  
  fetchPredictionData() {
    console.log('Fetching all prediction data for device ID:', this.deviceId);
    
    // Generate a common timestamp for all requests
    const timestamp = new Date().getTime();
    
    // Use the all-predictions endpoint to get all predictions at once
    return fetch(`/api/predictions/water-heaters/${this.deviceId}/all?_t=${timestamp}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Predictions failed: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('All predictions loaded successfully');
        
        // Mark data as initialized so we don't reload unnecessarily
        this.dataInitialized = true;
        
        // Store prediction data
        if (data.lifespan_estimation) this.lifespanPrediction = data.lifespan_estimation;
        if (data.anomaly_detection) this.anomalyDetection = data.anomaly_detection;
        if (data.usage_patterns) this.usagePatterns = data.usage_patterns;
        if (data.multi_factor) this.multiFactor = data.multi_factor;
        
        return data;
      })
      .catch(error => {
        console.error('Error loading all predictions:', error);
        return null;
      });
  }
};
