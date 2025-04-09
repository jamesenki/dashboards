/**
 * Mock Validation Script
 *
 * This script directly tests the mock implementations to ensure they're working correctly
 * without running the full Cucumber test framework.
 */

// Import the mock implementations
const { mockTelemetryService } = require('./tests/behavior/support/mocks/telemetry-service.mock');
const { mockUserService } = require('./tests/behavior/support/mocks/user-service.mock');
const { mockAnalyticsEngine } = require('./tests/behavior/support/mocks/analytics-engine.mock');

// Create instances of the mocks
const telemetryService = mockTelemetryService();
const userService = mockUserService();
const analyticsEngine = mockAnalyticsEngine();

// Helper function to run a test
const runTest = async (name, testFn) => {
  try {
    console.log(`\n🧪 Testing: ${name}`);
    await testFn();
    console.log(`✅ PASSED: ${name}`);
  } catch (error) {
    console.error(`❌ FAILED: ${name}`);
    console.error(`   Error: ${error.message}`);
    console.error(error);
  }
};

const validateObject = (obj, requiredProps) => {
  const missing = [];
  for (const prop of requiredProps) {
    if (obj[prop] === undefined) {
      missing.push(prop);
    }
  }

  if (missing.length > 0) {
    throw new Error(`Missing required properties: ${missing.join(', ')}`);
  }
  return true;
};

// Run the validation tests
const runAllTests = async () => {
  // Test 1: User Service - Get User By Role
  await runTest('User Service - getUserByRole', async () => {
    const roles = ['ADMIN', 'FACILITY_MANAGER', 'TECHNICIAN'];

    for (const role of roles) {
      const user = await userService.getUserByRole(role);
      if (!user) {
        throw new Error(`getUserByRole failed to return a user for role: ${role}`);
      }
      console.log(`   Found user for role ${role}: ${user.username}`);
    }
  });

  // Test 2: Analytics Engine - Generate Dashboard
  await runTest('Analytics Engine - getOperationalAnalytics', async () => {
    const deviceIds = ['device-001', 'device-002'];
    const dashboard = await analyticsEngine.getOperationalAnalytics(deviceIds);

    // Validate the dashboard structure
    validateObject(dashboard, [
      'reliabilityMetrics',
      'maintenanceEfficiency',
      'performanceTrends',
      'costBreakdown'
    ]);

    console.log('   Dashboard contains all required metrics');
  });

  // Test 3: Analytics Engine - Maintenance Records
  await runTest('Analytics Engine - addMaintenanceRecord', async () => {
    const deviceId = 'device-test-001';
    const record = {
      date: new Date(),
      type: 'repair',
      technician: 'John Doe',
      description: 'Fixed temperature sensor',
      parts: ['sensor-t1', 'cable-15cm'],
      cost: 120.50,
      duration: 45 // minutes
    };

    await analyticsEngine.addMaintenanceRecord(deviceId, record);

    // Verify we can retrieve the record
    const records = await analyticsEngine.getMaintenanceRecords(deviceId);
    if (!records || !Array.isArray(records) || records.length === 0) {
      throw new Error('Failed to retrieve maintenance records after adding one');
    }

    console.log(`   Successfully added and retrieved maintenance record`);
  });

  // Test 4: Telemetry Service - Generate Operational History
  await runTest('Telemetry Service - generateOperationalHistory', async () => {
    const deviceId = 'water-heater-test-001';
    const now = new Date();
    // Use a much shorter time range - just 1 day instead of a week
    const oneDayAgo = new Date(now.getTime() - (1 * 24 * 60 * 60 * 1000));

    try {
      // Generate minimal telemetry data
      await telemetryService.generateOperationalHistory(deviceId, oneDayAgo, now);

      // Verify we can retrieve the telemetry
      const telemetry = await telemetryService.getHistoricalTelemetry(
        deviceId,
        oneDayAgo,
        now
      );

      if (!telemetry || !Array.isArray(telemetry)) {
        throw new Error('Telemetry data is not returned as an array');
      }

      if (telemetry.length === 0) {
        throw new Error('No telemetry data was generated');
      }

      // Check that telemetry has the expected structure
      const sample = telemetry[0];
      if (!sample.timestamp) {
        throw new Error('Telemetry data is missing timestamp property');
      }

      // Check if typical water heater properties exist
      const hasTemperature = telemetry.some(t => t.temperature !== undefined);
      const hasPressure = telemetry.some(t => t.pressure !== undefined);

      if (!hasTemperature || !hasPressure) {
        throw new Error('Telemetry data is missing expected water heater properties');
      }

      console.log(`   Successfully generated and retrieved ${telemetry.length} telemetry points`);
    } catch (error) {
      console.error(`   Telemetry generation error: ${error.message}`);
      throw error;
    }
  });

  // Test 5: Test ROI Calculation (simplified for memory efficiency)
  await runTest('Analytics Engine - calculateMaintenanceROI', async () => {
    try {
      // Use a unique device ID for this test
      const deviceId = `device-test-${Date.now()}`;

      // Add just one minimal maintenance record
      const record = {
        date: new Date(),
        type: 'preventive',
        cost: 250.00
      };

      // Add the record
      await analyticsEngine.addMaintenanceRecord(deviceId, record);

      // Calculate ROI
      const roi = await analyticsEngine.calculateMaintenanceROI(deviceId);

      // Just validate key fields exist rather than all fields
      if (!roi || typeof roi !== 'object') {
        throw new Error('ROI calculation did not return an object');
      }

      // Check that at least totalROI is returned
      if (roi.totalROI === undefined) {
        throw new Error('ROI calculation is missing totalROI property');
      }

      console.log(`   Successfully calculated maintenance ROI: ${roi.totalROI}`);
    } catch (error) {
      console.error(`   ROI calculation error: ${error.message}`);
      throw error;
    }
  });

  console.log('\n=== All Tests Complete ===');
};

// Run all the tests
runAllTests().catch(error => {
  console.error('Test suite failed:', error);
  process.exit(1);
});
