/**
 * AquaTherm Water Heater Components
 * Provides AquaTherm-specific functionality for water heater UI
 */

// Constants for AquaTherm water heaters
const AQUATHERM_MODES = {
  ENERGY_SAVER: 'energy_saver',
  HIGH_DEMAND: 'high_demand',
  VACATION: 'vacation',
  HEAT_PUMP: 'heat_pump',
  ELECTRIC: 'electric'
};

// Mapping of backend mode values to user-friendly display names
const AQUATHERM_MODE_LABELS = {
  energy_saver: 'Energy Saver',
  high_demand: 'High Demand',
  vacation: 'Vacation',
  heat_pump: 'Heat Pump',
  electric: 'Electric'
};

/**
 * Class that extends the base water heater functionality with AquaTherm-specific features
 */
class AquaThermWaterHeaterHandler {
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
   * Initialize the AquaTherm handler
   */
  init() {
    if (this.initialized) return;

    // Extend the API client with AquaTherm-specific methods
    this.extendApiClient();

    // Extend the water heater list component
    this.extendWaterHeaterList();

    // Extend the water heater detail component
    this.extendWaterHeaterDetail();

    // Setup direct click handlers after a short delay to ensure DOM is updated
    setTimeout(() => this.setupCardClickHandlers(), 500);

    // Use a MutationObserver instead of setInterval to monitor for DOM changes
    // This is much more efficient than polling every 2 seconds
    this.setupMutationObserver();

    this.initialized = true;
    console.log('AquaTherm water heater handler initialized');
  }

  /**
   * Set up MutationObserver to watch for new AquaTherm cards
   * This replaces the inefficient setInterval approach
   */
  setupMutationObserver() {
    // Create a mutation observer to watch for new cards
    const observer = new MutationObserver((mutations) => {
      // Check if we need to set up click handlers
      let newCardsAdded = false;

      mutations.forEach(mutation => {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          // Check if any added nodes are or contain AquaTherm cards
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              if (node.classList?.contains('aquatherm-heater') ||
                  node.querySelector?.('.aquatherm-heater')) {
                newCardsAdded = true;
              }
            }
          });
        }
      });

      // Only run the handler setup if new cards were added
      if (newCardsAdded) {
        console.log('New AquaTherm cards detected - setting up click handlers');
        this.setupCardClickHandlers();
      }
    });

    // Start observing the document for changes to the DOM
    observer.observe(document.body, { childList: true, subtree: true });
  }

  /**
   * Set up direct click handlers for all AquaTherm cards
   * This ensures card clicks navigate to the detail page
   */
  setupCardClickHandlers() {
    const cards = document.querySelectorAll('.heater-card.aquatherm-heater');
    console.log(`Found ${cards.length} AquaTherm cards to set up click handlers for`);

    cards.forEach(card => {
      // Skip cards that already have click handlers
      if (card.hasAttribute('data-has-click-handler')) return;

      // Get the heater ID
      const heaterId = card.getAttribute('data-id');
      if (!heaterId) return;

      // SIMPLIFIED: Direct navigation handler matching the working implementation for regular cards
      // This removes the problematic event.preventDefault() call that was blocking navigation
      const onclickHandler = `window.location.href='/water-heaters/${heaterId}'; console.log('Navigating to /water-heaters/${heaterId}'); return false;`;

      card.setAttribute('onclick', onclickHandler);

      // Mark card as having a click handler
      card.setAttribute('data-has-click-handler', 'true');

      // Ensure card has pointer cursor
      card.style.cursor = 'pointer';

      console.log(`Added reliable onclick handler to card for heater ${heaterId}`);
    });
  }

  /**
   * Extend the API client with AquaTherm-specific methods
   */
  extendApiClient() {
    if (!window.api) {
      console.error('API client not found');
      return;
    }

    // Add AquaTherm-specific API methods
    window.api.getAquaThermWaterHeaters = async () => {
      try {
        return await fetch('/api/aquatherm-water-heaters', {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error('Failed to fetch AquaTherm water heaters:', error);
        throw error;
      }
    };

    window.api.getAquaThermWaterHeater = async (id) => {
      try {
        return await fetch(`/api/aquatherm-water-heaters/${id}`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }).then(response => {
          if (!response.ok) throw new Error(`API error: ${response.status}`);
          return response.json();
        });
      } catch (error) {
        console.error(`Failed to fetch AquaTherm water heater ${id}:`, error);
        throw error;
      }
    };

    window.api.getEcoNetStatus = async (id) => {
      try {
        return await fetch(`/api/aquatherm-water-heaters/${id}/eco-net-status`, {
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
        return await fetch(`/api/aquatherm-water-heaters/${id}/eco-net-status`, {
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

    window.api.setAquaThermWaterHeaterMode = async (id, mode) => {
      try {
        return await fetch(`/api/aquatherm-water-heaters/${id}/mode`, {
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
        console.error(`Failed to set mode for AquaTherm heater ${id}:`, error);
        throw error;
      }
    };

    window.api.getMaintenancePrediction = async (id) => {
      try {
        return await fetch(`/api/aquatherm-water-heaters/${id}/maintenance-prediction`, {
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
        return await fetch(`/api/aquatherm-water-heaters/${id}/efficiency-analysis`, {
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
   * Extend the water heater list component with AquaTherm-specific UI elements
   */
  extendWaterHeaterList() {
    if (!window.WaterHeaterList) {
      console.error('WaterHeaterList component not found');
      return;
    }

    // Extend the renderHeaterCard method to add AquaTherm-specific UI elements
    const originalRenderHeaterCard = window.WaterHeaterList.prototype.renderHeaterCard;
    // Override the render method to ensure all AquaTherm cards are properly clickable
const originalRender = window.WaterHeaterList.prototype.render;

window.WaterHeaterList.prototype.render = function() {
  // First call the original render method
  originalRender.call(this);

  // Now enhance all AquaTherm cards with proper click handling
  setTimeout(() => {
    const aquathermCards = document.querySelectorAll('.heater-card.aquatherm-heater');
    aquathermCards.forEach(card => {
      const heaterId = card.getAttribute('data-id');
      if (heaterId) {
        // Remove existing click listeners to prevent duplicates
        const newCard = card.cloneNode(true);
        card.parentNode.replaceChild(newCard, card);

        // Add a new click handler that ensures navigation works
        newCard.addEventListener('click', (e) => {
          // Only navigate if not clicking on a button or link
          if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' ||
              e.target.closest('button') || e.target.closest('a')) {
            return;
          }

          // Explicitly navigate to the water heater detail page
          console.log(`Navigating to water heater detail: ${heaterId}`);
          window.location.href = `/water-heaters/${heaterId}`;
        });
      }
    });
  }, 100); // Small timeout to ensure DOM is ready
};

    window.WaterHeaterList.prototype.renderHeaterCard = function(heater) {
      // Check if this is an AquaTherm water heater
      const isAquaTherm = heater.manufacturer && heater.manufacturer.toLowerCase() === 'aquatherm';

      // Add properties if they don't exist
      if (!heater.properties) {
        heater.properties = {
          heater_type: heater.id && heater.id.includes('hybrid') ? 'HYBRID' :
                       heater.id && heater.id.includes('tankless') ? 'TANKLESS' : 'TANK'
        };
      }

      // Call the original method
      const result = originalRenderHeaterCard.call(this, heater);

      if (!isAquaTherm) {
        return result;
      }

      // For AquaTherm heaters, enhance the rendered HTML with proper badges
      const parser = new DOMParser();
      const doc = parser.parseFromString(result, 'text/html');
      const card = doc.querySelector('.heater-card');

      // Ensure card has cursor pointer style for better UX
      if (card) {
        card.style.cursor = 'pointer';
      }

      if (card) {
        // Add the AquaTherm badge with consistent styling
        const badge = document.createElement('div');
        badge.className = 'aquatherm-badge';
        badge.textContent = 'AquaTherm';
        card.appendChild(badge);

        // Add heater type badge for clarity
        const typeBadge = document.createElement('div');
        const heaterType = heater.properties.heater_type || 'STANDARD';

        // Set the appropriate class based on heater type
        const typeClassName = heaterType.toLowerCase() === 'hybrid' ? 'hybrid-type' :
                               heaterType.toLowerCase() === 'tankless' ? 'tankless-type' : 'tank-type';

        typeBadge.className = `heater-type-badge ${typeClassName}`;
        typeBadge.textContent = heaterType;
        card.appendChild(typeBadge);

        // Add hybrid badge if applicable
        if (heater.properties && heater.properties.heater_type === 'HYBRID') {
          const hybridBadge = document.createElement('span');
          hybridBadge.className = 'hybrid-badge';
          hybridBadge.textContent = 'Hybrid';

          const titleEl = card.querySelector('.card-title');
          if (titleEl) {
            titleEl.appendChild(hybridBadge);
          }
        }

        // Return the modified card HTML
        return card.outerHTML;
      }

      return baseHtml;
    };

    // Extend the loadHeaters method to add AquaTherm-specific API calls
    const originalLoadHeaters = window.WaterHeaterList.prototype.loadHeaters;
    window.WaterHeaterList.prototype.loadHeaters = async function() {
      // Call the original method first
      await originalLoadHeaters.call(this);

      // Then try to fetch AquaTherm-specific water heaters
      try {
        if (window.api && window.api.getAquaThermWaterHeaters) {
          const aquaThermHeaters = await window.api.getAquaThermWaterHeaters();

          if (aquaThermHeaters && aquaThermHeaters.length > 0) {
            // Add AquaTherm heaters to the list
            const normalizedAquaThermHeaters = aquaThermHeaters.map(heater => this.normalizeHeaterData(heater));
            this.heaters = [...this.heaters, ...normalizedAquaThermHeaters];
            console.log('Added AquaTherm water heaters:', normalizedAquaThermHeaters.length);
          }
        }
      } catch (error) {
        console.error('Failed to load AquaTherm water heaters:', error);
      }

      // Re-render the list
      this.renderHeaters();
    };
  }

  /**
   * Extend the water heater detail component with AquaTherm-specific UI elements
   */
  extendWaterHeaterDetail() {
    // Find detail view container
    const detailView = document.getElementById('water-heater-detail');
    if (!detailView) return;

    // Watch for navigation events that might load a water heater detail view
    window.addEventListener('hashchange', () => this.setupDetailView());

    // Setup the detail view if we're on a water heater detail page
    this.setupDetailView();
  }

  /**
   * Set up the AquaTherm-specific UI elements in the detail view
   */
  setupDetailView() {
    const hash = window.location.hash.substring(1);
    if (!hash.startsWith('aqua-wh-')) return;

    // Get the detail content area
    const detailContent = document.getElementById('details-content');
    if (!detailContent) return;

    // Create the AquaTherm details section if it doesn't exist
    if (!detailContent.querySelector('.aquatherm-details')) {
      const aquaThermDetails = document.createElement('div');
      aquaThermDetails.className = 'aquatherm-details';
      aquaThermDetails.innerHTML = `
        <h3>AquaTherm Features</h3>
        <div class="row">
          <div class="col">
            <div class="data-item">
              <span class="label">Series:</span>
              <span class="value" id="aquatherm-series">Loading...</span>
            </div>
            <div class="data-item">
              <span class="label">EcoNet Enabled:</span>
              <span class="eco-net-status value" id="eco-net-status">Loading...</span>
            </div>
          </div>
          <div class="col">
            <div class="data-item">
              <span class="label">Energy Star:</span>
              <span class="value" id="energy-star-status">Loading...</span>
            </div>
          </div>
        </div>
        <div class="eco-net-controls">
          <label for="eco-net-toggle">EcoNet Connection:</label>
          <div class="toggle-switch">
            <input type="checkbox" id="eco-net-toggle">
            <span class="slider round"></span>
          </div>
          <span class="status-text" id="eco-net-toggle-status">Loading...</span>
        </div>
      `;

      detailContent.appendChild(aquaThermDetails);

      // Set up the toggle switch event listener
      const ecoNetToggle = document.getElementById('eco-net-toggle');
      if (ecoNetToggle) {
        ecoNetToggle.addEventListener('change', async (e) => {
          const isEnabled = e.target.checked;
          const heaterId = hash;

          try {
            await window.api.updateEcoNetStatus(heaterId, isEnabled);
            document.getElementById('eco-net-toggle-status').textContent = isEnabled ? 'Connected' : 'Disconnected';
            document.getElementById('eco-net-status').textContent = isEnabled ? 'Yes' : 'No';
          } catch (error) {
            console.error('Failed to update EcoNet status:', error);
            // Revert the toggle
            e.target.checked = !isEnabled;
            document.getElementById('eco-net-toggle-status').textContent = !isEnabled ? 'Connected' : 'Disconnected';
          }
        });
      }
    }

    // Setup operations tab content if needed
    const operationsContent = document.getElementById('operations-content');
    if (operationsContent && !operationsContent.querySelector('.aquatherm-mode-control')) {
      const modeControl = document.createElement('div');
      modeControl.className = 'aquatherm-mode-control control-panel';
      modeControl.innerHTML = `
        <h3>AquaTherm Operation Mode</h3>
        <div class="control-row">
          <label for="aquatherm-mode-selector">Select Mode:</label>
          <select id="aquatherm-mode-selector">
            <option value="energy_saver">Energy Saver</option>
            <option value="high_demand">High Demand</option>
            <option value="vacation">Vacation</option>
            <option value="heat_pump">Heat Pump</option>
            <option value="electric">Electric</option>
          </select>
          <button id="set-aquatherm-mode" class="btn btn-primary">Apply</button>
        </div>
        <div class="description">
          <p id="mode-description">Energy Saver mode optimizes energy usage while maintaining comfort.</p>
        </div>
      `;

      operationsContent.appendChild(modeControl);

      // Set up the mode selector and apply button
      const modeSelector = document.getElementById('aquatherm-mode-selector');
      const applyButton = document.getElementById('set-aquatherm-mode');
      const modeDescription = document.getElementById('mode-description');

      // Update the description when the mode is changed
      if (modeSelector) {
        modeSelector.addEventListener('change', (e) => {
          const selectedMode = e.target.value;

          // Update the description based on the selected mode
          switch (selectedMode) {
            case 'energy_saver':
              modeDescription.textContent = 'Energy Saver mode optimizes energy usage while maintaining comfort.';
              break;
            case 'high_demand':
              modeDescription.textContent = 'High Demand mode provides maximum hot water for busy household periods.';
              break;
            case 'vacation':
              modeDescription.textContent = 'Vacation mode minimizes energy usage when you\'re away from home.';
              break;
            case 'heat_pump':
              modeDescription.textContent = 'Heat Pump mode uses the heat pump exclusively for maximum efficiency.';
              break;
            case 'electric':
              modeDescription.textContent = 'Electric mode uses the electric elements exclusively for faster recovery.';
              break;
            default:
              modeDescription.textContent = '';
          }
        });
      }

      // Apply the selected mode when the button is clicked
      if (applyButton) {
        applyButton.addEventListener('click', async () => {
          const selectedMode = modeSelector.value;
          const heaterId = hash;

          try {
            applyButton.disabled = true;
            applyButton.textContent = 'Applying...';

            await window.api.setAquaThermWaterHeaterMode(heaterId, selectedMode);

            // Show success message
            const notification = document.createElement('div');
            notification.className = 'notification success';
            notification.textContent = `Mode successfully updated to ${AQUATHERM_MODE_LABELS[selectedMode]}.`;

            const notificationArea = document.querySelector('.notification-area') || document.body;
            notificationArea.appendChild(notification);

            // Remove the notification after a few seconds
            setTimeout(() => {
              notification.remove();
            }, 5000);
          } catch (error) {
            console.error('Failed to update mode:', error);

            // Show error message
            const notification = document.createElement('div');
            notification.className = 'notification error';
            notification.textContent = 'Failed to update mode. Please try again.';

            const notificationArea = document.querySelector('.notification-area') || document.body;
            notificationArea.appendChild(notification);

            // Remove the notification after a few seconds
            setTimeout(() => {
              notification.remove();
            }, 5000);
          } finally {
            applyButton.disabled = false;
            applyButton.textContent = 'Apply';
          }
        });
      }
    }

    // Load the water heater data
    this.loadWaterHeaterData(hash);
  }

  /**
   * Load the AquaTherm water heater data for the detail view
   * @param {string} id - The water heater ID
   */
  async loadWaterHeaterData(id) {
    if (!window.api || !window.api.getAquaThermWaterHeater) {
      console.error('API client not found or getAquaThermWaterHeater method not available');
      return;
    }

    try {
      // Get the water heater data
      const heater = await window.api.getAquaThermWaterHeater(id);

      // Update the UI with the heater data
      if (heater) {
        // Update series
        const seriesEl = document.getElementById('aquatherm-series');
        if (seriesEl) {
          seriesEl.textContent = heater.series || 'N/A';
        }

        // Update EcoNet status
        const ecoNetStatus = document.getElementById('eco-net-status');
        if (ecoNetStatus) {
          const isEcoNetEnabled = heater.properties && heater.properties.eco_net_enabled === true;
          ecoNetStatus.textContent = isEcoNetEnabled ? 'Yes' : 'No';
        }

        // Update Energy Star status
        const energyStarStatus = document.getElementById('energy-star-status');
        if (energyStarStatus) {
          const isEnergyStar = heater.properties && heater.properties.energy_star_certified === true;
          energyStarStatus.textContent = isEnergyStar ? 'Certified' : 'Not Certified';
        }

        // Update toggle switch
        const ecoNetToggle = document.getElementById('eco-net-toggle');
        const ecoNetToggleStatus = document.getElementById('eco-net-toggle-status');
        if (ecoNetToggle && ecoNetToggleStatus) {
          const isEcoNetEnabled = heater.properties && heater.properties.eco_net_enabled === true;
          ecoNetToggle.checked = isEcoNetEnabled;
          ecoNetToggleStatus.textContent = isEcoNetEnabled ? 'Connected' : 'Disconnected';
        }

        // Update mode selector
        const modeSelector = document.getElementById('aquatherm-mode-selector');
        if (modeSelector && heater.mode) {
          const mode = heater.mode.toLowerCase().replace(/\s+/g, '_');
          modeSelector.value = mode;

          // Trigger the change event to update the description
          modeSelector.dispatchEvent(new Event('change'));
        }
      }
    } catch (error) {
      console.error(`Failed to load AquaTherm water heater ${id}:`, error);
    }
  }
}

// Initialize the AquaTherm handler
const aquaThermHandler = new AquaThermWaterHeaterHandler();

// Export for use in other modules
window.AquaThermWaterHeaterHandler = AquaThermWaterHeaterHandler;
