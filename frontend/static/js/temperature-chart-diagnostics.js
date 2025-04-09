/**
 * Temperature Chart Diagnostics
 *
 * This script runs comprehensive diagnostics on the temperature chart in the History tab
 * to identify any issues with initialization, visibility, or data loading.
 *
 * Following TDD principles:
 * 1. RED: Identify issues through diagnostics
 * 2. GREEN: Gather information to solve the issues
 * 3. REFACTOR: Provide insights for a better implementation
 */

(function() {
  console.log('🔍 DIAGNOSTIC: Temperature Chart Inspector initializing...');

  // Run diagnostics when DOM is loaded
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(runDiagnostics, 1000);
  });

  // Also run diagnostics when history tab is clicked
  document.addEventListener('click', function(event) {
    if (event.target && event.target.dataset && event.target.dataset.tab === 'history') {
      console.log('🔍 DIAGNOSTIC: History tab clicked, scheduling diagnostics...');
      setTimeout(runDiagnostics, 1000);
    }
  });

  /**
   * Main diagnostic function for temperature chart
   */
  function runDiagnostics() {
    console.log('--------------------------------------------');
    console.log('🔍 DIAGNOSTIC: Running temperature chart diagnostics');
    console.log('--------------------------------------------');

    // Check if we're on the history tab
    const historyContent = document.getElementById('history-content');
    if (!historyContent || getComputedStyle(historyContent).display === 'none') {
      console.log('❌ DIAGNOSTIC: Not on history tab, diagnostics aborted');
      return;
    }

    console.log('✅ DIAGNOSTIC: On history tab, continuing diagnostics');

    // Get device ID
    const deviceId = getDeviceId();
    console.log(`ℹ️ DIAGNOSTIC: Device ID: ${deviceId || 'Not found'}`);

    // Check chart elements
    const diagnosticResults = {
      canvasExists: false,
      canvasVisible: false,
      chartInitialized: false,
      apiCalled: false,
      chartData: null,
      globalVariables: [],
      cssIssues: [],
      errors: []
    };

    // Check canvas existence and visibility
    const canvas = document.getElementById('temperature-chart');
    diagnosticResults.canvasExists = !!canvas;

    if (canvas) {
      const computedStyle = window.getComputedStyle(canvas);
      diagnosticResults.canvasVisible = computedStyle.display !== 'none' &&
                                       computedStyle.visibility !== 'hidden' &&
                                       computedStyle.opacity !== '0';

      console.log(`ℹ️ DIAGNOSTIC: Canvas exists: ${diagnosticResults.canvasExists}`);
      console.log(`ℹ️ DIAGNOSTIC: Canvas visible: ${diagnosticResults.canvasVisible}`);
      console.log(`ℹ️ DIAGNOSTIC: Canvas display: ${computedStyle.display}`);
      console.log(`ℹ️ DIAGNOSTIC: Canvas visibility: ${computedStyle.visibility}`);
      console.log(`ℹ️ DIAGNOSTIC: Canvas opacity: ${computedStyle.opacity}`);
      console.log(`ℹ️ DIAGNOSTIC: Canvas width: ${computedStyle.width}`);
      console.log(`ℹ️ DIAGNOSTIC: Canvas height: ${computedStyle.height}`);
    } else {
      console.log('❌ DIAGNOSTIC: Temperature chart canvas not found');
      diagnosticResults.errors.push('Canvas element not found');
    }

    // Check for chart initialization
    console.log('ℹ️ DIAGNOSTIC: Checking chart initialization...');

    // Check all possible chart variable names
    const possibleChartVars = [
      'temperatureChart',
      'temperatureHistoryChart',
      'historyTemperatureChart',
      'chart'
    ];

    for (const varName of possibleChartVars) {
      if (window[varName]) {
        console.log(`✅ DIAGNOSTIC: Found global variable: ${varName}`);
        diagnosticResults.globalVariables.push(varName);

        if (window[varName] instanceof Chart ||
            (window[varName].chart && window[varName].chart instanceof Chart)) {
          diagnosticResults.chartInitialized = true;
          console.log(`✅ DIAGNOSTIC: Chart initialized via ${varName}`);

          // Check chart data
          const chartInstance = window[varName] instanceof Chart ?
                               window[varName] :
                               window[varName].chart;

          if (chartInstance && chartInstance.data) {
            diagnosticResults.chartData = chartInstance.data;
            console.log(`✅ DIAGNOSTIC: Chart has data: ${JSON.stringify(chartInstance.data).substring(0, 100)}...`);
          } else {
            console.log('❌ DIAGNOSTIC: Chart instance exists but has no data');
            diagnosticResults.errors.push('Chart initialized but no data found');
          }
        }
      }
    }

    if (!diagnosticResults.chartInitialized) {
      console.log('❌ DIAGNOSTIC: No chart instance found in global scope');
      diagnosticResults.errors.push('No chart instance found');
    }

    // Check for any JavaScript errors
    if (window.onerror) {
      const originalOnError = window.onerror;
      window.onerror = function(message, source, lineno, colno, error) {
        console.log(`❌ DIAGNOSTIC: JavaScript error: ${message} at ${source}:${lineno}:${colno}`);
        diagnosticResults.errors.push(`JS Error: ${message}`);
        return originalOnError(message, source, lineno, colno, error);
      };
    }

    // Check API calls
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
      if (url.includes('/history/temperature')) {
        console.log(`✅ DIAGNOSTIC: API call detected: ${url}`);
        diagnosticResults.apiCalled = true;

        // Monitor the response
        return originalFetch(url, options)
          .then(response => {
            console.log(`ℹ️ DIAGNOSTIC: API response status: ${response.status}`);
            // Clone the response so we can still use it in the application
            const responseClone = response.clone();
            responseClone.json().then(data => {
              console.log(`ℹ️ DIAGNOSTIC: API response data: ${JSON.stringify(data).substring(0, 100)}...`);
            }).catch(err => {
              console.log(`❌ DIAGNOSTIC: Error parsing API response: ${err}`);
            });
            return response;
          })
          .catch(error => {
            console.log(`❌ DIAGNOSTIC: API error: ${error}`);
            diagnosticResults.errors.push(`API Error: ${error}`);
            throw error;
          });
      }
      return originalFetch(url, options);
    };

    // Create diagnostic display
    setTimeout(function() {
      createDiagnosticDisplay(diagnosticResults);
    }, 2000);
  }

  /**
   * Extract device ID from URL or page elements
   */
  function getDeviceId() {
    // Try to get from URL
    const urlPath = window.location.pathname;
    const pathSegments = urlPath.split('/');
    const deviceId = pathSegments[pathSegments.length - 1];

    // Validate it looks like a device ID
    if (deviceId && deviceId.startsWith('wh-')) {
      return deviceId;
    }

    // Try alternate ways to get device ID
    const deviceIdEl = document.getElementById('device-id');
    if (deviceIdEl && deviceIdEl.dataset.deviceId) {
      return deviceIdEl.dataset.deviceId;
    }

    return null;
  }

  /**
   * Create visual diagnostic display in the UI
   */
  function createDiagnosticDisplay(results) {
    const historyContent = document.getElementById('history-content');
    if (!historyContent) return;

    // Check if diagnostic element already exists
    let diagnosticEl = document.getElementById('temperature-chart-diagnostics');
    if (!diagnosticEl) {
      diagnosticEl = document.createElement('div');
      diagnosticEl.id = 'temperature-chart-diagnostics';
      diagnosticEl.className = 'diagnostic-panel';
      diagnosticEl.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: #fff;
        border-radius: 4px;
        padding: 10px;
        font-family: monospace;
        font-size: 12px;
        z-index: 9999;
        max-width: 400px;
        max-height: 300px;
        overflow: auto;
      `;

      // Add close button
      const closeBtn = document.createElement('button');
      closeBtn.textContent = 'Close';
      closeBtn.style.cssText = `
        position: absolute;
        top: 5px;
        right: 5px;
        background: #ff5252;
        color: white;
        border: none;
        border-radius: 3px;
        padding: 2px 5px;
        font-size: 10px;
        cursor: pointer;
      `;
      closeBtn.addEventListener('click', function() {
        diagnosticEl.style.display = 'none';
      });

      diagnosticEl.appendChild(closeBtn);
      historyContent.appendChild(diagnosticEl);
    }

    // Update content
    const statusColor = results.errors.length > 0 ? 'red' : 'green';
    const statusIcon = results.errors.length > 0 ? '❌' : '✅';

    diagnosticEl.innerHTML = `
      <h3 style="margin: 0 0 10px 0; color: ${statusColor};">${statusIcon} Temperature Chart Diagnostics</h3>
      <div style="margin-bottom: 5px;"><strong>Canvas Exists:</strong> ${results.canvasExists ? '✅ Yes' : '❌ No'}</div>
      <div style="margin-bottom: 5px;"><strong>Canvas Visible:</strong> ${results.canvasVisible ? '✅ Yes' : '❌ No'}</div>
      <div style="margin-bottom: 5px;"><strong>Chart Initialized:</strong> ${results.chartInitialized ? '✅ Yes' : '❌ No'}</div>
      <div style="margin-bottom: 5px;"><strong>API Called:</strong> ${results.apiCalled ? '✅ Yes' : '❌ No'}</div>
      <div style="margin-bottom: 5px;"><strong>Global Variables:</strong> ${results.globalVariables.join(', ') || 'None'}</div>
      ${results.errors.length > 0 ? `
        <div style="margin-top: 10px; color: red;">
          <strong>Errors:</strong>
          <ul style="margin: 5px 0; padding-left: 20px;">
            ${results.errors.map(err => `<li>${err}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      <button id="fix-temperature-chart" style="margin-top: 10px; background: #4CAF50; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Attempt Fix</button>
    `;

    // Add event listener to fix button
    const fixBtn = diagnosticEl.querySelector('#fix-temperature-chart');
    if (fixBtn) {
      fixBtn.addEventListener('click', emergencyChartFix);
    }
  }

  /**
   * Emergency fix for temperature chart
   */
  function emergencyChartFix() {
    console.log('🔧 DIAGNOSTIC: Attempting emergency chart fix...');

    const canvas = document.getElementById('temperature-chart');
    if (!canvas) {
      console.error('Cannot fix: canvas element not found');
      return;
    }

    // 1. Reset canvas display properties
    canvas.style.display = 'block';
    canvas.style.visibility = 'visible';
    canvas.style.opacity = '1';

    // 2. Reset canvas dimensions
    const container = canvas.parentElement;
    if (container) {
      canvas.width = container.clientWidth;
      canvas.height = container.clientHeight;
    }

    // 3. Force create new chart
    const deviceId = getDeviceId();
    if (!deviceId) {
      console.error('Cannot fix: device ID not found');
      return;
    }

    // 4. Load data and create chart
    const days = document.querySelector('.day-selector.active')?.getAttribute('data-days') || '7';
    const apiUrl = `/api/manufacturer/water-heaters/${deviceId}/history/temperature?days=${days}`;

    fetch(apiUrl)
      .then(response => response.json())
      .then(data => {
        console.log('🔧 DIAGNOSTIC: Got data, creating emergency chart');

        // Clear any existing chart
        if (window.temperatureHistoryChart instanceof Chart) {
          window.temperatureHistoryChart.destroy();
        }

        // Create new chart
        let chartData = data;
        if (Array.isArray(data)) {
          chartData = {
            labels: data.map(d => typeof d.timestamp === 'string' ? d.timestamp.split('T')[0] : d.timestamp),
            datasets: [{
              label: 'Temperature (°F)',
              data: data.map(d => d.temperature),
              borderColor: 'rgb(255, 99, 132)',
              backgroundColor: 'rgba(255, 99, 132, 0.2)',
            }]
          };
        }

        window.temperatureHistoryChart = new Chart(canvas, {
          type: 'line',
          data: chartData,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: {
                display: true,
                text: 'Temperature History (Emergency Fix)'
              }
            }
          }
        });

        console.log('🔧 DIAGNOSTIC: Emergency chart created successfully');
      })
      .catch(error => {
        console.error('Failed to create emergency chart:', error);
      });
  }
})();
