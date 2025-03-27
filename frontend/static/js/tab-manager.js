/**
 * TabManager.js - v2.0
 * 
 * A drastically simplified tab management system that uses basic DOM manipulation
 * to ensure tabs display correctly without stacking or visibility issues.
 * 
 * This implementation focuses on reliability and simplicity, with minimal dependencies
 * and straightforward tab switching logic.
 */

class TabManager {
  /**
   * Simple tab manager constructor
   * @param {string} [tabContainerId='tab-container'] - ID of the main tab container element
   */
  constructor(tabContainerId = 'tab-container') {
    // Standard event names for tab system
    this.EVENTS = {
      TAB_CHANGED: 'tabmanager:tabchanged',        // Fired when tab is changed
      COMPONENT_REGISTERED: 'tabmanager:component', // Fired when component is registered
      BEFORE_TAB_CHANGE: 'tabmanager:beforechange', // Fired before tab change for cleanup
      AFTER_INIT: 'tabmanager:initialized',         // Fired after TabManager is initialized
      DATA_REFRESH: 'tabmanager:datarefresh',       // For requesting data refresh across components
      ERROR: 'tabmanager:error',                    // For error broadcasting
      RECOVERY_ATTEMPT: 'tabmanager:recovery',      // Fired when recovery is attempted
      RECOVERY_SUCCESS: 'tabmanager:recoverysuccess', // Fired when recovery succeeds
      RECOVERY_FAILURE: 'tabmanager:recoveryfailure'  // Fired when recovery fails
    };
    
    // For backward compatibility
    this.EVENT_TAB_CHANGED = this.EVENTS.TAB_CHANGED;
    
    // Currently active tab ID
    this.activeTabId = null;
    
    // Simple map to track tab components
    this.components = {};
    
    // Event subscribers for custom events
    this.subscribers = {};
    
    // Element cache for performance optimization
    this.elements = {};
    
    // Root container for scoped element selection
    this.container = document.getElementById(tabContainerId);
    
    // Create a logger for this component
    this.logger = window.Logger ? new window.Logger('TabManager') : {
      debug: (msg, data) => console.debug(`[TabManager] ${msg}`, data || ''),
      info: (msg, data) => console.log(`[TabManager] ${msg}`, data || ''),
      warn: (msg, data) => console.warn(`[TabManager] ${msg}`, data || ''),
      error: (msg, err) => console.error(`[TabManager] ${msg}`, err || '')
    };
    
    // Error recovery settings
    this.recoverySettings = {
      maxRetries: 3,              // Maximum number of retries for an operation
      recoveryDelay: 500,         // Milliseconds between recovery attempts
      autoRecovery: true,         // Whether to automatically attempt recovery
      recoveryTimeout: 10000,     // Timeout for recovery operations
      retryCount: {}              // Track retry counts by operation
    };
    
    if (!this.container) {
      this.logger.warn(`No container found with ID '${tabContainerId}', using document as root`);
    }
    
    // Initialization state
    this.initialized = false;
    
    console.log('TabManager: Created new instance with enhanced event system and element caching');
  }
  
  /**
   * Get an element within the tab system's container
   * @param {string} selector - CSS selector for the element
   * @param {boolean} [cacheResult=true] - Whether to cache the result for future use
   * @param {string} [cacheKey=null] - Key to use for caching (defaults to selector)
   * @returns {HTMLElement|null} The element or null if not found
   */
  getElement(selector, cacheResult = true, cacheKey = null) {
    const key = cacheKey || selector;
    
    // Return cached element if available
    if (this.elements[key]) {
      return this.elements[key];
    }
    
    // Try to find element within container first (scoped)
    let element = null;
    if (this.container) {
      element = this.container.querySelector(selector);
    }
    
    // If not found in container, try document-wide as fallback
    if (!element) {
      // Handle ID selectors specially
      if (selector.startsWith('#')) {
        const id = selector.substring(1);
        element = document.getElementById(id);
      } else {
        element = document.querySelector(selector);
      }
    }
    
    // Cache result if requested
    if (element && cacheResult) {
      this.elements[key] = element;
    }
    
    return element;
  }
  
  /**
   * Get all elements matching a selector within the tab system's container
   * @param {string} selector - CSS selector for the elements
   * @returns {NodeList} The matching elements
   */
  getAllElements(selector) {
    // First try container-scoped query
    if (this.container) {
      return this.container.querySelectorAll(selector);
    }
    
    // Fallback to document-wide
    return document.querySelectorAll(selector);
  }
  
  /**
   * Initialize tab system - extremely simplified approach
   */
  init() {
    if (this.initialized) {
      this.logger.warn('Already initialized');
      return;
    }
    
    this.logger.info('Initializing tab system...');
    
    // Initialize error recovery tracker
    this._resetRecoveryState();
    
    // Cache frequently accessed DOM elements
    this.cacheElements();
    
    try {
      // Find all tab buttons using our scoped element selection
      const tabButtons = this.getAllElements('.tab-btn');
      this.logger.info(`Found ${tabButtons.length} tab buttons`);
      
      // Set up click listeners for all tab buttons
      tabButtons.forEach(btn => {
        // Get tab ID from button ID by removing -tab-btn suffix
        const tabId = btn.id.replace('-tab-btn', '');
        if (!tabId) return;
        
        // Add click handler
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          this.showTab(tabId);
        });
        
        // Cache button element for faster access
        this.elements[`${tabId}Button`] = btn;
        
        // Initialize component tracking for this tab
        this.components[tabId] = [];
        
        console.log(`TabManager: Setup tab '${tabId}'`);
      });
      
      // Set initial tab based on URL hash or default to first tab
      let initialTab = null;
      
      // Try to get tab ID from URL hash
      if (window.location.hash) {
        initialTab = window.location.hash.substring(1);
        // Verify this tab exists using our element selection method
        if (!this.getElement(`#${initialTab}-tab-btn`, false)) {
          initialTab = null;
        }
      }
      
      // If no valid hash tab, use the first tab or predictions for test environment
      if (!initialTab) {
        const isTestEnv = window.location.href.includes('localhost:8006');
        initialTab = isTestEnv ? 'predictions' : (tabButtons[0]?.id.replace('-tab-btn', ''));
      }
      
      // Show the initial tab with a slight delay to ensure DOM is ready
      if (initialTab) {
        setTimeout(() => {
          this.showTab(initialTab);
        }, 50);
      }
      
      // Listen for hash changes
      window.addEventListener('hashchange', () => {
        const tabId = window.location.hash.substring(1);
        // Use our element selection method to check if tab exists
        if (tabId && this.getElement(`#${tabId}-tab-btn`, false)) {
          this.showTab(tabId);
        }
      });
      
      // Set initialization flag only after successful completion
      this.initialized = true;
      console.log('TabManager: Initialization complete');
      return true;
    } catch (error) {
      this.logger.error('Error during tab system initialization:', error);
      
      // Dispatch error event
      this.dispatchEvent(this.EVENTS.ERROR, {
        source: 'init',
        error: error.message || 'Unknown error during initialization'
      });
      
      // Try to recover by showing a fallback tab
      try {
        let fallbackTab = null;
        if (document.getElementById('details-tab-btn')) {
          this.logger.info('Recovering by showing details tab');
          fallbackTab = 'details';
        } else if (document.querySelector('.tab-btn')) {
          // Get the first available tab as fallback
          fallbackTab = document.querySelector('.tab-btn').id.replace('-tab-btn', '');
          this.logger.info(`Recovering by showing first available tab: ${fallbackTab}`);
        }
        
        if (fallbackTab) {
          setTimeout(() => {
            this.showTab(fallbackTab);
          }, 50);
          
          // Set initialization flag even in recovery mode
          this.initialized = true;
          console.log('TabManager: Initialization completed in recovery mode');
          return true;
        }
      } catch (recoveryError) {
        this.logger.error('Error during initialization recovery:', recoveryError);
      }
      
      return false;
    }
  }
  
  /**
   * Register a component with a tab
   * @param {string} tabId - ID of the tab
   * @param {Object} component - Component to register
   * @param {string} componentId - Unique ID for the component
   */
  registerComponent(tabId, component, componentId) {
    if (!tabId || !component || !componentId) {
      console.error('TabManager: Missing parameters for registerComponent');
      return;
    }
    
    // Ensure we have a components array for this tab
    if (!this.components[tabId]) {
      this.components[tabId] = [];
    }
    
    // Add the component
    this.components[tabId].push({
      id: componentId,
      instance: component
    });
    
    console.log(`TabManager: Registered component '${componentId}' with tab '${tabId}'`);
    
    // If this tab is active, call reload method
    if (this.activeTabId === tabId && typeof component.reload === 'function') {
      component.reload();
    }
  }
  
  /**
   * Cache frequently accessed DOM elements for better performance
   */
  cacheElements() {
    // Tab container elements
    this.elements.tabContainer = this.container || this.getElement('.tab-container');
    this.elements.tabContentContainer = this.getElement('.tab-content-container');
    
    // Cache tab buttons and content elements
    const tabButtons = this.getAllElements('.tab-btn');
    tabButtons.forEach(btn => {
      const tabId = btn.id.replace('-tab-btn', '');
      if (!tabId) return;
      
      // Cache button element
      this.elements[`${tabId}Button`] = btn;
      
      // Cache content element
      const contentId = `${tabId}-content`;
      const contentElement = this.getElement(`#${contentId}`);
      if (contentElement) {
        this.elements[`${tabId}Content`] = contentElement;
      }
    });
    
    // Cache all tab content elements for isolation
    this.elements.allTabContent = Array.from(this.getAllElements('.tab-content'));
    
    console.log('TabManager: Cached DOM elements for optimal performance');
  }
  
  /**
   * Show a specific tab - core functionality with enhanced isolation
   * @param {string} tabId - Tab identifier (without -tab-btn suffix)
   */
  showTab(tabId) {
    if (!tabId) return;
    
    console.log(`TabManager: Showing tab '${tabId}'`);
    
    const previousTabId = this.activeTabId;
    if (previousTabId === tabId) {
      console.log(`TabManager: Tab '${tabId}' is already active`);
      return;
    }
    
    try {
      // STEP 1: Hide all tab content and deactivate all buttons
      // Use cached elements or get them fresh
      const allButtons = this.getAllElements('.tab-btn');
      allButtons.forEach(btn => btn.classList.remove('active'));
      
      // Aggressive hiding for all tab content using cached elements when possible
      const allContent = this.elements.allTabContent || this.getAllElements('.tab-content');
      allContent.forEach(content => {
        const contentId = content.id;
        const isTargetTab = contentId === `${tabId}-content`;
        
        if (!isTargetTab) {
          // Super aggressive hiding for non-target tabs
          content.style.display = 'none';
          content.style.visibility = 'hidden';
          content.style.opacity = '0';
          content.style.position = 'absolute';
          content.style.zIndex = '-100';
          content.style.pointerEvents = 'none';
          content.style.clip = 'rect(0, 0, 0, 0)';
          content.style.clipPath = 'inset(100%)';
          content.style.maxHeight = '0';
          content.style.transform = 'translateX(-10000px)';
          content.classList.remove('active');
          content.classList.add('tab-content-hidden');
          
          // Special approach for History tab when switching to Predictions, and vice versa
          // This helps prevent content leaking between these tabs
          if ((tabId === 'predictions' && contentId === 'history-content') || 
              (tabId === 'history' && contentId === 'predictions-content')) {
            
            // Add an extra empty div to prevent leaking content
            content.setAttribute('data-isolation', 'true');
          }
        }
      });
      
      // STEP 2: Show the selected tab
      // Activate the tab button (use cached element if available)
      const buttonKey = `${tabId}Button`;
      const button = this.elements[buttonKey] || this.getElement(`#${tabId}-tab-btn`, true, buttonKey);
      if (button) button.classList.add('active');
      
      // Show the content with multiple properties for visibility (use cached element if available)
      const contentKey = `${tabId}Content`;
      const content = this.elements[contentKey] || this.getElement(`#${tabId}-content`, true, contentKey);
      if (content) {
        // Reset all inline styles to ensure proper display
        content.removeAttribute('style');
        
        // Set visibility styles explicitly
        content.style.display = 'block';
        content.style.visibility = 'visible';
        content.style.opacity = '1';
        content.style.position = 'relative';
        content.style.zIndex = '100';
        content.style.pointerEvents = 'auto';
        content.classList.add('active');
        content.classList.remove('tab-content-hidden');
        
        // Clear any isolation attributes
        content.removeAttribute('data-isolation');
        
        // Force layout recalculation twice to ensure visibility changes take effect
        void content.offsetWidth;
        setTimeout(() => { void content.offsetWidth; }, 0);
        
        // Ensure proper stacking by moving this element to the end of its container
        const containerKey = 'tabContentContainer';
        const tabContentContainer = this.elements[containerKey] || this.getElement('.tab-content-container', true, containerKey);
        if (tabContentContainer) {
          tabContentContainer.appendChild(content);
          console.log(`TabManager: Repositioned ${tabId} content for proper stacking`);
        }
      }
      
      // Update active tab tracking
      this.activeTabId = tabId;
      
      // Update URL hash for direct linking
      if (history && history.replaceState) {
        history.replaceState(null, null, `#${tabId}`);
      }
      
      // STEP 3: Notify all registered components for this tab
      if (this.components[tabId] && this.components[tabId].length > 0) {
        this.components[tabId].forEach(component => {
          if (component.instance && typeof component.instance.reload === 'function') {
            console.log(`TabManager: Reloading component '${component.id}'`);
            try {
              component.instance.reload();
            } catch (err) {
              console.error(`TabManager: Error reloading component:`, err);
            }
          }
        });
      }
      
      // STEP 4: Dispatch tab change event
      this.dispatchEvent(this.EVENTS.TAB_CHANGED, {
        prevTabId: previousTabId,
        newTabId: tabId
      });
      
      console.log(`TabManager: Tab '${tabId}' activated successfully`);
      
    } catch (err) {
      console.error('TabManager: Error showing tab:', err);
      
      // Broadcast error to subscribers for better debugging
      this.dispatchEvent(this.EVENTS.ERROR, {
        source: 'showTab',
        tabId: tabId,
        error: err.message || 'Unknown error during tab switch'
      });
    }
  }
  
  /**
   * Check if a tab is currently active
   * @param {string} tabId - Tab identifier
   * @returns {boolean} Whether the tab is active
   */
  isTabActive(tabId) {
    return this.activeTabId === tabId;
  }
  
  /**
   * Get the active tab ID
   * @returns {string|null} The current active tab ID or null if none
   */
  getActiveTabId() {
    return this.activeTabId;
  }
  
  /**
   * Reset error recovery state
   * @private
   */
  _resetRecoveryState() {
    this.recoverySettings.retryCount = {};
  }
  
  /**
   * Attempt to recover from a tab switching error
   * @param {string} tabId - The tab that failed to activate
   * @param {string} previousTabId - The previously active tab
   * @param {Error} error - The error that occurred
   * @private
   */
  _attemptTabRecovery(tabId, previousTabId, error) {
    // Get operation identifier
    const operationId = `showTab:${tabId}`;
    
    // Check if we've exceeded max retries
    if (!this.recoverySettings.retryCount[operationId]) {
      this.recoverySettings.retryCount[operationId] = 0;
    }
    
    if (this.recoverySettings.retryCount[operationId] >= this.recoverySettings.maxRetries) {
      this.logger.error(`Recovery failed after ${this.recoverySettings.maxRetries} attempts for tab '${tabId}'`);
      
      // Dispatch recovery failure event
      this.dispatchEvent(this.EVENTS.RECOVERY_FAILURE, {
        tabId,
        previousTabId,
        error,
        attempts: this.recoverySettings.retryCount[operationId]
      });
      
      // Fall back to a known working tab if available, otherwise try the previous tab
      if (document.getElementById('details-tab-btn')) {
        this.logger.info('Recovering by switching to details tab');
        setTimeout(() => this.showTab('details'), this.recoverySettings.recoveryDelay);
      } else if (previousTabId && previousTabId !== tabId) {
        this.logger.info(`Recovering by switching back to previous tab: ${previousTabId}`);
        setTimeout(() => this.showTab(previousTabId), this.recoverySettings.recoveryDelay);
      }
      
      return;
    }
    
    // Increment retry counter
    this.recoverySettings.retryCount[operationId]++;
    
    // Dispatch recovery attempt event
    this.dispatchEvent(this.EVENTS.RECOVERY_ATTEMPT, {
      tabId,
      previousTabId,
      error,
      attempt: this.recoverySettings.retryCount[operationId],
      maxAttempts: this.recoverySettings.maxRetries
    });
    
    this.logger.info(`Recovery attempt ${this.recoverySettings.retryCount[operationId]} for tab '${tabId}'`);
    
    // Attempt recovery - first try cleaning the DOM
    this._cleanupTabDom(tabId);
    
    // Then retry showing the tab after a delay
    setTimeout(() => {
      try {
        this.logger.debug(`Retrying showTab for '${tabId}'`);
        this.showTab(tabId);
        
        // If we get here, recovery was successful
        this.logger.info(`Successfully recovered tab '${tabId}'`);
        
        // Dispatch recovery success event
        this.dispatchEvent(this.EVENTS.RECOVERY_SUCCESS, {
          tabId,
          previousTabId,
          attempts: this.recoverySettings.retryCount[operationId]
        });
        
        // Reset retry counter for this operation
        delete this.recoverySettings.retryCount[operationId];
      } catch (recoveryError) {
        this.logger.error(`Recovery attempt ${this.recoverySettings.retryCount[operationId]} failed:`, recoveryError);
        
        // Try again with exponential backoff
        const nextDelay = this.recoverySettings.recoveryDelay * (this.recoverySettings.retryCount[operationId] + 1);
        setTimeout(() => this._attemptTabRecovery(tabId, previousTabId, recoveryError), nextDelay);
      }
    }, this.recoverySettings.recoveryDelay);
  }
  
  /**
   * Clean up DOM issues that might be causing tab switching problems
   * @param {string} tabId - The tab ID to clean up
   * @private
   */
  _cleanupTabDom(tabId) {
    this.logger.debug(`Cleaning up DOM for tab '${tabId}'`);
    
    try {
      // Fix tab button if needed
      const tabButton = document.getElementById(`${tabId}-tab-btn`);
      if (tabButton) {
        // Fix any class issues
        tabButton.classList.remove('active');
        tabButton.classList.add('tab-btn');
      }
      
      // Fix tab content if needed
      const tabContent = document.getElementById(`${tabId}-content`);
      if (tabContent) {
        // Remove all inline styles and re-add the basics
        tabContent.removeAttribute('style');
        tabContent.style.display = 'none';
        
        // Ensure proper classes
        tabContent.classList.remove('active');
        tabContent.classList.add('tab-content');
        
        // Make sure it's actually in the DOM
        const tabContentContainer = document.querySelector('.tab-content-container');
        if (tabContentContainer && !tabContentContainer.contains(tabContent)) {
          this.logger.info(`Re-adding ${tabId}-content to the DOM`);
          tabContentContainer.appendChild(tabContent);
        }
      }
    } catch (error) {
      this.logger.error('Error during DOM cleanup:', error);
    }
  }
  
  /**
   * Get the currently active tab ID
   * @returns {string} Active tab ID
   */
  getActiveTabId() {
    return this.activeTabId;
  }
  
  /**
   * Reload all components for the active tab
   */
  reloadActiveTab() {
    if (!this.activeTabId) return;
    
    const components = this.components[this.activeTabId] || [];
    components.forEach(component => {
      if (component.instance && typeof component.instance.reload === 'function') {
        try {
          component.instance.reload();
        } catch (err) {
          console.error(`TabManager: Error reloading component ${component.id}:`, err);
        }
      }
    });
  }
  
  /**
   * Request a data refresh across all components or for a specific tab
   * This enables components to communicate data refresh needs without direct coupling
   * @param {Object} options - Refresh options
   * @param {string} [options.tabId] - Specific tab to refresh (if omitted, active tab is used)
   * @param {boolean} [options.forceRefresh=false] - Force refresh even for inactive tabs
   * @param {Object} [options.refreshData] - Optional data to pass with the refresh event
   * @returns {boolean} Success status
   */
  requestDataRefresh(options = {}) {
    const tabId = options.tabId || this.activeTabId;
    const forceRefresh = !!options.forceRefresh;
    
    if (!tabId && !forceRefresh) {
      console.warn('TabManager: Cannot request data refresh - no active tab and force refresh not specified');
      return false;
    }
    
    console.log(`TabManager: Requesting data refresh for ${tabId || 'all tabs'} (force: ${forceRefresh})`);
    
    // Dispatch event for the refresh
    this.dispatchEvent(this.EVENTS.DATA_REFRESH, {
      tabId,
      forceRefresh,
      refreshData: options.refreshData || {},
      timestamp: Date.now()
    });
    
    // If not forcing a refresh of all tabs, also directly call the reload method
    // on registered components for the specified tab
    if (tabId && !forceRefresh && this.components[tabId]) {
      this.components[tabId].forEach(component => {
        if (component.instance && typeof component.instance.reload === 'function') {
          try {
            console.log(`TabManager: Directly calling reload on ${component.id}`);
            component.instance.reload();
          } catch (err) {
            console.error(`TabManager: Error calling reload on component ${component.id}:`, err);
            this.dispatchEvent(this.EVENTS.ERROR, {
              source: 'requestDataRefresh',
              componentId: component.id,
              error: err.message
            });
          }
        }
      });
    }
    
    return true;
  }
  
  /**
   * Universal event dispatcher for the TabManager system
   * @param {string} eventName - Name of the event to dispatch
   * @param {Object} data - Data to include in the event detail
   * @param {boolean} bubbles - Whether the event bubbles up the DOM
   */
  dispatchEvent(eventName, data = {}, bubbles = true) {
    try {
      // Always add timestamp
      const detail = {
        ...data,
        timestamp: Date.now(),
        source: 'TabManager'
      };
      
      // Create and dispatch the event
      const event = new CustomEvent(eventName, { detail, bubbles });
      document.dispatchEvent(event);
      
      // Call any direct subscribers
      this._notifySubscribers(eventName, detail);
      
      console.log(`TabManager: Event dispatched: ${eventName}`, detail);
      return true;
    } catch (err) {
      console.error('TabManager: Error dispatching event:', err);
      return false;
    }
  }
  
  /**
   * Subscribe to TabManager events directly (without DOM events)
   * @param {string} eventName - Name of the event to listen for
   * @param {Function} callback - Function to call when event occurs
   * @param {Object} context - Optional context for callback execution
   * @returns {string} Subscription ID for unsubscribing
   */
  subscribe(eventName, callback, context = null) {
    if (!eventName || typeof callback !== 'function') {
      console.error('TabManager: Invalid subscription parameters');
      return null;
    }
    
    // Initialize event subscribers array if needed
    if (!this.subscribers[eventName]) {
      this.subscribers[eventName] = [];
    }
    
    // Generate unique subscription ID
    const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Add subscriber
    this.subscribers[eventName].push({
      id: subscriptionId,
      callback,
      context
    });
    
    console.log(`TabManager: New subscriber added for ${eventName}`);
    return subscriptionId;
  }
  
  /**
   * Unsubscribe from TabManager events
   * @param {string} subscriptionId - ID returned from subscribe method
   * @returns {boolean} Success status
   */
  unsubscribe(subscriptionId) {
    if (!subscriptionId) return false;
    
    // Check all event types for this subscription
    let found = false;
    Object.keys(this.subscribers).forEach(eventName => {
      const eventSubscribers = this.subscribers[eventName];
      const index = eventSubscribers.findIndex(sub => sub.id === subscriptionId);
      
      if (index !== -1) {
        eventSubscribers.splice(index, 1);
        found = true;
        console.log(`TabManager: Subscriber removed for ${eventName}`);
      }
    });
    
    return found;
  }
  
  /**
   * Notify all subscribers of an event
   * @private
   * @param {string} eventName - Event that occurred
   * @param {Object} detail - Event data
   */
  _notifySubscribers(eventName, detail) {
    const subscribers = this.subscribers[eventName] || [];
    
    subscribers.forEach(subscriber => {
      try {
        if (subscriber.context) {
          subscriber.callback.call(subscriber.context, detail);
        } else {
          subscriber.callback(detail);
        }
      } catch (err) {
        console.error(`TabManager: Error in subscriber callback for ${eventName}:`, err);
      }
    });
  }
  
  /**
   * Handle tab change event dispatch (legacy method)
   * @private
   */
  _dispatchEvent(newTabId, previousTabId) {
    // Use the new event system for consistency
    this.dispatchEvent(this.EVENTS.TAB_CHANGED, {
      newTabId,
      previousTabId
    });
    
    // Also dispatch the before change event
    this.dispatchEvent(this.EVENTS.BEFORE_TAB_CHANGE, {
      newTabId,
      previousTabId
    });
  }
}

// Create a singleton instance for global use
if (!window.tabManager) {
  window.tabManager = new TabManager();
  console.log('TabManager: Created global instance');
}

// Export class for module support
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TabManager;
}
