/**
 * Rheem Water Heater Components
 * Provides Rheem-specific functionality for water heater UI
 */

// Constants for Rheem water heaters
const RHEEM_MODES = {
  ENERGY_SAVER: 'energy_saver',
  HIGH_DEMAND: 'high_demand',
  VACATION: 'vacation',
  HEAT_PUMP: 'heat_pump',
  ELECTRIC: 'electric'
};

// Mapping of backend mode values to user-friendly display names
const RHEEM_MODE_LABELS = {
  energy_saver: 'Energy Saver',
  high_demand: 'High Demand',
  vacation: 'Vacation',
  heat_pump: 'Heat Pump',
  electric: 'Electric'
};

/**
 * Class that extends the base water heater functionality with Rheem-specific features
 */
class RheemWaterHeaterHandler {
  constructor() {
    // Track initialization state
    this.initialized = false;

    // Initialize when the DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      this.init();
    }
  }

  /**
   * Initialize the Rheem handler
   */
  init() {
    if (this.initialized) return;

    // Extend the API client with Rheem-specific methods
    this.extendApiClient();

    // Extend the water heater list component
    this.extendWaterHeaterList();

    // Extend the water heater detail component
    this.extendWaterHeaterDetail();

    this.initialized = true;
    console.log('Rheem water heater handler initialized');
  }

  /**
   * Extend the API client with Rheem-specific methods
   */
  extendApiClient() {
    if (!window.api) {
      console.error('API client not found');
      return;
    }

    // Add Rheem-specific API methods
    window.api.getRheemWaterHeaters = async () => {
      try {
        return await fetch('/api/rheem-water-heaters', {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error('Failed to fetch Rheem water heaters:', error);
        throw error;
      }
    };

    window.api.getRheemWaterHeater = async (id) => {
      try {
        return await fetch(`/api/rheem-water-heaters/${id}`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to fetch Rheem water heater ${id}:`, error);
        throw error;
      }
    };

    window.api.getEcoNetStatus = async (id) => {
      try {
        return await fetch(`/api/rheem-water-heaters/${id}/eco-net-status`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to fetch EcoNet status for heater ${id}:`, error);
        throw error;
      }
    };

    window.api.updateEcoNetStatus = async (id, status) => {
      try {
        return await fetch(`/api/rheem-water-heaters/${id}/eco-net-status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ enabled: status })
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to update EcoNet status for heater ${id}:`, error);
        throw error;
      }
    };

    window.api.setRheemWaterHeaterMode = async (id, mode) => {
      try {
        return await fetch(`/api/rheem-water-heaters/${id}/mode`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ mode: mode })
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to set mode for Rheem heater ${id}:`, error);
        throw error;
      }
    };

    window.api.getMaintenancePrediction = async (id) => {
      try {
        return await fetch(`/api/rheem-water-heaters/${id}/maintenance-prediction`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to fetch maintenance prediction for heater ${id}:`, error);
        throw error;
      }
    };

    window.api.getEfficiencyAnalysis = async (id) => {
      try {
        return await fetch(`/api/rheem-water-heaters/${id}/efficiency-analysis`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to fetch efficiency analysis for heater ${id}:`, error);
        throw error;
      }
    };
  }

  /**
   * Extend the water heater list component with Rheem-specific UI elements
   */
  extendWaterHeaterList() {
    if (!window.WaterHeaterList) {
      console.error('WaterHeaterList component not found');
      return;
    }

    // Store the original renderHeater method
    const originalRenderHeater = window.WaterHeaterList.prototype.renderHeater;

    // Override the renderHeater method to add Rheem-specific UI elements
    window.WaterHeaterList.prototype.renderHeater = function(heater) {
      // Call the original method to get the base HTML
      const baseHtml = originalRenderHeater.call(this, heater);

      // If this is not a Rheem heater, return the base HTML unchanged
      if (!heater.manufacturer || heater.manufacturer.toLowerCase() !== 'rheem') {
        return baseHtml;
      }

      // Create a DOM parser to modify the base HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(baseHtml, 'text/html');
      const card = doc.querySelector('.heater-card');

      // Add Rheem-specific classes and elements
      card.classList.add('rheem-heater');

      // Add Rheem badge
      const badge = document.createElement('div');
      badge.className = 'rheem-badge';
      badge.textContent = 'Rheem';
      card.appendChild(badge);

      // Add manufacturer info
      const info = document.createElement('div');
      info.className = 'manufacturer';
      info.textContent = 'Rheem';

      // Find the title element and insert the manufacturer info after it
      const title = card.querySelector('.card-title');
      if (title) {
        title.parentNode.insertBefore(info, title.nextSibling);
      } else {
        card.appendChild(info);
      }

      // Return the modified HTML
      return card.outerHTML;
    };
  }

  /**
   * Extend the water heater detail component with Rheem-specific UI elements
   */
  extendWaterHeaterDetail() {
    if (!window.WaterHeaterDetail) {
      console.error('WaterHeaterDetail component not found');
      return;
    }

    // Store the original render method
    const originalRender = window.WaterHeaterDetail.prototype.render;

    // Override the render method to add Rheem-specific UI elements
    window.WaterHeaterDetail.prototype.render = function() {
      // Call the original method first
      originalRender.call(this);

      // If this is not a Rheem heater, don't add Rheem-specific elements
      if (!this.heater.manufacturer || this.heater.manufacturer.toLowerCase() !== 'rheem') {
        return;
      }

      // Add Rheem-specific class to the container
      this.container.classList.add('rheem-detail');

      // Get the details tab content
      const detailsContent = document.getElementById('details-content');
      if (!detailsContent) {
        console.error('Details content element not found');
        return;
      }

      // Add Rheem-specific details section
      const rheemDetails = document.createElement('div');
      rheemDetails.className = 'rheem-details section';
      rheemDetails.innerHTML = `
        <h3>Rheem Features</h3>
        <div class="row">
          <div class="col">
            <div class="data-item">
              <span class="label">Series:</span>
              <span class="value">${this.heater.series || 'N/A'}</span>
            </div>
            <div class="data-item">
              <span class="label">EcoNet Enabled:</span>
              <span class="eco-net-status value">${this.heater.eco_net_enabled ? 'Yes' : 'No'}</span>
            </div>
          </div>
          <div class="col">
            <div class="data-item">
              <span class="label">Energy Star:</span>
              <span class="value">${this.heater.energy_star_certified ? 'Certified' : 'Not Certified'}</span>
            </div>
            <div class="data-item">
              <span class="label">UEF Rating:</span>
              <span class="value">${this.heater.uef_rating || 'N/A'}</span>
            </div>
          </div>
        </div>
        <div class="eco-net-controls">
          <label for="eco-net-toggle">EcoNet Connection:</label>
          <div class="toggle-switch">
            <input type="checkbox" id="eco-net-toggle" ${this.heater.eco_net_enabled ? 'checked' : ''}>
            <span class="slider round"></span>
          </div>
          <span class="status-text">${this.heater.eco_net_enabled ? 'Connected' : 'Disconnected'}</span>
        </div>
      `;

      // Insert the Rheem details after the basic details
      const detailsSection = detailsContent.querySelector('.detail-view');
      if (detailsSection) {
        detailsSection.appendChild(rheemDetails);
      } else {
        detailsContent.appendChild(rheemDetails);
      }

      // Set up EcoNet toggle functionality
      const ecoNetToggle = document.getElementById('eco-net-toggle');
      if (ecoNetToggle) {
        ecoNetToggle.addEventListener('change', async (event) => {
          try {
            const status = event.target.checked;
            const result = await window.api.updateEcoNetStatus(this.heaterId, status);

            // Update the status text
            const statusText = ecoNetToggle.parentNode.nextElementSibling;
            if (statusText) {
              statusText.textContent = status ? 'Connected' : 'Disconnected';
            }

            console.log('EcoNet status updated:', result);
          } catch (error) {
            console.error('Failed to update EcoNet status:', error);
            // Reset the toggle to its previous state
            event.target.checked = !event.target.checked;
          }
        });
      }

      // Add Rheem mode selector to operations tab
      this.addRheemModeSelector();

      // Add Rheem-specific prediction elements
      this.addRheemPredictionElements();
    };

    // Add a method to create the Rheem mode selector
    window.WaterHeaterDetail.prototype.addRheemModeSelector = function() {
      // Get the operations content element
      const operationsContent = document.getElementById('operations-content');
      if (!operationsContent) {
        console.error('Operations content element not found');
        return;
      }

      // Create the mode selector element
      const modeSelector = document.createElement('div');
      modeSelector.className = 'rheem-mode-control control-panel';

      // Determine which modes to show based on water heater type
      let modeOptions = '';

      // All heaters support these basic modes
      modeOptions += `
        <option value="${RHEEM_MODES.ENERGY_SAVER}">${RHEEM_MODE_LABELS[RHEEM_MODES.ENERGY_SAVER]}</option>
        <option value="${RHEEM_MODES.HIGH_DEMAND}">${RHEEM_MODE_LABELS[RHEEM_MODES.HIGH_DEMAND]}</option>
        <option value="${RHEEM_MODES.VACATION}">${RHEEM_MODE_LABELS[RHEEM_MODES.VACATION]}</option>
      `;

      // Hybrid heaters have additional modes
      if (this.heater.type === 'hybrid') {
        modeOptions += `
          <option value="${RHEEM_MODES.HEAT_PUMP}">${RHEEM_MODE_LABELS[RHEEM_MODES.HEAT_PUMP]}</option>
          <option value="${RHEEM_MODES.ELECTRIC}">${RHEEM_MODE_LABELS[RHEEM_MODES.ELECTRIC]}</option>
        `;
      }

      // Set up the HTML for the mode selector
      modeSelector.innerHTML = `
        <h3>Rheem Operation Mode</h3>
        <div class="control-row">
          <label for="rheem-mode-selector">Select Mode:</label>
          <select id="rheem-mode-selector">
            ${modeOptions}
          </select>
          <button id="set-rheem-mode" class="btn btn-primary">Apply</button>
        </div>
        <div class="description">
          <p id="mode-description">Energy Saver mode optimizes energy usage while maintaining comfort.</p>
        </div>
      `;

      // Add the mode selector to the operations content
      operationsContent.appendChild(modeSelector);

      // Set up event listeners for the mode selector
      const modeSelectorElement = document.getElementById('rheem-mode-selector');
      const setModeButton = document.getElementById('set-rheem-mode');
      const modeDescription = document.getElementById('mode-description');

      if (modeSelectorElement && setModeButton) {
        // Update description when mode is changed
        modeSelectorElement.addEventListener('change', (event) => {
          const selectedMode = event.target.value;
          switch (selectedMode) {
            case RHEEM_MODES.ENERGY_SAVER:
              modeDescription.textContent = 'Energy Saver mode optimizes energy usage while maintaining comfort.';
              break;
            case RHEEM_MODES.HIGH_DEMAND:
              modeDescription.textContent = 'High Demand mode provides maximum hot water output for periods of high usage.';
              break;
            case RHEEM_MODES.VACATION:
              modeDescription.textContent = 'Vacation mode reduces energy consumption while you are away.';
              break;
            case RHEEM_MODES.HEAT_PUMP:
              modeDescription.textContent = 'Heat Pump mode uses the heat pump exclusively for maximum efficiency.';
              break;
            case RHEEM_MODES.ELECTRIC:
              modeDescription.textContent = 'Electric mode uses traditional electric heating elements for fastest recovery.';
              break;
            default:
              modeDescription.textContent = '';
          }
        });

        // Handle mode setting
        setModeButton.addEventListener('click', async () => {
          try {
            const selectedMode = modeSelectorElement.value;
            await window.api.setRheemWaterHeaterMode(this.heaterId, selectedMode);

            // Show success message
            alert(`Mode set to ${RHEEM_MODE_LABELS[selectedMode]}`);
          } catch (error) {
            console.error('Failed to set mode:', error);
            alert('Failed to set mode. Please try again.');
          }
        });
      }
    };

    // Add a method to create Rheem-specific prediction elements
    window.WaterHeaterDetail.prototype.addRheemPredictionElements = function() {
      // Get the predictions content element
      const predictionsContent = document.getElementById('predictions-content');
      if (!predictionsContent) {
        console.error('Predictions content element not found');
        return;
      }

      // Create the Rheem maintenance prediction element
      const maintenancePrediction = document.createElement('div');
      maintenancePrediction.className = 'rheem-maintenance-prediction prediction-container';
      maintenancePrediction.innerHTML = `
        <div class="prediction-header">
          <h3>Rheem Maintenance Prediction</h3>
          <div class="prediction-controls">
            <button id="refresh-rheem-maintenance" class="btn btn-sm btn-primary">
              <i class="fas fa-sync-alt"></i> Refresh
            </button>
          </div>
        </div>
        <div class="prediction-content">
          <div class="loading">Loading prediction data...</div>
        </div>
      `;

      // Create the Rheem efficiency analysis element
      const efficiencyAnalysis = document.createElement('div');
      efficiencyAnalysis.className = 'rheem-efficiency-analysis prediction-container';
      efficiencyAnalysis.innerHTML = `
        <div class="prediction-header">
          <h3>Rheem Efficiency Analysis</h3>
          <div class="prediction-controls">
            <button id="refresh-rheem-efficiency" class="btn btn-sm btn-primary">
              <i class="fas fa-sync-alt"></i> Refresh
            </button>
          </div>
        </div>
        <div class="prediction-content">
          <div class="loading">Loading efficiency data...</div>
        </div>
      `;

      // Add the elements to the predictions dashboard
      const predictionsDashboard = predictionsContent.querySelector('#water-heater-predictions-dashboard');
      if (predictionsDashboard) {
        predictionsDashboard.appendChild(maintenancePrediction);
        predictionsDashboard.appendChild(efficiencyAnalysis);
      }

      // Load the initial prediction data
      this.loadMaintenancePrediction();
      this.loadEfficiencyAnalysis();

      // Set up event listeners for refresh buttons
      const refreshMaintenanceButton = document.getElementById('refresh-rheem-maintenance');
      if (refreshMaintenanceButton) {
        refreshMaintenanceButton.addEventListener('click', () => this.loadMaintenancePrediction());
      }

      const refreshEfficiencyButton = document.getElementById('refresh-rheem-efficiency');
      if (refreshEfficiencyButton) {
        refreshEfficiencyButton.addEventListener('click', () => this.loadEfficiencyAnalysis());
      }
    };

    // Add methods to load prediction data
    window.WaterHeaterDetail.prototype.loadMaintenancePrediction = async function() {
      try {
        const predictionElement = document.querySelector('.rheem-maintenance-prediction .prediction-content');
        if (!predictionElement) return;

        // Show loading state
        predictionElement.innerHTML = '<div class="loading">Loading prediction data...</div>';

        // Fetch the maintenance prediction data
        const prediction = await window.api.getMaintenancePrediction(this.heaterId);

        // Format the prediction data
        const nextMaintenanceDate = new Date(prediction.next_maintenance_date);
        const daysUntil = Math.ceil((nextMaintenanceDate - new Date()) / (1000 * 60 * 60 * 24));

        // Update the UI with the prediction data
        predictionElement.innerHTML = `
          <div class="prediction-result">
            <div class="prediction-summary">
              <div class="prediction-value">${daysUntil} days</div>
              <div class="prediction-label">until next maintenance</div>
            </div>
            <div class="prediction-details">
              <div class="detail-item">
                <span class="label">Next Maintenance:</span>
                <span class="value">${nextMaintenanceDate.toLocaleDateString()}</span>
              </div>
              <div class="detail-item">
                <span class="label">Confidence:</span>
                <span class="value">${(prediction.confidence * 100).toFixed(1)}%</span>
              </div>
              <div class="detail-item">
                <span class="label">Recommended Action:</span>
                <span class="value">${prediction.recommended_action}</span>
              </div>
            </div>
          </div>
        `;
      } catch (error) {
        console.error('Failed to load maintenance prediction:', error);
        const predictionElement = document.querySelector('.rheem-maintenance-prediction .prediction-content');
        if (predictionElement) {
          predictionElement.innerHTML = `
            <div class="error-message">
              Failed to load maintenance prediction data. Please try again.
            </div>
          `;
        }
      }
    };

    window.WaterHeaterDetail.prototype.loadEfficiencyAnalysis = async function() {
      try {
        const analysisElement = document.querySelector('.rheem-efficiency-analysis .prediction-content');
        if (!analysisElement) return;

        // Show loading state
        analysisElement.innerHTML = '<div class="loading">Loading efficiency data...</div>';

        // Fetch the efficiency analysis data
        const analysis = await window.api.getEfficiencyAnalysis(this.heaterId);

        // Calculate savings percentage
        const savingsPercentage = ((analysis.potential_savings / analysis.current_cost) * 100).toFixed(1);

        // Update the UI with the analysis data
        analysisElement.innerHTML = `
          <div class="prediction-result">
            <div class="prediction-summary">
              <div class="prediction-value">$${analysis.potential_savings.toFixed(2)}</div>
              <div class="prediction-label">potential monthly savings</div>
            </div>
            <div class="prediction-details">
              <div class="detail-item">
                <span class="label">Current Efficiency:</span>
                <span class="value">${(analysis.current_efficiency * 100).toFixed(1)}%</span>
              </div>
              <div class="detail-item">
                <span class="label">Target Efficiency:</span>
                <span class="value">${(analysis.target_efficiency * 100).toFixed(1)}%</span>
              </div>
              <div class="detail-item">
                <span class="label">Current Cost:</span>
                <span class="value">$${analysis.current_cost.toFixed(2)}/month</span>
              </div>
              <div class="detail-item">
                <span class="label">Potential Cost:</span>
                <span class="value">$${(analysis.current_cost - analysis.potential_savings).toFixed(2)}/month</span>
              </div>
              <div class="detail-item">
                <span class="label">Savings:</span>
                <span class="value">${savingsPercentage}%</span>
              </div>
            </div>
            <div class="recommendation">
              <h4>Recommendations:</h4>
              <ul>
                ${analysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
              </ul>
            </div>
          </div>
        `;
      } catch (error) {
        console.error('Failed to load efficiency analysis:', error);
        const analysisElement = document.querySelector('.rheem-efficiency-analysis .prediction-content');
        if (analysisElement) {
          analysisElement.innerHTML = `
            <div class="error-message">
              Failed to load efficiency analysis data. Please try again.
            </div>
          `;
        }
      }
    };
  }
}

// Initialize the Rheem handler
const rheemHandler = new RheemWaterHeaterHandler();

// Export for use in other modules
window.rheemHandler = rheemHandler;
