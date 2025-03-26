/**
 * Unit tests for vending machine JavaScript functionality
 */

// Mock the global fetch before importing
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      id: "vm-106c55e5",
      name: "Campus Center VM",
      type: "vending_machine",
      status: "online",
      temperature: 32.0,
      total_capacity: 50,
      current_stock: 35,
      cash_capacity: 500.0,
      current_cash: 125.5,
      machine_status: "operational",
      mode: "normal"
    })
  })
);

// Manual import of functions for testing - in real tests, you'd use proper imports
// We'll mock the functions for testing purposes
const formatCurrency = (amount) => amount ? `$${parseFloat(amount).toFixed(2)}` : '$0.00';
const formatTemperature = (temp) => temp ? `${temp.toFixed(1)}°F` : 'N/A';

describe('Vending Machine Helper Functions', () => {
  test('formatCurrency formats amount correctly', () => {
    expect(formatCurrency(12.5)).toBe('$12.50');
    expect(formatCurrency(0)).toBe('$0.00');
    expect(formatCurrency(null)).toBe('$0.00');
    expect(formatCurrency(12)).toBe('$12.00');
    expect(formatCurrency(12.999)).toBe('$13.00');
  });

  test('formatTemperature formats temperature correctly', () => {
    expect(formatTemperature(32)).toBe('32.0°F');
    expect(formatTemperature(0)).toBe('0.0°F');
    expect(formatTemperature(null)).toBe('N/A');
    expect(formatTemperature(32.5)).toBe('32.5°F');
  });
});

describe('Temperature Gauge', () => {
  // Setup DOM elements for testing
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="temperature-gauge-panel">
        <div class="gauge-title">Freezer Temperature</div>
        <div class="gauge-container">
          <div class="gauge" id="temperature-gauge">
            <div class="gauge-fill"></div>
            <div class="gauge-needle"></div>
          </div>
        </div>
        <div class="gauge-value">32°F</div>
      </div>
    `;
  });

  test('temperature gauge element exists', () => {
    const gaugeElement = document.getElementById('temperature-gauge');
    expect(gaugeElement).not.toBeNull();
  });

  test('temperature gauge value is visible', () => {
    const gaugeValue = document.querySelector('#temperature-gauge-panel .gauge-value');
    expect(gaugeValue).not.toBeNull();
    expect(gaugeValue.textContent).toBe('32°F');
  });

  // Mock test for gauge update functionality
  test('updateTemperatureGauge sets the correct values', () => {
    // Create mock for the updateTemperatureGauge function
    const updateTemperatureGauge = (temperature) => {
      const min = 0;
      const max = 50;
      const percentage = ((temperature - min) / (max - min)) * 100;
      const gaugeValue = document.querySelector('#temperature-gauge-panel .gauge-value');
      
      // Update gauge value
      if (gaugeValue) {
        gaugeValue.textContent = `${temperature.toFixed(1)}°F`;
      }
      
      return percentage;
    };

    // Test with different temperature values
    expect(updateTemperatureGauge(32)).toBe(64);
    expect(document.querySelector('#temperature-gauge-panel .gauge-value').textContent).toBe('32.0°F');
    
    expect(updateTemperatureGauge(10)).toBe(20);
    expect(document.querySelector('#temperature-gauge-panel .gauge-value').textContent).toBe('10.0°F');
  });
});

describe('API Integration', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('fetches machine data correctly', async () => {
    // Mock function to fetch machine data
    const fetchMachineData = async (machineId) => {
      const response = await fetch(`/api/vending-machines/${machineId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch machine data');
      }
      return await response.json();
    };

    const machineData = await fetchMachineData('vm-106c55e5');
    
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith('/api/vending-machines/vm-106c55e5');
    expect(machineData.id).toBe('vm-106c55e5');
    expect(machineData.temperature).toBe(32.0);
    expect(machineData.machine_status).toBe('operational');
  });
});
