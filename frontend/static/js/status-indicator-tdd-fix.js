/**
 * Status Indicator TDD Fix
 * Fixes the real-time connection status indicator following TDD principles
 * RED: Test the issue, confirm it's broken
 * GREEN: Implement minimal fix to make it work
 * REFACTOR: Improve the implementation without changing behavior
 */
(function() {
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🧪 TDD: Beginning Status Indicator test suite');
    
    // Define our test suite
    const tests = {
      // Test that the status indicator has no text content
      testStatusIndicatorHasNoText: function() {
        const indicator = document.getElementById('realtime-connection-status');
        if (!indicator) return { pass: false, error: 'Element not found' };
        
        // If the indicator has text content, the test fails
        if (indicator.textContent && indicator.textContent.trim() !== '') {
          return { 
            pass: false, 
            error: `Status indicator contains text: "${indicator.textContent}"` 
          };
        }
        
        return { pass: true };
      },
      
      // Test that connection type container displays the proper text
      testConnectionTypeText: function() {
        const container = document.getElementById('connection-type-container');
        if (!container) return { pass: false, error: 'Element not found' };
        
        // Get status from indicator class
        const indicator = document.getElementById('realtime-connection-status');
        if (!indicator) return { pass: false, error: 'Status indicator not found' };
        
        // Determine expected text
        let expectedText = 'Disconnected';
        if (indicator.classList.contains('connected')) {
          expectedText = 'Connected';
        } else if (indicator.classList.contains('connecting')) {
          expectedText = 'Connecting';
        }
        
        // If container text doesn't match expected status
        if (!container.textContent || !container.textContent.includes(expectedText)) {
          return {
            pass: false,
            error: `Connection type text "${container.textContent}" does not match expected "${expectedText}"`
          };
        }
        
        return { pass: true };
      }
    };
    
    // Run all tests
    function runTests() {
      console.log('🧪 Running Status Indicator tests...');
      let allPassed = true;
      
      // Run each test
      Object.keys(tests).forEach(testName => {
        const result = tests[testName]();
        
        if (result.pass) {
          console.log(`✅ ${testName}: PASS`);
        } else {
          console.error(`❌ ${testName}: FAIL - ${result.error}`);
          allPassed = false;
          
          // Implement fix for the failing test
          implementFixes();
        }
      });
      
      return allPassed;
    }
    
    // Implement the minimal fixes needed to make tests pass (GREEN phase)
    function implementFixes() {
      console.log('🔧 Implementing Status Indicator fixes...');
      
      // Fix 1: Clear any text from the status indicator
      const indicator = document.getElementById('realtime-connection-status');
      if (indicator) {
        // Remove text content
        indicator.textContent = '';
        
        // Ensure proper styling
        indicator.style.fontSize = '0';
        indicator.style.color = 'transparent';
        indicator.style.textIndent = '-9999px';
        indicator.style.overflow = 'hidden';
        
        console.log('✅ Fixed: Cleared text from status indicator');
      }
      
      // Fix 2: Ensure connection type has proper text
      const container = document.getElementById('connection-type-container');
      if (container && indicator) {
        // Determine proper status text
        let statusText = 'Disconnected';
        let textColor = '#e74c3c'; // Red
        
        if (indicator.classList.contains('connected')) {
          statusText = 'Connected';
          textColor = '#2ecc71'; // Green
        } else if (indicator.classList.contains('connecting')) {
          statusText = 'Connecting';
          textColor = '#f39c12'; // Yellow/orange
        }
        
        // Set proper text content
        container.innerHTML = `<span style="color: ${textColor}; font-weight: bold;">${statusText}</span>`;
        console.log(`✅ Fixed: Set connection type text to "${statusText}"`);
      }
      
      // Verify fixes worked
      setTimeout(runTests, 100);
    }
    
    // REFACTOR phase: Keep the UI consistent by monitoring for changes
    function setupMonitoring() {
      console.log('🔍 Setting up Status Indicator monitoring...');
      
      // Watch for changes to the status indicator
      const observer = new MutationObserver(function(mutations) {
        let needsCheck = false;
        
        mutations.forEach(function(mutation) {
          // Only check for changes to status indicator or its classes
          if (mutation.target.id === 'realtime-connection-status' || 
              (mutation.type === 'attributes' && mutation.attributeName === 'class')) {
            needsCheck = true;
          }
        });
        
        if (needsCheck) {
          runTests();
        }
      });
      
      // Start observing the document
      observer.observe(document.body, {
        attributes: true,
        childList: true,
        subtree: true
      });
      
      console.log('✅ Refactor: Set up monitoring to maintain status consistency');
      
      // Also run checks periodically
      setInterval(runTests, 2000);
    }
    
    // Run initial tests after a delay to ensure all elements are loaded
    setTimeout(function() {
      if (runTests()) {
        console.log('🎉 All Status Indicator tests PASSED!');
      } else {
        console.log('⚠️ Some Status Indicator tests FAILED, fixes were applied');
      }
      
      // Enter refactor phase
      setupMonitoring();
    }, 1000);
  });
})();
