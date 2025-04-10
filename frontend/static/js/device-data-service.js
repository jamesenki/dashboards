/**
 * Device Data Service
 *
 * A dedicated service for data fetching with:
 * - Request caching to reduce unnecessary network calls
 * - Proper error handling
 * - Request debouncing for performance
 * - Standardized data transformation
 */

(function() {
  'use strict';

  // Cache settings
  const CONFIG = {
    cacheTTL: 60000, // 1 minute cache lifetime
    temperatureHistoryCacheTTL: 300000, // 5 minutes for temperature history
    maxCacheSize: 50, // Maximum items in cache
    debounceTime: 300, // Debounce time in ms
  };

  // Data cache
  const cache = {
    data: {},
    timestamps: {},
    requests: {} // Track in-flight requests
  };

  // Initialize when ready
  document.addEventListener('DOMContentLoaded', initialize);
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(initialize, 100);
  }

  function initialize() {
    console.log('🔄 Device Data Service: Initializing');

    // Add event listener for tab changes to preload data
    if (window.OptimizedTabManager) {
      window.OptimizedTabManager.addEventListener('tabActivated', handleTabActivated);
    }

    // Expose the API
    exposePublicApi();

    console.log('🔄 Device Data Service: Initialized');
  }

  function handleTabActivated(tab) {
    // Preload data for specific tabs
    const deviceId = getDeviceId();
    if (!deviceId) return;

    if (tab.id === 'history' || tab.id === 'history-content') {
      // Preload temperature history for history tab
      getTemperatureHistory(deviceId);
    }
  }

  // Device data APIs
  function getDeviceDetails(deviceId) {
    return fetchWithCache(`device-details-${deviceId}`, `/api/water-heaters/${deviceId}`);
  }

  function getTemperatureHistory(deviceId, options = {}) {
    const days = options.days || 7;
    const limit = options.limit || 100;
    const cacheKey = `temperature-history-${deviceId}-${days}-${limit}`;

    // Use longer cache TTL for temperature history
    return fetchWithCache(
      cacheKey,
      `/api/device-shadow/${deviceId}/temperature-history?days=${days}&limit=${limit}`,
      CONFIG.temperatureHistoryCacheTTL
    );
  }

  function getDeviceStatus(deviceId) {
    // Status should have a short cache time
    return fetchWithCache(
      `device-status-${deviceId}`,
      `/api/water-heaters/${deviceId}/status`,
      30000 // 30 seconds TTL for status
    );
  }

  function getDevicePredictions(deviceId) {
    return fetchWithCache(
      `device-predictions-${deviceId}`,
      `/api/water-heaters/${deviceId}/predictions`
    );
  }

  // Cache management
  function fetchWithCache(cacheKey, url, ttl = CONFIG.cacheTTL) {
    return new Promise((resolve, reject) => {
      // Check if we already have a request in flight
      if (cache.requests[cacheKey]) {
        console.log(`🔄 Request already in flight for ${cacheKey}, piggybacking`);

        // Piggyback on the existing request
        cache.requests[cacheKey].push({ resolve, reject });
        return;
      }

      // Check cache freshness
      const now = Date.now();
      if (
        cache.data[cacheKey] &&
        cache.timestamps[cacheKey] &&
        now - cache.timestamps[cacheKey] < ttl
      ) {
        console.log(`🔄 Cache hit for ${cacheKey}`);
        resolve(cache.data[cacheKey]);
        return;
      }

      console.log(`🔄 Cache miss for ${cacheKey}, fetching data`);

      // Initialize request tracking
      cache.requests[cacheKey] = [{ resolve, reject }];

      // Fetch data
      fetch(url)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          // Update cache
          cache.data[cacheKey] = data;
          cache.timestamps[cacheKey] = Date.now();

          // Clean cache if too large
          cleanCacheIfNeeded();

          // Resolve all pending requests
          const pendingRequests = cache.requests[cacheKey];
          delete cache.requests[cacheKey];

          pendingRequests.forEach(request => request.resolve(data));
        })
        .catch(error => {
          console.error(`Error fetching ${url}:`, error);

          // Reject all pending requests
          const pendingRequests = cache.requests[cacheKey];
          delete cache.requests[cacheKey];

          pendingRequests.forEach(request => request.reject(error));
        });
    });
  }

  function cleanCacheIfNeeded() {
    const cacheKeys = Object.keys(cache.data);

    if (cacheKeys.length > CONFIG.maxCacheSize) {
      console.log(`🔄 Cache size (${cacheKeys.length}) exceeds limit, cleaning up`);

      // Sort cache entries by timestamp (oldest first)
      const sortedEntries = cacheKeys
        .map(key => ({ key, timestamp: cache.timestamps[key] || 0 }))
        .sort((a, b) => a.timestamp - b.timestamp);

      // Remove oldest entries to get back to max size
      const entriesToRemove = sortedEntries.slice(0, cacheKeys.length - CONFIG.maxCacheSize);

      entriesToRemove.forEach(entry => {
        delete cache.data[entry.key];
        delete cache.timestamps[entry.key];
      });

      console.log(`🔄 Removed ${entriesToRemove.length} oldest cache entries`);
    }
  }

  function invalidateCache(cacheKey) {
    if (cacheKey) {
      // Invalidate specific cache entry
      delete cache.data[cacheKey];
      delete cache.timestamps[cacheKey];
      console.log(`🔄 Invalidated cache for ${cacheKey}`);
    } else {
      // Invalidate entire cache
      Object.keys(cache.data).forEach(key => {
        delete cache.data[key];
        delete cache.timestamps[key];
      });
      console.log('🔄 Invalidated entire cache');
    }
  }

  // Utility functions
  function getDeviceId() {
    // Try to extract device ID from URL
    const path = window.location.pathname;
    const matches = path.match(/\/water-heaters\/(wh-[a-zA-Z0-9]+)/);

    if (matches && matches[1]) {
      return matches[1];
    }

    // Fallback: look for device ID in the DOM
    const deviceIdEl = document.querySelector('[data-device-id]');
    if (deviceIdEl) {
      return deviceIdEl.dataset.deviceId;
    }

    return null;
  }

  // Debounce helper
  function debounce(func, wait) {
    let timeout;
    return function(...args) {
      const context = this;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
  }

  // Public API
  function exposePublicApi() {
    window.DeviceDataService = {
      getDeviceDetails,
      getTemperatureHistory,
      getDeviceStatus,
      getDevicePredictions,
      invalidateCache,
      getCacheStats: () => ({
        size: Object.keys(cache.data).length,
        keys: Object.keys(cache.data),
        timestamps: { ...cache.timestamps }
      })
    };
  }
})();
