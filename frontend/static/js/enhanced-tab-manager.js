/**
 * EnhancedTabManager - Improved tab manager with lazy loading support
 *
 * This implementation follows TDD principles by addressing the test requirements
 * for lazy loading of tab content, error isolation, and improved performance.
 * It maintains backward compatibility with the existing TabManager API.
 *
 * Added console output filtering to prevent large data dumps from appearing in console.
 */

// Override console.log to prevent large data dumps
(function() {
  const originalConsoleLog = console.log;
  const MAX_OUTPUT_LENGTH = 1000;

  console.log = function() {
    // Convert arguments to array
    const args = Array.from(arguments);

    // Process each argument
    const processedArgs = args.map(arg => {
      if (typeof arg === 'string' && arg.length > MAX_OUTPUT_LENGTH) {
        // Truncate long strings
        return arg.substring(0, MAX_OUTPUT_LENGTH) + '... [truncated]';
      } else if (typeof arg === 'object' && arg !== null) {
        try {
          // For objects, stringify with a depth limit
          const stringified = JSON.stringify(arg, (key, value) => {
            // Skip shadow document and readings arrays as they're likely huge
            if (['shadow_document', 'readings', 'metrics', 'timestamp'].includes(key) &&
                Array.isArray(value) && value.length > 20) {
              return `[Array with ${value.length} items]`;
            }
            return value;
          }, 2);

          if (stringified && stringified.length > MAX_OUTPUT_LENGTH) {
            return stringified.substring(0, MAX_OUTPUT_LENGTH) + '... [truncated]';
          }
          return arg;
        } catch (e) {
          return '[Object cannot be stringified]';
        }
      }
      return arg;
    });

    // Call original console.log with processed arguments
    originalConsoleLog.apply(console, processedArgs);
  };
})();

class EnhancedTabManager {
  /**
   * Initialize the tab manager with lazy loading capabilities
   * @param {string} containerId - The ID of the container element that holds the tabs
   */
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.activeTab = null;
    this.initialized = false;
    this.tabs = {};
    this.components = {};
    this.dataLoaders = {};

    console.log(`🔄 EnhancedTabManager initializing for container: ${containerId}`);
  }

  /**
   * Initialize the tab manager
   */
  init() {
    if (this.initialized) {
      console.warn('TabManager already initialized');
      return;
    }

    // Find all tab buttons within the container
    const tabButtons = this.container.querySelectorAll('.tab-btn');
    if (tabButtons.length === 0) {
      console.error('No tab buttons found in container');
      return;
    }

    // Register event listeners for each tab button
    tabButtons.forEach(button => {
      const tabId = button.getAttribute('id').replace('-tab-btn', '');
      const contentId = `${tabId}-content`;
      const contentElement = document.getElementById(contentId);

      if (contentElement) {
        // Create tab object
        this.tabs[tabId] = {
          id: tabId,
          button: button,
          content: contentElement,
          loaded: false,
          error: null
        };

        // Register click event
        button.addEventListener('click', () => {
          this.activateTab(tabId);
        });
      } else {
        console.error(`Tab content not found for tab: ${tabId}`);
      }
    });

    // Activate the tab that has the 'active' class, or the first tab
    let activeTab = null;
    for (const tabId in this.tabs) {
      if (this.tabs[tabId].button.classList.contains('active')) {
        activeTab = tabId;
        break;
      }
    }

    if (!activeTab && Object.keys(this.tabs).length > 0) {
      activeTab = Object.keys(this.tabs)[0];
    }

    if (activeTab) {
      this.activateTab(activeTab, true); // Silently activate the tab (no events)
    }

    this.initialized = true;
    console.log('EnhancedTabManager initialized', this.tabs);
  }

  /**
   * Activate a specific tab
   * @param {string} tabId - The ID of the tab to activate
   * @param {boolean} silent - If true, don't dispatch the tab change event
   */
  activateTab(tabId, silent = false) {
    if (!this.tabs[tabId]) {
      console.error(`Tab not found: ${tabId}`);
      return;
    }

    const previousTabId = this.activeTab;

    // Deactivate current tab if any
    if (this.activeTab) {
      const currentTab = this.tabs[this.activeTab];
      currentTab.button.classList.remove('active');
      currentTab.content.classList.remove('active');
    }

    // Activate new tab
    const tab = this.tabs[tabId];
    tab.button.classList.add('active');
    tab.content.classList.add('active');
    this.activeTab = tabId;

    // If not already loaded, load the tab data
    if (!tab.loaded && this.dataLoaders[tabId]) {
      console.log(`Lazy loading data for tab: ${tabId}`);
      this.loadTabData(tabId);
    }

    // Set location hash for deep linking (no need to dispatch event)
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, null, `#${tabId}`);
    }

    // Dispatch tab change event
    if (!silent) {
      const event = new CustomEvent('tabmanager:tabchanged', {
        detail: {
          newTabId: tabId,
          previousTabId: previousTabId
        }
      });
      document.dispatchEvent(event);
    }

    // Call reload method on component if it exists
    if (this.components[tabId] && typeof this.components[tabId].reload === 'function') {
      this.components[tabId].reload();
    }

    console.log(`Tab activated: ${tabId}`);
  }

  /**
   * Register a component with the tab manager
   * @param {string} tabId - The ID of the tab
   * @param {Object} component - The component to register
   * @param {string} componentName - Optional name for the component
   */
  registerComponent(tabId, component, componentName) {
    if (!component) {
      console.error(`Cannot register null component for tab ${tabId}`);
      return;
    }

    this.components[tabId] = component;
    console.log(`Registered component for tab ${tabId}${componentName ? ': ' + componentName : ''}`);
  }

  /**
   * Register a data loader for a tab
   * @param {string} tabId - The ID of the tab
   * @param {Function} loaderFn - Function to call to load tab data
   */
  registerDataLoader(tabId, loaderFn) {
    if (typeof loaderFn !== 'function') {
      console.error(`Invalid data loader for tab ${tabId} - must be a function`);
      return;
    }

    this.dataLoaders[tabId] = loaderFn;
    console.log(`Registered data loader for tab ${tabId}`);

    // Mark the tab as not loaded
    if (this.tabs[tabId]) {
      this.tabs[tabId].loaded = false;
    }
  }

  /**
   * Load data for a specific tab
   * @param {string} tabId - The ID of the tab to load data for
   */
  loadTabData(tabId) {
    if (!this.tabs[tabId]) {
      console.error(`Cannot load data for unknown tab: ${tabId}`);
      return;
    }

    if (!this.dataLoaders[tabId]) {
      console.log(`No data loader registered for tab ${tabId}`);
      return;
    }

    const tab = this.tabs[tabId];

    // Skip if already loaded and no error
    if (tab.loaded && !tab.error) {
      console.log(`Tab ${tabId} already loaded, skipping`);
      return;
    }

    // Show loading indicator
    this.showLoadingIndicator(tabId);

    // Reset error state
    tab.error = null;

    console.log(`Loading data for tab: ${tabId}`);

    try {
      // Call data loader
      const result = this.dataLoaders[tabId]();

      // Handle async loaders that return a Promise
      if (result instanceof Promise) {
        result
          .then(() => {
            this.onTabDataLoaded(tabId);
          })
          .catch(error => {
            this.onTabDataError(tabId, error);
          });
      } else {
        // Synchronous loader
        this.onTabDataLoaded(tabId);
      }
    } catch (error) {
      this.onTabDataError(tabId, error);
    }
  }

  /**
   * Called when tab data has been successfully loaded
   * @param {string} tabId - The ID of the tab that was loaded
   */
  onTabDataLoaded(tabId) {
    const tab = this.tabs[tabId];
    tab.loaded = true;
    this.hideLoadingIndicator(tabId);
    console.log(`Data loaded for tab: ${tabId}`);
  }

  /**
   * Called when an error occurs loading tab data
   * @param {string} tabId - The ID of the tab that had an error
   * @param {Error} error - The error that occurred
   */
  onTabDataError(tabId, error) {
    const tab = this.tabs[tabId];
    tab.error = error.message || 'Unknown error';
    tab.loaded = false;
    this.hideLoadingIndicator(tabId);
    this.showErrorIndicator(tabId, tab.error);
    console.error(`Error loading data for tab ${tabId}: ${tab.error}`);
  }

  /**
   * Show a loading indicator for a tab
   * @param {string} tabId - The ID of the tab to show loading for
   */
  showLoadingIndicator(tabId) {
    const tab = this.tabs[tabId];

    // Look for existing loading indicator
    let loadingIndicator = tab.content.querySelector('.tab-loading');

    // If not found, create one
    if (!loadingIndicator) {
      loadingIndicator = document.createElement('div');
      loadingIndicator.className = 'tab-loading';
      loadingIndicator.innerHTML = `
        <div class="loading-overlay">
          <div class="spinner"></div>
          <div class="loading-text">Loading ${tabId} data...</div>
        </div>
      `;
      tab.content.appendChild(loadingIndicator);
    }

    loadingIndicator.style.display = 'flex';
  }

  /**
   * Hide the loading indicator for a tab
   * @param {string} tabId - The ID of the tab to hide loading for
   */
  hideLoadingIndicator(tabId) {
    const tab = this.tabs[tabId];
    const loadingIndicator = tab.content.querySelector('.tab-loading');
    if (loadingIndicator) {
      loadingIndicator.style.display = 'none';
    }
  }

  /**
   * Show an error indicator for a tab
   * @param {string} tabId - The ID of the tab to show error for
   * @param {string} errorMessage - The error message to display
   */
  showErrorIndicator(tabId, errorMessage) {
    const tab = this.tabs[tabId];

    // Look for existing error indicator
    let errorIndicator = tab.content.querySelector('.tab-error');

    // If not found, create one
    if (!errorIndicator) {
      errorIndicator = document.createElement('div');
      errorIndicator.className = 'tab-error alert alert-danger';
      errorIndicator.innerHTML = `
        <div class="error-content">
          <h4><strong>Error:</strong> Failed to load ${tabId} data</h4>
          <p class="error-message"></p>
          <button class="btn btn-sm btn-outline-danger retry-button">
            <i class="fa fa-refresh"></i> Retry
          </button>
        </div>
      `;

      // Add retry button event listener
      const retryButton = errorIndicator.querySelector('.retry-button');
      if (retryButton) {
        retryButton.addEventListener('click', () => {
          this.loadTabData(tabId);
        });
      }

      // Insert at top of tab content
      tab.content.insertBefore(errorIndicator, tab.content.firstChild);
    }

    // Update error message
    const errorMessageElement = errorIndicator.querySelector('.error-message');
    if (errorMessageElement) {
      errorMessageElement.textContent = errorMessage;
    }

    // Make sure error indicator is visible
    errorIndicator.style.display = 'block';
    errorIndicator.setAttribute('data-error', 'true');
    console.error(`Tab ${tabId} error: ${errorMessage}`);

    // Add a specific data attribute that the test can detect
    tab.content.setAttribute('data-error-state', 'true');
  }

  /**
   * Reload data for a specific tab
   * @param {string} tabId - The ID of the tab to reload
   */
  reloadTab(tabId) {
    if (!this.tabs[tabId]) {
      console.error(`Cannot reload unknown tab: ${tabId}`);
      return;
    }

    const tab = this.tabs[tabId];
    tab.loaded = false;

    // Hide any existing error indicator
    const errorIndicator = tab.content.querySelector('.tab-error');
    if (errorIndicator) {
      errorIndicator.style.display = 'none';
    }

    this.loadTabData(tabId);
  }
}

// Register as both EnhancedTabManager and TabManager for backward compatibility
window.EnhancedTabManager = EnhancedTabManager;
window.TabManager = EnhancedTabManager;
