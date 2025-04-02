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
      this.render();
    } catch (error) {
      console.error('Failed to initialize water heater list:', error);
      this.renderError('Failed to load water heaters. Please try again later.');
    }
  }

  async loadHeaters() {
    try {
      this.heaters = await api.getWaterHeaters();
      console.log('Loaded heaters:', this.heaters);
    } catch (error) {
      console.error('Error loading water heaters:', error);
      throw error;
    }
  }

  render() {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Water Heaters</h2>
          <button id="add-heater-btn" class="btn btn-primary">Add New</button>
        </div>
        <div class="card-body">
          ${this.renderHeaterList()}
        </div>
      </div>
    `;

    // Add event listeners
    document.getElementById('add-heater-btn')?.addEventListener('click', () => {
      // Navigate to add new heater page or show modal
      window.location.href = '/water-heaters/new';
    });

    // Add click events for each heater card
    this.heaters.forEach(heater => {
      document.getElementById(`heater-${heater.id}`)?.addEventListener('click', () => {
        window.location.href = `/water-heaters/${heater.id}`;
      });
    });
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

  renderHeaterCard(heater) {
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
            ${STATUS_LABELS[heater.heater_status]}
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
            Mode: ${heater.mode}
          </div>
          <div class="last-seen">
            Last seen: ${formatDate(heater.last_seen)}
          </div>
        </div>
      </div>
    `;
  }

  renderError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Water Heaters</h2>
        </div>
        <div class="card-body">
          <div class="error-message">${message}</div>
        </div>
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
    } catch (error) {
      console.error('Error loading water heater:', error);
      throw error;
    }
  }

  async updateTemperature(temperature) {
    try {
      this.heater = await api.updateTemperature(this.heaterId, temperature);
      // Update UI with new data
      document.getElementById('target-temp-value').textContent = formatTemperature(this.heater.target_temperature);
      document.getElementById('temp-slider').value = this.heater.target_temperature;
    } catch (error) {
      console.error('Error updating temperature:', error);
      alert('Failed to update temperature. Please try again.');
    }
  }

  async updateMode(mode) {
    try {
      this.heater = await api.updateMode(this.heaterId, mode);

      // Update UI with new mode
      const modeOptions = document.querySelectorAll('.mode-option');
      modeOptions.forEach(option => {
        option.classList.remove('active');
        if (option.getAttribute('data-mode') === this.heater.mode) {
          option.classList.add('active');
        }
      });

      // Also update heater status display
      const statusIndicator = document.getElementById('heater-status-indicator');
      const statusText = document.getElementById('heater-status-text');

      statusIndicator.className = 'status-indicator';
      statusIndicator.classList.add(
        this.heater.heater_status.toLowerCase() === 'heating' ? 'status-heating' : 'status-standby'
      );
      statusText.textContent = STATUS_LABELS[this.heater.heater_status];
    } catch (error) {
      console.error('Error updating mode:', error);
      alert('Failed to update mode. Please try again.');
    }
  }

  render() {
    if (!this.container || !this.heater) return;

    const statusClass = this.heater.status.toLowerCase() === 'online' ? 'status-online' : 'status-offline';
    const heaterStatusClass = this.heater.heater_status.toLowerCase() === 'heating' ? 'status-heating' : 'status-standby';

    this.container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <div>
            <a href="/water-heaters" class="btn btn-primary">Back to List</a>
            <h2 class="card-title">${this.heater.name}</h2>
          </div>
          <div>
            <span class="status-indicator ${statusClass}"></span>
            ${this.heater.status}
          </div>
        </div>

        <div class="card-body">
          <div class="heater-status">
            <h3>Status:
              <span id="heater-status-indicator" class="status-indicator ${heaterStatusClass}"></span>
              <span id="heater-status-text">${STATUS_LABELS[this.heater.heater_status]}</span>
            </h3>
          </div>

          <div class="temperature-display">
            ${formatTemperature(this.heater.current_temperature)}
          </div>

          <div class="temperature-control">
            <h3>Target Temperature: <span id="target-temp-value">${formatTemperature(this.heater.target_temperature)}</span></h3>
            <div class="slider-container">
              <input type="range" min="${this.heater.min_temperature}" max="${this.heater.max_temperature}"
                value="${this.heater.target_temperature}" class="slider" id="temp-slider" step="0.5">
            </div>
          </div>

          <div class="mode-control">
            <h3>Mode</h3>
            <div class="mode-selector">
              <div class="mode-option ${this.heater.mode === MODES.ECO ? 'active' : ''}" data-mode="${MODES.ECO}">
                Eco
              </div>
              <div class="mode-option ${this.heater.mode === MODES.BOOST ? 'active' : ''}" data-mode="${MODES.BOOST}">
                Boost
              </div>
              <div class="mode-option ${this.heater.mode === MODES.OFF ? 'active' : ''}" data-mode="${MODES.OFF}">
                Off
              </div>
            </div>
          </div>

          <div class="metrics-section">
            <h3>Metrics</h3>
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-label">Flow Rate</div>
                <div class="metric-value">${this.getLatestReading('flow_rate') || 'N/A'} L/min</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Pressure</div>
                <div class="metric-value">${this.getLatestReading('pressure') || 'N/A'} bar</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Energy Usage</div>
                <div class="metric-value">${this.getLatestReading('energy_usage') || 'N/A'} W</div>
              </div>
              <div class="metric-card">
                <div class="metric-label">Last Seen</div>
                <div class="metric-value">${formatDate(this.heater.last_seen)}</div>
              </div>
            </div>
          </div>

          <div class="readings-section">
            <h3>Temperature History</h3>
            <div class="readings-chart" id="temp-chart"></div>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    const tempSlider = document.getElementById('temp-slider');
    if (tempSlider) {
      tempSlider.addEventListener('input', (e) => {
        document.getElementById('target-temp-value').textContent = `${e.target.value}°C`;
      });

      tempSlider.addEventListener('change', (e) => {
        this.updateTemperature(parseFloat(e.target.value));
      });
    }

    const modeOptions = document.querySelectorAll('.mode-option');
    modeOptions.forEach(option => {
      option.addEventListener('click', () => {
        const mode = option.getAttribute('data-mode');
        this.updateMode(mode);
      });
    });
  }

  getLatestReading(metric) {
    if (!this.heater || !this.heater.readings || this.heater.readings.length === 0) {
      return null;
    }

    // Sort readings by timestamp in descending order
    const sortedReadings = [...this.heater.readings].sort((a, b) => {
      return new Date(b.timestamp) - new Date(a.timestamp);
    });

    // Return the value from the latest reading
    return sortedReadings[0][metric];
  }

  initCharts() {
    if (!this.heater || !this.heater.readings || this.heater.readings.length === 0) {
      document.getElementById('temp-chart').innerHTML = '<div class="empty-state">No temperature readings available.</div>';
      return;
    }

    // Sort readings by timestamp
    const sortedReadings = [...this.heater.readings].sort((a, b) => {
      return new Date(a.timestamp) - new Date(b.timestamp);
    });

    // Extract data for chart
    const labels = sortedReadings.map(r => new Date(r.timestamp).toLocaleTimeString());
    const tempData = sortedReadings.map(r => r.temperature);

    // For a simple implementation, we'll use a placeholder message
    // In a real implementation, you would use a library like Chart.js
    document.getElementById('temp-chart').innerHTML =
      `<div class="chart-placeholder">
        Temperature chart would be displayed here.
        Data points: ${tempData.length}
        Latest value: ${tempData[tempData.length - 1].toFixed(1)}°C
      </div>`;
  }

  renderError(message) {
    if (!this.container) return;

    this.container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <a href="/water-heaters" class="btn btn-primary">Back to List</a>
          <h2 class="card-title">Water Heater Details</h2>
        </div>
        <div class="card-body">
          <div class="error-message">${message}</div>
        </div>
      </div>
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
      this.renderError('Failed to load form. Please try again later.');
    }
  }

  async loadHeater() {
    try {
      this.heater = await api.getWaterHeater(this.heaterId);
    } catch (error) {
      console.error('Error loading water heater:', error);
      throw error;
    }
  }

  async saveHeater(formData) {
    try {
      let result;

      if (this.heaterId) {
        // Update existing heater (not implemented in API yet)
        alert('Editing existing heaters is not supported yet.');
        return;
      } else {
        // Create new heater
        result = await api.createWaterHeater(formData);
      }

      // Navigate to the detail page for the created/updated heater
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
    const name = isEdit ? this.heater.name : '';
    const targetTemp = isEdit ? this.heater.target_temperature : 45;
    const minTemp = isEdit ? this.heater.min_temperature : 40;
    const maxTemp = isEdit ? this.heater.max_temperature : 85;
    const mode = isEdit ? this.heater.mode : MODES.ECO;

    this.container.innerHTML = `
      <div class="card">
        <div class="card-header">
          <a href="/water-heaters" class="btn btn-primary">Back to List</a>
          <h2 class="card-title">${title}</h2>
        </div>
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
      <div class="card">
        <div class="card-header">
          <a href="/water-heaters" class="btn btn-primary">Back to List</a>
          <h2 class="card-title">Water Heater Form</h2>
        </div>
        <div class="card-body">
          <div class="error-message">${message}</div>
        </div>
      </div>
    `;
  }
}
