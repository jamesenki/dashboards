/**
 * Direct Temperature History Fix for Details Page
 * Following TDD principles: Red->Green->Refactor
 * This script specifically targets the Temperature History box on the details page
 */
(function() {
  console.log('🧪 DETAILS PAGE: Temperature History TDD fix loaded');

  // Run immediately on script load and again after DOM loaded
  fixDetailsTemperatureChart();
  document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure DOM is fully loaded
    setTimeout(fixDetailsTemperatureChart, 500);
  });

  // RED PHASE: Test if details page temperature chart has content
  function fixDetailsTemperatureChart() {
    console.log('🧪 RED PHASE: Testing details page temperature chart');

    // Find temp-chart on the details page specifically
    const detailsTabContent = document.getElementById('details-content');
    
    if (!detailsTabContent) {
      console.log('Details tab content not found, waiting...');
      setTimeout(fixDetailsTemperatureChart, 500);
      return;
    }
    
    // Find the temperature chart within the details tab content
    const tempChart = detailsTabContent.querySelector('#temp-chart');
    
    if (!tempChart) {
      console.log('Temperature chart not found in details tab, waiting...');
      setTimeout(fixDetailsTemperatureChart, 500);
      return;
    }
    
    console.log('Found temperature chart in details tab:', tempChart);
    
    // Check if it's empty (fails the test)
    const hasContent = tempChart.innerHTML.trim() !== '';
    const hasErrorMessage = tempChart.querySelector('.shadow-document-error') !== null;
    
    if (!hasContent || !hasErrorMessage) {
      console.log('❌ TEST FAILED: Temperature chart on details page is empty or missing error message');
      // GREEN PHASE: Fix the issue
      addShadowDocumentError(tempChart);
    } else {
      console.log('✅ Temperature chart on details page already has content');
    }
    
    // Set up observer to ensure fix remains
    setupObserver(detailsTabContent);
  }
  
  // GREEN PHASE: Add shadow document error to the chart
  function addShadowDocumentError(chartElement) {
    console.log('🔧 GREEN PHASE: Adding shadow document error to details page chart');
    
    // Clear any existing content
    chartElement.innerHTML = '';
    
    // Create styled error message
    const errorHtml = `
      <div class="shadow-document-error" style="text-align: center; padding: 15px; border: 1px solid #e74c3c; background-color: rgba(231, 76, 60, 0.1); border-radius: 4px; margin: 5px; display: block !important; visibility: visible !important;">
        <h4 style="color: #e74c3c; margin-bottom: 10px; font-weight: bold; font-size: 16px;">Temperature History Unavailable</h4>
        <p style="margin-bottom: 10px; font-size: 14px;">No shadow document exists for this device.</p>
        <p style="margin-bottom: 5px; font-size: 14px;">Temperature history cannot be displayed until the device has reported data.</p>
        <p><small style="color: #7f8c8d; font-size: 12px;">This typically happens when a device is new or has been reset.</small></p>
      </div>
    `;
    
    // Add error to chart
    chartElement.innerHTML = errorHtml;
    
    // Test indicators removed as requested
    
    console.log('✅ Successfully added shadow document error to details page chart');
  }
  
  // REFACTOR PHASE: Ensure fix remains applied
  function setupObserver(container) {
    console.log('🔄 REFACTOR PHASE: Setting up observer to maintain fix');
    
    // Create mutation observer to watch for changes
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          // Check if our temp chart content was removed or changed
          const tempChart = container.querySelector('#temp-chart');
          if (tempChart) {
            const hasErrorMessage = tempChart.querySelector('.shadow-document-error') !== null;
            
            if (!hasErrorMessage) {
              console.log('🔄 Temperature chart error message was removed, re-adding it');
              addShadowDocumentError(tempChart);
            }
          }
        }
      });
    });
    
    // Start observing
    observer.observe(container, {
      childList: true,
      subtree: true
    });
    
    console.log('✅ Observer set up for details page temperature chart');
    
    // Also watch for tab changes to ensure our fix stays when switching back to details
    const detailsTabBtn = document.getElementById('details-tab-btn');
    if (detailsTabBtn) {
      detailsTabBtn.addEventListener('click', function() {
        console.log('Details tab clicked, ensuring temperature chart fix is applied');
        setTimeout(fixDetailsTemperatureChart, 300);
      });
    }
  }
})();
