/**
 * Device Data Mock
 *
 * Provides mock data for BDD testing of the IoTSphere dashboard
 * Following device-agnostic approach with water heaters as reference implementation
 */

// Common manufacturers for test data
const MANUFACTURERS = {
  AQUATECH: 'AquaTech',
  HYDROMAX: 'HydroMax',
  THERMEX: 'Thermex',
  ECOSMART: 'EcoSmart'
};

// Common models by manufacturer
const MODELS = {
  [MANUFACTURERS.AQUATECH]: ['Pro 2000', 'Basic 1000', 'SmartHeat 500'],
  [MANUFACTURERS.HYDROMAX]: ['Elite 150', 'Commercial 300', 'EcoHeater 100'],
  [MANUFACTURERS.THERMEX]: ['Industrial HW80', 'Residential T50', 'Smart T35'],
  [MANUFACTURERS.ECOSMART]: ['Green 11', 'Efficiency Plus', 'Smart Connect']
};

// Device operation modes
const MODES = ['standby', 'heating', 'eco', 'vacation'];

// Connection statuses
const CONNECTION_STATUSES = ['connected', 'disconnected'];

/**
 * Creates a set of mock devices with different manufacturers
 */
function createMixedManufacturerDevices() {
  return [
    createDevice('wh-001', MANUFACTURERS.AQUATECH, 'Pro 2000', 'connected', true),
    createDevice('wh-002', MANUFACTURERS.HYDROMAX, 'Elite 150', 'connected', false),
    createDevice('wh-003', MANUFACTURERS.THERMEX, 'Industrial HW80', 'disconnected', false),
    createDevice('wh-004', MANUFACTURERS.ECOSMART, 'Green 11', 'connected', true),
    createDevice('wh-005', MANUFACTURERS.AQUATECH, 'Basic 1000', 'connected', false)
  ];
}

/**
 * Creates a set of mock devices with different connection statuses
 */
function createMixedConnectionStatusDevices() {
  return [
    createDevice('wh-001', MANUFACTURERS.AQUATECH, 'Pro 2000', 'connected', true),
    createDevice('wh-002', MANUFACTURERS.HYDROMAX, 'Elite 150', 'connected', false),
    createDevice('wh-003', MANUFACTURERS.THERMEX, 'Industrial HW80', 'disconnected', false),
    createDevice('wh-004', MANUFACTURERS.AQUATECH, 'SmartHeat 500', 'disconnected', true),
    createDevice('wh-005', MANUFACTURERS.HYDROMAX, 'Commercial 300', 'connected', false)
  ];
}

/**
 * Creates a single device with specified ID and optional parameters
 */
function createSingleDevice(deviceId, connectionStatus = 'connected', mode = 'heating') {
  const manufacturer = MANUFACTURERS.AQUATECH;
  const model = 'Pro 2000';
  const simulated = deviceId.includes('sim');

  return createDevice(deviceId, manufacturer, model, connectionStatus, simulated, mode);
}

/**
 * Creates a device with specified parameters
 */
function createDevice(deviceId, manufacturer, model, connectionStatus, simulated, mode = 'heating') {
  return {
    device_id: deviceId,
    manufacturer,
    model,
    serial_number: `${manufacturer.substring(0, 2).toUpperCase()}${new Date().getFullYear()}${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`,
    connection_status: connectionStatus,
    simulated,
    display_name: `${manufacturer} ${model} (${deviceId})`,
    state: createDeviceState(manufacturer, model, mode),
    last_updated: new Date().toISOString()
  };
}

/**
 * Creates a device state based on manufacturer and model
 */
function createDeviceState(manufacturer, model, mode = 'heating') {
  // Different baseline settings based on product line
  let baseTemp = 120;
  let powerConsumption = 1200;
  let waterFlow = 2.5;

  // Adjust base values by manufacturer
  if (manufacturer === MANUFACTURERS.AQUATECH) {
    baseTemp += 5;
    powerConsumption += 200;
  } else if (manufacturer === MANUFACTURERS.ECOSMART) {
    baseTemp -= 5;
    powerConsumption -= 200;
  }

  // Adjust by model type
  if (model.includes('Pro') || model.includes('Elite') || model.includes('Industrial')) {
    baseTemp += 10;
    powerConsumption += 300;
    waterFlow += 1;
  } else if (model.includes('Eco') || model.includes('Green')) {
    baseTemp -= 5;
    powerConsumption -= 300;
  }

  // Determine heating status based on mode
  const heatingStatus = mode === 'heating';

  return {
    temperature_current: baseTemp + (Math.random() * 10 - 5),
    temperature_setpoint: baseTemp,
    heating_status: heatingStatus,
    power_consumption_watts: heatingStatus ? powerConsumption : 50,
    water_flow_gpm: mode !== 'standby' ? waterFlow : 0,
    pressure_psi: 40 + (Math.random() * 10),
    mode
  };
}

// Mock telemetry data generation
const mockTelemetryData = {
  /**
   * Creates historical telemetry data for a device
   */
  createTelemetryHistory(deviceId) {
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);

    // Create 24 hours of hourly data points
    const hourlyData = [];
    for (let i = 0; i < 24; i++) {
      const timestamp = new Date(yesterday);
      timestamp.setHours(timestamp.getHours() + i);

      // Generate realistic temperature patterns
      // Morning rise, midday peak, evening plateau, night decline
      let tempModifier = 0;
      const hour = timestamp.getHours();

      if (hour >= 5 && hour < 10) {
        // Morning rise
        tempModifier = (hour - 5) * 2;
      } else if (hour >= 10 && hour < 15) {
        // Midday peak
        tempModifier = 10 + (hour - 10);
      } else if (hour >= 15 && hour < 20) {
        // Evening plateau
        tempModifier = 15;
      } else {
        // Night decline
        tempModifier = hour < 5 ? (20 + hour) * -0.5 : (hour - 20) * -3;
      }

      // Base temperature plus pattern modifier plus small random variation
      const baseTemp = 120;
      const targetTemp = 125;
      const currentTemp = baseTemp + tempModifier + (Math.random() * 2 - 1);

      // Power consumption varies with heating activity
      const heatingStatus = currentTemp < targetTemp - 2;
      const powerConsumption = heatingStatus ? 1200 + (Math.random() * 200 - 100) : 50 + (Math.random() * 20);

      // Water flow varies with time of day
      let waterFlow = 0;
      if ((hour >= 6 && hour < 9) || (hour >= 17 && hour < 22)) {
        // Peak usage times
        waterFlow = 2.5 + (Math.random() * 1.5);
      } else if (hour >= 9 && hour < 17) {
        // Moderate daytime usage
        waterFlow = 1 + (Math.random() * 1);
      } else {
        // Low nighttime usage
        waterFlow = Math.random() * 0.5;
      }

      hourlyData.push({
        timestamp: timestamp.toISOString(),
        temperature_current: currentTemp,
        temperature_setpoint: targetTemp,
        heating_status: heatingStatus,
        power_consumption_watts: powerConsumption,
        water_flow_gpm: waterFlow
      });
    }

    return {
      device_id: deviceId,
      series: {
        temperature_current: hourlyData.map(d => ({ timestamp: d.timestamp, value: d.temperature_current })),
        temperature_setpoint: hourlyData.map(d => ({ timestamp: d.timestamp, value: d.temperature_setpoint })),
        power_consumption_watts: hourlyData.map(d => ({ timestamp: d.timestamp, value: d.power_consumption_watts })),
        water_flow_gpm: hourlyData.map(d => ({ timestamp: d.timestamp, value: d.water_flow_gpm })),
        heating_status: hourlyData.map(d => ({ timestamp: d.timestamp, value: d.heating_status ? 1 : 0 }))
      }
    };
  }
};

// Mock performance data generation
const mockPerformanceData = {
  /**
   * Creates performance metrics data for a device
   */
  createPerformanceData(deviceId) {
    return {
      device_id: deviceId,
      timestamp: new Date().toISOString(),
      efficiency: {
        score: 85 + (Math.random() * 10 - 5),
        rating: 'B'
      },
      anomalies: {
        count: 0
      },
      energy_consumption: {
        current: 45.2 + (Math.random() * 5),
        trend: 'down',
        trend_value: -3.2,
        status: 'normal'
      },
      water_usage: {
        current: 120.5 + (Math.random() * 10),
        trend: 'stable',
        trend_value: 0.5,
        status: 'normal'
      },
      heating_cycles: {
        current: 24 + Math.floor(Math.random() * 5),
        trend: 'up',
        trend_value: 8.3,
        status: 'warning'
      },
      average_temperature: {
        current: 122.5 + (Math.random() * 5 - 2.5),
        trend: 'stable',
        trend_value: 0.2,
        status: 'normal'
      },
      recovery_rate: {
        current: 15.2 + (Math.random() * 2),
        trend: 'stable',
        trend_value: -0.5,
        status: 'normal'
      }
    };
  },

  /**
   * Creates performance data with anomalies for testing anomaly detection
   */
  createPerformanceDataWithAnomalies(deviceId) {
    const baseData = this.createPerformanceData(deviceId);

    // Add anomalies
    baseData.anomalies = {
      count: 3,
      items: [
        {
          id: 'anom-001',
          type: 'temperature_spike',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          description: 'Unusual temperature spike detected',
          severity: 'warning',
          confidence: 0.87
        },
        {
          id: 'anom-002',
          type: 'irregular_cycling',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          description: 'Irregular heating cycle pattern',
          severity: 'warning',
          confidence: 0.92
        },
        {
          id: 'anom-003',
          type: 'efficiency_drop',
          timestamp: new Date(Date.now() - 86400000).toISOString(),
          description: 'Significant efficiency decrease',
          severity: 'error',
          confidence: 0.95
        }
      ]
    };

    // Update other metrics to reflect anomalies
    baseData.efficiency.score = 65 + (Math.random() * 10 - 5);
    baseData.efficiency.rating = 'C';
    baseData.energy_consumption.status = 'warning';
    baseData.energy_consumption.trend = 'up';
    baseData.energy_consumption.trend_value = 12.5;
    baseData.heating_cycles.status = 'critical';

    return baseData;
  }
};

module.exports = {
  mockDeviceData: {
    createMixedManufacturerDevices,
    createMixedConnectionStatusDevices,
    createSingleDevice
  },
  mockTelemetryData,
  mockPerformanceData
};
