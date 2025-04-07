/**
 * Dashboard Summary Component
 * 
 * Displays summary metrics for water heater fleet including:
 * - Total Devices
 * - Connected Devices
 * - Disconnected Devices
 * - Simulated Devices
 * 
 * Part of the device-agnostic architecture, designed to be reusable across device types
 */
export class DashboardSummary extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    
    // Component state
    this.isLoading = true;
    this.error = null;
    this.metrics = {
      totalDevices: 0,
      connectedDevices: 0,
      disconnectedDevices: 0,
      simulatedDevices: 0
    };
    
    // Services will be injected
    this.deviceService = null;
  }
  
  /**
   * Initialize the component with services
   */
  initialize({ deviceService }) {
    this.deviceService = deviceService;
    this.render();
  }
  
  /**
   * Called when the element is connected to the DOM
   */
  connectedCallback() {
    this.render();
  }
  
  /**
   * Refresh the dashboard summary data
   */
  async refresh() {
    if (!this.deviceService) return;
    
    this.isLoading = true;
    this.error = null;
    this.render();
    
    try {
      // Get devices summary from service
      const metrics = await this.deviceService.getDevicesSummary();
      
      // Update state
      this.metrics = metrics;
      this.isLoading = false;
      
      // Re-render the component
      this.render();
      
      return metrics;
    } catch (error) {
      console.error('Error loading dashboard summary:', error);
      this.error = 'Failed to load summary data';
      this.isLoading = false;
      this.render();
      
      return null;
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
      
      .summary-container {
        position: relative;
      }
      
      .summary-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
      }
      
      .metric-card {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
      }
      
      .metric-card.total {
        border-top: 4px solid #2196F3;
      }
      
      .metric-card.connected {
        border-top: 4px solid #4CAF50;
      }
      
      .metric-card.disconnected {
        border-top: 4px solid #F44336;
      }
      
      .metric-card.simulated {
        border-top: 4px solid #673AB7;
      }
      
      .metric-value {
        font-size: 2.5rem;
        font-weight: 500;
        margin: 0.5rem 0;
      }
      
      .metric-label {
        font-size: 0.9rem;
        color: #757575;
      }
      
      .loading-container {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 10;
      }
      
      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(33, 150, 243, 0.2);
        border-top: 4px solid #2196F3;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 0.5rem;
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      
      .error-message {
        background-color: #FFEBEE;
        color: #F44336;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
      }
    `;
    
    // Define HTML template
    const template = `
      <div class="summary-container">
        ${this.error ? `
          <div class="error-message">
            ${this.error}
          </div>
        ` : ''}
        
        <div class="summary-metrics">
          <div class="metric-card total">
            <div class="metric-label">Total Devices</div>
            <div class="metric-value">${this.metrics.totalDevices}</div>
          </div>
          
          <div class="metric-card connected">
            <div class="metric-label">Connected Devices</div>
            <div class="metric-value">${this.metrics.connectedDevices}</div>
          </div>
          
          <div class="metric-card disconnected">
            <div class="metric-label">Disconnected Devices</div>
            <div class="metric-value">${this.metrics.disconnectedDevices}</div>
          </div>
          
          <div class="metric-card simulated">
            <div class="metric-label">Simulated Devices</div>
            <div class="metric-value">${this.metrics.simulatedDevices}</div>
          </div>
        </div>
        
        ${this.isLoading ? `
          <div class="loading-container">
            <div class="loading-spinner"></div>
            <div>Loading summary...</div>
          </div>
        ` : ''}
      </div>
    `;
    
    // Set the shadow DOM content
    this.shadowRoot.innerHTML = `<style>${styles}</style>${template}`;
  }
}
