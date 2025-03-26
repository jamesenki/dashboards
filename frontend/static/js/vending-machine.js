/**
 * Vending Machine UI Components
 */

// Constants
const MACHINE_MODES = {
  NORMAL: 'Normal',
  MAINTENANCE: 'Maintenance',
  ENERGY_SAVING: 'Energy Saving'
};

const MACHINE_STATUS = {
  OPERATIONAL: 'Operational',
  OUT_OF_ORDER: 'Out of Order',
  RESTOCKING: 'Restocking',
  LOW_PRODUCT: 'Low Product'
};

// Helper functions
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString();
}

function formatCurrency(amount) {
  return amount ? `$${parseFloat(amount).toFixed(2)}` : '$0.00';
}

function formatTemperature(temp) {
  return temp ? `${temp.toFixed(1)}°C` : 'N/A';
}

/**
 * Vending Machine List Component
 */
class VendingMachineList {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.machines = [];
    this.init();
  }

  async init() {
    try {
      await this.loadMachines();
      
      // Validate that we have proper data before rendering
      if (this.machines && Array.isArray(this.machines) && this.machines.length > 0) {
        console.log('Successfully loaded vending machines, rendering...');
        this.render();
      } else {
        console.warn('No vending machines data available or empty array received');
        if (this.machines && Array.isArray(this.machines) && this.machines.length === 0) {
          this.renderEmpty();
        } else {
          this.renderError('No vending machine data available. Please try again later.');
        }
      }
    } catch (error) {
      console.error('Failed to initialize vending machine list:', error);
      this.renderError('Failed to load vending machines. Please try again later.');
    }
  }

  async loadMachines() {
    try {
      console.log('Fetching vending machines from API...');
      
      // Try API call with fallback to direct fetch
      let response;
      try {
        // Use the API client if available
        if (typeof api !== 'undefined' && api.getVendingMachines) {
          response = await api.getVendingMachines();
        } else {
          throw new Error('API client not available');
        }
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch:', apiError);
        
        // Direct fetch fallback
        // Always use localhost:8006 for the API server
        const apiHost = 'localhost';
        // Fix the endpoint to handle redirects - use no trailing slash
        const apiUrl = `http://${apiHost}:8006/api/vending-machines`;
        
        const directResponse = await fetch(apiUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          },
          mode: 'cors',
          redirect: 'follow' // Explicitly follow redirects
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
        this.machines = response.filter(machine => {
          const isValid = machine && typeof machine === 'object' && machine.id;
          if (!isValid) {
            console.warn('Filtering out invalid machine object:', machine);
          }
          return isValid;
        }).map(machine => this.normalizeMachineData(machine));
        
        console.log('Processed machines:', this.machines);
      } else {
        console.error('Invalid API response format, expected array but got:', typeof response);
        this.machines = [];
        throw new Error('Invalid API response format');
      }
    } catch (error) {
      console.error('Error loading vending machines:', error);
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
        <h2>Vending Machines</h2>
        <a href="/vending-machines/new" class="btn btn-primary">Add New</a>
      </div>
      
      <div class="dashboard">
        ${this.machines.map(machine => this.renderMachineCard(machine)).join('')}
      </div>
    `;

    // Add click events for each machine card
    this.machines.forEach(machine => {
      document.getElementById(`machine-${machine.id}`)?.addEventListener('click', () => {
        window.location.href = `/vending-machines/${machine.id}#loaded`;
      });
    });
  }

  renderEmpty() {
    if (!this.container) return;
    
    this.container.innerHTML = `
      <div class="page-header">
        <h2>Vending Machines</h2>
        <a href="/vending-machines/new" class="btn btn-primary">Add New</a>
      </div>
      
      <div class="empty-state">
        <div class="empty-icon">📦</div>
        <h3>No Vending Machines Found</h3>
        <p>Click "Add New" to create your first vending machine.</p>
      </div>
    `;
  }

  renderError(message) {
    if (!this.container) return;
    
    this.container.innerHTML = `
      <div class="page-header">
        <h2>Vending Machines</h2>
        <a href="/vending-machines/new" class="btn btn-primary">Add New</a>
      </div>
      
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <h3>Something Went Wrong</h3>
        <p>${message || 'An error occurred while loading the vending machines.'}</p>
        <button class="btn btn-secondary" onclick="location.reload()">Try Again</button>
      </div>
    `;
  }

  /**
   * Load mock data as a fallback when API fails
   */
  loadMockData() {
    console.log('Loading mock vending machine data as fallback');
    this.machines = [
      {
        id: 'mock-vm-1',
        name: 'Polar Delight #1',
        status: 'ONLINE',
        machine_status: 'OPERATIONAL',
        mode: 'NORMAL',
        temperature: 4.0,
        location: 'Building A, Floor 1',
        current_cash: 125.50,
        cash_capacity: 500.0,
        total_capacity: 50,
        products: [
          {
            product_id: 'PD001',
            name: 'Polar Delight Classic',
            price: 2.50,
            quantity: 10,
            category: 'Beverages',
            location: 'A1'
          }
        ],
        last_reading: {
          timestamp: new Date().toISOString(),
          temperature: 4.0,
          power_consumption: 120.5,
          door_status: 'CLOSED',
          cash_level: 125.50,
          sales_count: 42
        }
      },
      {
        id: 'mock-vm-2',
        name: 'Polar Delight #2',
        status: 'ONLINE',
        machine_status: 'LOW_PRODUCT',
        mode: 'ENERGY_SAVING',
        temperature: 4.5,
        location: 'Building B, Floor 2',
        current_cash: 75.25,
        cash_capacity: 500.0,
        total_capacity: 50,
        products: [
          {
            product_id: 'PD001',
            name: 'Polar Delight Classic',
            price: 2.50,
            quantity: 2,
            category: 'Beverages',
            location: 'A1'
          },
          {
            product_id: 'PD002',
            name: 'Polar Delight Zero',
            price: 2.75,
            quantity: 8,
            category: 'Beverages',
            location: 'A2'
          }
        ],
        last_reading: {
          timestamp: new Date().toISOString(),
          temperature: 4.5,
          power_consumption: 90.5,
          door_status: 'CLOSED',
          cash_level: 75.25,
          sales_count: 28
        }
      }
    ].map(machine => this.normalizeMachineData(machine));
  }
  
  renderMachineCard(machine) {
    // Get inventory count
    const totalProducts = machine.products?.length || 0;
    const totalItems = machine.products?.reduce((sum, p) => sum + (p.quantity || 0), 0) || 0;
    const capacityPercentage = machine.total_capacity ? Math.min(100, Math.round((totalItems / machine.total_capacity) * 100)) : 0;
    
    // Get cash level
    const cashPercentage = machine.cash_capacity ? Math.min(100, Math.round((machine.current_cash / machine.cash_capacity) * 100)) : 0;
    
    // Determine status classes
    const statusClass = {
      'OPERATIONAL': 'status-success',
      'LOW_PRODUCT': 'status-warning',
      'RESTOCKING': 'status-info',
      'OUT_OF_ORDER': 'status-danger'
    }[machine.machine_status] || 'status-secondary';
    
    // Get last reading info
    const lastReading = machine.last_reading || {};
    
    return `
      <div id="machine-${machine.id}" class="device-card ${statusClass}">
        <div class="device-card-header">
          <div class="device-icon">
            <img src="/static/assets/images/vending-machine.png" alt="Vending Machine">
          </div>
          <div class="device-title">
            <h3>${machine.name || 'Unnamed Device'}</h3>
            <div class="device-status">
              <span class="status-indicator ${statusClass}"></span>
              ${MACHINE_STATUS[machine.machine_status] || 'Unknown'}
            </div>
          </div>
        </div>
        
        <div class="device-card-body">
          <div class="device-info">
            <div class="info-row">
              <span class="info-label">Location:</span>
              <span class="info-value">${machine.location || 'Not specified'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Mode:</span>
              <span class="info-value">${MACHINE_MODES[machine.mode] || 'Unknown'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Temperature:</span>
              <span class="info-value">${formatTemperature(machine.temperature)}</span>
            </div>
          </div>
          
          <div class="device-metrics">
            <div class="metric">
              <div class="metric-title">Cash Level</div>
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${cashPercentage}%"></div>
              </div>
              <div class="metric-value">${formatCurrency(machine.current_cash)}</div>
            </div>
            
            <div class="metric">
              <div class="metric-title">Inventory</div>
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${capacityPercentage}%"></div>
              </div>
              <div class="metric-value">${totalItems}/${machine.total_capacity || '?'} items</div>
            </div>
          </div>
        </div>
        
        <div class="device-card-footer">
          <div class="last-updated">Last updated: ${formatDate(lastReading.timestamp || new Date())}</div>
          <button class="btn btn-sm btn-primary">Details</button>
        </div>
      </div>
    `;
  }
  
  normalizeMachineData(machine) {
    // Create a copy with all required fields properly initialized
    return {
      id: machine.id || `temp-${Math.random().toString(36).substring(2, 10)}`,
      name: machine.name || 'Unnamed Vending Machine',
      status: machine.status || 'OFFLINE',
      machine_status: machine.machine_status || 'OPERATIONAL',
      mode: machine.mode || 'NORMAL',
      temperature: machine.temperature !== undefined ? machine.temperature : null,
      location: machine.location || '',
      current_cash: machine.current_cash !== undefined ? machine.current_cash : 0,
      cash_capacity: machine.cash_capacity || 500,
      total_capacity: machine.total_capacity || 50,
      products: Array.isArray(machine.products) ? machine.products : [],
      readings: Array.isArray(machine.readings) ? machine.readings : [],
      last_reading: machine.readings && machine.readings.length > 0 ? 
        machine.readings[machine.readings.length - 1] : 
        (machine.last_reading || null)
    };
  }
}

/**
 * Vending Machine Detail Component
 */
class VendingMachineDetail {
  constructor(containerId, machineId) {
    this.container = document.getElementById(containerId);
    this.machineId = machineId;
    this.machine = null;
    this.productCharts = {};
    this.temperatureChart = null;
    this.init();
  }

  async init() {
    try {
      await this.loadMachine();
      
      if (this.machine) {
        this.render();
        this.initCharts();
        this.setupEventListeners();
      } else {
        this.renderError('Unable to load vending machine details');
      }
    } catch (error) {
      console.error('Failed to initialize vending machine detail:', error);
      this.renderError('Failed to load vending machine. Please try again later.');
    }
  }

  async loadMachine() {
    try {
      let response;
      const apiUrl = `/api/vending-machines/${this.machineId}`;
      
      try {
        // Use the API client if available
        if (typeof api !== 'undefined' && api.getVendingMachine) {
          response = await api.getVendingMachine(this.machineId);
        } else {
          throw new Error('API client not available');
        }
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch:', apiError);
        
        // Direct fetch fallback
        const apiHost = window.location.hostname;
        const directUrl = `http://${apiHost}:8006${apiUrl}`;
        
        const directResponse = await fetch(directUrl, {
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
      }
      
      if (response && response.id) {
        this.machine = this.normalizeMachineData(response);
        console.log('Loaded machine detail:', this.machine);
      } else {
        console.error('Invalid API response format:', response);
        throw new Error('Invalid API response format');
      }
    } catch (error) {
      console.error('Error loading vending machine:', error);
      // Try to load mock data as fallback
      this.loadMockData();
      throw error;
    }
  }

  loadMockData() {
    console.log('Loading mock vending machine data as fallback');
    this.machine = {
      id: this.machineId || 'mock-vm-1',
      name: 'Polar Delight #1',
      status: 'ONLINE',
      machine_status: 'OPERATIONAL',
      mode: 'NORMAL',
      temperature: 4.0,
      location: 'Building A, Floor 1',
      model_number: 'PD-2000',
      serial_number: 'PD2023-12345',
      current_cash: 125.50,
      cash_capacity: 500.0,
      total_capacity: 50,
      products: [
        {
          product_id: 'PD001',
          name: 'Polar Delight Classic',
          price: 2.50,
          quantity: 10,
          category: 'Beverages',
          location: 'A1'
        },
        {
          product_id: 'PD002',
          name: 'Polar Delight Zero',
          price: 2.75,
          quantity: 8,
          category: 'Beverages',
          location: 'A2'
        }
      ],
      readings: Array.from({ length: 24 }, (_, i) => {
        const timestamp = new Date();
        timestamp.setHours(timestamp.getHours() - i);
        return {
          timestamp: timestamp.toISOString(),
          temperature: 4.0 + Math.random() * 0.5,
          power_consumption: 100 + Math.random() * 30,
          door_status: Math.random() > 0.9 ? 'OPEN' : 'CLOSED',
          cash_level: 125.50 - (i * 2),
          sales_count: 42 - i
        };
      }).reverse()
    };
  }

  render() {
    if (!this.container || !this.machine) return;

    const lastReading = this.machine.readings && this.machine.readings.length > 0 ? 
      this.machine.readings[this.machine.readings.length - 1] : {};
    
    const statusClass = {
      'OPERATIONAL': 'status-success',
      'LOW_PRODUCT': 'status-warning',
      'RESTOCKING': 'status-info',
      'OUT_OF_ORDER': 'status-danger'
    }[this.machine.machine_status] || 'status-secondary';
    
    this.container.innerHTML = `
      <div class="device-detail ${statusClass}">
        <div class="device-header">
          <div class="device-title">
            <h1>${this.machine.name}</h1>
            <div class="device-status">
              <span class="status-indicator ${statusClass}"></span>
              ${MACHINE_STATUS[this.machine.machine_status] || 'Unknown'}
            </div>
          </div>
          <div class="device-actions">
            <a href="/vending-machines/${this.machine.id}/edit" class="btn btn-primary">Edit</a>
          </div>
        </div>

        <div class="device-info-panel">
          <div class="info-section">
            <h3>Details</h3>
            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">Location</div>
                <div class="info-value">${this.machine.location || 'Not specified'}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Model</div>
                <div class="info-value">${this.machine.model_number || 'Not specified'}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Serial Number</div>
                <div class="info-value">${this.machine.serial_number || 'Not specified'}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Mode</div>
                <div class="info-value">${MACHINE_MODES[this.machine.mode] || 'Unknown'}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Temperature</div>
                <div class="info-value">${formatTemperature(lastReading.temperature || this.machine.temperature)}</div>
              </div>
              <div class="info-item">
                <div class="info-label">Cash Level</div>
                <div class="info-value">${formatCurrency(lastReading.cash_level || this.machine.current_cash)}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="device-dashboard">
          <div class="dashboard-section">
            <h3>Inventory</h3>
            <div class="inventory-container">
              <div class="inventory-header">
                <div class="inventory-col product-id">ID</div>
                <div class="inventory-col product-name">Product</div>
                <div class="inventory-col product-price">Price</div>
                <div class="inventory-col product-quantity">Quantity</div>
                <div class="inventory-col product-location">Location</div>
                <div class="inventory-col product-actions">Actions</div>
              </div>
              <div class="inventory-body">
                ${this.renderProductList()}
              </div>
              <div class="inventory-footer">
                <button id="add-product-btn" class="btn btn-primary">Add Product</button>
              </div>
            </div>
          </div>

          <div class="dashboard-section">
            <h3>Temperature History</h3>
            <div class="chart-container">
              <canvas id="temperature-chart"></canvas>
            </div>
          </div>

          <div class="dashboard-section">
            <h3>Recent Activity</h3>
            <div class="activity-list">
              ${this.renderActivityList()}
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  renderError(message) {
    if (!this.container) return;
    
    this.container.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <h3>Something Went Wrong</h3>
        <p>${message || 'An error occurred while loading the vending machine.'}</p>
        <button class="btn btn-secondary" onclick="location.reload()">Try Again</button>
      </div>
    `;
  }
  
  renderProductList() {
    if (!this.machine.products || !this.machine.products.length) {
      return `<div class="empty-inventory">No products in inventory. Add products to get started.</div>`;
    }
    
    return this.machine.products.map(product => {
      // Calculate stock status
      let stockStatus = 'normal';
      if (product.quantity <= 0) {
        stockStatus = 'out';
      } else if (product.quantity < 3) {
        stockStatus = 'low';
      }
      
      return `
        <div class="inventory-row ${stockStatus}" data-product-id="${product.product_id}">
          <div class="inventory-col product-id">${product.product_id}</div>
          <div class="inventory-col product-name">${product.name}</div>
          <div class="inventory-col product-price">${formatCurrency(product.price)}</div>
          <div class="inventory-col product-quantity">${product.quantity}</div>
          <div class="inventory-col product-location">${product.location || 'N/A'}</div>
          <div class="inventory-col product-actions">
            <button class="btn btn-sm btn-secondary product-adjust-btn" data-action="decrease">-</button>
            <button class="btn btn-sm btn-secondary product-adjust-btn" data-action="increase">+</button>
          </div>
        </div>
      `;
    }).join('');
  }
  
  renderActivityList() {
    if (!this.machine.readings || !this.machine.readings.length) {
      return `<div class="empty-activity">No recent activity available.</div>`;
    }
    
    // Show last 10 readings
    const recentReadings = this.machine.readings.slice(-10).reverse();
    
    return recentReadings.map(reading => {
      const doorStatus = reading.door_status === 'OPEN' ? 'opened' : 'closed';
      const salesInfo = reading.sales_count ? `${reading.sales_count} sales registered` : '';
      
      return `
        <div class="activity-item">
          <div class="activity-time">${formatDate(reading.timestamp)}</div>
          <div class="activity-description">
            <div>Temperature: ${formatTemperature(reading.temperature)}</div>
            <div>Power: ${reading.power_consumption ? reading.power_consumption.toFixed(1) + 'W' : 'N/A'}</div>
            ${reading.door_status ? `<div>Door ${doorStatus}</div>` : ''}
            ${salesInfo ? `<div>${salesInfo}</div>` : ''}
          </div>
        </div>
      `;
    }).join('');
  }
  
  initCharts() {
    // Initialize temperature chart if Chart.js is available
    if (typeof Chart !== 'undefined' && this.machine.readings && this.machine.readings.length > 0) {
      const ctx = document.getElementById('temperature-chart');
      if (ctx) {
        const readings = this.machine.readings.slice(-24); // Last 24 readings
        
        const data = {
          labels: readings.map(r => {
            const date = new Date(r.timestamp);
            return date.getHours() + ':' + date.getMinutes().toString().padStart(2, '0');
          }),
          datasets: [{
            label: 'Temperature (°C)',
            data: readings.map(r => r.temperature),
            borderColor: '#4bc0c0',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 2,
            tension: 0.2
          }]
        };
        
        this.temperatureChart = new Chart(ctx, {
          type: 'line',
          data: data,
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'top',
              },
              title: {
                display: true,
                text: 'Temperature History'
              }
            },
            scales: {
              y: {
                beginAtZero: false,
                suggestedMin: Math.min(...readings.map(r => r.temperature)) - 1,
                suggestedMax: Math.max(...readings.map(r => r.temperature)) + 1
              }
            }
          }
        });
      }
    }
  }
  
  setupEventListeners() {
    // Add product button
    const addProductBtn = document.getElementById('add-product-btn');
    if (addProductBtn) {
      addProductBtn.addEventListener('click', () => this.openAddProductModal());
    }
    
    // Product quantity adjustment buttons
    const adjustBtns = document.querySelectorAll('.product-adjust-btn');
    adjustBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const action = e.target.dataset.action;
        const productRow = e.target.closest('.inventory-row');
        const productId = productRow.dataset.productId;
        
        const quantityChange = action === 'increase' ? 1 : -1;
        this.updateProductQuantity(productId, quantityChange);
      });
    });
  }
  
  async updateProductQuantity(productId, quantityChange) {
    try {
      const apiUrl = `/api/vending-machines/${this.machineId}/products/${productId}/quantity`;
      const data = { quantity_change: quantityChange };
      
      // Try to use API client if available
      let response;
      try {
        if (typeof api !== 'undefined' && api.updateProductQuantity) {
          response = await api.updateProductQuantity(this.machineId, productId, quantityChange);
        } else {
          throw new Error('API client not available');
        }
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch:', apiError);
        
        // Direct fetch fallback
        const apiHost = window.location.hostname;
        const directUrl = `http://${apiHost}:8006${apiUrl}`;
        
        const directResponse = await fetch(directUrl, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(data),
          mode: 'cors'
        });
        
        if (!directResponse.ok) {
          throw new Error(`Direct API fetch failed: ${directResponse.status} ${directResponse.statusText}`);
        }
        
        response = await directResponse.json();
      }
      
      // Update the machine data and re-render
      if (response && response.id) {
        this.machine = this.normalizeMachineData(response);
        this.render();
        this.initCharts();
        this.setupEventListeners();
      }
    } catch (error) {
      console.error('Error updating product quantity:', error);
      alert('Failed to update product quantity. Please try again.');
    }
  }
  
  openAddProductModal() {
    // In a full implementation, this would open a modal for adding a new product
    alert('Add product functionality would be implemented here');
  }
  
  normalizeMachineData(machine) {
    // Create a copy with all required fields properly initialized
    return {
      id: machine.id || `temp-${Math.random().toString(36).substring(2, 10)}`,
      name: machine.name || 'Unnamed Vending Machine',
      status: machine.status || 'OFFLINE',
      machine_status: machine.machine_status || 'OPERATIONAL',
      mode: machine.mode || 'NORMAL',
      temperature: machine.temperature !== undefined ? machine.temperature : null,
      location: machine.location || '',
      model_number: machine.model_number || '',
      serial_number: machine.serial_number || '',
      current_cash: machine.current_cash !== undefined ? machine.current_cash : 0,
      cash_capacity: machine.cash_capacity || 500,
      total_capacity: machine.total_capacity || 50,
      products: Array.isArray(machine.products) ? machine.products : [],
      readings: Array.isArray(machine.readings) ? machine.readings : [],
      last_reading: machine.readings && machine.readings.length > 0 ? 
        machine.readings[machine.readings.length - 1] : 
        (machine.last_reading || null)
    };
  }
}

/**
 * Vending Machine Form Component
 */
class VendingMachineForm {
  constructor(containerId, machineId = null) {
    this.container = document.getElementById(containerId);
    this.machineId = machineId; // If provided, we're editing an existing machine
    this.machine = null;
    this.init();
  }

  async init() {
    try {
      if (this.machineId) {
        // Load existing machine for editing
        await this.loadMachine();
      }
      this.render();
    } catch (error) {
      console.error('Failed to initialize vending machine form:', error);
      this.renderError('Failed to load form. Please try again later.');
    }
  }

  async loadMachine() {
    try {
      let response;
      const apiUrl = `/api/vending-machines/${this.machineId}`;
      
      try {
        // Use the API client if available
        if (typeof api !== 'undefined' && api.getVendingMachine) {
          response = await api.getVendingMachine(this.machineId);
        } else {
          throw new Error('API client not available');
        }
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch:', apiError);
        
        // Direct fetch fallback
        const apiHost = window.location.hostname;
        const directUrl = `http://${apiHost}:8006${apiUrl}`;
        
        const directResponse = await fetch(directUrl, {
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
      }
      
      if (response && response.id) {
        this.machine = response;
        console.log('Loaded machine for editing:', this.machine);
      } else {
        console.error('Invalid API response format:', response);
        throw new Error('Invalid API response format');
      }
    } catch (error) {
      console.error('Error loading vending machine for editing:', error);
      throw error;
    }
  }

  async saveMachine(formData) {
    try {
      const isEditing = !!this.machineId;
      const apiUrl = isEditing ? 
        `/api/vending-machines/${this.machineId}` : 
        '/api/vending-machines';
      
      const method = isEditing ? 'PATCH' : 'POST';
      
      // Try to use API client if available
      let response;
      try {
        if (typeof api !== 'undefined') {
          if (isEditing && api.updateVendingMachine) {
            response = await api.updateVendingMachine(this.machineId, formData);
          } else if (!isEditing && api.createVendingMachine) {
            response = await api.createVendingMachine(formData);
          } else {
            throw new Error('API client method not available');
          }
        } else {
          throw new Error('API client not available');
        }
      } catch (apiError) {
        console.warn('API client request failed, trying direct fetch:', apiError);
        
        // Direct fetch fallback
        const apiHost = window.location.hostname;
        const directUrl = `http://${apiHost}:8006${apiUrl}`;
        
        const directResponse = await fetch(directUrl, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(formData),
          mode: 'cors'
        });
        
        if (!directResponse.ok) {
          throw new Error(`Direct API fetch failed: ${directResponse.status} ${directResponse.statusText}`);
        }
        
        response = await directResponse.json();
      }
      
      if (response && response.id) {
        // Redirect to the detail page for the saved machine
        window.location.href = `/vending-machines/${response.id}`;
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Error saving vending machine:', error);
      alert('Failed to save vending machine. Please try again.');
      throw error;
    }
  }

  render() {
    if (!this.container) return;
    
    const isEditing = !!this.machineId;
    const title = isEditing ? 'Edit Vending Machine' : 'Add New Vending Machine';
    
    this.container.innerHTML = `
      <div class="form-container">
        <h2>${title}</h2>
        <form id="vending-machine-form">
          <div class="form-group">
            <label for="name">Name</label>
            <input type="text" id="name" name="name" class="form-control" required 
              value="${isEditing && this.machine ? this.machine.name : ''}">
          </div>
          
          <div class="form-group">
            <label for="location">Location</label>
            <input type="text" id="location" name="location" class="form-control" 
              value="${isEditing && this.machine ? this.machine.location || '' : ''}">
          </div>
          
          <div class="form-group">
            <label for="model_number">Model Number</label>
            <input type="text" id="model_number" name="model_number" class="form-control" 
              value="${isEditing && this.machine ? this.machine.model_number || '' : ''}">
          </div>
          
          <div class="form-group">
            <label for="serial_number">Serial Number</label>
            <input type="text" id="serial_number" name="serial_number" class="form-control" 
              value="${isEditing && this.machine ? this.machine.serial_number || '' : ''}">
          </div>
          
          <div class="form-group">
            <label for="temperature">Temperature (°C)</label>
            <input type="number" id="temperature" name="temperature" step="0.1" class="form-control" 
              value="${isEditing && this.machine && this.machine.temperature !== null ? this.machine.temperature : '4.0'}">
          </div>
          
          <div class="form-group">
            <label for="total_capacity">Total Capacity</label>
            <input type="number" id="total_capacity" name="total_capacity" class="form-control" 
              value="${isEditing && this.machine ? this.machine.total_capacity || '50' : '50'}">
          </div>
          
          <div class="form-group">
            <label for="cash_capacity">Cash Capacity</label>
            <input type="number" id="cash_capacity" name="cash_capacity" step="0.01" class="form-control" 
              value="${isEditing && this.machine ? this.machine.cash_capacity || '500.00' : '500.00'}">
          </div>
          
          ${isEditing ? `
          <div class="form-group">
            <label for="current_cash">Current Cash</label>
            <input type="number" id="current_cash" name="current_cash" step="0.01" class="form-control" 
              value="${this.machine ? this.machine.current_cash || '0.00' : '0.00'}">
          </div>
          
          <div class="form-group">
            <label for="machine_status">Status</label>
            <select id="machine_status" name="machine_status" class="form-control">
              ${Object.entries(MACHINE_STATUS).map(([value, label]) => 
                `<option value="${value}" ${this.machine && this.machine.machine_status === value ? 'selected' : ''}>${label}</option>`
              ).join('')}
            </select>
          </div>
          
          <div class="form-group">
            <label for="mode">Mode</label>
            <select id="mode" name="mode" class="form-control">
              ${Object.entries(MACHINE_MODES).map(([value, label]) => 
                `<option value="${value}" ${this.machine && this.machine.mode === value ? 'selected' : ''}>${label}</option>`
              ).join('')}
            </select>
          </div>
          ` : ''}
          
          <div class="form-actions">
            <button type="submit" class="btn btn-primary">Save</button>
            <a href="${isEditing ? `/vending-machines/${this.machineId}` : '/vending-machines'}" class="btn btn-secondary">Cancel</a>
          </div>
        </form>
      </div>
    `;
    
    // Set up form submission handler
    const form = document.getElementById('vending-machine-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleFormSubmit(form);
      });
    }
  }
  
  handleFormSubmit(form) {
    const formData = {};
    
    // Get form field values
    formData.name = form.elements.name.value.trim();
    formData.location = form.elements.location.value.trim() || null;
    formData.model_number = form.elements.model_number.value.trim() || null;
    formData.serial_number = form.elements.serial_number.value.trim() || null;
    formData.temperature = parseFloat(form.elements.temperature.value) || null;
    formData.total_capacity = parseInt(form.elements.total_capacity.value) || null;
    formData.cash_capacity = parseFloat(form.elements.cash_capacity.value) || null;
    
    if (this.machineId) {
      // Additional fields for editing
      formData.current_cash = parseFloat(form.elements.current_cash.value) || null;
      formData.machine_status = form.elements.machine_status.value;
      formData.mode = form.elements.mode.value;
    }
    
    // Save the vending machine
    this.saveMachine(formData);
  }
  
  renderError(message) {
    if (!this.container) return;
    
    this.container.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <h3>Something Went Wrong</h3>
        <p>${message || 'An error occurred while loading the form.'}</p>
        <button class="btn btn-secondary" onclick="location.reload()">Try Again</button>
      </div>
    `;
  }
}
