/**
 * IoTSphere Shell Application
 * Handles routing and micro-frontend composition
 */

// Global event bus for cross-micro-frontend communication
window.EventBus = {
  events: {},
  subscribe: function(event, callback) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
    return () => this.unsubscribe(event, callback);
  },
  unsubscribe: function(event, callback) {
    if (this.events[event]) {
      this.events[event] = this.events[event].filter(cb => cb !== callback);
    }
  },
  publish: function(event, data) {
    if (this.events[event]) {
      this.events[event].forEach(callback => callback(data));
    }
  }
};

// Configuration for micro-frontends
const microFrontendConfig = {
  'water-heaters': {
    dashboard: {
      js: '/src/micro-frontends/water-heaters/dashboard/index.js',
      css: '/src/micro-frontends/water-heaters/dashboard/styles.css',
      mountPoint: 'micro-frontend-container'
    },
    details: {
      js: '/src/micro-frontends/water-heaters/details/index.js',
      css: '/src/micro-frontends/water-heaters/details/styles.css',
      mountPoint: 'micro-frontend-container'
    }
  },
  // Future device types will be added here
};

// Authentication state (simplified for demo)
const authState = {
  isAuthenticated: true,
  role: 'facility_manager',
  permissions: ['read:devices', 'write:devices']
};

/**
 * Router for handling hash-based navigation
 */
class Router {
  constructor() {
    this.routes = {};
    this.currentRoute = null;
    this.currentMicroFrontend = null;

    // Listen for hash changes
    window.addEventListener('hashchange', this.handleRouteChange.bind(this));
    
    // Handle initial route
    this.handleRouteChange();
  }

  /**
   * Register a route handler
   */
  register(path, handler) {
    this.routes[path] = handler;
    return this;
  }

  /**
   * Handle route changes
   */
  handleRouteChange() {
    const hash = window.location.hash || '#/';
    let matchedRoute = null;
    
    // Find matching route
    const paths = Object.keys(this.routes);
    for (const path of paths) {
      // Simple string matching for now
      // Could be enhanced with pattern matching
      if (hash.startsWith(path)) {
        matchedRoute = path;
        break;
      }
    }
    
    // Fall back to default route if no match
    if (!matchedRoute && this.routes['#/']) {
      matchedRoute = '#/';
    }
    
    // If we have a matched route, execute its handler
    if (matchedRoute && this.routes[matchedRoute]) {
      // Clean up previous micro-frontend if any
      if (this.currentMicroFrontend && this.currentMicroFrontend.unmount) {
        this.currentMicroFrontend.unmount();
      }
      
      // Mark active navigation item
      this.updateActiveNavigation(matchedRoute);
      
      // Execute route handler
      this.currentRoute = matchedRoute;
      this.currentMicroFrontend = this.routes[matchedRoute](hash);
    }
  }
  
  /**
   * Update active navigation item in the UI
   */
  updateActiveNavigation(route) {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    
    // Add active class to matching nav item
    document.querySelectorAll(`.nav-item[href="${route}"]`).forEach(item => {
      item.classList.add('active');
    });
    
    // Handle device type navigation in sidebar
    if (route.includes('water-heater')) {
      this.updateActiveDeviceType('water-heater');
    } else if (route.includes('vending-machine')) {
      this.updateActiveDeviceType('vending-machine');
    } else if (route.includes('robot')) {
      this.updateActiveDeviceType('robot');
    }
  }
  
  /**
   * Update active device type in the sidebar
   */
  updateActiveDeviceType(deviceType) {
    // Remove active class from all device types
    document.querySelectorAll('.device-type').forEach(item => {
      item.classList.remove('active');
    });
    
    // Add active class to matching device type
    document.querySelectorAll(`.device-type[data-type="${deviceType}"]`).forEach(item => {
      item.classList.add('active');
    });
  }
}

/**
 * Micro-frontend loader
 */
class MicroFrontendLoader {
  /**
   * Load a micro-frontend by device type and feature
   */
  static async load(deviceType, feature) {
    // Get configuration for micro-frontend
    const config = microFrontendConfig[deviceType] && microFrontendConfig[deviceType][feature];
    if (!config) {
      console.error(`No configuration found for ${deviceType}/${feature}`);
      return this.showError(`The ${feature} for ${deviceType} is not available.`);
    }
    
    // Show loading state
    this.showLoading();
    
    try {
      // Load CSS if specified
      if (config.css) {
        await this.loadCSS(config.css);
      }
      
      // Load and mount the micro-frontend
      const module = await import(config.js);
      const mountPoint = document.getElementById(config.mountPoint);
      
      // Clear loading state
      mountPoint.innerHTML = '';
      
      // Mount the micro-frontend
      const microFrontendInstance = await module.mount(mountPoint, {
        deviceType,
        feature,
        auth: authState,
        eventBus: window.EventBus
      });
      
      return microFrontendInstance;
    } catch (error) {
      console.error('Failed to load micro-frontend:', error);
      return this.showError('Failed to load the requested feature. Please try again later.');
    }
  }
  
  /**
   * Show loading state
   */
  static showLoading() {
    const container = document.getElementById('micro-frontend-container');
    container.innerHTML = `
      <div class="loading-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading...</div>
      </div>
    `;
  }
  
  /**
   * Show error state
   */
  static showError(message) {
    const container = document.getElementById('micro-frontend-container');
    container.innerHTML = `
      <div class="error-container">
        <div class="error-icon">!</div>
        <div class="error-message">${message}</div>
        <button class="btn-retry" onclick="window.location.reload()">Retry</button>
      </div>
    `;
    return {
      unmount: () => {} // No-op for error state
    };
  }
  
  /**
   * Load CSS file
   */
  static loadCSS(href) {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.onload = () => resolve();
      link.onerror = () => reject(new Error(`Failed to load CSS: ${href}`));
      document.head.appendChild(link);
    });
  }
}

// Initialize router and register routes
const router = new Router()
  .register('#/', () => {
    // Default route - redirect to water heaters dashboard
    window.location.hash = '#/dashboard/water-heaters';
    return null;
  })
  .register('#/dashboard', () => {
    // Dashboard route - default to water heaters
    window.location.hash = '#/dashboard/water-heaters';
    return null;
  })
  .register('#/dashboard/water-heaters', () => {
    // Water heaters dashboard
    return MicroFrontendLoader.load('water-heaters', 'dashboard');
  })
  .register('#/dashboard/water-heaters/', (route) => {
    // Handle specific water heater detail view
    // Extract ID from route, e.g., #/dashboard/water-heaters/wh-001
    const deviceId = route.split('/').pop();
    
    // Pass context to the micro-frontend
    return MicroFrontendLoader.load('water-heaters', 'details', { deviceId });
  });

// Device type selection in sidebar
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.device-type').forEach(item => {
    item.addEventListener('click', () => {
      const deviceType = item.getAttribute('data-type');
      window.location.hash = `#/dashboard/${deviceType}`;
    });
  });
});
