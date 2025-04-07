/**
 * Tab Diagnostics and Fixes
 * 
 * This script diagnoses and fixes tab visibility issues and status duplication problems
 * in the water heater dashboard.
 */

(function() {
  console.log('🚀 Tab Diagnostics loaded - analyzing issues...');
  
  // Wait for page to fully load
  window.addEventListener('DOMContentLoaded', function() {
    setTimeout(diagnoseAndFix, 500);
  });
  
  // If DOM is already loaded, run immediately
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(diagnoseAndFix, 500);
  }
  
  function diagnoseAndFix() {
    console.log('🔍 Starting tab diagnostics and fixes...');
    
    try {
      // Fix tab content styles and visibility
      fixTabContentStyles();
      
      // Fix operations dashboard duplication issue
      fixOperationsDashboardDuplication();
      
      // Fix history charts - ensure they're properly initialized
      fixHistoryCharts();
      
      // Improve TabManager behavior
      enhanceTabManager();
      
      console.log('✅ Tab diagnostics and fixes applied successfully!');
    } catch (error) {
      console.error('❌ Error in tab diagnostics:', error);
    }
  }
  
  // Fix tab content styles to prevent tab stacking and visibility issues
  function fixTabContentStyles() {
    console.log('🔧 Fixing tab content styles...');
    
    // Select all tab content divs
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabContents.forEach(tab => {
      // Remove any inline styles that might be causing problems
      tab.removeAttribute('style');
      
      // Remove extreme isolation classes
      tab.classList.remove('tab-content-hidden');
      
      // Make sure inactive tabs are properly hidden
      if (!tab.classList.contains('active')) {
        tab.style.display = 'none';
        tab.style.visibility = 'hidden';
        tab.style.opacity = '0';
      } else {
        tab.style.display = 'block';
        tab.style.visibility = 'visible';
        tab.style.opacity = '1';
      }
    });
    
    console.log(`🔧 Fixed styles for ${tabContents.length} tab content elements`);
  }
  
  // Fix operations dashboard duplication issue
  function fixOperationsDashboardDuplication() {
    console.log('🔧 Fixing operations dashboard duplication...');
    
    // Verify we have the operations content
    const operationsContent = document.getElementById('operations-content');
    if (!operationsContent) {
      console.warn('⚠️ Operations content not found - skipping fix');
      return;
    }
    
    // Check for duplicate status cards
    const statusItems = operationsContent.querySelectorAll('.status-item');
    const statusLabels = new Map();
    const duplicates = [];
    
    // Find duplicates
    statusItems.forEach(item => {
      const labelEl = item.querySelector('.status-label');
      if (!labelEl) return;
      
      const label = labelEl.textContent.trim();
      if (statusLabels.has(label)) {
        duplicates.push(item);
      } else {
        statusLabels.set(label, item);
      }
    });
    
    // Remove duplicates
    duplicates.forEach(item => {
      console.log(`🔧 Removing duplicate status item: ${item.querySelector('.status-label')?.textContent.trim()}`);
      item.remove();
    });
    
    console.log(`🔧 Removed ${duplicates.length} duplicate status items`);
    
    // Replace dashboard building with safer implementation
    if (window.WaterHeaterOperationsDashboard && window.WaterHeaterOperationsDashboard.prototype) {
      const originalBuild = window.WaterHeaterOperationsDashboard.prototype.buildDashboardUI;
      
      if (originalBuild) {
        console.log('🔧 Patching WaterHeaterOperationsDashboard.buildDashboardUI to prevent duplication');
        
        window.WaterHeaterOperationsDashboard.prototype.buildDashboardUI = function() {
          // Only build UI if it doesn't already exist
          const existingDashboard = this.container.querySelector('#operations-dashboard');
          if (existingDashboard) {
            console.log('🔧 Dashboard UI already exists, skipping rebuild');
            return;
          }
          
          // Call original implementation
          return originalBuild.apply(this, arguments);
        };
      }
    }
  }
  
  // Fix history charts - ensure they're properly initialized
  function fixHistoryCharts() {
    console.log('🔧 Fixing history charts...');
    
    // Verify we have the history content
    const historyContent = document.getElementById('history-content');
    if (!historyContent) {
      console.warn('⚠️ History content not found - skipping fix');
      return;
    }
    
    // Check if temperature chart exists
    const temperatureChart = document.getElementById('temperature-chart');
    if (!temperatureChart) {
      console.log('🔧 Temperature chart not found, creating it');
      
      // Find chart container
      const chartContainer = historyContent.querySelector('.chart-container');
      if (chartContainer) {
        // Create a new canvas element
        const canvas = document.createElement('canvas');
        canvas.id = 'temperature-chart';
        chartContainer.appendChild(canvas);
        console.log('🔧 Created temperature chart element');
      }
    }
    
    // Fix WaterHeaterHistoryDashboard to properly handle tab transitions
    if (window.WaterHeaterHistoryDashboard && window.WaterHeaterHistoryDashboard.prototype) {
      const originalReload = window.WaterHeaterHistoryDashboard.prototype.reload;
      
      if (originalReload) {
        console.log('🔧 Patching WaterHeaterHistoryDashboard.reload to handle tab transitions properly');
        
        window.WaterHeaterHistoryDashboard.prototype.reload = function() {
          // Only reload data if this tab is active
          if (window.tabManager && window.tabManager.getActiveTabId() === 'history') {
            console.log('🔧 History tab is active, safely reloading data');
            
            // Ensure chart canvases exist
            const tempChart = document.getElementById('temperature-chart');
            const energyChart = document.getElementById('energy-usage-chart');
            const pressureChart = document.getElementById('pressure-flow-chart');
            
            // Reinitialize charts if needed
            const reinitializeCharts = !this.temperatureChart || 
                                      !this.energyUsageChart || 
                                      !this.pressureFlowChart;
            
            if (reinitializeCharts) {
              console.log('🔧 Reinitializing charts during history tab reload');
              this.initializeCharts();
            }
            
            // Load fresh data
            this.loadHistoryData().catch(err => {
              console.error('🔧 Error loading history data:', err);
            });
          } else {
            console.log('🔧 History tab not active, skipping reload');
          }
        };
      }
    }
  }
  
  // Enhance TabManager to prevent visibility issues between tabs
  function enhanceTabManager() {
    console.log('🔧 Enhancing TabManager...');
    
    if (!window.tabManager) {
      console.warn('⚠️ TabManager not found - skipping enhancement');
      return;
    }
    
    // Replace showTab method with improved version
    const originalShowTab = window.tabManager.showTab;
    
    if (originalShowTab) {
      console.log('🔧 Patching TabManager.showTab to improve tab switching');
      
      window.tabManager.showTab = function(tabId) {
        console.log(`🔧 Enhanced tab switching to ${tabId}`);
        
        try {
          // Get all tab contents and buttons
          const allTabContents = document.querySelectorAll('.tab-content');
          const allTabButtons = document.querySelectorAll('.tab-btn');
          
          // First, hide all tabs to prevent stacking
          allTabContents.forEach(content => {
            // Remove all inline styles
            content.removeAttribute('style');
            
            // Ensure proper display
            content.style.display = 'none';
            content.style.visibility = 'hidden';
            content.style.opacity = '0';
            content.classList.remove('active');
          });
          
          // Reset all buttons
          allTabButtons.forEach(btn => {
            btn.classList.remove('active');
          });
          
          // Show only the selected tab
          const selectedContent = document.getElementById(`${tabId}-content`);
          if (selectedContent) {
            selectedContent.style.display = 'block';
            selectedContent.style.visibility = 'visible';
            selectedContent.style.opacity = '1';
            selectedContent.classList.add('active');
          }
          
          // Activate the selected button
          const selectedButton = document.getElementById(`${tabId}-tab-btn`);
          if (selectedButton) {
            selectedButton.classList.add('active');
          }
          
          // Update active tab ID
          this.activeTabId = tabId;
          
          // Update URL hash
          window.location.hash = tabId;
          
          // Call component reload method
          this.notifyTabChange(tabId);
          
          return true;
        } catch (error) {
          console.error('🔧 Error in enhanced tab switching:', error);
          
          // Fall back to original implementation
          return originalShowTab.call(this, tabId);
        }
      };
    }
  }
})();
