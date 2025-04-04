/**
 * Card Navigation Test - Uses event-based approach to test navigation
 * Following TDD principles, this defines how navigation SHOULD work
 * and tests against that specification
 */

(function() {
  console.clear();
  console.log('🧪 CARD NAVIGATION TEST - EVENT-BASED APPROACH');

  class CardNavigationTest {
    constructor() {
      this.results = {
        total: 0,
        passed: 0,
        failed: 0,
        details: []
      };

      // Create and inject a test results panel
      this.createResultsPanel();
    }

    createResultsPanel() {
      const panel = document.createElement('div');
      panel.style.position = 'fixed';
      panel.style.top = '10px';
      panel.style.right = '10px';
      panel.style.width = '400px';
      panel.style.maxHeight = '80vh';
      panel.style.overflow = 'auto';
      panel.style.background = 'rgba(0, 0, 0, 0.8)';
      panel.style.color = 'white';
      panel.style.padding = '15px';
      panel.style.borderRadius = '8px';
      panel.style.fontFamily = 'Arial, sans-serif';
      panel.style.zIndex = '9999';
      panel.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.5)';
      panel.innerHTML = '<h2 style="margin-top:0;">Card Navigation Test</h2><div id="test-log"></div>';
      document.body.appendChild(panel);

      this.resultsPanel = panel;
      this.logElement = document.getElementById('test-log');
    }

    log(message, type = 'info') {
      console.log(message);

      const entry = document.createElement('div');
      entry.style.marginBottom = '5px';
      entry.style.borderLeft = type === 'error' ? '3px solid #f44336' :
                                type === 'success' ? '3px solid #4caf50' :
                                '3px solid #2196f3';
      entry.style.paddingLeft = '8px';
      entry.style.fontSize = '14px';

      entry.innerHTML = message;
      this.logElement.appendChild(entry);
    }

    /**
     * Run all tests
     */
    async runTests() {
      this.log('👁️ Finding all cards...');
      const allCards = document.querySelectorAll('.heater-card');
      this.log(`Found ${allCards.length} cards to test`);

      // First let's verify all cards have onclick handlers
      this.log('🔍 Checking all cards for onclick handlers...');
      for (const card of allCards) {
        this.results.total++;
        const id = card.getAttribute('data-id') || card.id;
        const isAquaTherm = card.classList.contains('aquatherm-heater');

        this.log(`Testing card ${id} (${isAquaTherm ? 'AquaTherm' : 'Standard'})...`);

        // Test for onclick attribute
        if (card.hasAttribute('onclick')) {
          const onclickAttr = card.getAttribute('onclick');
          const expectedUrlPattern = `/water-heaters/${id}`;

          if (onclickAttr.includes(expectedUrlPattern)) {
            this.log(`✅ Card has valid onclick with URL: ${expectedUrlPattern}`, 'success');
            this.results.passed++;
          } else {
            this.log(`❌ Card has onclick but with WRONG URL pattern: ${onclickAttr.substring(0, 50)}...`, 'error');
            this.results.failed++;
            this.results.details.push({
              id,
              isAquaTherm,
              reason: 'Incorrect URL in onclick',
              actual: onclickAttr.substring(0, 50)
            });
          }
        } else {
          this.log(`❌ Card has NO onclick attribute`, 'error');
          this.results.failed++;
          this.results.details.push({
            id,
            isAquaTherm,
            reason: 'Missing onclick attribute'
          });
        }
      }

      // Now test actual click navigation using event listeners
      this.log('');
      this.log('🖱️ Testing actual click navigation...');

      let eventsRegistered = false;

      // See if we have our custom nav event
      document.addEventListener('card-navigation', () => {
        eventsRegistered = true;
      }, { once: true });

      // Try clicking a card
      const firstCard = allCards[0];
      const testEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true
      });
      firstCard.dispatchEvent(testEvent);

      // Check if events are being used
      if (!eventsRegistered) {
        this.log('⚠️ Cards are not using the recommended event-based navigation!', 'error');
        this.log('This makes testing difficult. Recommend implementing card-navigation events.', 'error');
      }

      // Summary
      this.log('');
      this.log('📊 TEST SUMMARY');

      if (this.results.failed > 0) {
        this.log(`❌ FAILED: ${this.results.failed} of ${this.results.total} cards have navigation issues`, 'error');
      } else {
        this.log(`✅ PASSED: All ${this.results.total} cards have valid navigation onclick handlers`, 'success');
      }

      // Show details of failed cards
      if (this.results.failed > 0) {
        this.log('');
        this.log('📋 FAILURE DETAILS:');
        this.results.details.forEach(detail => {
          this.log(`- Card ${detail.id} (${detail.isAquaTherm ? 'AquaTherm' : 'Standard'}): ${detail.reason}`, 'error');
        });
      }

      // Add fix button if there are failures
      if (this.results.failed > 0) {
        const fixButton = document.createElement('button');
        fixButton.innerHTML = 'Apply Navigation Fix';
        fixButton.style.marginTop = '15px';
        fixButton.style.padding = '8px 15px';
        fixButton.style.background = '#2196f3';
        fixButton.style.color = 'white';
        fixButton.style.border = 'none';
        fixButton.style.borderRadius = '4px';
        fixButton.style.cursor = 'pointer';

        fixButton.addEventListener('click', () => this.applyFix());

        this.logElement.appendChild(fixButton);
      }
    }

    /**
     * Apply fix to all cards with navigation issues
     */
    applyFix() {
      this.log('');
      this.log('🛠️ Applying navigation fixes...');

      const allCards = document.querySelectorAll('.heater-card');
      let fixedCount = 0;

      for (const card of allCards) {
        const id = card.getAttribute('data-id') || card.id;
        const expectedUrl = `/water-heaters/${id}`;

        // Create a proper click handler that uses both events and direct navigation
        const newOnClickHandler = `onclick="(function(e) {
          e.preventDefault();
          if(!e.target.closest('button') && !e.target.closest('a') && e.target.tagName !== 'BUTTON' && e.target.tagName !== 'A') {
            console.log('Card clicked, navigating to: ${expectedUrl}');
            const detailLink = '${expectedUrl}';
            // First dispatch event for testability
            const navEvent = new CustomEvent('card-navigation', {detail: {url: detailLink}});
            document.dispatchEvent(navEvent);
            // Then do actual navigation
            setTimeout(function() { window.location.href = detailLink; }, 10);
            return false;
          }
        })(event)"`;

        card.setAttribute('onclick', newOnClickHandler);
        fixedCount++;
      }

      this.log(`✅ Fixed navigation on ${fixedCount} cards`, 'success');
      this.log('Please reload the page and run the test again to verify fixes.');
    }
  }

  // Run the test
  const test = new CardNavigationTest();
  test.runTests();
})();
