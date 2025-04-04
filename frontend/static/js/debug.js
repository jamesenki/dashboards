/**
 * IoTSphere Debug and Logging Utilities
 *
 * A centralized debugging and diagnostic system for the IoTSphere application.
 * This module provides consistent error handling, logging, and diagnostic tools
 * for all components of the application.
 */

/**
 * LogLevel enum - defines the severity levels for logging
 */
const LogLevel = {
  DEBUG: 1,    // Detailed information for debugging purposes
  INFO: 2,     // General information about system operation
  WARN: 3,     // Warning conditions that don't impact functionality
  ERROR: 4,    // Error conditions that impact functionality
  CRITICAL: 5  // Critical errors that require immediate attention
};

/**
 * Debug configuration - controls debug behavior
 */
const DebugConfig = {
  // Current log level - only messages at this level or higher are displayed
  logLevel: LogLevel.INFO,

  // Whether to add timestamps to logs
  showTimestamps: true,

  // Whether to include component names in logs
  showComponent: true,

  // Send logs to remote service (when configured)
  remoteLogging: false,

  // URL for remote logging service
  remoteLoggingUrl: null,

  // Generate stack traces for errors
  includeStackTrace: true,

  // Store logs in memory for debug panel
  storeLogsLocally: true,

  // Maximum number of log entries to keep in memory
  maxLocalLogEntries: 1000
};

/**
 * In-memory log storage
 */
const LogStore = {
  entries: [],

  /**
   * Add a log entry to the store
   */
  addEntry(level, component, message, data) {
    if (DebugConfig.storeLogsLocally) {
      this.entries.push({
        timestamp: new Date(),
        level,
        component,
        message,
        data
      });

      // Trim if we exceed max entries
      if (this.entries.length > DebugConfig.maxLocalLogEntries) {
        this.entries.shift();
      }
    }
  },

  /**
   * Get all log entries
   */
  getEntries() {
    return [...this.entries];
  },

  /**
   * Clear all log entries
   */
  clear() {
    this.entries = [];
  },

  /**
   * Get logs for a specific component
   */
  getEntriesForComponent(component) {
    return this.entries.filter(entry => entry.component === component);
  },

  /**
   * Get logs at or above a certain level
   */
  getEntriesByLevel(minLevel) {
    return this.entries.filter(entry => entry.level >= minLevel);
  }
};

/**
 * Logger class - provides logging functionality for components
 */
class Logger {
  /**
   * Create a new logger for a component
   * @param {string} componentName - Name of the component using this logger
   */
  constructor(componentName) {
    this.componentName = componentName || 'Unknown';
  }

  /**
   * Format a log message with optional timestamp and component name
   */
  formatMessage(message) {
    let formattedMessage = '';

    if (DebugConfig.showTimestamps) {
      const now = new Date();
      const timeString = now.toISOString().split('T')[1].split('.')[0];
      formattedMessage += `[${timeString}] `;
    }

    if (DebugConfig.showComponent) {
      formattedMessage += `[${this.componentName}] `;
    }

    formattedMessage += message;
    return formattedMessage;
  }

  /**
   * Log a debug message
   */
  debug(message, data) {
    if (DebugConfig.logLevel <= LogLevel.DEBUG) {
      console.debug(this.formatMessage(message), data || '');
      LogStore.addEntry(LogLevel.DEBUG, this.componentName, message, data);
    }
  }

  /**
   * Log an info message
   */
  info(message, data) {
    if (DebugConfig.logLevel <= LogLevel.INFO) {
      console.log(this.formatMessage(message), data || '');
      LogStore.addEntry(LogLevel.INFO, this.componentName, message, data);
    }
  }

  /**
   * Log a warning message
   */
  warn(message, data) {
    if (DebugConfig.logLevel <= LogLevel.WARN) {
      console.warn(this.formatMessage(message), data || '');
      LogStore.addEntry(LogLevel.WARN, this.componentName, message, data);
    }
  }

  /**
   * Log an error message
   */
  error(message, error) {
    if (DebugConfig.logLevel <= LogLevel.ERROR) {
      console.error(this.formatMessage(message), error || '');

      // Add stack trace if available and configured
      let errorData = error;
      if (DebugConfig.includeStackTrace && error instanceof Error) {
        errorData = {
          message: error.message,
          stack: error.stack,
          name: error.name
        };
      }

      LogStore.addEntry(LogLevel.ERROR, this.componentName, message, errorData);

      // Send to remote logging if enabled
      if (DebugConfig.remoteLogging && DebugConfig.remoteLoggingUrl) {
        this.sendRemoteLog(LogLevel.ERROR, message, errorData);
      }
    }
  }

  /**
   * Log a critical error message
   */
  critical(message, error) {
    if (DebugConfig.logLevel <= LogLevel.CRITICAL) {
      console.error(this.formatMessage(`CRITICAL: ${message}`), error || '');

      // Add stack trace if available
      let errorData = error;
      if (DebugConfig.includeStackTrace && error instanceof Error) {
        errorData = {
          message: error.message,
          stack: error.stack,
          name: error.name
        };
      }

      LogStore.addEntry(LogLevel.CRITICAL, this.componentName, message, errorData);

      // Always send critical errors to remote logging if enabled
      if (DebugConfig.remoteLogging && DebugConfig.remoteLoggingUrl) {
        this.sendRemoteLog(LogLevel.CRITICAL, message, errorData);
      }
    }
  }

  /**
   * Send a log to the remote logging service
   * @param {number} level - Log level
   * @param {string} message - Log message
   * @param {*} data - Additional data to log
   */
  async sendRemoteLog(level, message, data) {
    if (!DebugConfig.remoteLoggingUrl) return;

    try {
      await fetch(DebugConfig.remoteLoggingUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          level,
          component: this.componentName,
          message,
          data,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href
        })
      });
    } catch (e) {
      // Don't recurse by calling this.error
      console.error('Failed to send remote log:', e);
    }
  }
}

/**
 * Global error handler to catch unhandled errors
 */
window.addEventListener('error', (event) => {
  const logger = new Logger('GlobalErrorHandler');
  logger.error(`Unhandled error: ${event.message} at ${event.filename}:${event.lineno}`, {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error
  });
});

/**
 * Global promise rejection handler
 */
window.addEventListener('unhandledrejection', (event) => {
  const logger = new Logger('GlobalPromiseHandler');
  logger.error('Unhandled promise rejection', event.reason);
});

/**
 * Diagnostic APIs for testing the system
 */
const Diagnostics = {
  /**
   * Test API connectivity
   */
  async testApiConnectivity() {
    const logger = new Logger('Diagnostics');
    logger.info('Testing API connectivity...');

    try {
      const response = await fetch('/api/health-check');
      if (response.ok) {
        logger.info('API connection successful');
        return true;
      } else {
        logger.error(`API connection failed with status: ${response.status}`);
        return false;
      }
    } catch (error) {
      logger.error('API connection test failed', error);
      return false;
    }
  },

  /**
   * Test water heater API specifically
   */
  async testWaterHeaterApi() {
  try {
    // Get the server hostname and port for direct API access
    const apiHost = window.location.hostname;
    const apiUrl = `http://${apiHost}:8006/api/water-heaters/`;

    console.log('Fetching water heaters directly from:', apiUrl);
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      },
      mode: 'cors'
    });
    console.log('Response status:', response.status, response.statusText);

    if (response.ok) {
      const data = await response.json();
      console.log('Water heaters data:', data);
      console.log('First water heater:', data[0]);

      // Check data structure for potential issues
      if (data && Array.isArray(data)) {
        console.log('Received array of', data.length, 'water heaters');

        // Check for required properties
        const firstItem = data[0];
        if (firstItem) {
          const expectedProps = ['id', 'name', 'type', 'status', 'current_temperature', 'target_temperature', 'mode', 'heater_status'];
          const missingProps = expectedProps.filter(prop => firstItem[prop] === undefined);

          if (missingProps.length > 0) {
            console.error('Missing required properties:', missingProps);
          } else {
            console.log('All required properties present');
          }
        }
      } else {
        console.error('Expected an array of water heaters but got:', typeof data);
      }
    } else {
      console.error('Failed to fetch water heaters:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('Error testing water heater API:', error);
  }
}

// Export diagnostic modules to window
try {
  window.Diagnostics = Diagnostics;
  window.Logger = Logger;
  window.LogLevel = LogLevel;
  window.LogStore = LogStore;
} catch (e) {
  console.error('Error exporting debug modules:', e);
}

// Only run test if explicitly requested via URL parameter
if (window.location.search.includes('test_api=true')) {
  console.log('Running water heater API test');
  Diagnostics.testWaterHeaterApi();
}
