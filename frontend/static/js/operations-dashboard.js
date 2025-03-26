/**
 * Operations Dashboard JavaScript
 * IoTSphere - Polar Delight Real-time Operations Dashboard
 */

/**
 * Initialize all gauges on the page
 */
function initializeGauges() {
  // Get all gauge containers
  const gaugeContainers = document.querySelectorAll('.gauge-container');
  
  // Add needle element to each gauge
  gaugeContainers.forEach(gauge => {
    // Create and append needle if it doesn't exist yet
    if (!gauge.querySelector('.gauge-needle')) {
      const needle = document.createElement('div');
      needle.className = 'gauge-needle';
      gauge.appendChild(needle);
    }
    
    // Get the gauge value and update position
    const value = parseFloat(gauge.getAttribute('data-value'));
    updateGaugePosition(gauge.id, value);
  });
}

/**
 * Update gauge needle position based on percentage value
 * @param {string} gaugeId - ID of the gauge element
 * @param {number} percentValue - Value between 0-100
 */
function updateGaugePosition(gaugeId, percentValue) {
  const gauge = document.getElementById(gaugeId);
  if (!gauge) return;
  
  const needle = gauge.querySelector('.gauge-needle');
  if (!needle) return;
  
  // Convert percentage to degrees (0% = -90deg, 100% = 90deg)
  const degrees = -90 + (percentValue * 1.8);
  
  // Apply rotation
  needle.style.transform = `rotate(${degrees}deg)`;
}

/**
 * Update inventory data with values from operations data
 * @param {Array} inventoryData - Array of inventory items from operations data
 */
function updateInventoryData(inventoryData) {
  if (!Array.isArray(inventoryData) || inventoryData.length === 0) {
    console.warn('Invalid inventory data received:', inventoryData);
    return;
  }
  
  console.log('Updating inventory data:', inventoryData);
  
  // Map of flavor names to their corresponding inventory items in the DOM
  const inventoryItemMap = {};
  document.querySelectorAll('.inventory-item').forEach(item => {
    const label = item.querySelector('.inventory-label');
    if (label) {
      inventoryItemMap[label.textContent.trim()] = item;
    }
  });
  
  // Update each inventory item
  inventoryData.forEach(item => {
    const domItem = inventoryItemMap[item.name];
    if (!domItem) return;
    
    const level = item.level || 0;
    const maxCapacity = item.max_capacity || 100;
    const percentage = Math.min(100, (level / maxCapacity) * 100);
    
    // Update value display
    const valueElement = domItem.querySelector('.inventory-value');
    if (valueElement) {
      valueElement.textContent = `${level}/${maxCapacity}`;
    }
    
    // Update bar width
    const bar = domItem.querySelector('.inventory-bar');
    if (bar) {
      bar.style.width = `${percentage}%`;
      
      // Update color based on level
      bar.className = 'inventory-bar';
      if (percentage <= 20) {
        bar.classList.add('low');
      } else if (percentage <= 50) {
        bar.classList.add('medium');
      } else {
        bar.classList.add('high');
      }
    }
  });
}

/**
 * Update inventory bar widths based on value
 */
function updateInventoryBars() {
  const inventoryBars = document.querySelectorAll('.inventory-bar');
  
  inventoryBars.forEach(bar => {
    const container = bar.parentElement;
    const item = container.parentElement;
    const valueElement = item.querySelector('.inventory-value');
    
    if (valueElement) {
      const valueText = valueElement.textContent;
      const match = valueText.match(/(\d+)[\/](\d+)/);
      
      if (match && match[1] && match[2]) {
        const value = parseInt(match[1], 10);
        const maxValue = parseInt(match[2], 10);
        const percentage = Math.min(100, (value / maxValue) * 100);
        
        // Animate width change
        bar.style.width = `${percentage}%`;
        
        // Add color based on inventory level
        if (percentage <= 20) {
          bar.style.background = 'linear-gradient(to right, #e74c3c, #e74c3c)';
        } else if (percentage <= 50) {
          bar.style.background = 'linear-gradient(to right, #f39c12, #f39c12)';
        } else {
          bar.style.background = 'linear-gradient(to right, #3498db, #2980b9)';
        }
      }
    }
  });
}

/**
 * Add visual effects to status indicators
 */
function enhanceStatusIndicators() {
  // Style status values based on class
  const statusValues = document.querySelectorAll('.status-value');
  
  statusValues.forEach(status => {
    // Add pulsing effect to statuses that need attention
    if (status.classList.contains('offline') || 
        status.classList.contains('door-open') ||
        status.textContent.includes('Warning') ||
        status.textContent.includes('No')) {
      
      status.classList.add('pulse-attention');
    }
  });
}

/**
 * Add event listeners for interactive dashboard elements
 */
function setupDashboardInteractions() {
  // Make panels expandable on click
  const panels = document.querySelectorAll('.gauge-panel, .status-panel, .inventory-item');
  
  panels.forEach(panel => {
    panel.addEventListener('click', function() {
      // Toggle expanded class
      this.classList.toggle('expanded');
    });
  });
}

/**
 * Set up automatic refresh for real-time data
 * @param {string} machineId - ID of the current machine
 * @param {number} interval - Refresh interval in milliseconds
 */
function setupAutoRefresh(machineId, interval = 30000) {
  // Only set up auto refresh if we're on the operations tab
  const operationsTab = document.querySelector('.tab.active');
  if (operationsTab && operationsTab.textContent.includes('Remote Operations')) {
    // Set up interval for refreshing data
    const refreshInterval = setInterval(() => {
      // Check if we're still on the operations tab
      const activeTab = document.querySelector('.tab.active');
      if (!activeTab || !activeTab.textContent.includes('Remote Operations')) {
        // If we've switched away, clear the interval
        clearInterval(refreshInterval);
        return;
      }
      
      // Refresh the data
      loadRealtimeOperationsData(machineId);
    }, interval);
    
    // Store the interval ID so it can be cleared when switching tabs
    window.activeRefreshInterval = refreshInterval;
  } else if (window.activeRefreshInterval) {
    // Clear any existing refresh interval if we're not on the operations tab
    clearInterval(window.activeRefreshInterval);
    window.activeRefreshInterval = null;
  }
}

/**
 * Initialize the operations dashboard
 */
function initializeOperationsDashboard() {
  // Initialize all components
  initializeGauges();
  updateInventoryBars();
  enhanceStatusIndicators();
  setupDashboardInteractions();
  
  // Get current machine ID for auto-refresh
  const machineSelector = document.getElementById('machine-selector');
  if (machineSelector && machineSelector.value) {
    setupAutoRefresh(machineSelector.value);
  }
}

/**
 * Load real-time operations data for a vending machine
 * @param {string} machineId - ID of the machine to load data for
 */
function loadRealtimeOperationsData(machineId) {
  if (!machineId) return;
  
  // Show loading state
  const statusItems = document.querySelectorAll('.status-value');
  statusItems.forEach(item => {
    item.textContent = 'Loading...';
  });
  
  // Fetch data from API
  console.log(`Fetching operations data from: /api/ice-cream-machines/${machineId}/operations`);
  // Try to use MachineService if available, otherwise make direct fetch
  let dataPromise;
  
  if (window.MachineService && typeof window.MachineService.getOperationsData === 'function') {
    console.log('Using MachineService to get operations data');
    dataPromise = window.MachineService.getOperationsData(machineId);
  } else {
    console.log('MachineService not found or getOperationsData not available, using direct fetch');
    // Direct fetch as fallback
    dataPromise = fetch(`/api/ice-cream-machines/${machineId}/operations`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      });
  }
  
  dataPromise.then(data => {
    console.log('Operations data received:', data);
    // Update loading indicators with real data
    updateStatusIndicators(data);
    updateGaugeValues(data);
    
    // Update inventory data
    if (data && data.ice_cream_inventory) {
      console.log('Updating inventory with:', data.ice_cream_inventory);
      updateInventoryData(data.ice_cream_inventory);
    } else {
      // Use default inventory if none available
      console.log('No inventory data found, using defaults');
      const defaultInventory = [
        { name: 'Vanilla', level: 75, max_capacity: 100 },
        { name: 'Chocolate', level: 60, max_capacity: 100 },
        { name: 'Strawberry', level: 85, max_capacity: 100 },
        { name: 'Mint', level: 45, max_capacity: 100 }
      ];
      updateInventoryData(defaultInventory);
    }
    
    // Initialize components with new data
    setTimeout(() => {
      initializeGauges();
      enhanceStatusIndicators();
    }, 500);
    })
    .catch(error => {
      console.error('Error fetching operations data:', error);
      // Show error state
      setErrorState();
    });
}

/**
 * Update status indicators with real data
 * @param {Object} data - Operations data from API
 */
function updateStatusIndicators(data) {
  // Get status values
  const machineStatus = document.querySelector('.status-item:nth-child(1) .status-value');
  const podCodeStatus = document.querySelector('.status-item:nth-child(2) .status-value');
  const cupDetectStatus = document.querySelector('.status-item:nth-child(3) .status-value');
  const podBinStatus = document.querySelector('.status-item:nth-child(4) .status-value');
  const customerDoorStatus = document.querySelector('.status-item:nth-child(5) .status-value');
  
  // Update with real data if available
  if (data && data.status) {
    if (machineStatus) {
      machineStatus.textContent = data.status.machine || 'Online';
      machineStatus.className = 'status-value ' + (data.status.machine === 'Online' ? 'online' : 'offline');
    }
    
    if (podCodeStatus) {
      podCodeStatus.textContent = data.status.pod_code || 'OK';
      podCodeStatus.className = 'status-value ' + (data.status.pod_code === 'OK' ? 'online' : 'offline');
    }
    
    if (cupDetectStatus) {
      cupDetectStatus.textContent = data.status.cup_detect || 'Present';
      cupDetectStatus.className = 'status-value ' + (data.status.cup_detect === 'Present' ? 'online' : 'offline');
    }
    
    if (podBinStatus) {
      podBinStatus.textContent = data.status.pod_bin || 'Closed';
      podBinStatus.className = 'status-value ' + (data.status.pod_bin === 'Closed' ? 'online' : 'offline');
    }
    
    if (customerDoorStatus) {
      customerDoorStatus.textContent = data.status.customer_door || 'Closed';
      customerDoorStatus.className = 'status-value ' + (data.status.customer_door === 'Closed' ? 'online' : 'offline');
    }
  }
}

/**
 * Update gauge values with real data
 * @param {Object} data - Operations data from API
 */
function updateGaugeValues(data) {
  // Update gauge values if available
  if (data && data.gauges) {
    // Asset Health gauge
    const assetHealthGauge = document.getElementById('asset-health-gauge');
    if (assetHealthGauge && data.gauges.asset_health) {
      assetHealthGauge.setAttribute('data-value', data.gauges.asset_health);
      const assetHealthValue = document.querySelector('#asset-health-panel .gauge-value');
      if (assetHealthValue) {
        assetHealthValue.textContent = data.gauges.asset_health_display || '75%';
      }
    }
    
    // Freezer Temperature gauge
    const freezerTempGauge = document.getElementById('freezer-temp-gauge');
    if (freezerTempGauge && data.gauges.freezer_temp) {
      freezerTempGauge.setAttribute('data-value', data.gauges.freezer_temp);
      const freezerTempValue = document.querySelector('#freezer-temp-panel .gauge-value');
      if (freezerTempValue) {
        freezerTempValue.textContent = data.gauges.freezer_temp_display || '5 °F';
      }
    }
    
    // Dispense Force gauge
    const dispenseForceGauge = document.getElementById('dispense-force-gauge');
    if (dispenseForceGauge && data.gauges.dispense_force) {
      dispenseForceGauge.setAttribute('data-value', data.gauges.dispense_force);
      const dispenseForceValue = document.querySelector('#dispense-force-panel .gauge-value');
      if (dispenseForceValue) {
        dispenseForceValue.textContent = data.gauges.dispense_force_display || '48 lb';
      }
    }
    
    // Cycle Time gauge
    const cycleTimeGauge = document.getElementById('cycle-time-gauge');
    if (cycleTimeGauge && data.gauges.cycle_time) {
      cycleTimeGauge.setAttribute('data-value', data.gauges.cycle_time);
      const cycleTimeValue = document.querySelector('#cycle-time-panel .gauge-value');
      if (cycleTimeValue) {
        cycleTimeValue.textContent = data.gauges.cycle_time_display || '13 sec';
      }
    }
  }
}

/**
 * Set error state for all indicators
 */
function setErrorState() {
  // Update status values to show error
  const statusItems = document.querySelectorAll('.status-value');
  statusItems.forEach(item => {
    item.textContent = 'Error';
    item.className = 'status-value offline';
  });
  
  // Update gauge values to show default
  document.querySelectorAll('.gauge-value').forEach(gauge => {
    gauge.textContent = 'N/A';
  });
}

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Set up tab change listeners to initialize dashboard when tab is changed
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', function() {
      // If this is the operations tab, initialize the dashboard after data is loaded
      if (this.textContent.includes('Remote Operations')) {
        // Wait a bit for data to load
        setTimeout(initializeOperationsDashboard, 1500);
      }
    });
  });
  
  // Initialize with default machine if available
  const machineSelector = document.getElementById('machine-selector');
  if (machineSelector && machineSelector.value) {
    // Load initial data
    loadRealtimeOperationsData(machineSelector.value);
  }
});
