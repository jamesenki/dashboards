/**
 * Anomaly Alerts Component
 *
 * Displays real-time anomaly alerts and predictive maintenance warnings
 * for water heater devices. Part of the device-agnostic IoTSphere architecture.
 */
export class AnomalyAlerts extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Component state
    this.device = null;
    this.deviceId = null;
    this.alerts = [];
    this.isLoading = true;
    this.error = null;

    // Alert polling
    this.pollInterval = null;
    this.pollRate = 60000; // 1 minute
  }

  /**
   * Initialize the component
   */
  initialize({ device, deviceId }) {
    this.device = device;
    this.deviceId = deviceId || (device ? device.device_id : null);

    if (this.deviceId) {
      this.loadAlerts();
      this.startPolling();
    }

    this.render();
  }

  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }

  /**
   * Called when the element is disconnected from the DOM
   */
  disconnectedCallback() {
    this.stopPolling();
  }

  /**
   * Load alerts from the API
   */
  async loadAlerts() {
    if (!this.deviceId) return;

    this.isLoading = true;
    this.error = null;
    this.render();

    try {
      // In a real implementation, this would call an actual API
      // For now, we'll simulate the API response
      const response = await this.fetchAnomalyAlerts(this.deviceId);

      this.alerts = response.alerts;
      this.isLoading = false;
      this.render();

      return response.alerts;
    } catch (error) {
      console.error('Error loading anomaly alerts:', error);
      this.error = 'Failed to load alerts';
      this.isLoading = false;
      this.render();

      return [];
    }
  }

  /**
   * Start polling for alert updates
   */
  startPolling() {
    this.stopPolling(); // Clear any existing interval

    this.pollInterval = setInterval(() => {
      this.loadAlerts();
    }, this.pollRate);
  }

  /**
   * Stop polling for alert updates
   */
  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  /**
   * Refresh alerts data
   */
  refresh() {
    return this.loadAlerts();
  }

  /**
   * Update device data
   */
  updateDevice(updatedDevice) {
    this.device = updatedDevice;
    this.render();
  }

  /**
   * Handle alert dismissal
   */
  async dismissAlert(alertId) {
    try {
      // In a real implementation, this would call an API
      // to mark the alert as dismissed
      await this.dismissAnomalyAlert(alertId);

      // Remove the alert from the local list
      this.alerts = this.alerts.filter(alert => alert.id !== alertId);
      this.render();
    } catch (error) {
      console.error('Error dismissing alert:', error);
      // Show error message
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
      }

      .alerts-container {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        margin-bottom: 1.5rem;
      }

      .alerts-header {
        padding: 1rem 1.5rem;
        background-color: #F5F5F5;
        border-bottom: 1px solid #E0E0E0;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .alerts-title {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 500;
        display: flex;
        align-items: center;
      }

      .alerts-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 22px;
        height: 22px;
        border-radius: 11px;
        background-color: #F44336;
        color: white;
        font-size: 0.8rem;
        margin-left: 0.5rem;
        padding: 0 6px;
      }

      .refresh-button {
        background: none;
        border: none;
        cursor: pointer;
        color: #757575;
        display: flex;
        align-items: center;
        font-size: 0.9rem;
      }

      .refresh-button:hover {
        color: #424242;
      }

      .alerts-body {
        max-height: 400px;
        overflow-y: auto;
      }

      .alert-item {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #E0E0E0;
        position: relative;
      }

      .alert-item:last-child {
        border-bottom: none;
      }

      .alert-item.critical {
        background-color: #FFEBEE;
      }

      .alert-item.warning {
        background-color: #FFF8E1;
      }

      .alert-item.info {
        background-color: #E1F5FE;
      }

      .alert-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
      }

      .alert-severity {
        display: inline-block;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
      }

      .alert-severity.critical {
        background-color: #EF5350;
        color: white;
      }

      .alert-severity.warning {
        background-color: #FFC107;
        color: #212121;
      }

      .alert-severity.info {
        background-color: #29B6F6;
        color: white;
      }

      .alert-time {
        font-size: 0.8rem;
        color: #757575;
      }

      .alert-title {
        font-weight: 500;
        margin: 0 0 0.5rem 0;
      }

      .alert-description {
        font-size: 0.9rem;
        margin: 0 0 0.5rem 0;
        color: #424242;
      }

      .alert-recommendation {
        font-size: 0.9rem;
        margin: 0.5rem 0 0 0;
        padding-left: 1rem;
        border-left: 3px solid #2196F3;
        color: #424242;
      }

      .alert-actions {
        display: flex;
        justify-content: flex-end;
        margin-top: 0.75rem;
      }

      .alert-button {
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        cursor: pointer;
        background: none;
        border: 1px solid #E0E0E0;
        margin-left: 0.5rem;
        display: flex;
        align-items: center;
      }

      .alert-button.dismiss {
        color: #757575;
      }

      .alert-button.dismiss:hover {
        background-color: #EEEEEE;
      }

      .alert-button.action {
        background-color: #2196F3;
        color: white;
        border: none;
      }

      .alert-button.action:hover {
        background-color: #1E88E5;
      }

      .loading-container {
        padding: 2rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }

      .loading-spinner {
        width: 30px;
        height: 30px;
        border: 3px solid rgba(33, 150, 243, 0.2);
        border-top: 3px solid #2196F3;
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
        text-align: center;
        color: #F44336;
      }

      .empty-container {
        padding: 2rem;
        text-align: center;
        color: #757575;
      }

      .empty-icon {
        font-size: 2rem;
        margin-bottom: 1rem;
        opacity: 0.5;
      }
    `;

    // Define HTML template
    let alertsBody;

    if (this.isLoading) {
      alertsBody = `
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <div>Loading alerts...</div>
        </div>
      `;
    } else if (this.error) {
      alertsBody = `
        <div class="error-container">
          <div>${this.error}</div>
          <button class="alert-button action" id="retry-button">Retry</button>
        </div>
      `;
    } else if (this.alerts.length === 0) {
      alertsBody = `
        <div class="empty-container">
          <div class="empty-icon">✓</div>
          <div>No anomalies detected</div>
          <div>The device appears to be operating normally</div>
        </div>
      `;
    } else {
      alertsBody = `
        <div class="alerts-body">
          ${this.alerts.map(alert => this.renderAlert(alert)).join('')}
        </div>
      `;
    }

    const template = `
      <div class="alerts-container">
        <div class="alerts-header">
          <h3 class="alerts-title">
            Anomaly Alerts
            ${this.alerts.length > 0 ? `<span class="alerts-count">${this.alerts.length}</span>` : ''}
          </h3>
          <button class="refresh-button" id="refresh-alerts">
            <span>🔄</span>
          </button>
        </div>

        ${alertsBody}
      </div>
    `;

    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;

    // Add event listeners
    this.addEventListeners();
  }

  /**
   * Render a single alert
   */
  renderAlert(alert) {
    return `
      <div class="alert-item ${alert.severity}">
        <div class="alert-header">
          <span class="alert-severity ${alert.severity}">${alert.severity}</span>
          <span class="alert-time">${this.formatTimestamp(alert.timestamp)}</span>
        </div>

        <h4 class="alert-title">${alert.title}</h4>
        <div class="alert-description">${alert.description}</div>

        ${alert.recommendation ? `
          <div class="alert-recommendation">
            <strong>Recommendation:</strong> ${alert.recommendation}
          </div>
        ` : ''}

        <div class="alert-actions">
          ${alert.action ? `
            <button class="alert-button action" data-action="${alert.action}" data-alert-id="${alert.id}">
              ${alert.actionText || 'Take Action'}
            </button>
          ` : ''}

          <button class="alert-button dismiss" data-dismiss-alert="${alert.id}">
            Dismiss
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Add event listeners
   */
  addEventListeners() {
    // Refresh button
    const refreshButton = this.shadowRoot.querySelector('#refresh-alerts');
    if (refreshButton) {
      refreshButton.addEventListener('click', () => {
        this.refresh();
      });
    }

    // Retry button
    const retryButton = this.shadowRoot.querySelector('#retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => {
        this.refresh();
      });
    }

    // Dismiss alert buttons
    const dismissButtons = this.shadowRoot.querySelectorAll('[data-dismiss-alert]');
    dismissButtons.forEach(button => {
      button.addEventListener('click', () => {
        const alertId = button.getAttribute('data-dismiss-alert');
        this.dismissAlert(alertId);
      });
    });

    // Action buttons
    const actionButtons = this.shadowRoot.querySelectorAll('[data-action]');
    actionButtons.forEach(button => {
      button.addEventListener('click', () => {
        const action = button.getAttribute('data-action');
        const alertId = button.getAttribute('data-alert-id');
        this.handleAlertAction(action, alertId);
      });
    });
  }

  /**
   * Handle alert action click
   */
  handleAlertAction(action, alertId) {
    // In a real implementation, this would trigger the specific action
    console.log(`Taking action "${action}" for alert ${alertId}`);

    // For demonstration, we'll just dismiss the alert after action
    this.dismissAlert(alertId);

    // Dispatch an event that could be handled by parent components
    this.dispatchEvent(new CustomEvent('alert-action', {
      bubbles: true,
      composed: true,
      detail: {
        action,
        alertId
      }
    }));
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown time';

    try {
      const date = new Date(timestamp);

      // If it's today, show time only
      const today = new Date();
      if (date.toDateString() === today.toDateString()) {
        return `Today at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }

      // If it's yesterday, show "Yesterday"
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      }

      // Otherwise, show full date
      return date.toLocaleString();
    } catch (e) {
      return timestamp;
    }
  }

  /**
   * Simulate fetching anomaly alerts from an API
   * In a real implementation, this would be an actual API call
   */
  async fetchAnomalyAlerts(deviceId) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Generate some mock alerts based on device ID to ensure consistency
    const hash = this.hashCode(deviceId);
    const numAlerts = hash % 5; // 0-4 alerts

    const alerts = [];

    if (numAlerts > 0) {
      // Add a critical alert for some devices
      if (hash % 7 === 0) {
        alerts.push({
          id: `alert-c-${deviceId}-${Date.now()}`,
          severity: 'critical',
          title: 'Pressure Exceeding Safe Limits',
          description: 'The water heater pressure is approaching unsafe levels. This could indicate a malfunctioning pressure relief valve.',
          recommendation: 'Immediately check the pressure relief valve and consider calling a professional technician if the issue persists.',
          timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
          action: 'schedule-maintenance',
          actionText: 'Schedule Maintenance'
        });
      }

      // Add some warning alerts
      if (hash % 3 === 1 || numAlerts > 2) {
        alerts.push({
          id: `alert-w1-${deviceId}-${Date.now()}`,
          severity: 'warning',
          title: 'Heating Element Efficiency Declining',
          description: 'The primary heating element is showing signs of reduced efficiency. This may lead to increased energy consumption and longer heating times.',
          recommendation: 'Consider inspecting the heating element for sediment buildup or damage during your next maintenance.',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
          action: null
        });
      }

      if (hash % 4 === 2 || numAlerts > 3) {
        alerts.push({
          id: `alert-w2-${deviceId}-${Date.now()}`,
          severity: 'warning',
          title: 'Unusual Temperature Fluctuations',
          description: 'Temperature readings have shown unusual fluctuations over the past 24 hours, which may indicate sensor issues or control problems.',
          recommendation: 'Monitor the temperature readings closely and consider a diagnostic check if fluctuations continue.',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(), // 5 hours ago
          action: 'view-temperature-history',
          actionText: 'View History'
        });
      }

      // Add some info alerts
      if (hash % 5 === 3 || numAlerts > 1) {
        alerts.push({
          id: `alert-i1-${deviceId}-${Date.now()}`,
          severity: 'info',
          title: 'Maintenance Recommended Soon',
          description: 'Based on usage patterns and time since last maintenance, a routine inspection is recommended within the next 30 days.',
          recommendation: 'Schedule a standard maintenance check to ensure optimal performance and prevent potential issues.',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
          action: 'schedule-maintenance',
          actionText: 'Schedule Maintenance'
        });
      }
    }

    return { alerts };
  }

  /**
   * Simulate dismissing an anomaly alert
   * In a real implementation, this would be an API call
   */
  async dismissAnomalyAlert(alertId) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    // Simulate successful API response
    return { success: true };
  }

  /**
   * Simple string hash code function for generating deterministic mock data
   */
  hashCode(str) {
    let hash = 0;
    if (str.length === 0) return hash;

    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }

    return Math.abs(hash);
  }
}
