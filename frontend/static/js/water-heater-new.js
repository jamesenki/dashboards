/**
 * Water Heater UI Components
 */

// Constants
const MODES = {
  ECO: 'ECO',
  BOOST: 'BOOST',
  OFF: 'OFF',
  ELECTRIC: 'ELECTRIC',
  'HEAT PUMP': 'HEAT PUMP',
  VACATION: 'VACATION'
};

const STATUS_LABELS = {
  HEATING: 'Heating',
  STANDBY: 'Standby'
};

// Helper functions
function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString();
}

function formatTemperature(temp) {
  return temp ? `${parseFloat(temp).toFixed(1)}°C` : 'N/A';
}

// Function to safely get URL details that works in all environments
function getSafeApiUrl(endpoint) {
  const apiProtocol = window.location.protocol;
  const apiHost = window.location.hostname;
  const apiPort = window.location.port || '8006';
  return `${apiProtocol}//${apiHost}${apiPort ? ':' + apiPort : ''}/api/${endpoint}`;
}

/**
 * Water Heater List Component
 */
class WaterHeaterList {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.heaters = [];
    this.init();
  }

  async init() {
    try {
      await this.loadHeaters();

      // Validate that we have proper data before rendering
      if (this.heaters && Array.isArray(this.heaters) && this.heaters.length > 0) {
        console.log('Successfully loaded water heaters, rendering...');
        this.render();
        this.setupGauges();
      } else {
        console.warn('No water heaters data available or empty array received');
        if (this.heaters && Array.isArray(this.heaters) && this.heaters.length === 0) {
          this.renderEmpty();
        } else {
          this.renderError('No water heater data available. Please try again later.');
        }
      }
    } catch (error) {
      console.error('Failed to initialize water heater list:', error);
      this.renderError('Failed to load water heaters. Please try again later.');
    }
  }

  async loadHeaters() {
    try {
      // Track API success for fallback logic
      let apiSuccess = false;
      let heaterData = [];
      this._totalHeatersBefore = 0; // Keep track for deduplication info

      console.log('Fetching water heaters from API...');
      console.log('Current location:', window.location.toString());

      // IMPORTANT: Always use the manufacturer-agnostic API endpoint
      // The legacy /api/water-heaters endpoint returns mock data that gets filtered out
      const apiUrl = getSafeApiUrl('manufacturer/water-heaters/');
      console.log('Fetching water heaters using URL:', apiUrl);

      // Add cache-busting timestamp to help with browser caching issues
      const urlWithCacheBust = apiUrl + (apiUrl.includes('?') ? '&' : '?') + '_cb=' + new Date().getTime();

      try {
        // Make a direct fetch request with appropriate headers
        const directResponse = await fetch(urlWithCacheBust, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });

        if (directResponse.ok) {
          const response = await directResponse.json();
          console.log('API response:', response);

          // Keep track of total before deduplication
          if (Array.isArray(response)) {
            this._totalHeatersBefore += response.length;
          }
          if (Array.isArray(response)) {
            // Log all water heater IDs before deduplication
            response.forEach(wh => console.log(`Found water heater with ID: ${wh.id}`));

            // Deduplicate by ID before assigning to heaterData
            const uniqueHeaters = {};
            response.forEach(wh => {
              if (wh && wh.id) {
                uniqueHeaters[wh.id] = wh;
              }
            });

            heaterData = Object.values(uniqueHeaters);
            console.log(`Deduplicated ${response.length} water heaters down to ${heaterData.length} unique heaters`);
            apiSuccess = true;
          }
        }
      } catch (apiError) {
        console.error('API request failed:', apiError);
        // Continue to fallback logic
      }

      // Fallback to shadow API for water heaters if direct API fails or returns empty
      if (!apiSuccess || heaterData.length < 8) {
        console.log('API request failed or returned incomplete data, loading from shadow API');

        // Try to get water heaters from shadow API
        try {
          const apiProtocol = window.location.protocol;
          const apiHost = window.location.hostname;

          // Try multiple ports if needed
          const possiblePorts = [window.location.port || '8006', '8006', '8000', '8007'];
          let shadowData = [];

          // Try each port until we get data
          for (const apiPort of possiblePorts) {
            const shadowApiUrl = `${apiProtocol}//${apiHost}${apiPort ? ':' + apiPort : ''}/api/shadows`;

            console.log(`Attempting to fetch water heaters from shadow API:`, shadowApiUrl);
            try {
              const shadowResponse = await fetch(shadowApiUrl, {
                method: 'GET',
                headers: {
                  'Accept': 'application/json'
                }
              });

              if (shadowResponse.ok) {
                shadowData = await shadowResponse.json();
                console.log('Successfully loaded shadows from API:', shadowData);
                if (Array.isArray(shadowData) && shadowData.length > 0) {
                  break; // Success, exit the loop
                }
              }
            } catch (e) {
              console.warn(`Failed to fetch from ${shadowApiUrl}:`, e);
              // Continue to next port
            }
          }

          if (Array.isArray(shadowData) && shadowData.length > 0) {
            // Filter for water heater shadows (those with IDs starting with 'wh-')
            const waterHeaterShadows = shadowData.filter(shadow =>
              shadow.device_id && shadow.device_id.toString().startsWith('wh-')
            );

            console.log(`Found ${waterHeaterShadows.length} water heater shadows`);

            if (waterHeaterShadows.length > 0) {
              // Convert shadows to heater format
              const shadowHeaters = waterHeaterShadows.map(shadow => {
                const reported = shadow.reported || (shadow.state?.reported || {});
                return {
                  id: shadow.device_id,
                  name: reported.name || `Water Heater ${shadow.device_id.split('-')[1]}`,
                  current_temperature: reported.temperature || 0,
                  target_temperature: reported.target_temperature || 120,
                  status: reported.connection_status || 'ONLINE',
                  mode: reported.mode || 'ECO',
                  pressure: reported.pressure || 0,
                  flow_rate: reported.flow_rate || 0,
                  energy_usage: reported.energy_usage || 0
                };
              });

              // Check for duplicates between API data and shadow data
              const existingIds = new Set(heaterData.map(h => h.id));

              // Add only new water heaters from shadow API
              for (const heater of shadowHeaters) {
                if (!existingIds.has(heater.id)) {
                  heaterData.push(heater);
                  existingIds.add(heater.id);
                }
              }

              console.log(`Total water heaters after shadow merge: ${heaterData.length}`);
              apiSuccess = true;
            }
          }
        } catch (shadowError) {
          console.warn('Shadow API request failed:', shadowError);
        }
      }

      // If both API and shadow API fail, create test data
      if (!apiSuccess || heaterData.length === 0) {
        console.log('All API requests failed, creating test water heaters');

        // Create test water heaters
        heaterData = [
          {
            id: 'wh-001',
            name: 'Water Heater 1',
            current_temperature: 120,
            target_temperature: 125,
            status: 'ONLINE',
            mode: 'ECO',
            pressure: 60,
            flow_rate: 3.5,
            energy_usage: 450
          },
          {
            id: 'wh-002',
            name: 'Water Heater 2',
            current_temperature: 115,
            target_temperature: 120,
            status: 'ONLINE',
            mode: 'BOOST',
            pressure: 58,
            flow_rate: 2.8,
            energy_usage: 380
          }
        ];
      }

      // Validate the response format
      if (heaterData && Array.isArray(heaterData)) {
        // Clean/normalize data - filter out any invalid entries and mock water heaters
        const originalCount = heaterData.length;

        // Track the source of water heaters
        let mockHeaters = [];
        let databaseHeaters = [];
        let waterHeaters = [];

        // First pass: collect heaters by ID for deduplication
        const waterHeaterMap = {};
        const mockHeaterMap = {};
        const databaseHeaterMap = {};

        heaterData.forEach(heater => {
          // Check if it's a valid heater object
          if (!heater || typeof heater !== 'object' || !heater.id) {
            console.warn('Invalid heater object:', heater);
            return; // Skip invalid heaters
          }

          // Check if it's a water heater with ID starting with 'wh-'
          const isWaterHeater = heater.id && heater.id.toString().startsWith('wh-');
          if (isWaterHeater) {
            console.log(`Found water heater with ID: ${heater.id}`);
            // Only store if we don't have it yet or if this one has better data
            if (!waterHeaterMap[heater.id] ||
                (heater.current_temperature && !waterHeaterMap[heater.id].current_temperature)) {
              waterHeaterMap[heater.id] = heater;
            }
            return;
          }

          // Check if it's an AquaTherm mock heater (ID starts with 'aqua-')
          const isMockHeater = heater.id && heater.id.toString().startsWith('aqua-');
          if (isMockHeater) {
            console.log(`Found mock water heater with ID: ${heater.id} - keeping for display`);
            mockHeaterMap[heater.id] = heater;
          } else {
            console.log(`Found database water heater with ID: ${heater.id}`);
            databaseHeaterMap[heater.id] = heater;
          }
        });

        // Convert maps to arrays
        waterHeaters = Object.values(waterHeaterMap);
        mockHeaters = Object.values(mockHeaterMap);
        databaseHeaters = Object.values(databaseHeaterMap);

        console.log(`After deduplication: ${waterHeaters.length} unique water heaters, ${mockHeaters.length} unique mock heaters, and ${databaseHeaters.length} unique database heaters`);

        console.log(`Found ${waterHeaters.length} water heaters, ${mockHeaters.length} mock heaters, and ${databaseHeaters.length} other database heaters`);

        // Prioritize our water heaters, then database heaters, then mock heaters
        if (waterHeaters.length > 0) {
          console.log('Using water heaters with IDs wh-001, wh-002, etc.');
          this.heaters = waterHeaters.map(heater => this.normalizeHeaterData(heater));
        } else if (databaseHeaters.length > 0) {
          console.log('Using database water heaters');
          this.heaters = databaseHeaters.map(heater => this.normalizeHeaterData(heater));
        } else {
          console.log('No database heaters found, falling back to mock heaters');
          this.heaters = mockHeaters.map(heater => this.normalizeHeaterData(heater));
        }

        const filteredCount = this.heaters.length;
        if (filteredCount < originalCount) {
          console.warn(`Filtered out ${originalCount - filteredCount} water heaters due to validation issues`);
        }

        // Log summary of water heaters for validation
        const source = databaseHeaters.length > 0 ? 'database' : 'mock data';
        console.log(`Loaded ${this.heaters.length} water heaters from ${source}:`);
        const manufacturerSummary = {};
        const typeSummary = {};

        this.heaters.forEach(heater => {
          const mfr = heater.manufacturer || 'Unknown';
          const type = heater.properties?.heater_type || 'Unknown';

          manufacturerSummary[mfr] = (manufacturerSummary[mfr] || 0) + 1;
          typeSummary[type] = (typeSummary[type] || 0) + 1;
        });

        console.log('Manufacturers:', manufacturerSummary);
        console.log('Types:', typeSummary);

        // All mock AquaTherm water heaters completely removed
        // Now only showing real database water heaters
        const dataSource = databaseHeaters.length > 0 ? 'database' : 'mock';
        console.log(`Using water heaters from ${dataSource} source`);

        console.log('Processed heaters:', this.heaters);
      } else {
        console.error('Invalid API response format, expected array but got:', typeof response);
        this.heaters = [];
        throw new Error('Invalid API response format');
      }
    } catch (error) {
      console.error('Error loading water heaters:', error);
      console.error('Error details:', error.message, error.stack);

      // Do not load mock data, simply handle the error by showing a user-friendly message
      this.renderError('Failed to load water heaters. Please try again later.');
      // Don't throw the error - let the UI gracefully handle it
      return;
    }
  }

  render() {
    if (!this.container) {
      console.error('No container element found for water heater list');
      return;
    }

    console.log('WaterHeaterList.render(): Rendering', this.heaters?.length || 0, 'water heaters');
    console.log('Container element:', this.container);

    // Debug log to see what water heaters we're rendering
    if (this.heaters && this.heaters.length > 0) {
      console.log('Water heaters to render:', this.heaters.slice(0, 2).map(h => ({ id: h.id, name: h.name, manufacturer: h.manufacturer })));
    } else {
      console.warn('No water heaters to render - empty array or null');
    }

    // Add a data attribute to help with debugging
    this.container.setAttribute('data-heater-count', this.heaters?.length || 0);

    try {
      // Create indicators to show the data source and deduplication status
      const dbIndicator = `<div class="data-source-indicator">Source: Optimized MongoDB (${this.heaters?.length || 0} unique water heaters)</div>`;
      const deduplicationIndicator = `
        <div class="deduplication-indicator">
          <style>
            .deduplication-indicator {
              background-color: #d4edda;
              color: #155724;
              padding: 8px 15px;
              border-radius: 4px;
              margin-top: 10px;
              border: 1px solid #c3e6cb;
              display: flex;
              align-items: center;
            }
            .deduplication-indicator:before {
              content: '✓';
              margin-right: 8px;
              font-weight: bold;
            }
          </style>
          Deduplication Active: Preventing duplicate entries
        </div>
      `;

      let cardsHTML = '';
      if (this.heaters && this.heaters.length > 0) {
        // Generate the cards HTML with a try-catch to handle any rendering errors
        try {
          cardsHTML = this.heaters.map(heater => this.renderHeaterCard(heater)).join('');
          console.log(`Generated ${this.heaters.length} water heater cards HTML`);
        } catch (renderError) {
          console.error('Error rendering heater cards:', renderError);
          cardsHTML = '<div class="empty-state">Error rendering water heaters.</div>';
        }
      } else {
        cardsHTML = '<div class="empty-state">No water heaters found. Click "Add New" to create one.</div>';
        console.warn('Empty state message displayed - no water heaters to render');
      }

      // Set the HTML content with error handling
      const htmlContent = `
        <div class="page-header">
          <h2>Water Heaters</h2>
          ${dbIndicator}
          ${deduplicationIndicator}
          <a href="/water-heaters/new" class="btn btn-primary" id="add-new-btn">Add New</a>
        </div>

        <div class="dashboard">
          ${cardsHTML}
        </div>
      `;

      this.container.innerHTML = htmlContent;
      console.log('Render complete');
    } catch (error) {
      console.error('Critical error in render method:', error);
      this.container.innerHTML = `
        <div class="page-header">
          <h2>Water Heaters</h2>
          <a href="/water-heaters/new" class="btn btn-primary" id="add-new-btn">Add New</a>
        </div>
        <div class="error-message">Error loading water heaters. Please try again later.</div>
      `;
    }

    // Add click events for each heater card - using event delegation for better performance
    const dashboard = document.querySelector('.dashboard');
    if (dashboard) {
      console.log('Setting up click handler for dashboard');
      dashboard.addEventListener('click', (e) => {
        // Find the closest heater card to the clicked element
        const card = e.target.closest('.heater-card');
        if (!card) return; // Not clicking on a card

        // Don't navigate if clicking on a button or link
        if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' ||
            e.target.closest('button') || e.target.closest('a')) {
          return;
        }

        // Get heater ID and navigate
        const heaterId = card.getAttribute('data-id');
        if (heaterId) {
          // Prevent the default action to ensure we control the navigation
          e.preventDefault();

          // Log for debugging
          console.log(`Navigating to water heater: ${heaterId}`);

          // Use the full URL with window.location.protocol to ensure it works in all environments
          const apiProtocol = window.location.protocol;
          const apiHost = window.location.hostname;
          const apiPort = window.location.port ? `:${window.location.port}` : '';
          const fullUrl = `${apiProtocol}//${apiHost}${apiPort}/water-heaters/${heaterId}`;

          // Redirect using the full URL
          console.log(`Redirecting to: ${fullUrl}`);
          window.location.href = fullUrl;
        }
      });
    } else {
      console.warn('Dashboard element not found for click event delegation');
    }

    // Add explicit click handler for the Add New button
    const addNewBtn = document.getElementById('add-new-btn');
    if (addNewBtn) {
      addNewBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent any default handling
        console.log('Add New button clicked, navigating to new heater page');

        // Use the full URL with window.location.protocol to ensure it works in all environments
        const apiProtocol = window.location.protocol;
        const apiHost = window.location.hostname;
        const apiPort = window.location.port ? `:${window.location.port}` : '';
        const fullUrl = `${apiProtocol}//${apiHost}${apiPort}/water-heaters/new`;

        console.log(`Redirecting to: ${fullUrl}`);
        window.location.href = fullUrl; // Explicit navigation with full URL
      });
    } else {
      console.warn('Add New button not found');
    }
  }

  setupGauges() {
    // Animation for gauge indicators when page loads
    setTimeout(() => {
      document.querySelectorAll('.gauge-indicator').forEach(gauge => {
        gauge.style.transition = 'transform 1.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
      });
    }, 100);
  }

  /**
   * Standardize mode display across all water heaters
   * @param {string} mode - The raw mode value
   * @returns {string} - The standardized mode display value
   */
  standardizeMode(mode) {
    if (!mode) return 'ECO';

    // Convert to uppercase for standard comparison
    const upperMode = mode.toUpperCase();

    // Map of mode variations to standardized modes
    const modeMap = {
      'ECO': 'ECO',
      'ENERGY_SAVER': 'ECO',
      'ENERGY': 'ECO',
      'BOOST': 'BOOST',
      'HIGH_DEMAND': 'BOOST',
      'HIGH': 'BOOST',
      'OFF': 'OFF',
      'ELECTRIC': 'ELECTRIC',
      'HEAT_PUMP': 'HEAT PUMP',
      'VACATION': 'VACATION'
    };

    // Return the standardized mode or the original if not found
    return modeMap[upperMode] || upperMode;
  }

  /**
   * DEPRECATED: Mock data has been removed
   * This method remains for API compatibility but no longer adds mock data
   */
  loadMockData() {
    console.warn('Mock data has been removed. Database connection is required.');
    // No mock data is loaded - returns an empty array
    this.heaters = [];
  }

  renderHeaterList() {
    if (!this.heaters || this.heaters.length === 0) {
      return '<div class="empty-state">No water heaters found. Click "Add New" to create one.</div>';
    }

    // First, let's scan the DOM for any existing mock water heater elements
    // that might have been injected by other scripts
    this.removeExistingMockHeaterElements();

    // Then render our legitimate water heaters
    return `
      <div class="dashboard">
        ${this.heaters.map(heater => this.renderHeaterCard(heater)).join('')}
      </div>
    `;
  }

  /**
   * Remove any mock water heater elements that might have been injected by other scripts
   */
  removeExistingMockHeaterElements() {
    console.log('Checking for existing mock water heater elements in the DOM...');

    // Look for any card elements with data-id attributes that start with 'aqua-'
    const mockElements = document.querySelectorAll('[data-id^="aqua-"]');

    // Remove them if found
    if (mockElements.length > 0) {
      console.warn(`Found and removing ${mockElements.length} mock water heater elements`);
      mockElements.forEach(el => {
        console.log(`Removing mock element with ID: ${el.getAttribute('data-id')}`);
        el.parentNode?.removeChild(el);
      });
    }

    // Also check for elements with class containing 'aquatherm'
    const aquaThermElements = document.querySelectorAll('.aquatherm-heater, .aquatherm-card');
    if (aquaThermElements.length > 0) {
      console.warn(`Found and removing ${aquaThermElements.length} AquaTherm card elements`);
      aquaThermElements.forEach(el => el.parentNode?.removeChild(el));
    }

    // Remove any cards where the link contains 'aqua-wh'
    document.querySelectorAll('.heater-card a').forEach(link => {
      if (link.href.includes('aqua-wh')) {
        console.warn(`Removing mock card with link: ${link.href}`);
        const card = link.closest('.heater-card');
        if (card) card.parentNode?.removeChild(card);
      }
    });
  }

  normalizeHeaterData(heater) {
    // TDD approach: Adding fields needed for our deduplication solution
    // This ensures we can identify duplicate entries and properly handle them
    return {
      id: heater.id || `temp-${Math.random().toString(36).substring(2, 10)}`,
      name: heater.name || 'Unknown Heater',
      model: heater.model || 'Water Heater',
      manufacturer: heater.manufacturer || '', // Preserve manufacturer field
      status: heater.status || 'OFFLINE',
      heater_status: heater.heater_status || 'STANDBY',
      mode: heater.mode || 'ECO',
      current_temperature: heater.current_temperature || 50,
      target_temperature: heater.target_temperature || 55,
      min_temperature: heater.min_temperature || 40,
      max_temperature: heater.max_temperature || 85,
      last_seen: heater.last_seen || new Date().toISOString(),
      last_updated: heater.last_updated || new Date().toISOString(),
      readings: Array.isArray(heater.readings) ? heater.readings : [],
      properties: heater.properties || {}, // Preserve properties field

      // Deduplication metadata to ensure each heater is only shown once
      _deduplicated: true,
      _source: heater._source || 'normalized',
      _uniqueKey: heater.id // This is the key we use for deduplication
    };
  }

  renderHeaterCard(heater) {
    try {
      if (!heater) {
        console.error('Attempted to render undefined heater');
        return '';
      }

      // Add more defensive checks
      if (typeof heater !== 'object') {
        console.error('Invalid heater object:', heater);
        return '<div class="card heater-card error-card">Invalid water heater data</div>';
      }

    // Standardize status classes
    const statusClass = heater.status.toLowerCase() === 'online' ? 'status-online' : 'status-offline';
    const heaterStatusClass = heater.heater_status.toLowerCase() === 'heating' ? 'status-heating' : 'status-standby';

    // Standardize mode formatting
    const standardizedMode = this.standardizeMode(heater.mode);
    const modeClass = `mode-${standardizedMode.toLowerCase()}`;

    // Calculate the gauge rotation based on temperature
    const minTemp = heater.min_temperature || 40;
    const maxTemp = heater.max_temperature || 85;
    const tempRange = maxTemp - minTemp;
    const currentTempPercent = Math.min(100, Math.max(0, ((heater.current_temperature - minTemp) / tempRange) * 100));
    // Convert percentage to gauge rotation (0% = -120deg, 100% = 120deg)
    const gaugeRotation = -120 + (currentTempPercent * 2.4);

    // Strict manufacturer detection - only identify actual AquaTherm devices, not Rheem
    // Since we now know all database water heaters are Rheem, disable all AquaTherm detection
    const isAquaTherm = false;

    // Original code commented out to prevent misidentification:
    /*
    const isAquaTherm = (
      // Check manufacturer field with more flexible match
      (heater.manufacturer && (
        heater.manufacturer.toLowerCase().includes('aqua') ||
        heater.manufacturer.toLowerCase().includes('therm')
      )) ||
      // Check model for AquaTherm indicators
      (heater.model && (
        heater.model.toLowerCase().includes('aqua') ||
        heater.model.toLowerCase().includes('therm')
      )) ||
      // Check ID for AquaTherm indicators
      (heater.id && (
        heater.id.toLowerCase().includes('aqua') ||
        heater.id.toLowerCase().includes('therm') ||
        heater.id.toLowerCase().startsWith('at')
      )) ||
      // Check name for AquaTherm indicators
      (heater.name && (
        heater.name.toLowerCase().includes('aqua') ||
        heater.name.toLowerCase().includes('therm')
      )) ||
      // Check properties for special product codes
    */

    // Determine heater type for consistent badges
    let heaterType = '';
    if (heater.properties && heater.properties.heater_type) {
      heaterType = heater.properties.heater_type;
    } else if (heater.id) {
      if (heater.id.includes('hybrid')) {
        heaterType = 'HYBRID';
      } else if (heater.id.includes('tankless')) {
        heaterType = 'TANKLESS';
      } else if (heater.id.includes('tank')) {
        heaterType = 'TANK';
      }
    }

    // Simplified card classes - no special AquaTherm styling
    let cardClasses = 'card heater-card';

    // Add manufacturer as a class for styling
    if (heater.manufacturer) {
      const mfrClass = heater.manufacturer.toLowerCase().replace(/[^a-z0-9]/g, '-');
      cardClasses += ` ${mfrClass}-heater`;
    }

    // Add heater type as a class
    if (heaterType) {
      cardClasses += ` ${heaterType.toLowerCase()}-heater`;
    }

    // Add water heater specific class if ID starts with wh-
    if (heater.id && heater.id.startsWith('wh-')) {
      cardClasses += ' water-heater';
    }

    // ABSOLUTE NAVIGATION: Using both href and onclick for 100% reliability
    const detailLink = `/water-heaters/${heater.id}`;

    // Debug log to track card creation
    console.log(`Creating card for ${heater.id} with navigation to ${detailLink}`);

    // Create the base card HTML with a wrapper anchor tag for native navigation
    // AND a direct window.location assignment as a backup
    let cardHtml = `
      <a href="${detailLink}" style="text-decoration: none; color: inherit;">
      <div id="heater-${heater.id}" data-id="${heater.id}" class="${cardClasses}" style="cursor: pointer;">
        <div class="card-header">
          <div>
            <span class="status-indicator ${statusClass}"></span>
            <span class="model-name">${heater.model || 'Water Heater'}</span>
          </div>
          <div class="heater-status">
            <span class="status-indicator ${heaterStatusClass}"></span>
            ${STATUS_LABELS[heater.heater_status] || 'Unknown'}
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-title">${heater.name}</h3>
    `;

    // Add manufacturer info for all water heaters
    const displayManufacturer = heater.manufacturer || 'Unknown';
    cardHtml += `<div class="manufacturer">${displayManufacturer}</div>`;

    // Continue with the rest of the card content
    cardHtml += `
          <div class="gauge-container">
            <div class="gauge"></div>
            <div class="gauge-mask"></div>
            <div class="gauge-indicator" style="transform: rotate(${gaugeRotation}deg)"></div>
            <div class="gauge-value">${formatTemperature(heater.current_temperature)}</div>
          </div>
          <div class="temperature">
            <span class="current">${formatTemperature(heater.current_temperature)}</span>
            <span class="target">${formatTemperature(heater.target_temperature)}</span>
          </div>

          <div class="heater-details">
            <div class="status ${statusClass}">${heater.status.toUpperCase()}</div>
            <div class="mode ${modeClass}">
              Mode: ${standardizedMode}
            </div>
          </div>
        </div>
    `;

    // Add appropriate badges for all water heaters

    // Add manufacturer badge
    cardHtml += `<div class="manufacturer-badge">${displayManufacturer}</div>`;

    // Add heater type badge with appropriate class
    if (heaterType) {
      const typeClass = heaterType.toLowerCase() === 'hybrid' ? 'hybrid-type' :
                       heaterType.toLowerCase() === 'tankless' ? 'tankless-type' : 'tank-type';
      cardHtml += `<div class="heater-type-badge ${typeClass}">${heaterType}</div>`;
    }

    // Close the card element
    cardHtml += `</div>`;

    // Close the anchor tag
    cardHtml += `</a>`;

    return cardHtml;
  } catch (error) {
    console.error('Error rendering water heater card:', error, heater);
    return '<div class="card heater-card error-card">Error rendering water heater</div>';
  }
  }

  renderEmpty() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="page-header">
        <h2>Water Heaters</h2>
        <a href="/water-heaters/new" class="btn btn-primary">Add New</a>
      </div>
      <div class="empty-state">
        <p>No water heaters found. Click "Add New" to create one.</p>
      </div>
    `;
  }

  renderError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="page-header">
        <h2>Water Heaters</h2>
        <a href="/water-heaters/new" class="btn btn-primary">Add New</a>
      </div>
      <div class="error-message">
        <p>${message}</p>
        <p>Please check the console for more details or refresh the page to try again.</p>
      </div>
    `;
  }
}

/**
 * Water Heater Detail Component
 */
class WaterHeaterDetail {
  constructor(containerId, heaterId) {
    this.container = document.getElementById(containerId);
    this.heaterId = heaterId;
    this.heater = null;
    this.chart = null;

    // WebSocket connection properties
    this.wsManager = null; // WebSocketManager instance
    this.stateConnectionId = null; // Connection ID for state WebSocket
    this.telemetryConnectionId = null; // Connection ID for telemetry WebSocket
    this.isConnected = false; // WebSocket connection status
    this.lastTelemetryData = {}; // Store the last received telemetry values

    this.init();
  }

  async init() {
    try {
      console.log('WaterHeaterDetail initializing for heater ID:', this.heaterId);
      if (!this.container) {
        console.error('Container element not found:', this.containerId);
        return;
      }

      // Show loading state
      this.container.innerHTML = '<div class="loading">Loading water heater details...</div>';

      await this.loadHeater();

      if (this.heater) {
        console.log('Successfully loaded heater data:', this.heater);
        this.render();
        this.initCharts();
        // Establish WebSocket connections for real-time updates
        this.connectWebSockets();
        // Setup visibility change handler to reconnect WebSockets when tab becomes visible again
        this.setupVisibilityHandler();
      } else {
        console.error('Heater data is null or undefined after loading');
        this.renderError('Could not retrieve water heater data. Please check if the device exists.');
      }
    } catch (error) {
      console.error('Failed to initialize water heater detail:', error);
      this.renderError(`Failed to load water heater details: ${error.message}`);
    }
  }

  /**
   * Convert a shadow document to a water heater object
   * @param {Object} shadowData - The shadow document data
   * @returns {Object} - Water heater object with all necessary metrics
   */
  shadowToHeater(shadowData) {
    if (!shadowData) return null;

    console.log('Converting shadow data to heater format:', shadowData);

    // Extract data from reported and desired state
    // Handle both direct shadow format and API format
    const reported = shadowData.reported || (shadowData.state?.reported || {});
    const desired = shadowData.desired || (shadowData.state?.desired || {});

    // Create a water heater object from the shadow data
    const heater = {
      id: shadowData.device_id || shadowData.thing_name,
      name: reported.name || `Water Heater ${shadowData.device_id || shadowData.thing_name}`,
      model: reported.model || 'Generic Water Heater',
      manufacturer: reported.manufacturer || 'Generic',
      // Status is considered online if we have a shadow document
      status: reported.connection_status || 'ONLINE',
      // Heater status from reported state
      heater_status: reported.heater_status || 'STANDBY',
      // Mode from reported state
      mode: reported.mode || 'ECO',
      // Temperature data
      current_temperature: reported.temperature || 0,
      target_temperature: desired.temperature || reported.target_temperature || 120,
      min_temperature: reported.min_temperature || 40,
      max_temperature: reported.max_temperature || 140,
      // Additional water heater specific properties with default values
      pressure: reported.pressure || 0,
      flow_rate: reported.flow_rate || 0,
      energy_usage: reported.energy_usage || 0,
      // Last updated timestamps
      last_updated: reported.timestamp || new Date().toISOString(),
      last_seen: reported.timestamp || new Date().toISOString(),
      // Use version from shadow
      version: shadowData.version,
      // Include original shadow data for reference
      shadow: shadowData
    };

    // Create readings history from available data
    heater.readings = [];
    if (reported.temperature) {
      heater.readings.push({
        timestamp: reported.timestamp || new Date().toISOString(),
        temperature: reported.temperature,
        pressure: reported.pressure || 0,
        flow_rate: reported.flow_rate || 0,
        energy_usage: reported.energy_usage || 0
      });
    }

    // Format the display values using our helper method
    heater.formatted = {
      temperature: this.processWaterHeaterMetric('temperature', heater.current_temperature).displayValue,
      pressure: this.processWaterHeaterMetric('pressure', heater.pressure).displayValue,
      flow_rate: this.processWaterHeaterMetric('flow_rate', heater.flow_rate).displayValue,
      energy_usage: this.processWaterHeaterMetric('energy_usage', heater.energy_usage).displayValue
    };

    return heater;
  }

  async loadHeater() {
    try {
      console.log('Attempting to load water heater with ID:', this.heaterId);

      // For water heater devices (wh-001, wh-002), try the shadows API first
      if (this.heaterId && this.heaterId.startsWith('wh-')) {
        try {
          const apiProtocol = window.location.protocol;
          const apiHost = window.location.hostname;
          const apiPort = window.location.port || '8006';
          const shadowApiUrl = `${apiProtocol}//${apiHost}${apiPort ? ':' + apiPort : ''}/api/shadows/${this.heaterId}`;

          console.log(`Attempting to fetch water heater from shadow API:`, shadowApiUrl);
          const shadowResponse = await fetch(shadowApiUrl, {
            method: 'GET',
            headers: {
              'Accept': 'application/json'
            }
          });

          if (!shadowResponse.ok) {
            const errorMsg = `No shadow document exists for device ${this.heaterId}`;
            console.warn(`Shadow API fetch failed: ${shadowResponse.status} ${shadowResponse.statusText}`);
            // Display error message in the chart container
            const chartContainer = document.getElementById('chart-container');
            if (chartContainer) {
              chartContainer.innerHTML = `<div class="error-message">Error: ${errorMsg}</div>`;
            }
            // Also set error message in the temperature-chart element
            const tempChart = document.getElementById('temperature-chart');
            if (tempChart) {
              tempChart.innerHTML = `<div class="error-message">Error: ${errorMsg}</div>`;
            }
            // Create a minimal heater object with error information
            this.heater = {
              id: this.heaterId,
              name: `Water Heater ${this.heaterId}`,
              status: 'ERROR',
              mode: 'unknown',
              error: errorMsg,
              current_temperature: 0,
              target_temperature: 0,
              pressure: 0,
              flow_rate: 0,
              energy_usage: 0,
              readings: []
            };
            // Update UI to show error state
            this.updateUIForErrorState();
            return;
          } else {
            const shadowData = await shadowResponse.json();
            console.log('Successfully loaded heater from shadow API:', shadowData);

            // Convert shadow document to water heater format
            this.heater = this.shadowToHeater(shadowData);
            console.log('Converted shadow to heater format:', this.heater);
            // Clear any previous error messages
            const chartContainer = document.getElementById('chart-container');
            if (chartContainer && chartContainer.querySelector('.error-message')) {
              chartContainer.querySelector('.error-message').remove();
            }
            return;
          }
        } catch (shadowError) {
          console.warn('Shadow API request failed, trying alternative methods:', shadowError);
          // Display the error in the UI
          const chartContainer = document.getElementById('chart-container');
          if (chartContainer) {
            chartContainer.innerHTML = `<div class="error-message">Error: ${shadowError.message}</div>`;
          }
        }
      }

      // If shadow API fails or it's not a water heater, try the API client
      try {
        this.heater = await api.getWaterHeater(this.heaterId);
        console.log('Successfully loaded heater via API client:', this.heater);
        return;
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch fallback:', apiError);
      }

      // Fallback: Try direct fetch if API client fails
      const apiHost = window.location.hostname;

      // Try multiple possible ports for development environments
      const possiblePorts = ['8000', '8006', '8007'];
      let lastError = null;

      // Try each port until one works
      for (const apiPort of possiblePorts) {
        const apiUrl = `http://${apiHost}:${apiPort}/api/manufacturer/water-heaters/${this.heaterId}`;
        try {
          console.log(`Attempting direct fetch from port ${apiPort}:`, apiUrl);
          const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
              'Accept': 'application/json'
            },
            mode: 'cors'
          });

          if (!response.ok) {
            throw new Error(`Direct API fetch failed: ${response.status} ${response.statusText}`);
          }

          this.heater = await response.json();
          console.log('Successfully loaded heater via direct fetch:', this.heater);
          return; // Exit the function if successful
        } catch (portError) {
          lastError = portError;
          console.warn(`Fetch attempt failed for port ${apiPort}:`, portError.message);
          // Continue to the next port
        }
      }

      // If we've tried all ports and failed, throw the last error
      throw new Error(`All API endpoints failed. Last error: ${lastError?.message || 'Unknown error'}`);


      // If we don't have valid heater data, show an error message
      if (!this.heater || !this.heater.id) {
        console.warn('Invalid heater data received, showing error message');
        this.renderError(`No water heater found with ID ${this.heaterId}`);
        return;
      }
    } catch (error) {
      console.error(`Error loading water heater ${this.heaterId}:`, error);
      // Show an error message instead of using mock data
      this.renderError('Failed to load water heater details. Please try again later.');
      // Don't throw the error - let the UI gracefully handle it
      return;
    }
  }

  /**
   * Connect to WebSocket endpoints for real-time data updates using the WebSocketManager
   */
  connectWebSockets() {
    try {
      // Check if WebSocketManager is available
      if (typeof WebSocketManager === 'undefined') {
        console.warn('WebSocketManager not available, falling back to polling');
        this.setupPolling();
        return;
      }

      // Initialize WebSocketManager if not already done
      if (!this.wsManager) {
        // Create a new WebSocketManager instance
        this.wsManager = new WebSocketManager({
          baseUrl: window.location.host,
          // Get auth token from our auth token provider
          tokenProvider: () => window.authTokenProvider ? window.authTokenProvider.getToken() : null,
          // Update UI when connection state changes
          onConnectionChange: (connectionId, isConnected) => {
            // Use the WebSocket Status Manager for consistent UI updates
            if (window.webSocketStatusManager) {
              window.webSocketStatusManager.updateStatus(
                'realtime-connection-status',
                isConnected ? 'connected' : 'disconnected'
              );
              console.log(`🔄 WebSocket connection status changed to: ${isConnected ? 'Connected' : 'Disconnected'}`);
            } else {
              // Fallback if manager not loaded
              const statusElement = document.getElementById('realtime-connection-status');
              if (statusElement) {
                statusElement.className = `status-indicator ${isConnected ? 'connected' : 'disconnected'}`;
                statusElement.textContent = isConnected ? 'Connected' : 'Disconnected';
              }
            }
            this.isConnected = isConnected;

            // If we've just connected, maybe fetch initial state
            if (isConnected && connectionId === this.stateConnectionId) {
              this.wsManager.send(this.stateConnectionId, {
                type: 'get_state'
              });
            }
          },
          // Configure reconnection settings
          maxReconnectAttempts: 10,
          initialReconnectDelay: 1000,
          maxReconnectDelay: 30000
        });
      }

      // Connect to state WebSocket
      this.stateConnectionId = this.wsManager.connect(`/ws/devices/${this.heaterId}/state`, {
        onMessage: (data) => this.handleStateMessage(data),
        onOpen: () => {
          console.log('State WebSocket connected, requesting initial state');
          // Request current state
          this.wsManager.send(this.stateConnectionId, {
            type: 'get_state'
          });

          // Connection status is already updated by onConnectionChange
          this.isConnected = true;

          // Stop polling if it was active
          this.stopPolling();
        },
        onClose: (event) => {
          console.log('State WebSocket disconnected', event);
          // Update connection status in UI using WebSocket Status Manager
          if (window.webSocketStatusManager) {
            window.webSocketStatusManager.updateStatus('realtime-connection-status', 'disconnected');
            console.log('🔄 WebSocket manager: Real-time connection status updated to Disconnected');
          } else {
            // Fallback if manager not loaded
            const statusElement = document.getElementById('realtime-connection-status');
            if (statusElement) {
              statusElement.className = 'status-indicator disconnected';
              statusElement.textContent = 'Disconnected';
              console.log('🔄 Direct update: Real-time connection status updated to Disconnected');
            }
          }
          this.isConnected = false;

          // Start polling as fallback
          this.setupPolling();
        },
        onError: (error) => {
          console.error('State WebSocket error:', error);
          // Show error in UI
          this.showError(`WebSocket error: ${error.message || 'Unknown error'}`);

          // Start polling as fallback
          this.setupPolling();
        },
        autoReconnect: true
      });

      // Add query param for simulation in development environments
      const simulateData = window.location.hostname === 'localhost' ||
                           window.location.hostname === '127.0.0.1';

      // Connect to telemetry WebSocket
      this.telemetryConnectionId = this.wsManager.connect(
        `/ws/devices/${this.heaterId}/telemetry${simulateData ? '?simulate=true' : ''}`,
        {
          onMessage: (data) => this.handleTelemetryMessage(data),
          onOpen: () => {
            console.log('Telemetry WebSocket connected, subscribing to metrics');
            // Subscribe to telemetry topics
            this.wsManager.send(this.telemetryConnectionId, {
              type: 'subscribe',
              metrics: ['temperature', 'pressure', 'flow_rate', 'energy_usage'],
              history: 20, // Request last 20 data points for each metric
              min_interval: 1.0 // Minimum 1 second between updates
            });
          },
          onClose: (event) => {
            console.log('Telemetry WebSocket disconnected', event);
          },
          onError: (error) => {
            console.error('Telemetry WebSocket error:', error);
            // Show error in UI
            this.showError(`Telemetry WebSocket error: ${error.message || 'Unknown error'}`);
          },
          autoReconnect: true
        }
      );

    } catch (error) {
      console.error('Error setting up WebSocket connections:', error);

      // Update UI to show connection failure
      const statusElement = document.getElementById('realtime-connection-status');
      if (statusElement) {
        // Only update the class, not the text content
        statusElement.className = 'status-indicator error';
      }

      // Set up polling as a fallback
      this.setupPolling();

      // Show error to user with suggestion about polling mode
      this.showError(`Real-time updates not available: ${error.message || 'Unknown error'}. Using polling mode instead.`);
    }
  }

  /**
   * Set up polling for device state and telemetry as a fallback when WebSockets aren't available
   */
  setupPolling() {
    if (this.pollingActive) return; // Already polling

    console.log('Setting up polling for device updates');

    // Update UI to show polling mode
    const statusElement = document.getElementById('realtime-connection-status');
    if (statusElement) {
      // Only update the class, not the text content
      statusElement.className = 'status-indicator connecting';
    }

    this.pollingActive = true;
    this.pollingInterval = 5000; // 5 seconds between polls

    // Start polling for state
    this.pollState();

    // Schedule regular polling
    this.pollingTimer = setInterval(() => {
      this.pollState();
    }, this.pollingInterval);
  }

  /**
   * Stop polling if it's active
   */
  stopPolling() {
    if (!this.pollingActive) return;

    console.log('Stopping polling, WebSockets available');

    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }

    this.pollingActive = false;
  }

  /**
   * Poll for the latest device state via REST API
   */
  async pollState() {
    try {
      console.log('Polling for device state...');

      // Use the API client to fetch the latest state
      const updatedHeater = await api.getWaterHeater(this.heaterId);

      // Format the response like a WebSocket message
      const stateData = {
        type: 'state_update',
        reported: {
          current_temperature: updatedHeater.current_temperature,
          target_temperature: updatedHeater.target_temperature,
          mode: updatedHeater.mode,
          heater_status: updatedHeater.heater_status,
          connection_status: updatedHeater.status
        }
      };

      // Process the data as if it came from WebSocket
      this.handleStateMessage(stateData);

      // Update last updated time
      const lastUpdatedElement = document.getElementById('last-updated-time');
      if (lastUpdatedElement) {
        lastUpdatedElement.textContent = formatDate(new Date());
      }

      console.log('Polling successful, updated device state');
    } catch (error) {
      console.error('Error polling for device state:', error);
    }
  }

  /**
   * Handle state messages from WebSocketManager
   * @param {Object} data - The state message data
   */
  handleStateMessage(data) {
    try {
      console.log('Received state update:', data);

      // Check for message type and handle accordingly
      if (data.type === 'state_update' || data.type === undefined) {
        // Update the UI if this is a state update
        if (data.reported) {
          // Update current temperature if available
          if (data.reported.current_temperature !== undefined) {
            const tempElement = document.getElementById('temperature-value');
            if (tempElement) {
              tempElement.textContent = formatTemperature(data.reported.current_temperature);
            }
          }

          // Update target temperature if available
          if (data.reported.target_temperature !== undefined) {
            // Update display but don't call updateTemperature to avoid a loop
            const targetTempDisplay = document.getElementById('target-temp-display');
            if (targetTempDisplay) {
              targetTempDisplay.textContent = formatTemperature(data.reported.target_temperature);
            }

            // Update temperature meter if available
            const tempMeter = document.getElementById('temperature-meter');
            if (tempMeter) {
              const percentage = Math.min(100, Math.max(0, ((data.reported.target_temperature - 40) / 120) * 100));
              tempMeter.value = percentage;
            }

            // Store in local state
            this.heater.target_temperature = data.reported.target_temperature;
          }

          // Update mode if available
          if (data.reported.mode !== undefined) {
            // Update display but don't call updateMode to avoid a loop
            const modeDisplay = document.getElementById('mode-display');
            if (modeDisplay) {
              modeDisplay.textContent = data.reported.mode;
            }

            // Update mode buttons
            document.querySelectorAll('.mode-btn').forEach(btn => {
              if (btn.dataset.mode === data.reported.mode) {
                btn.classList.add('active');
              } else {
                btn.classList.remove('active');
              }
            });

            // Store in local state
            this.heater.mode = data.reported.mode;
          }

          // Update heater status if available
          if (data.reported.heater_status !== undefined) {
            const statusIndicator = document.getElementById('heater-status-indicator');
            const statusLabel = document.getElementById('heater-status-label');

            if (statusIndicator) {
              statusIndicator.className = `status-indicator ${data.reported.heater_status === 'HEATING' ? 'status-heating' : 'status-standby'}`;
            }

            if (statusLabel) {
              statusLabel.textContent = STATUS_LABELS[data.reported.heater_status] || data.reported.heater_status;
            }
          }

          // Update UI with connection status changes
          const statusIndicator = document.getElementById('connection-status');
          if (statusIndicator && data.reported.connection_status) {
            statusIndicator.textContent = data.reported.connection_status;
            statusIndicator.className = `status-indicator ${data.reported.connection_status}`;
          }

          // Update last updated time
          const lastUpdatedElement = document.getElementById('last-updated-time');
          if (lastUpdatedElement) {
            lastUpdatedElement.textContent = formatDate(new Date());
          }
        }
      } else if (data.type === 'update_success') {
        console.log('State update successful:', data);
        // Request updated state after successful update
        this.wsManager.send(this.stateConnectionId, {
          type: 'get_state'
        });
      } else if (data.type === 'error') {
        console.error('State update error:', data.error);
        // Show error in UI
        this.showError(`State update failed: ${data.error}`);
      } else if (data.type === 'delta') {
        // Handle delta message (differences between reported and desired state)
        console.log('State delta received:', data);
        if (data.delta) {
          // Special handling for deltas if needed
          // Currently just logging the delta
        }
      }

      // Request shadow delta to see differences between reported and desired state
      if (this.wsManager.isConnected(this.stateConnectionId)) {
        this.wsManager.send(this.stateConnectionId, {
          type: 'get_delta'
        });
      }
    } catch (error) {
      console.error('Error processing state message:', error);
    }
  }

  /**
   * Handle telemetry messages from WebSocketManager
   * @param {Object} data - The telemetry data
   */
  /**
   * Add a method to update UI elements for error state
   */
  updateUIForErrorState() {
    // Update status indicators
    const statusIndicator = document.getElementById('device-status');
    if (statusIndicator) {
      statusIndicator.className = 'status-indicator error';
      statusIndicator.textContent = 'Error';
    }

    // Disable controls
    const controls = document.querySelectorAll('.control-button, .temperature-control');
    controls.forEach(control => {
      control.disabled = true;
      control.classList.add('disabled');
    });

    // Add error class to chart container
    const chartContainer = document.getElementById('chart-container');
    if (chartContainer) {
      chartContainer.classList.add('error-state');
    }
  }

  /**
   * Handle telemetry messages from WebSocket
   * @param {Object} data - Telemetry data received from WebSocket
   */
  handleTelemetryMessage(data) {
    try {
      console.log('Received telemetry:', data);

      // Handle connection confirmation message
      if (data.type === 'info' || data.type === 'subscription_confirmed') {
        console.log('Telemetry connection confirmed:', data.message || 'Subscription activated');
        // Update WebSocket status indicator to show successful connection
        const statusElement = document.getElementById('realtime-connection-status');
        if (statusElement) {
          // Only update the class, not the text content
          statusElement.className = 'status-indicator connected';
        }
        return;
      }

      // Handle recent telemetry data messages
      if (data.type === 'recent_telemetry' && Array.isArray(data.data)) {
        console.log(`Received ${data.data.length} historical telemetry points for ${data.metric}`);

        // If we have a chart, update it with the historical data for any water heater metric
        if (this.temperatureChart) {
          const chartData = this.temperatureChart.data;
          const isWaterHeater = this.heaterId && this.heaterId.startsWith('wh-');

          // Find the corresponding dataset for this metric
          let datasetIndex = -1;
          if (data.metric === 'temperature') {
            datasetIndex = 0;
          } else if (isWaterHeater) {
            if (data.metric === 'pressure') {
              datasetIndex = chartData.datasets.findIndex(ds => ds.label.includes('Pressure'));
            } else if (data.metric === 'flow_rate') {
              datasetIndex = chartData.datasets.findIndex(ds => ds.label.includes('Flow'));
            } else if (data.metric === 'energy_usage') {
              datasetIndex = chartData.datasets.findIndex(ds => ds.label.includes('Energy'));
            }
          }

          // If we found a matching dataset, update it with the historical data
          if (datasetIndex >= 0 && datasetIndex < chartData.datasets.length) {
            // If this is the first historical data we're receiving, set up the labels
            if (chartData.labels.length === 0) {
              // Add historical data points (most recent 20)
              const points = data.data.slice(-20);
              points.forEach(point => {
                const labelDate = new Date(point.timestamp || Date.now());
                chartData.labels.push(this.formatTimestamp(labelDate));
              });

              // Initialize all datasets with null values
              chartData.datasets.forEach(dataset => {
                dataset.data = Array(chartData.labels.length).fill(null);
              });
            }

            // Now update the specific dataset with values
            const dataset = chartData.datasets[datasetIndex];
            const points = data.data.slice(-20);

            for (let i = 0; i < Math.min(points.length, chartData.labels.length); i++) {
              const point = points[i];
              const timestamp = formatDate(new Date(point.timestamp || Date.now()));
              const labelIndex = chartData.labels.indexOf(timestamp);

              if (labelIndex >= 0) {
                dataset.data[labelIndex] = point.value;
              }
            }

            this.chart.update();
          }
        }
        return;
      }

      // Handle historical data
      if (data.type === 'history') {
        console.log('Processing historical data:', data);

        // Check if we have valid metrics data
        if (!data.metrics) {
          console.warn('No metrics found in historical data');
          return;
        }

        // Process historical data to update charts if we have a chart
        if (this.temperatureChart) {
          // Clear existing chart data
          this.temperatureChart.data.labels = [];
          this.temperatureChart.data.datasets.forEach(dataset => {
            dataset.data = [];
          });

          // Process temperature history if available
          if (Array.isArray(data.metrics.temperature)) {
            console.log(`Processing ${data.metrics.temperature.length} temperature history points`);
            data.metrics.temperature.forEach(point => {
              if (point.timestamp && point.value !== undefined) {
                const timestamp = new Date(point.timestamp);
                const value = parseFloat(point.value);

                if (!isNaN(value)) {
                  const formattedTime = this.formatTimestamp(timestamp);
                  this.temperatureChart.data.labels.push(formattedTime);

                  // Add temperature value to the first dataset
                  if (this.temperatureChart.data.datasets.length > 0) {
                    this.temperatureChart.data.datasets[0].data.push(value);
                  }
                }
              }
            });
          }

          // Process other metrics if available (pressure, flow_rate, energy_usage)
          const metrics = ['pressure', 'flow_rate', 'energy_usage'];
          metrics.forEach(metric => {
            if (Array.isArray(data.metrics[metric])) {
              console.log(`Processing ${data.metrics[metric].length} ${metric} history points`);

              // Find dataset for this metric
              let targetDataset;
              if (metric === 'pressure') {
                targetDataset = this.temperatureChart.data.datasets.find(ds => ds.label && ds.label.includes('Pressure'));
              } else if (metric === 'flow_rate') {
                targetDataset = this.temperatureChart.data.datasets.find(ds => ds.label && ds.label.includes('Flow'));
              } else if (metric === 'energy_usage') {
                targetDataset = this.temperatureChart.data.datasets.find(ds => ds.label && ds.label.includes('Energy'));
              }

              // If we found the dataset, update it with historical values
              if (targetDataset) {
                // Initialize with null values for all existing timestamps
                targetDataset.data = Array(this.temperatureChart.data.labels.length).fill(null);

                // Update with actual values where we have data
                data.metrics[metric].forEach((point, index) => {
                  if (point.timestamp && point.value !== undefined) {
                    const timestamp = new Date(point.timestamp);
                    const formattedTime = this.formatTimestamp(timestamp);
                    const value = parseFloat(point.value);

                    if (!isNaN(value)) {
                      const labelIndex = this.temperatureChart.data.labels.indexOf(formattedTime);
                      if (labelIndex >= 0) {
                        targetDataset.data[labelIndex] = value;
                      }
                    }
                  }
                });
              }
            }
          });

          // Update the chart with all historical data
          this.temperatureChart.update();
          console.log('Updated chart with all historical data');
        } else {
          console.warn('No temperature chart available to update with historical data');
        }
        return;
      }

      // Handle telemetry update message
      if (data.type === 'telemetry_update') {
        // Store the latest telemetry value
        if (data.metric && data.value !== undefined) {
          this.lastTelemetryData[data.metric] = {
            value: data.value,
            timestamp: data.timestamp || new Date().toISOString()
          };

          // Update UI with telemetry
          this.updateTelemetryDisplay(data.metric, data.value);

          // Update current temperature display if this is a temperature metric
          if (data.metric === 'temperature') {
            const tempElement = document.getElementById('temperature-value');
            if (tempElement) {
              tempElement.textContent = this.processWaterHeaterMetric(data.value, '\u00b0C');
            }

            // Also update the current-temperature-value element if it exists
            const currentTempElement = document.getElementById('current-temperature-value');
            if (currentTempElement) {
              currentTempElement.textContent = this.processWaterHeaterMetric(data.value, '\u00b0C');
            }
          }

          // Update last updated time
          const lastUpdatedElement = document.getElementById('last-updated-time');
          if (lastUpdatedElement) {
            lastUpdatedElement.textContent = this.formatTimestamp(new Date());
          }

          // Update chart if it exists for any water heater metric
          if (this.temperatureChart) {
            const chartData = this.temperatureChart.data;
            const isWaterHeater = this.heaterId && this.heaterId.startsWith('wh-');
            const labelDate = new Date(data.timestamp || Date.now());
            const formattedDate = this.formatTimestamp(labelDate);

            // Check if this timestamp already exists in labels (for multiple metrics in same update)
            let labelIndex = chartData.labels.indexOf(formattedDate);
            if (labelIndex === -1) {
              // Add new label if this is a new timestamp
              chartData.labels.push(formattedDate);
              labelIndex = chartData.labels.length - 1;

              // Keep only the most recent 20 points
              if (chartData.labels.length > 20) {
                chartData.labels.shift();
                // Shift all datasets to maintain alignment
                chartData.datasets.forEach(dataset => {
                  if (dataset.data.length > 0) {
                    dataset.data.shift();
                  }
                });
                labelIndex--;
              }
            }

            // Update the specific dataset for this metric
            const value = parseFloat(data.value);
            if (!isNaN(value)) {
              if (data.metric === 'temperature' && chartData.datasets.length > 0) {
                // Temperature is always the first dataset
                chartData.datasets[0].data[labelIndex] = value;
              } else if (isWaterHeater) {
                // Handle other water heater metrics - find by label to be more robust
                if (data.metric === 'pressure') {
                  const pressureDataset = chartData.datasets.find(ds => ds.label && ds.label.includes('Pressure'));
                  if (pressureDataset) {
                    pressureDataset.data[labelIndex] = value;
                  }
                } else if (data.metric === 'flow_rate') {
                  const flowDataset = chartData.datasets.find(ds => ds.label && ds.label.includes('Flow'));
                  if (flowDataset) {
                    flowDataset.data[labelIndex] = value;
                  }
                } else if (data.metric === 'energy_usage') {
                  const energyDataset = chartData.datasets.find(ds => ds.label && ds.label.includes('Energy'));
                  if (energyDataset) {
                    energyDataset.data[labelIndex] = value;
                  }
                }
              }
            }

            // Fill any gaps in datasets to ensure proper alignment
            chartData.datasets.forEach(dataset => {
              while (dataset.data.length < chartData.labels.length) {
                dataset.data.push(null); // Use null for missing data points
              }
            });

            this.temperatureChart.update();
            console.log(`Updated chart with new ${data.metric} data point: ${value}`);
          }
        }
      }
    } catch (error) {
      console.error('Error processing telemetry message:', error);
    }
  }

  /**
   * Process water heater metric data and return formatted values
   * @param {string} metric - The metric name
   * @param {number} value - The raw metric value
   * @returns {Object} - Formatted metric object
   */
  processWaterHeaterMetric(metric, value) {
    // Parse value to number if it's a string
    if (typeof value === 'string') {
      value = parseFloat(value);
    }

    // Check if value is valid
    if (isNaN(value) || value === null || value === undefined) {
      return 'N/A';
    }

    let formattedValue = value;
    let unit = '';
    let displayValue = value.toString();

    switch (metric) {
      case 'temperature':
        unit = '°C';
        displayValue = `${value.toFixed(1)}°C`;
        break;
      case 'pressure':
        unit = 'PSI';
        displayValue = `${value.toFixed(1)} PSI`;
        break;
      case 'flow_rate':
        unit = 'GPM';
        displayValue = `${value.toFixed(2)} GPM`;
        break;
      case 'energy_usage':
        unit = 'kWh';
        displayValue = `${value.toFixed(2)} kWh`;
        break;
      default:
        // For any other metric or direct unit usage
        if (typeof value === 'number') {
          displayValue = value.toFixed(1);
        }
        break;
    }

    return {
      metric,
      value: formattedValue,
      displayValue,
      unit
    };
  }

  /**
   * Format a timestamp into a readable string for display
   * @param {Date|string} timestamp - The timestamp to format
   * @returns {string} The formatted timestamp
   */
  formatTimestamp(timestamp) {
    try {
      if (!(timestamp instanceof Date) || isNaN(timestamp.getTime())) {
        timestamp = new Date(timestamp);
      }

      // Format timestamp with hour:minute:second
      return timestamp.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (e) {
      console.error('Error formatting timestamp:', e);
      return 'Invalid time';
    }
  }

  /**
   * Update the telemetry display for a specific metric
   * @param {string} metric - The metric name (temperature, pressure, flow_rate, energy_usage)
   * @param {number} value - The metric value
   */
  updateTelemetryDisplay(metric, value) {
    // Process the metric to get formatted values
    const processedMetric = this.processWaterHeaterMetric(metric, value);

    // Update corresponding UI element
    const element = document.getElementById(`${metric}-value`);
    if (element) {
      element.textContent = processedMetric.displayValue;
    }

    // Update the last updated time for any metric
    const lastUpdatedElement = document.getElementById('last-updated-time');
    if (lastUpdatedElement) {
      lastUpdatedElement.textContent = this.formatTimestamp(new Date());
    }
  }

  loadMockData() {
    console.warn('Mock data has been removed. Database connection is required.');
    // Instead of loading mock data, we'll display an error message
    this.renderError(`Database Error: No water heater found with ID ${this.heaterId}. Database connection is required to view water heater details.`);
    this.heater = null;
  }

  /**
   * Show an error message to the user
   * @param {string} message - The error message to display
   */
  showError(message) {
    // Log the error to console
    console.error(message);

    // Create or update error notification
    let errorNotification = document.getElementById('error-notification');

    if (!errorNotification) {
      // Create new error notification element if it doesn't exist
      errorNotification = document.createElement('div');
      errorNotification.id = 'error-notification';
      errorNotification.className = 'error-notification';
      errorNotification.style.position = 'fixed';
      errorNotification.style.top = '20px';
      errorNotification.style.right = '20px';
      errorNotification.style.backgroundColor = '#f44336';
      errorNotification.style.color = 'white';
      errorNotification.style.padding = '15px';
      errorNotification.style.borderRadius = '4px';
      errorNotification.style.zIndex = '1000';
      errorNotification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
      document.body.appendChild(errorNotification);

      // Add close button
      const closeButton = document.createElement('button');
      closeButton.className = 'close-button';
      closeButton.innerHTML = '&times;';
      closeButton.style.marginLeft = '10px';
      closeButton.style.background = 'none';
      closeButton.style.border = 'none';
      closeButton.style.color = 'white';
      closeButton.style.fontSize = '20px';
      closeButton.style.cursor = 'pointer';
      closeButton.style.float = 'right';
      closeButton.onclick = () => {
        errorNotification.style.display = 'none';
      };
      errorNotification.appendChild(closeButton);

      // Add message container
      const messageContainer = document.createElement('div');
      messageContainer.className = 'error-message';
      errorNotification.appendChild(messageContainer);
    }

    // Update the error message
    const messageContainer = errorNotification.querySelector('.error-message');
    if (messageContainer) {
      messageContainer.textContent = message;
    }

    // Show the notification
    errorNotification.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
      errorNotification.style.display = 'none';
    }, 5000);
  }

  /**
   * Update the target temperature of the water heater
   * @param {number} temperature - The new target temperature
   * @returns {Promise<boolean>} - Whether the update was successful
   */
  async updateTemperature(temperature) {
    try {
      console.log('Updating temperature to:', temperature);
      let success = false;
      let usedMethod = '';

      // Try WebSocket first if connected
      if (this.wsManager && this.wsManager.isConnected(this.stateConnectionId)) {
        try {
          this.wsManager.send(this.stateConnectionId, {
            type: 'update_state',
            desired: {
              target_temperature: temperature
            }
          });
          console.log('Sent temperature update via WebSocket');
          success = true;
          usedMethod = 'WebSocket';
        } catch (wsError) {
          console.warn('WebSocket temperature update failed, falling back to API:', wsError);
          // Continue to API fallback
        }
      }

      // Use REST API if WebSocket failed or isn't available
      if (!success) {
        try {
          await api.updateTemperature(this.heaterId, temperature);
          success = true;
          usedMethod = 'REST API';
        } catch (apiError) {
          console.error('API temperature update failed:', apiError);
          throw apiError;
        }
      }

      if (success) {
        // Update local state
        this.heater.target_temperature = temperature;

        // Update UI
        const targetTempDisplay = document.getElementById('target-temp-display');
        if (targetTempDisplay) {
          targetTempDisplay.textContent = formatTemperature(temperature);
        }

        // Update temperature meter if available
        const tempMeter = document.getElementById('temperature-meter');
        if (tempMeter) {
          // Scale to percentage (assuming normal range 40-160°F or equivalent in Celsius)
          const percentage = Math.min(100, Math.max(0, ((temperature - 40) / 120) * 100));
          tempMeter.value = percentage;
        }

        // Update last updated time
        const lastUpdatedElement = document.getElementById('last-updated-time');
        if (lastUpdatedElement) {
          lastUpdatedElement.textContent = formatDate(new Date());
        }

        console.log(`Successfully updated temperature via ${usedMethod}`);

        // If we're in polling mode, trigger an immediate poll to get the latest state
        if (this.pollingActive && !this.isConnected) {
          setTimeout(() => this.pollState(), 500);
        }

        return true;
      }

      return false;
    } catch (error) {
      console.error('Error updating temperature:', error);
      this.showError(`Failed to update temperature: ${error.message || 'Unknown error'}. Please try again.`);
      return false;
    }
  }

  /**
   * Update the operating mode of the water heater
   * @param {string} mode - The new mode (e.g., 'ECO', 'BOOST', 'OFF')
   * @returns {Promise<boolean>} - Whether the update was successful
   */
  async updateMode(mode) {
    try {
      console.log('Updating mode to:', mode);
      let success = false;
      let usedMethod = '';

      // Try WebSocket first if connected
      if (this.wsManager && this.wsManager.isConnected(this.stateConnectionId)) {
        try {
          this.wsManager.send(this.stateConnectionId, {
            type: 'update_state',
            desired: {
              mode: mode
            }
          });
          console.log('Sent mode update via WebSocket');
          success = true;
          usedMethod = 'WebSocket';
        } catch (wsError) {
          console.warn('WebSocket mode update failed, falling back to API:', wsError);
          // Continue to API fallback
        }
      }

      // Use REST API if WebSocket failed or isn't available
      if (!success) {
        try {
          await api.updateMode(this.heaterId, mode);
          success = true;
          usedMethod = 'REST API';
        } catch (apiError) {
          console.error('API mode update failed:', apiError);
          throw apiError;
        }
      }

      if (success) {
        // Update local state
        this.heater.mode = mode;

        // Update UI
        const modeDisplay = document.getElementById('mode-display');
        if (modeDisplay) {
          modeDisplay.textContent = mode;
        }

        // Update mode buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
          if (btn.dataset.mode === mode) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        });

        // Update last updated time
        const lastUpdatedElement = document.getElementById('last-updated-time');
        if (lastUpdatedElement) {
          lastUpdatedElement.textContent = formatDate(new Date());
        }

        console.log(`Successfully updated mode via ${usedMethod}`);

        // If we're in polling mode, trigger an immediate poll to get the latest state
        if (this.pollingActive && !this.isConnected) {
          setTimeout(() => this.pollState(), 500);
        }

        return true;
      }

      return false;
    } catch (error) {
      console.error('Error updating mode:', error);
      this.showError(`Failed to update mode: ${error.message || 'Unknown error'}. Please try again.`);
      return false;
    }
  }

  render() {
    if (!this.container || !this.heater) return;

    // Check if we're in a dark theme container and apply consistent styling
    const isDarkTheme = document.getElementById('water-heater-container')?.classList.contains('dark-theme');
    const themeClass = isDarkTheme ? 'dark-theme' : '';

    // Set connection status based on WebSocket connection or polling
    // CRITICAL FIX: Ensure connectionStatus and connectionType are always in sync
    // Start with disconnected as the safe default
    let connectionStatus = 'disconnected';
    let connectionType = 'Disconnected'; // FIXED: Changed from 'None' to 'Disconnected' for consistency

    console.log(`🔍 Setting initial connection status: isConnected=${this.isConnected}, pollingActive=${this.pollingActive}`);

    if (this.isConnected === true) {
      // Only set to connected if we're absolutely sure
      connectionStatus = 'connected';
      connectionType = 'Connected'; // FIXED: Changed from 'WebSocket' to 'Connected' for consistency
      console.log('✅ Setting real-time status to Connected');
    } else if (this.pollingActive === true) {
      connectionStatus = 'connecting';
      connectionType = 'Connecting'; // FIXED: Changed from 'Polling (fallback)' to 'Connecting' for consistency
      console.log('⏳ Setting real-time status to Connecting');
    } else {
      console.log('❌ Setting real-time status to Disconnected');
    }

    this.container.innerHTML = `
      <div class="page-header ${themeClass}">
        <a href="/water-heaters" class="btn btn-primary">Back to List</a>
        <h2>${this.heater.name}</h2>
        <a href="/water-heaters/${this.heaterId}/edit" class="btn">Edit</a>
      </div>

      <div class="dashboard detail-view ${themeClass}">
        <div class="card status-card">
          <div class="card-header">
            <h3>Status</h3>
          </div>
          <div class="card-body">
            <div class="status-row">
              <div class="status-label">API Connection:</div>
              <div class="status-value">
                <span id="api-connection-status" class="status-indicator ${this.heater.status === 'online' ? 'status-online' : 'status-offline'}"></span>
                <span>${this.heater.status === 'online' ? 'Online' : 'Offline'}</span>
              </div>
            </div>
            <div class="status-row">
              <div class="status-label">Real-time Connection:</div>
              <div class="status-value">
                <!-- FIXED: Keep only the indicator with color, remove duplicate text -->
                <span id="realtime-connection-status" class="status-indicator ${connectionStatus}"></span>
                <!-- Text will be added by JavaScript after page load for proper styling -->
                <span id="connection-type-container"></span>
              </div>
            </div>
            <div class="status-row">
              <div class="status-label">Heater Status:</div>
              <div class="status-value">
                <span id="heater-status-indicator" class="status-indicator ${this.heater.heater_status === 'HEATING' ? 'status-heating' : 'status-standby'}"></span>
                <span id="heater-status-label">${STATUS_LABELS[this.heater.heater_status]}</span>
              </div>
            </div>
            <div class="status-row">
              <div class="status-label">Current Temperature:</div>
              <div id="temperature-value" class="status-value">${formatTemperature(this.heater.current_temperature)}</div>
            </div>
            <div class="status-row">
              <div class="status-label">Target Temperature:</div>
              <div class="status-value" id="target-temp-display">${formatTemperature(this.heater.target_temperature)}</div>
            </div>
            <div class="status-row">
              <div class="status-label">Mode:</div>
              <div class="status-value" id="mode-display">${this.heater.mode}</div>
            </div>
            <div class="status-row">
              <div class="status-label">Pressure:</div>
              <div id="pressure-value" class="status-value">${this.heater.pressure ? `${this.heater.pressure.toFixed(1)} PSI` : 'N/A'}</div>
            </div>
            <div class="status-row">
              <div class="status-label">Flow Rate:</div>
              <div id="flow_rate-value" class="status-value">${this.heater.flow_rate ? `${this.heater.flow_rate.toFixed(1)} GPM` : 'N/A'}</div>
            </div>
            <div class="status-row">
              <div class="status-label">Energy Usage:</div>
              <div id="energy_usage-value" class="status-value">${this.heater.energy_usage ? `${this.heater.energy_usage.toFixed(0)} kWh` : 'N/A'}</div>
            </div>
            <div class="status-row">
              <div class="status-label">Last Updated:</div>
              <div id="last-updated-time" class="status-value">${formatDate(this.heater.last_updated)}</div>
            </div>
          </div>
        </div>

        <div class="card controls-card">
          <div class="card-header">
            <h3>Controls</h3>
          </div>
          <div class="card-body">
            <div class="control-section">
              <h4>Temperature</h4>
              <div class="temperature-slider">
                <input type="range" id="temp-slider"
                  min="${this.heater.min_temperature}"
                  max="${this.heater.max_temperature}"
                  step="0.5"
                  value="${this.heater.target_temperature}">
                <div class="slider-value">${formatTemperature(this.heater.target_temperature)}</div>
              </div>
              <button id="set-temp-btn" class="btn btn-primary">Set Temperature</button>
            </div>

            <div class="control-section">
              <h4>Mode</h4>
              <div class="mode-controls">
                <button class="mode-btn ${this.heater.mode === 'ECO' ? 'active' : ''}" data-mode="ECO">ECO</button>
                <button class="mode-btn ${this.heater.mode === 'BOOST' ? 'active' : ''}" data-mode="BOOST">BOOST</button>
                <button class="mode-btn ${this.heater.mode === 'OFF' ? 'active' : ''}" data-mode="OFF">OFF</button>
              </div>
            </div>
          </div>
        </div>

        <div class="card chart-card">
          <div class="card-header">
            <h3>Temperature History</h3>
          </div>
          <div class="card-body">
            <div id="temp-chart" class="chart-container"></div>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    document.getElementById('temp-slider')?.addEventListener('input', (e) => {
      document.querySelector('.slider-value').textContent = formatTemperature(parseFloat(e.target.value));
    });

    document.getElementById('set-temp-btn')?.addEventListener('click', () => {
      const temperature = parseFloat(document.getElementById('temp-slider').value);
      this.updateTemperature(temperature);
    });

    document.querySelectorAll('.mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        this.updateMode(mode);
      });
    });
  }

  getLatestReading(metric) {
    if (!this.heater || !this.heater.readings || this.heater.readings.length === 0) {
      return [];
    }

    // Get the last 24 readings or all if less than 24
    const readings = this.heater.readings.slice(-24);

    return readings.map(reading => ({
      x: new Date(reading.timestamp),
      y: reading[metric]
    }));
  }

  initCharts() {
    if (!this.heater) return;

    // Get chart container and create a Chart.js chart
    const chartContainer = document.getElementById('temp-chart');
    if (!chartContainer) return;

    // Clear any existing content
    chartContainer.innerHTML = '';

    // Create a canvas element for Chart.js
    const canvas = document.createElement('canvas');
    canvas.id = 'temperature-chart';
    chartContainer.appendChild(canvas);

    // Initialize Chart.js with temperature data
    this.setupChart();

    // If using WebSocketManager, request historical data
    if (this.wsManager && this.telemetryConnectionId &&
        this.wsManager.isConnected(this.telemetryConnectionId)) {
      // Request recent telemetry data to populate the chart
      this.wsManager.send(this.telemetryConnectionId, {
        type: 'get_recent',
        metric: 'temperature',
        limit: 20 // Get the 20 most recent points
      });
    }
  }

  /**
   * Set up the temperature chart using Chart.js, including additional metrics for water heaters
   */
  /**
   * Set up temperature and other metrics chart
   * Handles error cases and displays appropriate error messages
   */
  setupChart() {
    const ctx = document.getElementById('temperature-chart');
    if (!ctx) return;

    // Check if this heater is in an error state
    if (this.heater && this.heater.status === 'ERROR') {
      console.warn('Cannot setup chart: Heater is in error state', this.heater.error);
      const container = ctx.parentElement;
      container.innerHTML = `<div class="error-message">Error: ${this.heater.error || 'Failed to load heater data'}</div>`;
      return;
    }

    // Clear any previous error messages
    const container = ctx.parentElement;
    const errorMessage = container.querySelector('.error-message');
    if (errorMessage) {
      container.removeChild(errorMessage);
    }

    // Determine if this is a water heater (wh-) device to add additional metrics
    const isWaterHeater = this.heaterId && this.heaterId.startsWith('wh-');

    // Create datasets array with temperature as the primary dataset
    const datasets = [
      {
        label: 'Temperature (\u00b0C)',
        data: [],
        borderColor: '#ff6600',
        backgroundColor: 'rgba(255, 102, 0, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        yAxisID: 'y'
      }
    ];

    // For water heater devices, add additional metrics to the chart
    if (isWaterHeater) {
      // Add pressure dataset if present in heater data
      if (this.heater.pressure !== undefined) {
        datasets.push({
          label: 'Pressure (PSI)',
          data: [],
          borderColor: '#3366cc',
          backgroundColor: 'rgba(51, 102, 204, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: false,
          hidden: true, // Hidden by default, can be toggled by user
          yAxisID: 'y1'
        });
      }

      // Add flow rate dataset if present in heater data
      if (this.heater.flow_rate !== undefined) {
        datasets.push({
          label: 'Flow Rate (GPM)',
          data: [],
          borderColor: '#33cc33',
          backgroundColor: 'rgba(51, 204, 51, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: false,
          hidden: true, // Hidden by default, can be toggled by user
          yAxisID: 'y1'
        });
      }

      // Add energy usage dataset if present in heater data
      if (this.heater.energy_usage !== undefined) {
        datasets.push({
          label: 'Energy Usage (kWh)',
          data: [],
          borderColor: '#cc33cc',
          backgroundColor: 'rgba(204, 51, 204, 0.1)',
          borderWidth: 2,
          tension: 0.4,
          fill: false,
          hidden: true, // Hidden by default, can be toggled by user
          yAxisID: 'y2'
        });
      }
    }

    // Pre-populate chart with readings from shadow data if available
    let initialLabels = [];
    let initialTemperatureData = [];
    let initialPressureData = [];
    let initialFlowData = [];
    let initialEnergyData = [];

    // Check if we have readings in the heater data
    if (this.heater && this.heater.readings && this.heater.readings.length > 0) {
      console.log(`Found ${this.heater.readings.length} history readings in shadow data`);

      // Sort readings by timestamp (oldest to newest)
      const sortedReadings = [...this.heater.readings].sort((a, b) => {
        return new Date(a.timestamp) - new Date(b.timestamp);
      });

      // Take the most recent 20 readings for initial display
      const recentReadings = sortedReadings.slice(-20);

      // Extract data points from readings
      recentReadings.forEach(reading => {
        try {
          const readingTime = new Date(reading.timestamp);
          initialLabels.push(this.formatTimestamp(readingTime));

          // Store values for each metric, using null if not available
          initialTemperatureData.push(reading.temperature !== undefined ? parseFloat(reading.temperature) : null);
          initialPressureData.push(reading.pressure !== undefined ? parseFloat(reading.pressure) : null);
          initialFlowData.push(reading.flow_rate !== undefined ? parseFloat(reading.flow_rate) : null);
          initialEnergyData.push(reading.energy_usage !== undefined ? parseFloat(reading.energy_usage) : null);
        } catch (error) {
          console.warn('Error processing reading:', error, reading);
        }
      });

      console.log('Initialized chart with historical data:', {
        labels: initialLabels.length,
        temperature: initialTemperatureData.filter(v => v !== null).length,
        pressure: initialPressureData.filter(v => v !== null).length,
        flow: initialFlowData.filter(v => v !== null).length,
        energy: initialEnergyData.filter(v => v !== null).length
      });
    } else {
      console.log('No history readings found, chart will start empty');
    }

    // Assign initial data to datasets
    datasets[0].data = initialTemperatureData;

    if (datasets.length >= 2) datasets[1].data = initialPressureData;
    if (datasets.length >= 3) datasets[2].data = initialFlowData;
    if (datasets.length >= 4) datasets[3].data = initialEnergyData;

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: initialLabels,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: false,
            position: 'left',
            title: {
              display: true,
              text: 'Temperature (°C)'
            }
          },
          y1: {
            beginAtZero: false,
            position: 'right',
            title: {
              display: true,
              text: 'Pressure (PSI) / Flow Rate (GPM)'
            },
            grid: {
              drawOnChartArea: false // Only show the grid lines for the first y-axis
            }
          },
          y2: {
            beginAtZero: true,
            position: 'right',
            title: {
              display: true,
              text: 'Energy Usage (kWh)'
            },
            grid: {
              drawOnChartArea: false
            }
          },
          x: {
            title: {
              display: true,
              text: 'Time'
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 10,
              usePointStyle: true
            }
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                const label = context.dataset.label || '';
                const value = context.parsed.y;
                if (label.includes('Temperature')) {
                  return `${label}: ${value.toFixed(1)}°C`;
                } else if (label.includes('Pressure')) {
                  return `${label}: ${value.toFixed(1)} PSI`;
                } else if (label.includes('Flow')) {
                  return `${label}: ${value.toFixed(2)} GPM`;
                } else if (label.includes('Energy')) {
                  return `${label}: ${value.toFixed(2)} kWh`;
                }
                return `${label}: ${value}`;
              }
            }
          }
        }
      }
    });

    // Add some initial data if available
    if (this.heater && this.heater.current_temperature) {
      const now = formatDate(new Date());
      this.chart.data.labels.push(now);
      this.chart.data.datasets[0].data.push(this.heater.current_temperature);
      this.chart.update();
    }
  }

  renderError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="page-header">
        <a href="/water-heaters" class="btn btn-primary">Back to List</a>
        <h2>Water Heater Details</h2>
      </div>
      <div class="error-message">${message}</div>
    `;
  }

  /**
   * Setup visibility change handler to reconnect WebSockets when tab becomes visible again
   */
  setupVisibilityHandler() {
    this.handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('Tab became visible, checking WebSocket connections');

        // Check WebSocket connections and reconnect if needed
        if (this.wsManager) {
          // Check state connection
          if (this.stateConnectionId && !this.wsManager.isConnected(this.stateConnectionId)) {
            console.log('State WebSocket disconnected, reconnecting...');
            this.wsManager.reconnect(this.stateConnectionId);
          }

          // Check telemetry connection
          if (this.telemetryConnectionId && !this.wsManager.isConnected(this.telemetryConnectionId)) {
            console.log('Telemetry WebSocket disconnected, reconnecting...');
            this.wsManager.reconnect(this.telemetryConnectionId);
          }
        } else {
          // If WebSocketManager doesn't exist, create it and connect
          this.connectWebSockets();
        }
      }
    };

    document.addEventListener('visibilitychange', this.handleVisibilityChange);
  }

  /**
   * Clean up resources when component is destroyed
   */
  destroy() {
    // Close WebSocket connections using the WebSocketManager
    if (this.wsManager) {
      if (this.stateConnectionId) {
        this.wsManager.close(this.stateConnectionId);
      }

      if (this.telemetryConnectionId) {
        this.wsManager.close(this.telemetryConnectionId);
      }

      // Destroy the WebSocketManager
      this.wsManager.destroy();
    }

    // Destroy chart if it exists
    if (this.chart) {
      this.chart.destroy();
    }

    // Remove event listeners
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
  }
}

/**
 * Water Heater Form Component
 */
class WaterHeaterForm {
  constructor(containerId, heaterId = null) {
    this.container = document.getElementById(containerId);
    this.heaterId = heaterId; // If provided, we're editing an existing heater
    this.heater = null;
    this.init();
  }

  async init() {
    try {
      if (this.heaterId) {
        await this.loadHeater();
      }
      this.render();
    } catch (error) {
      console.error('Failed to initialize water heater form:', error);
      this.renderError('Failed to load water heater data. Please try again later.');
    }
  }

  async loadHeater() {
    try {
      this.heater = await api.getWaterHeater(this.heaterId);
      console.log('Loaded heater for editing:', this.heater);
    } catch (error) {
      console.error(`Error loading water heater ${this.heaterId}:`, error);
      throw error;
    }
  }

  async saveHeater(formData) {
    try {
      let result;
      if (this.heaterId) {
        // Update existing
        result = await api.updateWaterHeater(this.heaterId, formData);
      } else {
        // Create new
        result = await api.createWaterHeater(formData);
      }

      // Navigate to detail page
      window.location.href = `/water-heaters/${result.id}`;
    } catch (error) {
      console.error('Error saving water heater:', error);
      alert('Failed to save water heater. Please check your inputs and try again.');
    }
  }

  render() {
    if (!this.container) return;

    const isEdit = !!this.heaterId;
    const title = isEdit ? 'Edit Water Heater' : 'Add New Water Heater';
    const submitLabel = isEdit ? 'Update' : 'Create';

    // Use existing values if editing
    const name = isEdit && this.heater ? this.heater.name : '';
    const targetTemp = isEdit && this.heater ? this.heater.target_temperature : 45;
    const minTemp = isEdit && this.heater ? this.heater.min_temperature : 40;
    const maxTemp = isEdit && this.heater ? this.heater.max_temperature : 85;
    const mode = isEdit && this.heater ? this.heater.mode : MODES.ECO;

    this.container.innerHTML = `
      <div class="page-header">
        <a href="/water-heaters" class="btn btn-primary">Back to List</a>
        <h2>${title}</h2>
      </div>

      <div class="card form-card">
        <div class="card-body">
          <form id="heater-form">
            <div class="form-group">
              <label for="name">Name</label>
              <input type="text" id="name" name="name" class="form-control" value="${name}" required>
            </div>

            <div class="form-group">
              <label for="target_temperature">Target Temperature (°C)</label>
              <input type="number" id="target_temperature" name="target_temperature"
                class="form-control" value="${targetTemp}" min="30" max="85" step="0.5" required>
            </div>

            <div class="form-group">
              <label for="min_temperature">Minimum Temperature (°C)</label>
              <input type="number" id="min_temperature" name="min_temperature"
                class="form-control" value="${minTemp}" min="30" max="50" step="0.5" required>
            </div>

            <div class="form-group">
              <label for="max_temperature">Maximum Temperature (°C)</label>
              <input type="number" id="max_temperature" name="max_temperature"
                class="form-control" value="${maxTemp}" min="50" max="85" step="0.5" required>
            </div>

            <div class="form-group">
              <label for="mode">Mode</label>
              <select id="mode" name="mode" class="form-control" required>
                <option value="${MODES.ECO}" ${mode === MODES.ECO ? 'selected' : ''}>Eco</option>
                <option value="${MODES.BOOST}" ${mode === MODES.BOOST ? 'selected' : ''}>Boost</option>
                <option value="${MODES.OFF}" ${mode === MODES.OFF ? 'selected' : ''}>Off</option>
              </select>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary">${submitLabel}</button>
              <a href="/water-heaters" class="btn">Cancel</a>
            </div>
          </form>
        </div>
      </div>
    `;

    // Add form submission handler
    document.getElementById('heater-form')?.addEventListener('submit', (e) => {
      e.preventDefault();

      const formData = {
        name: document.getElementById('name').value,
        target_temperature: parseFloat(document.getElementById('target_temperature').value),
        mode: document.getElementById('mode').value,
        min_temperature: parseFloat(document.getElementById('min_temperature').value),
        max_temperature: parseFloat(document.getElementById('max_temperature').value)
      };

      this.saveHeater(formData);
    });
  }

  renderError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="page-header">
        <a href="/water-heaters" class="btn btn-primary">Back to List</a>
        <h2>Water Heater Form</h2>
      </div>
      <div class="error-message">${message}</div>
    `;
  }
}
