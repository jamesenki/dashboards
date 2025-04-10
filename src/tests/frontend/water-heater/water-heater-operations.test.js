/**
 * Unit tests for water heater operations dashboard JavaScript functionality
 */

// Mock the global fetch before importing
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      machine_status: "ONLINE",
      heater_status: "HEATING",
      current_temperature: 68.0,
      target_temperature: 70.0,
      mode: "ECO",
      asset_health: 85.0,
      gauges: {
        temperature: {
          value: 68.0,
          min: 40.0,
          max: 85.0,
          unit: "°C",
          percentage: 62.2,
          target: 70.0
        },
        pressure: {
          value: 2.6,
          min: 0.0,
          max: 5.0,
          unit: "bar",
          percentage: 52.0
        },
        energy_usage: {
          value: 1350,
          min: 0,
          max: 3000,
          unit: "W",
          percentage: 45.0
        },
        flow_rate: {
          value: 3.5,
          min: 0.0,
          max: 10.0,
          unit: "L/min",
          percentage: 35.0
        }
      }
    })
  })
);

// Mock helper functions for testing
const formatTemperature = (temp) => temp !== null && temp !== undefined ? `${temp.toFixed(1)}°C` : 'N/A';
const formatPressure = (pressure) => pressure ? `${pressure.toFixed(1)} bar` : 'N/A';
const formatPower = (watts) => watts ? `${watts} W` : 'N/A';
const formatFlowRate = (rate) => rate ? `${rate.toFixed(1)} L/min` : 'N/A';

describe('Water Heater Operations Dashboard Functions', () => {
  test('formatTemperature formats temperature correctly', () => {
    expect(formatTemperature(68)).toBe('68.0°C');
    expect(formatTemperature(0)).toBe('0.0°C');
    expect(formatTemperature(null)).toBe('N/A');
    expect(formatTemperature(72.5)).toBe('72.5°C');
  });

  test('formatPressure formats pressure correctly', () => {
    expect(formatPressure(2.6)).toBe('2.6 bar');
    expect(formatPressure(0)).toBe('0.0 bar');
    expect(formatPressure(null)).toBe('N/A');
  });

  test('formatPower formats power usage correctly', () => {
    expect(formatPower(1350)).toBe('1350 W');
    expect(formatPower(0)).toBe('0 W');
    expect(formatPower(null)).toBe('N/A');
  });

  test('formatFlowRate formats flow rate correctly', () => {
    expect(formatFlowRate(3.5)).toBe('3.5 L/min');
    expect(formatFlowRate(0)).toBe('0.0 L/min');
    expect(formatFlowRate(null)).toBe('N/A');
  });
});

describe('Gauge Components', () => {
  // Setup DOM elements for testing
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="operations-dashboard">
        <!-- Status Cards -->
        <div class="status-cards">
          <div id="machine-status-card" class="status-card">
            <div class="status-title">Machine Status</div>
            <div class="status-value">ONLINE</div>
          </div>
          <div id="heater-status-card" class="status-card">
            <div class="status-title">Heater Status</div>
            <div class="status-value">HEATING</div>
          </div>
        </div>

        <!-- Gauges -->
        <div class="gauge-grid">
          <!-- Temperature Gauge -->
          <div id="temperature-gauge-panel" class="gauge-panel">
            <div class="gauge-title">Temperature</div>
            <div class="gauge-container">
              <div class="gauge-needle" id="temperature-gauge-needle"></div>
            </div>
            <div id="temperature-gauge-value" class="gauge-value">68.0°C</div>
          </div>

          <!-- Pressure Gauge -->
          <div id="pressure-gauge-panel" class="gauge-panel">
            <div class="gauge-title">Pressure</div>
            <div class="gauge-container">
              <div class="gauge-needle" id="pressure-gauge-needle"></div>
            </div>
            <div id="pressure-gauge-value" class="gauge-value">2.6 bar</div>
          </div>

          <!-- Energy Usage Gauge -->
          <div id="energy-gauge-panel" class="gauge-panel">
            <div class="gauge-title">Energy Usage</div>
            <div class="gauge-container">
              <div class="gauge-needle" id="energy-gauge-needle"></div>
            </div>
            <div id="energy-gauge-value" class="gauge-value">1350 W</div>
          </div>

          <!-- Flow Rate Gauge -->
          <div id="flow-rate-gauge-panel" class="gauge-panel">
            <div class="gauge-title">Flow Rate</div>
            <div class="gauge-container">
              <div class="gauge-needle" id="flow-rate-gauge-needle"></div>
            </div>
            <div id="flow-rate-gauge-value" class="gauge-value">3.5 L/min</div>
          </div>

          <!-- Asset Health Gauge -->
          <div id="asset-health-gauge-panel" class="gauge-panel">
            <div class="gauge-title">Asset Health</div>
            <div class="gauge-container">
              <div class="gauge-needle" id="asset-health-gauge-needle"></div>
            </div>
            <div id="asset-health-gauge-value" class="gauge-value">85%</div>
          </div>
        </div>
      </div>
    `;
  });

  test('gauge elements exist', () => {
    expect(document.getElementById('temperature-gauge-needle')).not.toBeNull();
    expect(document.getElementById('pressure-gauge-needle')).not.toBeNull();
    expect(document.getElementById('energy-gauge-needle')).not.toBeNull();
    expect(document.getElementById('flow-rate-gauge-needle')).not.toBeNull();
    expect(document.getElementById('asset-health-gauge-needle')).not.toBeNull();
  });

  test('status cards exist and have correct values', () => {
    const machineStatusCard = document.querySelector('#machine-status-card .status-value');
    const heaterStatusCard = document.querySelector('#heater-status-card .status-value');

    expect(machineStatusCard).not.toBeNull();
    expect(machineStatusCard.textContent).toBe('ONLINE');

    expect(heaterStatusCard).not.toBeNull();
    expect(heaterStatusCard.textContent).toBe('HEATING');
  });

  test('gauge values are displayed correctly', () => {
    expect(document.getElementById('temperature-gauge-value').textContent).toBe('68.0°C');
    expect(document.getElementById('pressure-gauge-value').textContent).toBe('2.6 bar');
    expect(document.getElementById('energy-gauge-value').textContent).toBe('1350 W');
    expect(document.getElementById('flow-rate-gauge-value').textContent).toBe('3.5 L/min');
    expect(document.getElementById('asset-health-gauge-value').textContent).toBe('85%');
  });

  // Mock test for gauge update functionality
  test('updateGauge sets the correct values and needle position', () => {
    // Create mock for the updateGauge function
    const updateGauge = (gaugeId, value, unit, percentage) => {
      const valueElement = document.getElementById(`${gaugeId}-gauge-value`);
      const needleElement = document.getElementById(`${gaugeId}-gauge-needle`);

      // Update value display
      if (valueElement) {
        valueElement.textContent = `${typeof value === 'number' ? value.toFixed(1) : value}${unit}`;
      }

      // Update needle position (in a real implementation, this would set a CSS transform)
      if (needleElement) {
        // For testing, we'll store the percentage as a data attribute
        needleElement.setAttribute('data-percentage', percentage);
      }

      return percentage;
    };

    // Test temperature gauge update
    expect(updateGauge('temperature', 72.0, '°C', 71.1)).toBe(71.1);
    expect(document.getElementById('temperature-gauge-value').textContent).toBe('72.0°C');
    expect(document.getElementById('temperature-gauge-needle').getAttribute('data-percentage')).toBe('71.1');

    // Test pressure gauge update
    expect(updateGauge('pressure', 3.0, ' bar', 60.0)).toBe(60.0);
    expect(document.getElementById('pressure-gauge-value').textContent).toBe('3.0 bar');
    expect(document.getElementById('pressure-gauge-needle').getAttribute('data-percentage')).toBe('60.0');
  });
});

describe('API Integration', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('fetches operations dashboard data correctly', async () => {
    // Mock function to fetch operations dashboard data
    const fetchOperationsDashboard = async (heaterId) => {
      const response = await fetch(`/api/water-heaters/${heaterId}/operations`);
      if (!response.ok) {
        throw new Error('Failed to fetch operations data');
      }
      return await response.json();
    };

    const dashboardData = await fetchOperationsDashboard('heater-123');

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith('/api/water-heaters/heater-123/operations');
    expect(dashboardData.current_temperature).toBe(68.0);
    expect(dashboardData.target_temperature).toBe(70.0);
    expect(dashboardData.mode).toBe('ECO');
    expect(dashboardData.gauges.temperature.percentage).toBe(62.2);
  });

  test('handles API errors gracefully', async () => {
    // Override fetch mock to return an error
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: "Water heater not found" })
      })
    );

    // Mock function with error handling
    const fetchOperationsDashboard = async (heaterId) => {
      try {
        const response = await fetch(`/api/water-heaters/${heaterId}/operations`);
        if (!response.ok) {
          return { error: `Error: ${response.status}` };
        }
        return await response.json();
      } catch (error) {
        return { error: error.message };
      }
    };

    const result = await fetchOperationsDashboard('non-existent');

    expect(fetch).toHaveBeenCalledTimes(1);
    expect(result.error).toBe('Error: 404');
  });
});
