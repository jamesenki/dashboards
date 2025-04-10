/**
 * IoTSphere Debugging and Performance Monitoring
 *
 * Provides performance monitoring capabilities and debug tools for IoTSphere.
 * Follows TDD principles by focusing on measurable performance metrics.
 */
(function() {
  'use strict';

  // Create global namespace
  window.IoTSphereMonitor = {};

  // Configuration
  const CONFIG = {
    performanceMonitoring: true,
    errorTracking: true,
    networkMonitoring: true,
    logLevel: 'info', // 'debug', 'info', 'warn', 'error'
    samplingRate: 1.0, // 1.0 = 100% of page loads are monitored
    metricsEndpoint: '/api/v1/metrics', // Where to send metrics if enabled
    storageKey: 'iotsphere_metrics'
  };

  // Performance metrics storage
  const metrics = {
    pageLoad: {},
    navigation: {},
    apiCalls: {},
    errors: [],
    resources: {},
    userInteractions: {}
  };

  /**
   * Initialize the monitoring system
   */
  function init() {
    // Only run if we should sample this page view (for throttling in production)
    if (Math.random() > CONFIG.samplingRate) {
      console.log('Performance monitoring disabled for this page view (sampling)');
      return;
    }

    console.log('🔍 IoTSphere Debug & Performance Monitoring: Initializing...');

    // Start tracking page load metrics
    trackPageLoadMetrics();

    // Setup API call monitoring
    monitorApiCalls();

    // Track errors
    setupErrorTracking();

    // Monitor network requests
    if (CONFIG.networkMonitoring) {
      monitorNetworkRequests();
    }

    // Track user interactions
    trackUserInteractions();

    // Register metric collection and reporting
    window.addEventListener('beforeunload', function() {
      finalizeMetrics();
      storeMetricsLocally();
    });

    // Note: we're not setting up automatic server reporting
    // as that would require extra backend support

    console.log('🔍 Monitoring initialized successfully');
  }

  /**
   * Track page load performance metrics
   */
  function trackPageLoadMetrics() {
    // Only run if the Performance API is available
    if (!window.performance || !window.performance.timing) {
      console.warn('Performance API not available, cannot track page load metrics');
      return;
    }

    // Store navigation timing metrics
    const navTiming = performance.timing;
    const startTime = navTiming.navigationStart;

    metrics.pageLoad = {
      // Time to first byte
      ttfb: navTiming.responseStart - navTiming.navigationStart,

      // DOM content loaded
      domContentLoaded: navTiming.domContentLoadedEventEnd - navTiming.navigationStart,

      // Page fully loaded
      pageLoad: navTiming.loadEventEnd - navTiming.navigationStart,

      // DNS lookup time
      dns: navTiming.domainLookupEnd - navTiming.domainLookupStart,

      // Connection time
      connect: navTiming.connectEnd - navTiming.connectStart,

      // Request time
      request: navTiming.responseEnd - navTiming.requestStart,

      // Response download time
      response: navTiming.responseEnd - navTiming.responseStart,

      // DOM processing time
      domProcessing: navTiming.domComplete - navTiming.domLoading,

      // Date/time of measurement
      timestamp: new Date().toISOString(),

      // Page URL (without query params)
      url: window.location.pathname
    };

    // Add additional paint timing metrics if available
    if (window.performance && window.performance.getEntriesByType) {
      const paintMetrics = performance.getEntriesByType('paint');

      paintMetrics.forEach(function(entry) {
        if (entry.name === 'first-paint') {
          metrics.pageLoad.firstPaint = entry.startTime;
        } else if (entry.name === 'first-contentful-paint') {
          metrics.pageLoad.firstContentfulPaint = entry.startTime;
        }
      });
    }

    log('debug', 'Page load metrics:', metrics.pageLoad);
  }

  /**
   * Monitor API calls using fetch and XMLHttpRequest
   */
  function monitorApiCalls() {
    // Store original fetch
    const originalFetch = window.fetch;

    // Override fetch to monitor API calls
    window.fetch = function() {
      const startTime = performance.now();
      const fetchArgs = arguments;
      const url = typeof fetchArgs[0] === 'string' ? fetchArgs[0] : fetchArgs[0].url;

      // Only track API calls, not all fetch requests
      const isApiCall = url.includes('/api/') || url.includes('/ws/');

      // Call original fetch
      return originalFetch.apply(this, arguments).then(function(response) {
        if (isApiCall) {
          const endTime = performance.now();
          const duration = endTime - startTime;

          // Store API call metrics
          recordApiCall(url, duration, response.status);
        }
        return response;
      }).catch(function(error) {
        if (isApiCall) {
          const endTime = performance.now();
          const duration = endTime - startTime;

          // Store failed API call
          recordApiCall(url, duration, 0, error.message);
        }
        throw error;
      });
    };

    // Also monitor XMLHttpRequest for older code
    const originalXhrOpen = XMLHttpRequest.prototype.open;
    const originalXhrSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function() {
      this._url = arguments[1];
      this._method = arguments[0];
      this._startTime = performance.now();
      return originalXhrOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function() {
      const xhr = this;
      const url = xhr._url;
      const isApiCall = url.includes('/api/') || url.includes('/ws/');

      if (isApiCall) {
        xhr.addEventListener('load', function() {
          const endTime = performance.now();
          const duration = endTime - xhr._startTime;
          recordApiCall(url, duration, xhr.status);
        });

        xhr.addEventListener('error', function() {
          const endTime = performance.now();
          const duration = endTime - xhr._startTime;
          recordApiCall(url, duration, 0, 'XHR error');
        });
      }

      return originalXhrSend.apply(this, arguments);
    };
  }

  /**
   * Record API call metrics
   */
  function recordApiCall(url, duration, status, errorMsg) {
    // Extract API endpoint name from URL
    const urlObj = new URL(url, window.location.origin);
    const path = urlObj.pathname;

    // Create API metrics entry
    const apiMetric = {
      endpoint: path,
      duration: Math.round(duration),
      status: status,
      timestamp: new Date().toISOString()
    };

    if (errorMsg) {
      apiMetric.error = errorMsg;
    }

    // Store in metrics object
    if (!metrics.apiCalls[path]) {
      metrics.apiCalls[path] = [];
    }

    metrics.apiCalls[path].push(apiMetric);

    // Log for debugging
    log('debug', `API call: ${path} - ${duration}ms - status: ${status}`);
  }

  /**
   * Setup tracking of JavaScript errors
   */
  function setupErrorTracking() {
    if (!CONFIG.errorTracking) return;

    // Store original error handler
    const originalOnError = window.onerror;

    // Override error handler
    window.onerror = function(message, source, lineno, colno, error) {
      // Record error
      const errorDetails = {
        message: message,
        source: source,
        lineno: lineno,
        colno: colno,
        stack: error && error.stack ? error.stack : 'No stack trace',
        timestamp: new Date().toISOString(),
        url: window.location.pathname
      };

      metrics.errors.push(errorDetails);

      log('error', 'JavaScript error:', errorDetails);

      // Call original handler if it exists
      if (typeof originalOnError === 'function') {
        return originalOnError.apply(this, arguments);
      }

      return false;
    };

    // Also track unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
      const errorDetails = {
        message: 'Unhandled Promise Rejection',
        reason: event.reason ? event.reason.message || String(event.reason) : 'Unknown reason',
        stack: event.reason && event.reason.stack ? event.reason.stack : 'No stack trace',
        timestamp: new Date().toISOString(),
        url: window.location.pathname
      };

      metrics.errors.push(errorDetails);

      log('error', 'Unhandled Promise Rejection:', errorDetails);
    });
  }

  /**
   * Monitor network requests for resource loading
   */
  function monitorNetworkRequests() {
    // Use Resource Timing API if available
    if (window.performance && window.performance.getEntriesByType) {
      // Get all resource timing entries
      const processResources = function() {
        const resources = performance.getEntriesByType('resource');

        resources.forEach(function(resource) {
          const url = resource.name;
          const fileType = getResourceType(url);

          if (!metrics.resources[fileType]) {
            metrics.resources[fileType] = [];
          }

          // Only add if we haven't already tracked this resource
          const exists = metrics.resources[fileType].some(r => r.url === url);
          if (!exists) {
            metrics.resources[fileType].push({
              url: url,
              duration: Math.round(resource.duration),
              size: resource.transferSize || 0,
              startTime: Math.round(resource.startTime)
            });
          }
        });
      };

      // Process resources now and again before page unload
      setTimeout(processResources, 3000);
      window.addEventListener('beforeunload', processResources);
    }
  }

  /**
   * Get resource type from URL
   */
  function getResourceType(url) {
    const extension = url.split('.').pop().split('?')[0].toLowerCase();

    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(extension)) {
      return 'image';
    } else if (['js'].includes(extension)) {
      return 'script';
    } else if (['css'].includes(extension)) {
      return 'style';
    } else if (['html', 'htm'].includes(extension)) {
      return 'html';
    } else if (['json'].includes(extension) || url.includes('/api/')) {
      return 'api';
    } else {
      return 'other';
    }
  }

  /**
   * Track user interactions for UX metrics
   */
  function trackUserInteractions() {
    // Track tab switches
    trackTabSwitching();

    // Track button clicks
    trackButtonClicks();

    // Track form interactions
    trackFormInteractions();
  }

  /**
   * Track tab switching
   */
  function trackTabSwitching() {
    // Find all tabs
    const tabElements = document.querySelectorAll('.tab, [data-tab], .nav-item');

    tabElements.forEach(function(tab) {
      tab.addEventListener('click', function() {
        const tabId = this.dataset.tab || this.id || this.textContent.trim();

        if (!metrics.userInteractions.tabSwitches) {
          metrics.userInteractions.tabSwitches = [];
        }

        metrics.userInteractions.tabSwitches.push({
          tabId: tabId,
          timestamp: new Date().toISOString()
        });

        log('debug', `Tab switch: ${tabId}`);
      });
    });
  }

  /**
   * Track button clicks
   */
  function trackButtonClicks() {
    // Find all buttons
    const buttons = document.querySelectorAll('button, .btn, [type="button"]');

    buttons.forEach(function(button) {
      button.addEventListener('click', function() {
        const buttonId = this.id || this.textContent.trim() || 'unnamed-button';

        if (!metrics.userInteractions.buttonClicks) {
          metrics.userInteractions.buttonClicks = [];
        }

        metrics.userInteractions.buttonClicks.push({
          buttonId: buttonId,
          timestamp: new Date().toISOString()
        });

        log('debug', `Button click: ${buttonId}`);
      });
    });
  }

  /**
   * Track form interactions
   */
  function trackFormInteractions() {
    // Find all forms
    const forms = document.querySelectorAll('form');

    forms.forEach(function(form) {
      form.addEventListener('submit', function(event) {
        const formId = this.id || this.name || 'unnamed-form';

        if (!metrics.userInteractions.formSubmits) {
          metrics.userInteractions.formSubmits = [];
        }

        metrics.userInteractions.formSubmits.push({
          formId: formId,
          timestamp: new Date().toISOString()
        });

        log('debug', `Form submit: ${formId}`);
      });
    });
  }

  /**
   * Finalize metrics before reporting
   */
  function finalizeMetrics() {
    // Add session duration
    metrics.sessionDuration = {
      startTime: window.performance.timing.navigationStart,
      endTime: Date.now(),
      duration: Date.now() - window.performance.timing.navigationStart
    };

    // Add page information
    metrics.pageInfo = {
      url: window.location.pathname,
      title: document.title,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };

    log('info', 'Finalized metrics:', metrics);
  }

  /**
   * Store metrics locally
   */
  function storeMetricsLocally() {
    try {
      // Get existing metrics
      let storedMetrics = JSON.parse(localStorage.getItem(CONFIG.storageKey) || '[]');

      // Add new metrics
      storedMetrics.push(metrics);

      // Keep only the last 10 page views to avoid excessive storage
      if (storedMetrics.length > 10) {
        storedMetrics = storedMetrics.slice(-10);
      }

      // Store back to localStorage
      localStorage.setItem(CONFIG.storageKey, JSON.stringify(storedMetrics));

      log('debug', 'Metrics stored locally');
    } catch (e) {
      console.error('Failed to store metrics locally:', e);
    }
  }

  /**
   * Logging helper
   */
  function log(level, message, data) {
    const logLevels = {
      debug: 0,
      info: 1,
      warn: 2,
      error: 3
    };

    // Only log if the level is sufficient
    if (logLevels[level] >= logLevels[CONFIG.logLevel]) {
      if (data) {
        console[level](`[IoTSphereMonitor] ${message}`, data);
      } else {
        console[level](`[IoTSphereMonitor] ${message}`);
      }
    }
  }

  // Public API
  const IoTSphereMonitor = {
    /**
     * Get the current metrics
     */
    getMetrics: function() {
      return JSON.parse(JSON.stringify(metrics)); // Return a copy
    },

    /**
     * Get stored metrics
     */
    getStoredMetrics: function() {
      try {
        return JSON.parse(localStorage.getItem(CONFIG.storageKey) || '[]');
      } catch (e) {
        console.error('Failed to retrieve stored metrics:', e);
        return [];
      }
    },

    /**
     * Clear stored metrics
     */
    clearStoredMetrics: function() {
      localStorage.removeItem(CONFIG.storageKey);
      log('info', 'Cleared stored metrics');
    },

    /**
     * Log a custom metric
     */
    logCustomMetric: function(category, name, value) {
      if (!metrics.customMetrics) {
        metrics.customMetrics = {};
      }

      if (!metrics.customMetrics[category]) {
        metrics.customMetrics[category] = [];
      }

      metrics.customMetrics[category].push({
        name: name,
        value: value,
        timestamp: new Date().toISOString()
      });

      log('debug', `Custom metric: ${category}.${name} = ${value}`);
    },

    /**
     * Measure a specific action's duration
     */
    measureDuration: function(actionName, callback) {
      const startTime = performance.now();

      try {
        // Execute the callback
        const result = callback();

        // Handle promises
        if (result && typeof result.then === 'function') {
          return result.then(function(value) {
            const duration = performance.now() - startTime;

            IoTSphereMonitor.logCustomMetric('performance', actionName, duration);

            return value;
          }).catch(function(error) {
            const duration = performance.now() - startTime;

            IoTSphereMonitor.logCustomMetric('performance', actionName, duration);
            IoTSphereMonitor.logCustomMetric('errors', actionName, error.message || String(error));

            throw error;
          });
        } else {
          // Handle synchronous results
          const duration = performance.now() - startTime;

          IoTSphereMonitor.logCustomMetric('performance', actionName, duration);

          return result;
        }
      } catch (error) {
        const duration = performance.now() - startTime;

        IoTSphereMonitor.logCustomMetric('performance', actionName, duration);
        IoTSphereMonitor.logCustomMetric('errors', actionName, error.message || String(error));

        throw error;
      }
    }
  };

  // Expose to global scope
  window.IoTSphereMonitor = IoTSphereMonitor;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
