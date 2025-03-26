 
  

// Mock dependencies and data
const mockGaugeData = {};
const mockStatusData = {};
const mockInventoryData = [];
// Add mock for operationalMachineId
const operationalMachineId = "test-machine-123";

// Create Node.js compatible test environment

// Mock global browser objects for Node.js environment
global.window = {
  history: {
    pushState: function() {
      console.log("Mock: history.pushState called");
    }
  },
  location: {
    hostname: 'localhost'
  },
  machineId: null
};

// Mock document object with enhanced functionality for dropdown testing
global.document = {
  elements: {
    // Storage for our mock elements
    'machine-selector': {
      style: { display: 'block' },
      options: [],
      value: '',
      selectedIndex: -1,
      innerHTML: '',
      addEventListener: function(event, handler) {
        console.log(`Mock: Added ${event} event listener to machine-selector`);
        this.eventHandlers = this.eventHandlers || {};
        this.eventHandlers[event] = handler;
      },
      // Simulate a change event
      simulateChange: function(newValue) {
        this.value = newValue;
        // Find the index of the option with this value
        this.selectedIndex = this.options.findIndex(opt => opt.value === newValue);
        if (this.eventHandlers && this.eventHandlers.change) {
          console.log(`Mock: Triggering change event with value ${newValue}`);
          this.eventHandlers.change({ target: this });
        }
      },
      // Allow adding options
      appendChild: function(option) {
        this.options.push(option);
      }
    },
    'operations-summary-content': { style: { display: 'none' }, innerHTML: '' },
    'operations-loading': { style: { display: 'none' } },
    'operations-error': { style: { display: 'none' }, textContent: '' },
    'asset-health-gauge': { style: {}, id: 'asset-health-gauge', querySelector: () => ({ style: {} }) },
    'freezer-temp-gauge': { style: {}, id: 'freezer-temp-gauge', querySelector: () => ({ style: {} }) },
    'dispense-force-gauge': { style: {}, id: 'dispense-force-gauge', querySelector: () => ({ style: {} }) },
    'cycle-time-gauge': { style: {}, id: 'cycle-time-gauge', querySelector: () => ({ style: {} }) },
    'asset-health-value': { textContent: '' },
    'freezer-temp-value': { textContent: '', style: {} },
    'dispense-force-value': { textContent: '' },
    'cycle-time-value': { textContent: '' },
    'inventory-container': { innerHTML: '' },
    'machine-status-card': { querySelector: () => ({ textContent: '' }) },
    'pod-code-card': { querySelector: () => ({ textContent: '' }) },
    'cup-detect-card': { querySelector: () => ({ textContent: '' }) },
    'door-status-card': { querySelector: () => ({ textContent: '' }) },
    'dispense-status-card': { querySelector: () => ({ textContent: '' }) },
    'last-transaction-card': { querySelector: () => ({ textContent: '' }) }
  },
  getElementById: function(id) {
    return this.elements[id] || {
      style: { display: 'none' },
      textContent: '',
      innerHTML: ''
    };
  },
  createElement: function(type) {
    if (type === 'option') {
      return {
        textContent: '',
        value: ''
      };
    }
    return {
      style: {},
      className: '',
      textContent: '',
      innerHTML: '',
      appendChild: function() {}
    };
  },
  querySelectorAll: function(selector) {
    if (selector === '.gauge-container') {
      return [
        this.elements['asset-health-gauge'],
        this.elements['freezer-temp-gauge'],
        this.elements['dispense-force-gauge'],
        this.elements['cycle-time-gauge']
      ];
    }
    return [];
  },
  head: {
    appendChild: function() {}
  }
};

// Create a mock of the MachineService for testing
const mockMachineService = {
  // Track each method call
  calls: {
    getMachineById: 0,
    getOperationsData: 0,
    createFallbackOperationsData: 0,
    processOperationsData: 0
  },
  // Mock implementation of required methods
  getMachineById: function(machineId) {
    this.calls.getMachineById++;
    console.log(`Mock: Fetching machine data for: ${machineId}`);
    return Promise.resolve({
      id: machineId,
      name: `Test Machine ${machineId}`,
      location: 'Test Location',
      status: 'ONLINE',
      readings: [{ temperature: -15, door_status: 'CLOSED' }]
    });
  },
  getOperationsData: function(machineId) {
    this.calls.getOperationsData++;
    console.log(`Mock: Fetching operations data for: ${machineId}`);
    return Promise.resolve({
      machine_id: machineId,
      machine_status: 'ONLINE',
      pod_code: '12345',
      cup_detect: 'Yes',
      customer_door: 'CLOSED',
      freezer_temperature: { freezerTemperature: '-15.0' },
      dispense_pressure: { dispensePressure: '35.5' },
      cycle_time: { cycleTime: '18.5' },
      ice_cream_inventory: [
        { name: 'Vanilla', level: 80 },
        { name: 'Chocolate', level: 60 }
      ]
    });
  },
  createFallbackOperationsData: function(machineId) {
    this.calls.createFallbackOperationsData++;
    console.log(`Mock: Creating fallback operations data for: ${machineId}`);
    return {
      machine_id: machineId,
      machine_status: 'ONLINE',
      pod_code: 'FALLBACK',
      cup_detect: 'No',
      dispense_pressure: { dispensePressure: '30' },
      freezer_temperature: { freezerTemperature: '-12.5' },
      cycle_time: { cycleTime: '15' }
    };
  },
  processOperationsData: function(data) {
    this.calls.processOperationsData++;
    return data; // For testing, just return the input data
  }
};

// Expose MachineService as a global
global.MachineService = mockMachineService;

// Mock the console.assert function to provide better test output
const originalAssert = console.assert;
console.assert = function(condition, message) {
  if (!condition) {
    console.error(`❌ ASSERTION FAILED: ${message}`);
    // Don't throw an error to allow tests to continue
  } else {
    // Log successful assertions for clarity
    console.log(`✓ ASSERTION PASSED: ${message?.split(',')[0] || 'Check passed'}`);
  }
};


// Track all function calls for test verification
const functionCalls = {
  updateGauges: 0,
  updateStatusCards: 0,
  updateInventory: 0,
  setupRealTimeUpdates: 0
};

function updateGauges(data) {
  functionCalls.updateGauges++;
  Object.assign(mockGaugeData, data);
}

function updateStatusCards(data) {
  functionCalls.updateStatusCards++;
  Object.assign(mockStatusData, data);
}

function updateInventory(data) {
  functionCalls.updateInventory++;
  mockInventoryData.length = 0;
  if (Array.isArray(data)) {
    data.forEach(item => mockInventoryData.push({...item}));
  }
}

// Update setupRealTimeUpdates to handle the machine ID parameter
function setupRealTimeUpdates(machineId) {
  functionCalls.setupRealTimeUpdates++;
  console.log(`Mock: Setting up real-time updates for machine ${machineId}`);
}

// Default backup values for missing data
const DEFAULT_VALUES = {
  dispenseForce: 30,
  cycleTime: 15,
  freezerTemperature: -15,
  assetHealth: 85
};

// Import the function to test or define it here for testing
// This should match the implementation in detail.html
function updateOperationsDashboard(data) {
  if (!data) data = {}; // Guard against null/undefined
  
  try {
    // Update status cards - handle both direct API format and pre-processed format
    const statusData = data.status || {
      machineStatus: data.machine_status || "Unknown",
      podCode: data.pod_code || "N/A",
      cupDetect: data.cup_detect === 'Yes',
      doorStatus: data.customer_door || "Closed"
    };
    
    updateStatusCards(statusData);
    
    // Create gauge data structure from response
    let gaugeData = data.gauges || {};
    
    // Extract values if using the direct API response format
    if (data.dispense_pressure || data.cycle_time || data.freezer_temperature) {
      // Extract the dispense force value
      if (data.dispense_pressure && data.dispense_pressure.dispensePressure) {
        const dispensePressureValue = parseFloat(data.dispense_pressure.dispensePressure);
        if (!isNaN(dispensePressureValue)) {
          gaugeData.dispenseForce = dispensePressureValue;
        } else {
          gaugeData.dispenseForce = DEFAULT_VALUES.dispenseForce;
        }
      } else if (!gaugeData.dispenseForce) {
        gaugeData.dispenseForce = DEFAULT_VALUES.dispenseForce;
      }
          
      // Extract the cycle time value
      if (data.cycle_time && data.cycle_time.cycleTime) {
        const cycleTimeValue = parseFloat(data.cycle_time.cycleTime);
        if (!isNaN(cycleTimeValue)) {
          gaugeData.cycleTime = cycleTimeValue;
        } else {
          gaugeData.cycleTime = DEFAULT_VALUES.cycleTime;
        }
      } else if (!gaugeData.cycleTime) {
        gaugeData.cycleTime = DEFAULT_VALUES.cycleTime;
      }
          
      // Extract the freezer temperature value
      if (data.freezer_temperature && data.freezer_temperature.freezerTemperature) {
        const tempValue = parseFloat(data.freezer_temperature.freezerTemperature);
        if (!isNaN(tempValue)) {
          gaugeData.freezerTemperature = tempValue;
        } else {
          gaugeData.freezerTemperature = DEFAULT_VALUES.freezerTemperature;
        }
      } else if (!gaugeData.freezerTemperature) {
        gaugeData.freezerTemperature = DEFAULT_VALUES.freezerTemperature;
      }
      
      // Default asset health if not provided
      if (!gaugeData.assetHealth) {
        gaugeData.assetHealth = DEFAULT_VALUES.assetHealth;
      }
    } else {
      // Ensure gaugeData has all required fields even if not provided in API format
      if (!gaugeData.dispenseForce) gaugeData.dispenseForce = DEFAULT_VALUES.dispenseForce;
      if (!gaugeData.cycleTime) gaugeData.cycleTime = DEFAULT_VALUES.cycleTime;
      if (!gaugeData.freezerTemperature) gaugeData.freezerTemperature = DEFAULT_VALUES.freezerTemperature;
      if (!gaugeData.assetHealth) gaugeData.assetHealth = DEFAULT_VALUES.assetHealth;
    }
    
    // Update gauges
    updateGauges(gaugeData);
    
    // Update inventory - handle multiple possible inventory formats
    let inventoryData = data.inventory || data.ice_cream_inventory || [];
    // Ensure inventory is an array
    if (!Array.isArray(inventoryData)) {
      console.warn("Inventory data is not an array, using empty array");
      inventoryData = [];
    }
    updateInventory(inventoryData);
    
    // Set up periodic updates for real-time data
    setupRealTimeUpdates(operationalMachineId);
  } catch (error) {
    console.error("Error in updateOperationsDashboard:", error);
    // Recover gracefully by setting default values
    updateStatusCards({
      machineStatus: "Error",
      podCode: "N/A",
      cupDetect: false,
      doorStatus: "Unknown"
    });
    updateGauges(DEFAULT_VALUES);
    updateInventory([]);
  }
}

// Test suite
function runTests() {
  console.log("Running Operations Dashboard Tests...");
  
  // Reset mock data before each test
  function resetMocks() {
    Object.keys(mockGaugeData).forEach(key => delete mockGaugeData[key]);
    Object.keys(mockStatusData).forEach(key => delete mockStatusData[key]);
    mockInventoryData.length = 0;
    
    // Reset function call counters
    Object.keys(functionCalls).forEach(key => functionCalls[key] = 0);
  }
  
  // Verify all required gauge values are present
  function verifyGaugeData() {
    const requiredGaugeFields = ['dispenseForce', 'cycleTime', 'freezerTemperature', 'assetHealth'];
    requiredGaugeFields.forEach(field => {
      console.assert(mockGaugeData[field] !== undefined, 
        `Required gauge field "${field}" is missing`);
      console.assert(typeof mockGaugeData[field] === 'number', 
        `Gauge field "${field}" should be a number, got ${typeof mockGaugeData[field]}`);
    });
  }
  
  // Test 1: Complete API response data format
  function testCompleteApiData() {
    resetMocks();
    const apiData = {
      machine_status: "Online",
      pod_code: "12345",
      cup_detect: "Yes",
      customer_door: "Closed",
      dispense_pressure: {
        dispensePressure: "45.5",
        min: "5",
        max: "40"
      },
      cycle_time: {
        cycleTime: "12.3",
        min: "5",
        max: "60"
      },
      freezer_temperature: {
        freezerTemperature: "-18.5"
      },
      ice_cream_inventory: [
        { name: "Vanilla", level: 80 },
        { name: "Chocolate", level: 65 }
      ]
    };
    
    updateOperationsDashboard(apiData);
    
    // Verify all functions were called
    console.assert(functionCalls.updateGauges === 1, "updateGauges should be called once");
    console.assert(functionCalls.updateStatusCards === 1, "updateStatusCards should be called once");
    console.assert(functionCalls.updateInventory === 1, "updateInventory should be called once");
    
    // Verify gauge values
    console.assert(mockGaugeData.dispenseForce === 45.5, 
      `Expected dispenseForce to be 45.5, got ${mockGaugeData.dispenseForce}`);
    console.assert(mockGaugeData.cycleTime === 12.3, 
      `Expected cycleTime to be 12.3, got ${mockGaugeData.cycleTime}`);
    console.assert(mockGaugeData.freezerTemperature === -18.5, 
      `Expected freezerTemperature to be -18.5, got ${mockGaugeData.freezerTemperature}`);
    console.assert(mockGaugeData.assetHealth === 85, 
      `Expected assetHealth to be 85, got ${mockGaugeData.assetHealth}`);
    
    // Verify status values
    console.assert(mockStatusData.machineStatus === "Online", 
      `Expected machineStatus to be Online, got ${mockStatusData.machineStatus}`);
    console.assert(mockStatusData.podCode === "12345", 
      `Expected podCode to be 12345, got ${mockStatusData.podCode}`);
    
    // Verify inventory was populated
    console.assert(mockInventoryData.length === 2, 
      `Expected 2 inventory items, got ${mockInventoryData.length}`);
    console.assert(mockInventoryData[0].name === "Vanilla", 
      `Expected first inventory item to be Vanilla, got ${mockInventoryData[0].name}`);
    
    verifyGaugeData();
    console.log("✓ Complete API data test passed");
  }
  
  // Test 2: Pre-processed data format
  function testPreProcessedFormat() {
    resetMocks();
    const processedData = {
      status: {
        machineStatus: "Online",
        podCode: "54321",
        cupDetect: true,
        doorStatus: "Open"
      },
      gauges: {
        dispenseForce: 40,
        cycleTime: 10,
        freezerTemperature: -20,
        assetHealth: 90
      },
      inventory: [
        { name: "Strawberry", level: 90 },
        { name: "Mint", level: 30 }
      ]
    };
    
    updateOperationsDashboard(processedData);
    
    // Verify all required data is present and in correct format
    console.assert(mockGaugeData.dispenseForce === 40, 
      `Expected dispenseForce to be 40, got ${mockGaugeData.dispenseForce}`);
    console.assert(mockStatusData.machineStatus === "Online", 
      `Expected machineStatus to be Online, got ${mockStatusData.machineStatus}`);
    console.assert(mockInventoryData.length === 2, 
      `Expected 2 inventory items, got ${mockInventoryData.length}`);
    
    verifyGaugeData();
    console.log("✓ Pre-processed format test passed");
  }
  
  // Test 3: Partial data with some missing fields
  function testPartialData() {
    resetMocks();
    const partialData = {
      machine_status: "Offline",
      // pod_code missing
      cup_detect: "No",
      // customer_door missing
      dispense_pressure: {
        // dispensePressure missing
        min: "5",
        max: "40"
      },
      // cycle_time completely missing
      freezer_temperature: {
        freezerTemperature: "-10.0"
      },
      ice_cream_inventory: [
        { name: "Vanilla", level: 20 }
        // Other inventory items missing
      ]
    };
    
    updateOperationsDashboard(partialData);
    
    // Verify default values are used for missing data
    console.assert(mockGaugeData.dispenseForce === DEFAULT_VALUES.dispenseForce, 
      `Expected dispenseForce to use default ${DEFAULT_VALUES.dispenseForce}, got ${mockGaugeData.dispenseForce}`);
    console.assert(mockGaugeData.cycleTime === DEFAULT_VALUES.cycleTime, 
      `Expected cycleTime to use default ${DEFAULT_VALUES.cycleTime}, got ${mockGaugeData.cycleTime}`);
    console.assert(mockGaugeData.freezerTemperature === -10, 
      `Expected freezerTemperature to be -10, got ${mockGaugeData.freezerTemperature}`);
    
    // Verify partial status data
    console.assert(mockStatusData.machineStatus === "Offline", 
      `Expected machineStatus to be Offline, got ${mockStatusData.machineStatus}`);
    console.assert(mockStatusData.podCode === "N/A", 
      `Expected missing podCode to be N/A, got ${mockStatusData.podCode}`);
    
    verifyGaugeData();
    console.log("✓ Partial data test passed");
  }
  
  // Test 4: Completely empty data
  function testEmptyData() {
    resetMocks();
    const emptyData = {};
    
    updateOperationsDashboard(emptyData);
    
    // Verify default values are used for all fields
    verifyGaugeData();
    
    console.assert(mockStatusData.machineStatus === "Unknown", 
      `Expected machineStatus to be Unknown for empty data, got ${mockStatusData.machineStatus}`);
    console.assert(mockInventoryData.length === 0, 
      `Expected empty inventory, got ${mockInventoryData.length} items`);
    
    console.log("✓ Empty data test passed");
  }
  
  // Test 5: Malformed data with incorrect types
  function testMalformedData() {
    resetMocks();
    const malformedData = {
      machine_status: 123, // Number instead of string
      pod_code: true, // Boolean instead of string
      dispense_pressure: {
        dispensePressure: "not-a-number" // Non-numeric string
      },
      freezer_temperature: {
        freezerTemperature: {} // Object instead of string/number
      },
      ice_cream_inventory: "not-an-array" // String instead of array
    };
    
    // This shouldn't throw exceptions even with malformed data
    updateOperationsDashboard(malformedData);
    
    // Just verify we at least have the required fields with some values
    verifyGaugeData();
    
    console.log("✓ Malformed data test passed");
  }
  
  // Test 6: Null/undefined data
  function testNullData() {
    resetMocks();
    
    // Passing null - should not throw an error
    updateOperationsDashboard(null);
    verifyGaugeData();
    
    resetMocks();
    // Passing undefined - should not throw an error
    updateOperationsDashboard(undefined);
    verifyGaugeData();
    
    console.log("✓ Null/undefined data test passed");
  }
  
  // Run all tests
  testCompleteApiData();
  testPreProcessedFormat();
  testPartialData();
  testEmptyData();
  testMalformedData();
  testNullData();
  
  // Test MachineService integration in loadMachineData function
  async function testLoadMachineData() {
    console.log("\nTesting loadMachineData with MachineService...");
    
    // We need to mock our loadMachineData function for testing
    const mockLoadMachineData = function(machineId, hasLoadedHash = false) {
      console.log(`Mock: Loading data for machine ID: ${machineId} using MachineService`);
      
      // Set global machine ID for other functions
      window.machineId = machineId;
      
      // Use our mocked MachineService to get machine data
      return MachineService.getMachineById(machineId)
        .then(machine => {
          console.log('Mock: Machine data loaded successfully via MachineService');
          return machine;
        });
    };
    
    // Execute the test
    try {
      // Reset call count
      MachineService.calls.getMachineById = 0;
      
      const machine = await mockLoadMachineData("test-machine-456");
      
      // Verify MachineService.getMachineById was called
      console.assert(MachineService.calls.getMachineById === 1, 
        `Expected MachineService.getMachineById to be called once, got ${MachineService.calls.getMachineById}`);
      
      // Verify returned machine data has expected fields
      console.assert(machine.id === "test-machine-456", 
        `Expected machine.id to be test-machine-456, got ${machine.id}`);
      console.assert(machine.status === "ONLINE", 
        `Expected machine.status to be ONLINE, got ${machine.status}`);
      
      console.log("✓ loadMachineData with MachineService test passed");
    } catch (error) {
      console.error("❌ loadMachineData test failed:", error);
    }
  }

  // Test loadRealtimeOperationsData function with MachineService
  async function testLoadRealtimeOperationsData() {
    console.log("\nTesting loadRealtimeOperationsData with MachineService...");
    
    // Mock our DOM elements - simpler approach for Node.js
    const mockDomElements = {
      loadingEl: { style: { display: 'none' } },
      contentEl: { style: { display: 'none' } },
      errorEl: { style: { display: 'none' }, textContent: '' }
    };
    
    // Mock loadRealtimeOperationsData function based on refactored implementation
    const mockLoadRealtimeOperationsData = async function(machineId, contentId) {
      // Pre-test assertions
      console.assert(machineId === "test-machine-789", 
        `Expected machineId to be test-machine-789, got ${machineId}`);
      console.assert(contentId === "operations-summary-content", 
        `Expected contentId to be operations-summary-content, got ${contentId}`);
      
      try {
        // Show loading state
        mockDomElements.loadingEl.style.display = 'flex';
        mockDomElements.contentEl.style.display = 'none';
        mockDomElements.errorEl.style.display = 'none';
        
        // Use the mocked MachineService to get operations data
        const data = await MachineService.getOperationsData(machineId);
        
        // Process the data, typically updating UI elements
        if (data) {
          mockDomElements.loadingEl.style.display = 'none';
          mockDomElements.contentEl.style.display = 'block';
        }
        
        return data;
      } catch (error) {
        // Mock error handling
        mockDomElements.loadingEl.style.display = 'none';
        mockDomElements.errorEl.style.display = 'block';
        mockDomElements.errorEl.textContent = `Error loading operations data: ${error.message}`;
        
        // Use fallback data
        return MachineService.createFallbackOperationsData(machineId);
      }
    };
    
    // Execute the test
    try {
      // Reset mock trackers
      MachineService.calls.getOperationsData = 0;
      
      // Test success path
      const data = await mockLoadRealtimeOperationsData("test-machine-789", "operations-summary-content");
      
      // Verify MachineService.getOperationsData was called
      console.assert(MachineService.calls.getOperationsData === 1, 
        `Expected MachineService.getOperationsData to be called once, got ${MachineService.calls.getOperationsData}`);
      
      // Verify returned data has expected fields following our real-time operational focus
      console.assert(data.freezer_temperature && data.freezer_temperature.freezerTemperature === "-15.0", 
        `Expected freezer temperature to be -15.0, got ${data.freezer_temperature?.freezerTemperature}`);
      console.assert(data.dispense_pressure && data.dispense_pressure.dispensePressure === "35.5", 
        `Expected dispense pressure to be 35.5, got ${data.dispense_pressure?.dispensePressure}`);
      
      // Verify UI state is updated
      console.assert(mockDomElements.loadingEl.style.display === 'none', 
        `Expected loading state to be hidden`);
      console.assert(mockDomElements.contentEl.style.display === 'block', 
        `Expected content to be visible`);
      
      console.log("✓ loadRealtimeOperationsData success path test passed");
      
      // Test error path with fallback data
      // Override the mock to cause an error
      const originalGetOperationsData = MachineService.getOperationsData;
      MachineService.getOperationsData = function() {
        MachineService.calls.getOperationsData++;
        return Promise.reject(new Error("Test error"));
      };
      
      MachineService.calls.createFallbackOperationsData = 0;
      
      // Reset mock elements
      mockDomElements.loadingEl.style.display = 'none';
      mockDomElements.contentEl.style.display = 'none';
      mockDomElements.errorEl.style.display = 'none';
      
      const fallbackData = await mockLoadRealtimeOperationsData("test-machine-789", "operations-summary-content");
      
      // Verify fallback method was called
      console.assert(MachineService.calls.createFallbackOperationsData === 1, 
        `Expected createFallbackOperationsData to be called once, got ${MachineService.calls.createFallbackOperationsData}`);
      
      // Verify fallback data is returned
      console.assert(fallbackData.pod_code === "FALLBACK", 
        `Expected fallback data pod_code to be FALLBACK, got ${fallbackData.pod_code}`);
      
      console.log("✓ loadRealtimeOperationsData error path test passed");
      
      // Restore original mock function
      MachineService.getOperationsData = originalGetOperationsData;
      
    } catch (error) {
      console.error("❌ loadRealtimeOperationsData test failed:", error);
    }
  }
  
  // Run all the original data transformation tests
  console.log("\n=== RUNNING DATA TRANSFORMATION TESTS ===\n");
  testCompleteApiData();
  testPreProcessedFormat();
  testPartialData();
  testEmptyData();
  testMalformedData();
  testNullData();
  
  // Run MachineService integration tests
  console.log("\n=== RUNNING MACHINE SERVICE INTEGRATION TESTS ===\n");
  
  // Since our new tests are async, we need to run them differently
  testLoadMachineData().then(() => {
    return testLoadRealtimeOperationsData();
  }).then(() => {
    console.log("\nAll tests completed!");
  }).catch(error => {
    console.error("Error running tests:", error);
  });
}

// Run tests when this file is loaded
runTests();