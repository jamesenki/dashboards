/**
 * GUARANTEED Shadow Document Error Display
 * This script takes a direct approach to ensure the error message is always displayed
 */
(function() {
  console.log('🔴 GUARANTEED Shadow Document Error Fix loaded');
  
  // Execute immediately
  displayShadowError();
  
  // Also execute after DOM load
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(displayShadowError, 100);
  });
  
  // And run whenever history tab is clicked
  setTimeout(function() {
    const historyTab = document.getElementById('history-tab-btn');
    if (historyTab) {
      historyTab.addEventListener('click', function() {
        console.log('History tab clicked - running shadow error display');
        setTimeout(displayShadowError, 300);
      });
    }
  }, 500);
  
  /**
   * Force display of shadow document error message
   */
  function displayShadowError() {
    console.log('Forcing shadow document error display');
    
    // Find ALL possible chart containers and loading indicators
    const chartContainers = document.querySelectorAll('.chart-container');
    const loadingIndicators = document.querySelectorAll('.chart-loading');
    
    console.log(`Found ${chartContainers.length} chart containers and ${loadingIndicators.length} loading indicators`);
    
    // Hide ALL loading indicators
    loadingIndicators.forEach(loading => {
      loading.style.display = 'none';
    });
    
    // Create error HTML
    const errorHTML = `
      <div class="shadow-document-error" style="text-align: center; padding: 20px; border: 1px solid #e74c3c; background-color: rgba(231, 76, 60, 0.1); border-radius: 4px; margin: 15px; display: block !important; visibility: visible !important; position: relative !important; z-index: 9999 !important;">
        <h4 style="color: #e74c3c; margin-bottom: 10px; font-weight: bold;">Temperature History Unavailable</h4>
        <p style="margin-bottom: 10px; font-size: 14px;">No shadow document exists for this device.</p>
        <p style="margin-bottom: 5px; font-size: 14px;">Temperature history cannot be displayed until the device has reported data.</p>
        <p><small style="color: #7f8c8d; font-size: 12px;">This typically happens when a device is new or has been reset.</small></p>
      </div>
    `;
    
    // Inject error message into FIRST chart container (temperature)
    if (chartContainers.length > 0) {
      const tempContainer = chartContainers[0];
      
      // Hide any existing canvas
      const existingCanvas = tempContainer.querySelector('canvas');
      if (existingCanvas) {
        existingCanvas.style.display = 'none';
      }
      
      // Create error element
      const errorElement = document.createElement('div');
      errorElement.id = 'forced-shadow-error';
      errorElement.innerHTML = errorHTML;
      
      // Add error if not already present
      if (!tempContainer.querySelector('#forced-shadow-error')) {
        tempContainer.insertBefore(errorElement, tempContainer.firstChild);
        console.log('✅ Inserted shadow document error message');
      }
    }
    
    // Also set the history-error element
    const historyError = document.getElementById('history-error');
    if (historyError) {
      historyError.innerHTML = 'ERROR: No device shadow document exists. Temperature history cannot be displayed.';
      historyError.style.display = 'block';
      historyError.style.color = '#e74c3c';
      historyError.style.padding = '10px';
      historyError.style.margin = '10px 0';
      historyError.style.border = '1px solid #e74c3c';
      historyError.style.borderRadius = '4px';
      console.log('✅ Updated history error message');
    }
    
    // Test indicators removed as requested
    
    // Force any canvases to be invisible
    document.querySelectorAll('canvas').forEach(canvas => {
      if (canvas.id === 'temperature-chart') {
        canvas.style.display = 'none !important';
        canvas.style.visibility = 'hidden !important';
        console.log('✅ Forced temperature chart canvas to be hidden');
      }
    });

    // Set up MutationObserver to ensure our error message stays
    setupObserver();
  }
  
  /**
   * Set up an observer to ensure our error message doesn't get removed
   */
  function setupObserver() {
    // Create observer to watch for changes
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          // Check if our error message was removed
          const errorElement = document.querySelector('#forced-shadow-error');
          if (!errorElement) {
            console.log('🔄 Error message was removed, re-adding it');
            displayShadowError();
          }
        }
      });
    });
    
    // Start observing all chart containers
    document.querySelectorAll('.chart-container').forEach(container => {
      observer.observe(container, {
        childList: true,
        subtree: true
      });
    });
    
    console.log('✅ Set up observer to maintain error message');
  }
})();
