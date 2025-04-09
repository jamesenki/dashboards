/**
 * Device Filters Component
 *
 * Provides filtering capabilities for the water heater dashboard
 * Supporting the device-agnostic IoTSphere architecture with reusable filtering patterns
 */
export class DeviceFilters extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.manufacturers = [];
    this.isLoading = false;
    this.activeFilters = {};

    // Event callback
    this.onFilterChange = null;

    // References to filter elements
    this.filterInputs = {};
  }

  /**
   * Initialize the component with services and event handlers
   */
  initialize({ deviceService, onFilterChange }) {
    this.deviceService = deviceService;
    this.onFilterChange = onFilterChange;

    // Load manufacturers for filtering
    this.loadManufacturers();

    this.render();
  }

  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }

  /**
   * Load manufacturers for filter options
   */
  async loadManufacturers() {
    if (!this.deviceService) return;

    this.isLoading = true;
    this.render();

    try {
      // Get unique manufacturers from the device service
      const manufacturers = await this.deviceService.getManufacturers();

      // Update state
      this.manufacturers = manufacturers;
      this.isLoading = false;

      // Re-render the component
      this.render();

      return manufacturers;
    } catch (error) {
      console.error('Error loading manufacturers:', error);
      this.isLoading = false;
      this.render();

      return [];
    }
  }

  /**
   * Handle filter changes and notify parent
   */
  handleFilterChange() {
    // Get current filter values
    const manufacturerFilter = this.filterInputs.manufacturer?.value || null;
    const connectionStatusFilter = this.filterInputs.connectionStatus?.value || null;
    const onlySimulatedFilter = this.filterInputs.onlySimulated?.checked || false;

    // Build filter object
    const filters = {};

    if (manufacturerFilter && manufacturerFilter !== 'all') {
      filters.manufacturer = manufacturerFilter;
    }

    if (connectionStatusFilter && connectionStatusFilter !== 'all') {
      filters.connectionStatus = connectionStatusFilter;
    }

    if (onlySimulatedFilter) {
      filters.onlySimulated = true;
    }

    // Update active filters
    this.activeFilters = filters;

    // Update active filter badges
    this.updateActiveFilterBadges();

    // Notify parent component
    if (this.onFilterChange) {
      this.onFilterChange(filters);
    }
  }

  /**
   * Update the active filter badges UI
   */
  updateActiveFilterBadges() {
    const activeFiltersContainer = this.shadowRoot.querySelector('.active-filters');
    if (!activeFiltersContainer) return;

    // Clear existing badges
    activeFiltersContainer.innerHTML = '';

    // Check if we have any active filters
    const hasActiveFilters = Object.keys(this.activeFilters).length > 0;

    // Update container visibility
    activeFiltersContainer.style.display = hasActiveFilters ? 'flex' : 'none';

    // If no active filters, nothing more to do
    if (!hasActiveFilters) return;

    // Create badges for each active filter
    Object.entries(this.activeFilters).forEach(([key, value]) => {
      let label = '';

      switch (key) {
        case 'manufacturer':
          label = `Manufacturer: ${value}`;
          break;
        case 'connectionStatus':
          label = `Status: ${value}`;
          break;
        case 'onlySimulated':
          label = 'Simulated Only';
          break;
        default:
          label = `${key}: ${value}`;
      }

      const badge = document.createElement('div');
      badge.className = 'filter-badge';
      badge.innerHTML = `
        <span>${label}</span>
        <button class="badge-remove" data-filter="${key}">×</button>
      `;

      activeFiltersContainer.appendChild(badge);

      // Add click handler to remove button
      const removeButton = badge.querySelector('.badge-remove');
      removeButton.addEventListener('click', () => {
        this.removeFilter(key);
      });
    });

    // Add "Clear all" button if we have multiple filters
    if (Object.keys(this.activeFilters).length > 1) {
      const clearAllButton = document.createElement('button');
      clearAllButton.className = 'clear-all-btn';
      clearAllButton.textContent = 'Clear All';

      clearAllButton.addEventListener('click', () => {
        this.clearAllFilters();
      });

      activeFiltersContainer.appendChild(clearAllButton);
    }
  }

  /**
   * Remove a specific filter
   */
  removeFilter(filterKey) {
    // Update filter input control
    switch (filterKey) {
      case 'manufacturer':
        this.filterInputs.manufacturer.value = 'all';
        break;
      case 'connectionStatus':
        this.filterInputs.connectionStatus.value = 'all';
        break;
      case 'onlySimulated':
        this.filterInputs.onlySimulated.checked = false;
        break;
    }

    // Remove from active filters
    const { [filterKey]: removed, ...remainingFilters } = this.activeFilters;
    this.activeFilters = remainingFilters;

    // Update UI
    this.updateActiveFilterBadges();

    // Notify parent
    if (this.onFilterChange) {
      this.onFilterChange(this.activeFilters);
    }
  }

  /**
   * Clear all active filters
   */
  clearAllFilters() {
    // Reset all filter inputs
    if (this.filterInputs.manufacturer) {
      this.filterInputs.manufacturer.value = 'all';
    }

    if (this.filterInputs.connectionStatus) {
      this.filterInputs.connectionStatus.value = 'all';
    }

    if (this.filterInputs.onlySimulated) {
      this.filterInputs.onlySimulated.checked = false;
    }

    // Clear active filters
    this.activeFilters = {};

    // Update UI
    this.updateActiveFilterBadges();

    // Notify parent
    if (this.onFilterChange) {
      this.onFilterChange({});
    }
  }

  /**
   * Render the component
   */
  render() {
    // Define CSS styles
    const styles = `
      :host {
        display: block;
        width: 100%;
        margin-bottom: 1.5rem;
      }

      .filters-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1rem;
      }

      .filters-title {
        margin: 0 0 1rem 0;
        font-size: 1rem;
        color: #757575;
      }

      .filters-form {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        align-items: center;
      }

      .filter-group {
        display: flex;
        flex-direction: column;
        min-width: 200px;
      }

      .filter-label {
        font-size: 0.8rem;
        color: #757575;
        margin-bottom: 0.3rem;
      }

      .filter-select {
        padding: 0.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        font-family: inherit;
        font-size: 0.9rem;
        background-color: white;
      }

      .checkbox-filter {
        display: flex;
        align-items: center;
        margin-top: 0.5rem;
      }

      .checkbox-filter input {
        margin-right: 0.5rem;
      }

      .active-filters {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #f0f0f0;
        display: none;
      }

      .filter-badge {
        display: flex;
        align-items: center;
        background-color: #E3F2FD;
        color: #2196F3;
        font-size: 0.8rem;
        padding: 0.3rem 0.5rem;
        border-radius: 16px;
      }

      .badge-remove {
        background: none;
        border: none;
        color: #2196F3;
        margin-left: 0.3rem;
        cursor: pointer;
        font-size: 1rem;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .badge-remove:hover {
        color: #1976D2;
      }

      .clear-all-btn {
        background: none;
        border: none;
        color: #757575;
        font-size: 0.8rem;
        cursor: pointer;
        margin-left: auto;
      }

      .clear-all-btn:hover {
        color: #212121;
        text-decoration: underline;
      }

      @media (max-width: 768px) {
        .filters-form {
          flex-direction: column;
          align-items: stretch;
        }

        .filter-group {
          width: 100%;
        }
      }
    `;

    // Define HTML template
    const template = `
      <div class="filters-container">
        <h3 class="filters-title">Filter Devices</h3>

        <div class="filters-form">
          <!-- Manufacturer filter -->
          <div class="filter-group">
            <label class="filter-label" for="manufacturer-filter">Manufacturer</label>
            <select id="manufacturer-filter" class="filter-select">
              <option value="all">All Manufacturers</option>
              ${this.manufacturers.map(manufacturer =>
                `<option value="${manufacturer}">${manufacturer}</option>`
              ).join('')}
            </select>
          </div>

          <!-- Connection status filter -->
          <div class="filter-group">
            <label class="filter-label" for="status-filter">Connection Status</label>
            <select id="status-filter" class="filter-select">
              <option value="all">All Statuses</option>
              <option value="connected">Connected</option>
              <option value="disconnected">Disconnected</option>
            </select>
          </div>

          <!-- Simulated devices filter -->
          <div class="checkbox-filter">
            <input type="checkbox" id="simulated-filter">
            <label for="simulated-filter">Show only simulated devices</label>
          </div>
        </div>

        <!-- Active filters display -->
        <div class="active-filters">
          <!-- Filter badges will be added here dynamically -->
        </div>
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Store references to filter inputs
    this.filterInputs = {
      manufacturer: this.shadowRoot.querySelector('#manufacturer-filter'),
      connectionStatus: this.shadowRoot.querySelector('#status-filter'),
      onlySimulated: this.shadowRoot.querySelector('#simulated-filter')
    };

    // Add event listeners to filters
    if (this.filterInputs.manufacturer) {
      this.filterInputs.manufacturer.addEventListener('change', () => {
        this.handleFilterChange();
      });
    }

    if (this.filterInputs.connectionStatus) {
      this.filterInputs.connectionStatus.addEventListener('change', () => {
        this.handleFilterChange();
      });
    }

    if (this.filterInputs.onlySimulated) {
      this.filterInputs.onlySimulated.addEventListener('change', () => {
        this.handleFilterChange();
      });
    }

    // Initialize active filters display
    this.updateActiveFilterBadges();
  }
}
