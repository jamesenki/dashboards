/**
 * Device Events Component
 *
 * Displays event history and activity logs for water heater devices
 * Part of the device-agnostic IoTSphere platform architecture
 */
export class DeviceEvents extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.device = null;
    this.deviceId = null;
    this.events = [];
    this.isLoading = true;
    this.error = null;

    // Filtering and pagination
    this.filterType = 'all';
    this.currentPage = 1;
    this.eventsPerPage = 10;
    this.totalPages = 1;
  }

  /**
   * Initialize the component
   */
  initialize({ device, deviceId }) {
    this.device = device;
    this.deviceId = deviceId || (device ? device.device_id : null);

    this.render();

    // Data will be loaded when the tab becomes visible via the refresh() method
  }

  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }

  /**
   * Load device events
   */
  async loadEvents() {
    if (!this.deviceId) return;

    this.isLoading = true;
    this.error = null;
    this.render();

    try {
      // In a real implementation, this would call an API endpoint
      // For now, we'll use mock data
      const response = await this.fetchDeviceEvents();

      this.events = response.events;
      this.totalPages = Math.ceil(this.events.length / this.eventsPerPage);
      this.isLoading = false;
      this.render();

      return response.events;
    } catch (error) {
      console.error('Error loading device events:', error);
      this.error = 'Failed to load device events';
      this.isLoading = false;
      this.render();

      return [];
    }
  }

  /**
   * Refresh the data
   */
  refresh() {
    return this.loadEvents();
  }

  /**
   * Filter events by type
   */
  filterEvents(type) {
    this.filterType = type;
    this.currentPage = 1; // Reset to first page when filtering
    this.render();
  }

  /**
   * Change page
   */
  changePage(page) {
    if (page < 1 || page > this.totalPages) return;

    this.currentPage = page;
    this.render();
  }

  /**
   * Get current page of events after filtering
   */
  getCurrentPageEvents() {
    // Apply filter
    const filteredEvents = this.filterType === 'all'
      ? this.events
      : this.events.filter(event => event.category === this.filterType);

    // Update total pages based on filtered results
    this.totalPages = Math.ceil(filteredEvents.length / this.eventsPerPage);

    // Get current page
    const startIndex = (this.currentPage - 1) * this.eventsPerPage;
    return filteredEvents.slice(startIndex, startIndex + this.eventsPerPage);
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
      }

      .events-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
      }

      .events-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
      }

      .events-title {
        font-size: 1.2rem;
        font-weight: 500;
        margin: 0;
      }

      .filter-container {
        display: flex;
        gap: 0.5rem;
      }

      .filter-button {
        padding: 0.4rem 0.8rem;
        border-radius: 16px;
        font-size: 0.8rem;
        cursor: pointer;
        background-color: #f5f5f5;
        border: none;
      }

      .filter-button.active {
        background-color: #2196F3;
        color: white;
      }

      .events-table {
        width: 100%;
        border-collapse: collapse;
      }

      .events-table th {
        text-align: left;
        padding: 0.75rem 1rem;
        border-bottom: 2px solid #e0e0e0;
        font-weight: 500;
      }

      .events-table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f0f0f0;
      }

      .events-table tr:last-child td {
        border-bottom: none;
      }

      .event-timestamp {
        color: #757575;
        font-size: 0.9rem;
        white-space: nowrap;
      }

      .event-type {
        display: flex;
        align-items: center;
      }

      .event-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.5rem;
        font-size: 0.8rem;
        color: white;
      }

      .event-icon.status { background-color: #2196F3; }
      .event-icon.alert { background-color: #F44336; }
      .event-icon.maintenance { background-color: #FF9800; }
      .event-icon.user { background-color: #4CAF50; }
      .event-icon.system { background-color: #9C27B0; }

      .event-description {
        font-size: 0.9rem;
      }

      .event-details {
        font-size: 0.85rem;
        color: #757575;
        margin-top: 0.25rem;
      }

      .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 1.5rem;
        gap: 0.5rem;
      }

      .page-button {
        width: 32px;
        height: 32px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        border: 1px solid #e0e0e0;
        background-color: white;
      }

      .page-button.active {
        background-color: #2196F3;
        color: white;
        border-color: #2196F3;
      }

      .page-button:hover:not(.active) {
        background-color: #f5f5f5;
      }

      .page-button.disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .loading-container {
        padding: 3rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }

      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(33, 150, 243, 0.2);
        border-top: 4px solid #2196F3;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .error-container {
        padding: 1.5rem;
        background-color: #FFEBEE;
        color: #F44336;
        border-radius: 4px;
        text-align: center;
      }

      .empty-container {
        padding: 3rem;
        text-align: center;
        color: #757575;
      }
    `;

    // Define HTML template
    let contentHtml;

    if (this.isLoading) {
      contentHtml = `
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <div>Loading device events...</div>
        </div>
      `;
    } else if (this.error) {
      contentHtml = `
        <div class="error-container">
          <div>${this.error}</div>
          <button class="filter-button" id="retry-button">Retry</button>
        </div>
      `;
    } else if (this.events.length === 0) {
      contentHtml = `
        <div class="empty-container">
          <div>No events found for this device</div>
        </div>
      `;
    } else {
      const currentEvents = this.getCurrentPageEvents();

      contentHtml = `
        <div class="events-header">
          <h3 class="events-title">Device Events</h3>

          <div class="filter-container">
            <button class="filter-button ${this.filterType === 'all' ? 'active' : ''}" data-filter="all">
              All
            </button>
            <button class="filter-button ${this.filterType === 'status' ? 'active' : ''}" data-filter="status">
              Status
            </button>
            <button class="filter-button ${this.filterType === 'alert' ? 'active' : ''}" data-filter="alert">
              Alerts
            </button>
            <button class="filter-button ${this.filterType === 'maintenance' ? 'active' : ''}" data-filter="maintenance">
              Maintenance
            </button>
            <button class="filter-button ${this.filterType === 'user' ? 'active' : ''}" data-filter="user">
              User Actions
            </button>
            <button class="filter-button ${this.filterType === 'system' ? 'active' : ''}" data-filter="system">
              System
            </button>
          </div>
        </div>

        <table class="events-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Type</th>
              <th>Event</th>
            </tr>
          </thead>
          <tbody>
            ${currentEvents.length === 0 ? `
              <tr>
                <td colspan="3" class="empty-container">No events match the selected filter</td>
              </tr>
            ` : currentEvents.map(event => `
              <tr>
                <td class="event-timestamp">${this.formatTimestamp(event.timestamp)}</td>
                <td class="event-type">
                  <div class="event-icon ${event.category}">${this.getEventIcon(event.category)}</div>
                  ${this.formatEventType(event.category)}
                </td>
                <td>
                  <div class="event-description">${event.description}</div>
                  ${event.details ? `<div class="event-details">${event.details}</div>` : ''}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        ${this.totalPages > 1 ? this.renderPagination() : ''}
      `;
    }

    const template = `
      <div class="events-container">
        ${contentHtml}
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Add event listeners
    this.addEventListeners();
  }

  /**
   * Render pagination controls
   */
  renderPagination() {
    // Determine which page buttons to show
    let pageButtons = [];

    // Always show first page
    pageButtons.push(1);

    // Show ellipsis if there's a gap after page 1
    if (this.currentPage > 3) {
      pageButtons.push('...');
    }

    // Show adjacent pages
    for (let i = Math.max(2, this.currentPage - 1); i <= Math.min(this.totalPages - 1, this.currentPage + 1); i++) {
      if (!pageButtons.includes(i)) {
        pageButtons.push(i);
      }
    }

    // Show ellipsis if there's a gap before last page
    if (this.currentPage < this.totalPages - 2) {
      pageButtons.push('...');
    }

    // Always show last page if there is more than one page
    if (this.totalPages > 1 && !pageButtons.includes(this.totalPages)) {
      pageButtons.push(this.totalPages);
    }

    return `
      <div class="pagination">
        <button class="page-button ${this.currentPage === 1 ? 'disabled' : ''}" id="prev-page">
          &laquo;
        </button>

        ${pageButtons.map(page => {
          if (page === '...') {
            return `<span>...</span>`;
          }
          return `
            <button class="page-button ${page === this.currentPage ? 'active' : ''}" data-page="${page}">
              ${page}
            </button>
          `;
        }).join('')}

        <button class="page-button ${this.currentPage === this.totalPages ? 'disabled' : ''}" id="next-page">
          &raquo;
        </button>
      </div>
    `;
  }

  /**
   * Add event listeners
   */
  addEventListeners() {
    // Filter buttons
    const filterButtons = this.shadowRoot.querySelectorAll('[data-filter]');
    filterButtons.forEach(button => {
      button.addEventListener('click', () => {
        const filterType = button.getAttribute('data-filter');
        this.filterEvents(filterType);
      });
    });

    // Page buttons
    const pageButtons = this.shadowRoot.querySelectorAll('[data-page]');
    pageButtons.forEach(button => {
      button.addEventListener('click', () => {
        const page = parseInt(button.getAttribute('data-page'));
        this.changePage(page);
      });
    });

    // Previous page button
    const prevButton = this.shadowRoot.querySelector('#prev-page');
    if (prevButton) {
      prevButton.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.changePage(this.currentPage - 1);
        }
      });
    }

    // Next page button
    const nextButton = this.shadowRoot.querySelector('#next-page');
    if (nextButton) {
      nextButton.addEventListener('click', () => {
        if (this.currentPage < this.totalPages) {
          this.changePage(this.currentPage + 1);
        }
      });
    }

    // Retry button
    const retryButton = this.shadowRoot.querySelector('#retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => {
        this.refresh();
      });
    }
  }

  /**
   * Get icon for event category
   */
  getEventIcon(category) {
    switch (category) {
      case 'status': return '↻';
      case 'alert': return '!';
      case 'maintenance': return '⚙';
      case 'user': return '👤';
      case 'system': return '💻';
      default: return '•';
    }
  }

  /**
   * Format event type for display
   */
  formatEventType(category) {
    switch (category) {
      case 'status': return 'Status Change';
      case 'alert': return 'Alert';
      case 'maintenance': return 'Maintenance';
      case 'user': return 'User Action';
      case 'system': return 'System';
      default: return category;
    }
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';

    try {
      const date = new Date(timestamp);

      // If it's today, show time only
      const today = new Date();
      if (date.toDateString() === today.toDateString()) {
        return `Today ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }

      // If it's yesterday, show "Yesterday"
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }

      // If it's within last 7 days, show day name
      const lastWeek = new Date();
      lastWeek.setDate(lastWeek.getDate() - 7);
      if (date > lastWeek) {
        return date.toLocaleDateString([], { weekday: 'short' }) +
               ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      }

      // Otherwise show date and time
      return date.toLocaleDateString() + ' ' +
             date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return timestamp;
    }
  }

  /**
   * Simulate fetching device events from an API
   * In a real implementation, this would be an actual API call
   */
  async fetchDeviceEvents() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Generate mock events based on device ID
    const events = [];
    const baseTime = new Date();

    // Status events
    events.push({
      id: `ev-status-1-${this.deviceId}`,
      category: 'status',
      description: 'Device connected',
      details: 'Device established a stable connection to the IoTSphere platform.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 2).toISOString() // 2 hours ago
    });

    events.push({
      id: `ev-status-2-${this.deviceId}`,
      category: 'status',
      description: 'Heating cycle started',
      details: 'Water temperature dropped below setpoint, heating element activated.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 4).toISOString() // 4 hours ago
    });

    events.push({
      id: `ev-status-3-${this.deviceId}`,
      category: 'status',
      description: 'Heating cycle completed',
      details: 'Water temperature reached setpoint, heating element deactivated.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 3.5).toISOString() // 3.5 hours ago
    });

    // Maintenance events
    events.push({
      id: `ev-maint-1-${this.deviceId}`,
      category: 'maintenance',
      description: 'Scheduled maintenance performed',
      details: 'Regular maintenance and inspection completed. Anode rod replaced and sediment flushed.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * 30).toISOString() // 30 days ago
    });

    // Alert events
    events.push({
      id: `ev-alert-1-${this.deviceId}`,
      category: 'alert',
      description: 'High pressure detected',
      details: 'Pressure briefly exceeded recommended levels but returned to normal range. Possible expansion tank issue.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 12).toISOString() // 12 hours ago
    });

    // User events
    events.push({
      id: `ev-user-1-${this.deviceId}`,
      category: 'user',
      description: 'Temperature setpoint changed',
      details: 'User modified temperature setpoint from 120°F to 125°F.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * 2).toISOString() // 2 days ago
    });

    events.push({
      id: `ev-user-2-${this.deviceId}`,
      category: 'user',
      description: 'Vacation mode enabled',
      details: 'User activated vacation mode with return date set to next week.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * 10).toISOString() // 10 days ago
    });

    events.push({
      id: `ev-user-3-${this.deviceId}`,
      category: 'user',
      description: 'Vacation mode disabled',
      details: 'User manually deactivated vacation mode before scheduled end date.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * 5).toISOString() // 5 days ago
    });

    // System events
    events.push({
      id: `ev-system-1-${this.deviceId}`,
      category: 'system',
      description: 'Firmware updated',
      details: 'Device firmware automatically updated to version 2.3.4.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * 15).toISOString() // 15 days ago
    });

    events.push({
      id: `ev-system-2-${this.deviceId}`,
      category: 'system',
      description: 'Performance analysis completed',
      details: 'Monthly performance analysis shows 94% efficiency rating, which is within optimal range.',
      timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * 7).toISOString() // 7 days ago
    });

    // Add more random events to fill out the list
    const eventTypes = [
      {
        category: 'status',
        descriptions: [
          'Device disconnected temporarily',
          'Operating mode changed to Eco',
          'Operating mode changed to Standard',
          'Entering energy saving period',
          'Exiting energy saving period'
        ]
      },
      {
        category: 'alert',
        descriptions: [
          'Temperature sensor fluctuation detected',
          'Low flow rate detected',
          'Communication latency increased',
          'Minor temperature inconsistency detected',
          'Pressure relief valve activated briefly'
        ]
      },
      {
        category: 'system',
        descriptions: [
          'Diagnostic scan completed',
          'Energy usage report generated',
          'Cloud connectivity verified',
          'Settings backup created',
          'System health check completed'
        ]
      }
    ];

    for (let i = 0; i < 25; i++) {
      const typeIndex = Math.floor(Math.random() * eventTypes.length);
      const eventType = eventTypes[typeIndex];

      const descIndex = Math.floor(Math.random() * eventType.descriptions.length);
      const description = eventType.descriptions[descIndex];

      const daysAgo = Math.floor(Math.random() * 60) + 1; // Random time in last 60 days

      events.push({
        id: `ev-rand-${i}-${this.deviceId}`,
        category: eventType.category,
        description: description,
        details: null,
        timestamp: new Date(baseTime - 1000 * 60 * 60 * 24 * daysAgo).toISOString()
      });
    }

    // Sort events by timestamp (most recent first)
    events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    return { events };
  }
}
