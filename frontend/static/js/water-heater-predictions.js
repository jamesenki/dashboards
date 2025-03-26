/**
 * Water Heater Predictions Dashboard
 * Handles the display and interaction with water heater lifespan predictions
 */
class WaterHeaterPredictionsDashboard {
  constructor(containerId, deviceId) {
    this.container = document.getElementById(containerId);
    this.deviceId = deviceId;
    this.fetchingData = false;
    
    // Rendering state items
    this.lifespanPrediction = null;
    
    // Initialize the predictions dashboard
    this.renderTemplate();
    this.bindEventListeners();
    this.fetchPredictionData();
  }
  
  /**
   * Initialize the dashboard by finding DOM elements
   * (No template loading needed as we've embedded the template in the HTML)
   */
  renderTemplate() {
    // Cache DOM elements
    this.loadingElement = document.getElementById('lifespan-loading');
    this.errorElement = document.getElementById('lifespan-error');
    this.errorMessageElement = document.getElementById('lifespan-error-message');
    this.predictionCardElement = document.getElementById('lifespan-prediction-card');
    
    // Initialize data views if we already have data
    if (this.lifespanPrediction) {
      this.renderPredictionData();
    }
  }
  
  /**
   * Bind event listeners for the dashboard
   */
  bindEventListeners() {
    // Use event delegation since the elements may not exist yet
    document.addEventListener('click', event => {
      // Handle refresh button click
      if (event.target.closest('#refresh-lifespan-prediction')) {
        this.fetchPredictionData();
      }
    });
  }
  
  /**
   * Fetch the lifespan prediction data from the API
   */
  fetchPredictionData() {
    if (this.fetchingData) return;
    
    this.fetchingData = true;
    this.showLoading();
    
    const timestamp = new Date().getTime();
    const endpoint = `/api/predictions/water-heaters/${this.deviceId}/lifespan-estimation?_t=${timestamp}`;
    
    // Use the application's existing API client pattern
    fetch(endpoint)
      .then(response => {
        if (!response.ok) {
          if (response.status === 404) {
            // Special handling for 404s - water heater may have been regenerated
            throw new Error('Water heater not found. The server may have been restarted.');
          } else {
            throw new Error(`Request failed with status: ${response.status}`);
          }
        }
        return response.json();
      })
      .then(response => {
        this.lifespanPrediction = response;
        this.renderPredictionData();
      })
      .catch(error => {
        console.error('Error fetching lifespan prediction:', error);
        
        // If it's a 404 error (water heater not found), offer to redirect to the water heaters list
        if (error.message && error.message.includes('Water heater not found')) {
          this.showError(`${error.message} <br><br><a href="/water-heaters" class="btn btn-primary">View Available Water Heaters</a>`);
        } else {
          this.showError(error.message || 'Failed to retrieve lifespan prediction data');
        }
      })
      .finally(() => {
        this.fetchingData = false;
      });
  }
  
  /**
   * Display loading state
   */
  showLoading() {
    if (this.loadingElement) {
      this.loadingElement.style.display = 'block';
    }
    
    if (this.errorElement) {
      this.errorElement.style.display = 'none';
    }
    
    if (this.predictionCardElement) {
      this.predictionCardElement.style.display = 'none';
    }
  }
  
  /**
   * Display error state
   */
  showError(message) {
    if (this.loadingElement) {
      this.loadingElement.style.display = 'none';
    }
    
    if (this.errorElement) {
      this.errorElement.style.display = 'block';
      // Use innerHTML instead of textContent to support HTML content
      this.errorMessageElement.innerHTML = message;
    }
    
    if (this.predictionCardElement) {
      this.predictionCardElement.style.display = 'none';
    }
  }
  
  /**
   * Render the prediction data in the UI
   */
  renderPredictionData() {
    if (!this.loadingElement || !this.predictionCardElement) return;
    
    // Hide loading and error states
    this.loadingElement.style.display = 'none';
    this.errorElement.style.display = 'none';
    
    // Show prediction card
    this.predictionCardElement.style.display = 'block';
    
    // Extract data from the prediction
    const predictedValue = this.lifespanPrediction.predicted_value;
    const confidence = this.lifespanPrediction.confidence;
    const rawDetails = this.lifespanPrediction.raw_details || {};
    const actions = this.lifespanPrediction.recommended_actions || [];
    
    // Update lifespan gauge and percentage
    const gauge = document.getElementById('lifespan-gauge');
    const percentage = document.getElementById('lifespan-percentage');
    
    if (gauge) {
      gauge.style.setProperty('--percentage', `${predictedValue * 100}%`);
      
      // Set gauge color based on remaining lifespan
      if (predictedValue >= 0.7) {
        gauge.style.background = `conic-gradient(#10b981 ${predictedValue * 100}%, #2d3748 0%)`; // Green
      } else if (predictedValue >= 0.3) {
        gauge.style.background = `conic-gradient(#f59e0b ${predictedValue * 100}%, #2d3748 0%)`; // Yellow/Orange
      } else {
        gauge.style.background = `conic-gradient(#ef4444 ${predictedValue * 100}%, #2d3748 0%)`; // Red
      }
    }
    
    if (percentage) {
      percentage.textContent = `${Math.round(predictedValue * 100)}%`;
    }
    
    // Update lifespan summary text
    const summary = document.getElementById('lifespan-summary');
    if (summary) {
      if (predictedValue >= 0.7) {
        summary.textContent = 'Your water heater is in good condition with significant remaining lifespan.';
      } else if (predictedValue >= 0.3) {
        summary.textContent = 'Your water heater is showing moderate wear. Consider scheduling maintenance.';
      } else if (predictedValue >= 0.05) {
        summary.textContent = 'Your water heater is nearing the end of its useful life. Plan for replacement soon.';
      } else {
        summary.textContent = 'Your water heater has reached the end of its expected lifespan. Immediate replacement recommended.';
      }
    }
    
    // Update details
    document.getElementById('current-age').textContent = rawDetails.current_age_years ? 
      `${rawDetails.current_age_years} years` : 'Unknown';
      
    document.getElementById('total-lifespan').textContent = rawDetails.total_expected_lifespan_years ? 
      `${rawDetails.total_expected_lifespan_years} years` : 'Unknown';
      
    document.getElementById('remaining-years').textContent = rawDetails.estimated_remaining_years ?
      `${rawDetails.estimated_remaining_years} years` : 'Unknown';
      
    document.getElementById('prediction-confidence').textContent = 
      `${Math.round(confidence * 100)}%`;
      
    // Update contributing factors
    const factorsList = document.getElementById('contributing-factors-list');
    if (factorsList) {
      factorsList.innerHTML = '';
      
      if (rawDetails.contributing_factors && rawDetails.contributing_factors.length > 0) {
        rawDetails.contributing_factors.forEach(factor => {
          const li = document.createElement('li');
          li.textContent = factor;
          factorsList.appendChild(li);
        });
      } else {
        const li = document.createElement('li');
        li.textContent = 'No specific factors provided';
        factorsList.appendChild(li);
      }
    }
    
    // Update recommended actions
    const actionsContainer = document.getElementById('lifespan-actions-list');
    if (actionsContainer) {
      actionsContainer.innerHTML = '';
      
      if (actions && actions.length > 0) {
        actions.forEach(action => {
          const actionItem = document.createElement('div');
          actionItem.className = 'action-item';
          
          // Format the due date if present
          let dueDateFormatted = 'Not specified';
          let isDueSoon = false;
          let isUrgent = false;
          
          if (action.due_date) {
            const dueDate = new Date(action.due_date);
            const now = new Date();
            const daysDiff = Math.ceil((dueDate - now) / (1000 * 60 * 60 * 24));
            
            dueDateFormatted = dueDate.toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'short', 
              day: 'numeric' 
            });
            
            isDueSoon = daysDiff <= 30;
            isUrgent = daysDiff <= 7;
          }
          
          const dueDateClass = isUrgent ? 'due-urgent' : (isDueSoon ? 'due-soon' : '');
          
          // Create action item HTML
          actionItem.innerHTML = `
            <div class="action-header">
              <div class="action-title">${action.description}</div>
              <div class="action-severity severity-${action.severity.toLowerCase()}">${action.severity}</div>
            </div>
            <div class="action-description">${action.impact}</div>
            <div class="action-meta">
              <div class="action-meta-item">
                <span class="meta-label">Benefit</span>
                <span class="meta-value">${action.expected_benefit}</span>
              </div>
              <div class="action-meta-item">
                <span class="meta-label">Due Date</span>
                <span class="meta-value due-date ${dueDateClass}">${dueDateFormatted}</span>
              </div>
            </div>
          `;
          
          actionsContainer.appendChild(actionItem);
        });
      } else {
        actionsContainer.innerHTML = '<p>No specific actions recommended at this time.</p>';
      }
    }
  }
}

// Add to window for global access
window.WaterHeaterPredictionsDashboard = WaterHeaterPredictionsDashboard;
