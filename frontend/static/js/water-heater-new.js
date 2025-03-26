/**
 * Water Heater UI Components
 */

// Constants
const MODES = {
  ECO: 'ECO',
  BOOST: 'BOOST',
  OFF: 'OFF'
};

const STATUS_LABELS = {
  HEATING: 'Heating',
  STANDBY: 'Standby'
};

// Helper functions
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString();
}

function formatTemperature(temp) {
  return temp ? `${temp.toFixed(1)}°C` : 'N/A';
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
      console.log('Fetching water heaters from API...');
      
      // If the regular API call fails, try a direct fetch as a fallback
      let response;
      try {
        response = await api.getWaterHeaters();
        console.log('API response from client:', response);
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch:', apiError);
        
        // Direct fetch fallback
        const apiHost = window.location.hostname;
        const apiUrl = `http://${apiHost}:8006/api/water-heaters/`;
        
        const directResponse = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          },
          mode: 'cors'
        });
        
        if (!directResponse.ok) {
          throw new Error(`Direct API fetch failed: ${directResponse.status} ${directResponse.statusText}`);
        }
        
        response = await directResponse.json();
        console.log('Direct fetch response:', response);
      }
      
      // Validate the response format
      if (response && Array.isArray(response)) {
        // Clean/normalize data - filter out any invalid entries
        this.heaters = response.filter(heater => {
          const isValid = heater && typeof heater === 'object' && heater.id;
          if (!isValid) {
            console.warn('Filtering out invalid heater object:', heater);
          }
          return isValid;
        }).map(heater => this.normalizeHeaterData(heater));
        
        console.log('Processed heaters:', this.heaters);
      } else {
        console.error('Invalid API response format, expected array but got:', typeof response);
        this.heaters = [];
        throw new Error('Invalid API response format');
      }
    } catch (error) {
      console.error('Error loading water heaters:', error);
      console.error('Error details:', error.message, error.stack);
      
      // Try to load some mock data as a last resort
      this.loadMockData();
      throw error;
    }
  }

  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="page-header">
        <h2>Water Heaters</h2>
        <a href="/water-heaters/new" class="btn btn-primary">Add New</a>
      </div>
      
      <div class="dashboard">
        ${this.heaters.map(heater => this.renderHeaterCard(heater)).join('')}
      </div>
    `;

    // Add click events for each heater card
    this.heaters.forEach(heater => {
      document.getElementById(`heater-${heater.id}`)?.addEventListener('click', () => {
        window.location.href = `/water-heaters/${heater.id}`;
      });
    });
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
   * Load mock data as a fallback when API fails
   */
  loadMockData() {
    console.log('Loading mock water heater data as fallback');
    this.heaters = [
      {
        id: 'mock-wh-1',
        name: 'Demo Water Heater 1',
        status: 'ONLINE',
        heater_status: 'HEATING',
        mode: 'ECO',
        current_temperature: 65,
        target_temperature: 70,
        min_temperature: 40,
        max_temperature: 85,
        location: 'Kitchen',
        last_seen: new Date().toISOString()
      },
      {
        id: 'mock-wh-2',
        name: 'Demo Water Heater 2',
        status: 'ONLINE',
        heater_status: 'STANDBY',
        mode: 'BOOST',
        current_temperature: 72,
        target_temperature: 72,
        min_temperature: 40,
        max_temperature: 85,
        location: 'Bathroom',
        last_seen: new Date().toISOString()
      }
    ].map(heater => this.normalizeHeaterData(heater));
  }

  renderHeaterList() {
    if (!this.heaters || this.heaters.length === 0) {
      return '<div class="empty-state">No water heaters found. Click "Add New" to create one.</div>';
    }

    return `
      <div class="dashboard">
        ${this.heaters.map(heater => this.renderHeaterCard(heater)).join('')}
      </div>
    `;
  }

  normalizeHeaterData(heater) {
    // Create a copy with all required fields properly initialized
    return {
      id: heater.id || `temp-${Math.random().toString(36).substring(2, 10)}`,
      name: heater.name || 'Unknown Heater',
      model: heater.model || 'Water Heater',
      status: heater.status || 'OFFLINE',
      heater_status: heater.heater_status || 'STANDBY',
      mode: heater.mode || 'ECO',
      current_temperature: heater.current_temperature || 50,
      target_temperature: heater.target_temperature || 55,
      min_temperature: heater.min_temperature || 40,
      max_temperature: heater.max_temperature || 85,
      last_seen: heater.last_seen || new Date().toISOString(),
      last_updated: heater.last_updated || new Date().toISOString(),
      readings: Array.isArray(heater.readings) ? heater.readings : []
    };
  }
  
  renderHeaterCard(heater) {
    if (!heater) {
      console.error('Attempted to render undefined heater');
      return '';
    }
    
    const statusClass = heater.status.toLowerCase() === 'online' ? 'status-online' : 'status-offline';
    const heaterStatusClass = heater.heater_status.toLowerCase() === 'heating' ? 'status-heating' : 'status-standby';
    const modeClass = `mode-${heater.mode}`;
    
    // Calculate the gauge rotation based on temperature
    const minTemp = heater.min_temperature || 40;
    const maxTemp = heater.max_temperature || 85;
    const tempRange = maxTemp - minTemp;
    const currentTempPercent = Math.min(100, Math.max(0, ((heater.current_temperature - minTemp) / tempRange) * 100));
    // Convert percentage to gauge rotation (0% = -120deg, 100% = 120deg)
    const gaugeRotation = -120 + (currentTempPercent * 2.4);
    
    return `
      <div id="heater-${heater.id}" class="card heater-card" style="cursor: pointer;">
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
          <div class="gauge-container">
            <div class="gauge"></div>
            <div class="gauge-mask"></div>
            <div class="gauge-indicator" style="transform: rotate(${gaugeRotation}deg)"></div>
            <div class="gauge-value">${formatTemperature(heater.current_temperature)}</div>
          </div>
          <div class="gauge-label">${heater.name}</div>
          
          <div class="heater-details">
            <div class="target-temp">
              Target: ${formatTemperature(heater.target_temperature)}
            </div>
            <div class="mode-label ${modeClass}">
              ${heater.mode}
            </div>
          </div>
        </div>
      </div>
    `;
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
    this.init();
  }

  async init() {
    try {
      await this.loadHeater();
      this.render();
      this.initCharts();
    } catch (error) {
      console.error('Failed to initialize water heater detail:', error);
      this.renderError('Failed to load water heater details. Please try again later.');
    }
  }

  async loadHeater() {
    try {
      this.heater = await api.getWaterHeater(this.heaterId);
      console.log('Loaded heater:', this.heater);
    } catch (error) {
      console.error(`Error loading water heater ${this.heaterId}:`, error);
      throw error;
    }
  }

  async updateTemperature(temperature) {
    try {
      await api.updateWaterHeater(this.heaterId, { target_temperature: temperature });
      this.heater.target_temperature = temperature;
      document.getElementById('target-temp-display').textContent = formatTemperature(temperature);
    } catch (error) {
      console.error('Error updating temperature:', error);
      alert('Failed to update temperature. Please try again.');
    }
  }

  async updateMode(mode) {
    try {
      await api.updateWaterHeater(this.heaterId, { mode });
      this.heater.mode = mode;
      
      // Update UI
      document.getElementById('mode-display').textContent = mode;
      document.querySelectorAll('.mode-btn').forEach(btn => {
        if (btn.dataset.mode === mode) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    } catch (error) {
      console.error('Error updating mode:', error);
      alert('Failed to update mode. Please try again.');
    }
  }

  render() {
    if (!this.container || !this.heater) return;

    this.container.innerHTML = `
      <div class="page-header">
        <a href="/water-heaters" class="btn btn-primary">Back to List</a>
        <h2>${this.heater.name}</h2>
        <a href="/water-heaters/${this.heaterId}/edit" class="btn">Edit</a>
      </div>
      
      <div class="dashboard detail-view">
        <div class="card status-card">
          <div class="card-header">
            <h3>Status</h3>
          </div>
          <div class="card-body">
            <div class="status-row">
              <div class="status-label">Connection:</div>
              <div class="status-value">
                <span class="status-indicator ${this.heater.status === 'online' ? 'status-online' : 'status-offline'}"></span>
                ${this.heater.status === 'online' ? 'Online' : 'Offline'}
              </div>
            </div>
            <div class="status-row">
              <div class="status-label">Heater Status:</div>
              <div class="status-value">
                <span class="status-indicator ${this.heater.heater_status === 'HEATING' ? 'status-heating' : 'status-standby'}"></span>
                ${STATUS_LABELS[this.heater.heater_status]}
              </div>
            </div>
            <div class="status-row">
              <div class="status-label">Current Temperature:</div>
              <div class="status-value">${formatTemperature(this.heater.current_temperature)}</div>
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
              <div class="status-label">Last Updated:</div>
              <div class="status-value">${formatDate(this.heater.last_updated)}</div>
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

    // Simple placeholder chart using a canvas
    const chartContainer = document.getElementById('temp-chart');
    if (!chartContainer) return;

    // Create a canvas element
    const canvas = document.createElement('canvas');
    canvas.width = chartContainer.clientWidth;
    canvas.height = 200;
    chartContainer.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    
    // Draw a simple line chart
    ctx.strokeStyle = '#3a86ff';
    ctx.lineWidth = 2;
    ctx.beginPath();

    // Generate some fake data points
    const currentTemp = this.heater.current_temperature || 55;
    const points = [];
    for (let i = 0; i < 24; i++) {
      // Random fluctuation around current temperature
      points.push(currentTemp + (Math.random() * 10 - 5));
    }

    // Scale points to fit canvas
    const min = Math.min(...points) - 5;
    const max = Math.max(...points) + 5;
    const range = max - min;
    
    // Draw the line
    points.forEach((point, index) => {
      const x = (index / (points.length - 1)) * canvas.width;
      const y = canvas.height - ((point - min) / range) * canvas.height * 0.8;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Draw axes
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height - 20);
    ctx.lineTo(canvas.width, canvas.height - 20);
    ctx.stroke();
    
    // Draw axis labels
    ctx.fillStyle = '#b0b0b0';
    ctx.font = '10px Arial';
    ctx.fillText('Past 24 hours', canvas.width / 2 - 30, canvas.height - 5);
    ctx.fillText(`${min.toFixed(0)}°C`, 5, canvas.height - 25);
    ctx.fillText(`${max.toFixed(0)}°C`, 5, 15);
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
