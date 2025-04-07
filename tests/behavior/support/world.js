const { setWorldConstructor } = require('@cucumber/cucumber');
const { mockDeviceRepository } = require('./mocks/device-repository.mock');
const { mockTelemetryService } = require('./mocks/telemetry-service.mock');
const { mockUserService } = require('./mocks/user-service.mock');
const { mockAnalyticsEngine } = require('./mocks/analytics-engine.mock');

/**
 * Custom World class
 * Provides context between steps
 */
class CustomWorld {
  constructor() {
    // Initialize test context to store data between steps
    this.testContext = {
      errors: [],
      currentUser: null,
      currentDeviceId: null
    };

    // Initialize mocks
    this.deviceRepository = mockDeviceRepository();
    this.telemetryService = mockTelemetryService();
    this.userService = mockUserService();
    this.analyticsEngine = mockAnalyticsEngine();

    // Utility helpers
    this.getRandomSubset = (array, count) => {
      const shuffled = [...array].sort(() => 0.5 - Math.random());
      return shuffled.slice(0, Math.min(count, array.length));
    };

    // Helper methods for generating test data
    this.generateRealisticDeviceHistory = async (deviceId, deviceType, customer, variationIndex) => {
      // Simple implementation to avoid token limits
      const telemetryPoints = 24; // Generate 24 hours of data
      for (let i = 0; i < telemetryPoints; i++) {
        await this.telemetryService.addTelemetryDataPoint(deviceId, {
          timestamp: new Date(Date.now() - (i * 60 * 60 * 1000)),
          temperature: 120 + Math.random() * 20 - 10,
          pressure: 40 + Math.random() * 10 - 5,
          flowRate: 15 + Math.random() * 8 - 4,
          energyConsumption: 2.5 + Math.random() * 1.5,
          status: Math.random() > 0.95 ? 'WARNING' : 'NORMAL'
        });
      }
    };

    this.generateSegmentBasedTelemetry = async (deviceId, deviceType, utilizationPattern) => {
      // Simple implementation to avoid token limits
      const operatingHours = utilizationPattern.dailyOperatingHours || 12;
      const telemetryPoints = operatingHours; // One point per operating hour
      
      for (let i = 0; i < telemetryPoints; i++) {
        await this.telemetryService.addTelemetryDataPoint(deviceId, {
          timestamp: new Date(Date.now() - (i * 60 * 60 * 1000)),
          temperature: 120 + Math.random() * 20 - 10,
          pressure: 40 + Math.random() * 10 - 5,
          flowRate: 15 + Math.random() * 8 - 4,
          energyConsumption: 2.5 + Math.random() * 1.5,
          status: Math.random() > 0.95 ? 'WARNING' : 'NORMAL'
        });
      }
    };
    
    // Authentication helper method
    this.authenticateUser = async (role) => {
      try {
        // Use the existing authenticate method from the user service mock
        const user = await this.userService.authenticate({ role });
        
        // Store the current user in the test context
        this.testContext.currentUser = user;
        
        return user;
      } catch (error) {
        console.error(`Authentication failed for role: ${role}`, error);
        return null;
      }
    };
    
    // Helper method for device registration
    this.registerDevice = async (deviceData) => {
      try {
        // Use the existing registerDevice method from the device repository mock
        const device = await this.deviceRepository.registerDevice(deviceData);
        
        // Return the registered device
        return device;
      } catch (error) {
        console.error(`Device registration failed:`, error);
        throw error;
      }
    };
    
    /**
     * Generate device type specific history data based on the device type
     * @param {string} deviceId - The ID of the device
     * @param {string} deviceType - The type of device (water-heater, hvac, refrigeration, etc.)
     * @param {Date} startDate - Start date for the history (optional)
     * @param {Date} endDate - End date for the history (optional)
     * @returns {Promise<void>}
     */
    this.generateDeviceTypeSpecificHistory = async (deviceId, deviceType, startDate = null, endDate = null) => {
      // Set default dates if not provided
      const start = startDate || new Date(Date.now() - (180 * 24 * 60 * 60 * 1000)); // 180 days ago
      const end = endDate || new Date(); // now
      
      // Generate telemetry data specific to the device type
      let telemetryPoints = Math.floor((end - start) / (3600 * 1000)); // hourly data points
      const maxPoints = 168; // Cap at 1 week of hourly data to avoid excessive processing
      telemetryPoints = Math.min(telemetryPoints, maxPoints);
      
      // Generate different telemetry patterns based on device type
      for (let i = 0; i < telemetryPoints; i++) {
        const timestamp = new Date(end.getTime() - (i * 3600 * 1000)); // work backwards from end date
        
        // Base data structure all devices will have
        const telemetryData = {
          timestamp,
          status: Math.random() > 0.95 ? 'WARNING' : 'NORMAL',
          energyConsumption: 0
        };
        
        // Add device-specific telemetry data
        switch (deviceType) {
          case 'water-heater':
            telemetryData.temperature = 120 + Math.random() * 20 - 10;
            telemetryData.pressure = 40 + Math.random() * 10 - 5;
            telemetryData.flowRate = 15 + Math.random() * 8 - 4;
            telemetryData.energyConsumption = 2.5 + Math.random() * 1.5;
            break;
          
          case 'hvac':
            telemetryData.temperature = 72 + Math.random() * 10 - 5;
            telemetryData.airflow = 400 + Math.random() * 100 - 50;
            telemetryData.filterStatus = Math.random() > 0.8 ? 'NEEDS_REPLACEMENT' : 'GOOD';
            telemetryData.energyConsumption = 4.2 + Math.random() * 2.5;
            break;
          
          case 'refrigeration':
            telemetryData.temperature = 38 + Math.random() * 8 - 4;
            telemetryData.doorOpenCount = Math.floor(Math.random() * 20);
            telemetryData.compressorDutyCycle = 0.4 + Math.random() * 0.4;
            telemetryData.energyConsumption = 3.8 + Math.random() * 2.0;
            break;
          
          case 'vending-machine':
            telemetryData.temperature = 50 + Math.random() * 10 - 5;
            telemetryData.inventoryLevel = Math.random();
            telemetryData.transactions = Math.floor(Math.random() * 30);
            telemetryData.energyConsumption = 1.2 + Math.random() * 0.8;
            break;
          
          case 'robot':
            telemetryData.batteryLevel = Math.random();
            telemetryData.motorTemperature = 85 + Math.random() * 30 - 15;
            telemetryData.cycleTime = 120 + Math.random() * 60 - 30;
            telemetryData.errorRate = Math.random() * 0.05;
            telemetryData.energyConsumption = 5.5 + Math.random() * 3.0;
            break;
          
          case 'vehicle':
            telemetryData.batteryLevel = Math.random();
            telemetryData.mileage = Math.random() * 100;
            telemetryData.engineTemperature = 180 + Math.random() * 40 - 20;
            telemetryData.tirePressure = 32 + Math.random() * 6 - 3;
            telemetryData.energyConsumption = 12.5 + Math.random() * 8.0;
            break;
          
          default:
            // Generic IoT device telemetry
            telemetryData.temperature = 75 + Math.random() * 30 - 15;
            telemetryData.humidity = 50 + Math.random() * 20 - 10;
            telemetryData.signalStrength = -60 - Math.random() * 30;
            telemetryData.energyConsumption = 2.0 + Math.random() * 1.0;
        }
        
        // Add the telemetry data point
        await this.telemetryService.addTelemetryDataPoint(deviceId, telemetryData);
      }
    };
    
    /**
     * Generate operational history for a device over a time period
     * @param {string} deviceId - The ID of the device
     * @param {Date} startDate - Start date for the history
     * @param {Date} endDate - End date for the history
     * @returns {Promise<void>}
     */
    this.generateOperationalHistory = async (deviceId, startDate, endDate) => {
      // Use the telemetry service to generate the operational history
      await this.telemetryService.generateOperationalHistory(deviceId, startDate, endDate);
    };
    
    /**
     * Generate maintenance history for a device
     * @param {string} deviceId - The ID of the device
     * @param {Date} startDate - Start date for the history
     * @param {Date} endDate - End date for the history
     * @returns {Promise<void>}
     */
    this.generateMaintenanceHistory = async (deviceId, startDate, endDate) => {
      // Create some sample maintenance records over the time period
      const months = Math.ceil((endDate - startDate) / (30 * 24 * 60 * 60 * 1000));
      
      // Generate periodic maintenance records (approximately monthly)
      for (let i = 0; i < months; i++) {
        const recordDate = new Date(startDate);
        recordDate.setMonth(startDate.getMonth() + i);
        
        // Add some randomness to the date
        recordDate.setDate(recordDate.getDate() + Math.floor(Math.random() * 10));
        
        // Only include if still in range
        if (recordDate <= endDate) {
          const maintenanceRecord = {
            id: `maint-${deviceId}-${i}`,
            deviceId,
            timestamp: recordDate,
            type: i % 3 === 0 ? 'SCHEDULED' : 'ROUTINE',
            technician: 'Test Technician',
            description: `${i % 3 === 0 ? 'Scheduled' : 'Routine'} maintenance performed`,
            cost: 100 + Math.random() * 200,
            duration: 60 + Math.random() * 120, // minutes
            components: ['filter', 'thermostat', 'heating element'].slice(0, Math.floor(Math.random() * 3) + 1),
            issues: i % 5 === 0 ? ['minor leak', 'efficiency loss'] : [],
            resolutions: i % 5 === 0 ? ['sealed connection', 'replaced part'] : []
          };
          
          // Add this to the analytics engine
          if (this.analyticsEngine.addMaintenanceRecord) {
            await this.analyticsEngine.addMaintenanceRecord(maintenanceRecord);
          }
        }
      }
    };
    
    /**
     * Generate reliability metrics for a device
     * @param {string} deviceId - The ID of the device
     * @param {Date} startDate - Start date for the history
     * @param {Date} endDate - End date for the history
     * @returns {Promise<void>}
     */
    this.generateReliabilityMetrics = async (deviceId, startDate, endDate) => {
      // Create reliability metrics for the device
      const metrics = {
        deviceId,
        period: {
          start: startDate,
          end: endDate
        },
        uptime: 0.985 + (Math.random() * 0.015),  // 98.5% - 100%
        meanTimeBetweenFailures: 720 + (Math.random() * 240), // 720-960 hours
        meanTimeToRepair: 2 + (Math.random() * 3), // 2-5 hours
        failureRate: 0.001 + (Math.random() * 0.002), // 0.1% - 0.3%
        performanceEfficiency: 0.92 + (Math.random() * 0.08) // 92% - 100%
      };
      
      // Store metrics in test context for later verification
      this.testContext.reliabilityMetrics = metrics;
    };
  }
}

setWorldConstructor(CustomWorld);
