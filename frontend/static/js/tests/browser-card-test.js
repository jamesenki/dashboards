/**
 * Browser-based Card Navigation Test
 * This test runs directly in the browser and verifies actual click navigation
 */

(function() {
  console.clear();
  console.log('🧪 STARTING BROWSER-BASED CARD NAVIGATION TEST');
  console.log('This test runs in the browser and checks actual click navigation');

  // Collect test results
  const results = {
    total: 0,
    passed: 0,
    failed: 0,
    details: []
  };

  // Get all cards
  const allCards = document.querySelectorAll('.heater-card');
  const aquathermCards = document.querySelectorAll('.heater-card.aquatherm-heater');

  console.log(`Found ${allCards.length} total cards, ${aquathermCards.length} AquaTherm cards`);

  // Track which cards should be AquaTherm
  const nonAquathermCards = [];
  allCards.forEach(card => {
    const id = card.getAttribute('data-id') || card.id;
    const model = card.querySelector('.model-name')?.textContent || '';
    const manufacturer = card.querySelector('.manufacturer')?.textContent || '';
    const name = card.querySelector('.card-title')?.textContent || '';

    const textToCheck = `${id} ${model} ${manufacturer} ${name}`.toLowerCase();
    const shouldBeAquaTherm = textToCheck.includes('aqua') ||
                             textToCheck.includes('therm') ||
                             id.startsWith('aqua');

    if (shouldBeAquaTherm && !card.classList.contains('aquatherm-heater')) {
      nonAquathermCards.push({
        id: id,
        text: textToCheck
      });
    }
  });

  if (nonAquathermCards.length > 0) {
    console.error(`❌ Found ${nonAquathermCards.length} cards that should be AquaTherm but aren't identified as such`);
    nonAquathermCards.forEach(card => {
      console.error(`  - ${card.id}: ${card.text.substring(0, 50)}...`);
    });
  }

  // Test click navigation for all cards
  console.log('\n🧪 TESTING CLICK NAVIGATION FOR ALL CARDS');

  // Create a visual overlay to show test results
  const testDisplay = document.createElement('div');
  testDisplay.style.position = 'fixed';
  testDisplay.style.top = '10px';
  testDisplay.style.right = '10px';
  testDisplay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
  testDisplay.style.color = 'white';
  testDisplay.style.padding = '10px';
  testDisplay.style.borderRadius = '5px';
  testDisplay.style.zIndex = '10000';
  testDisplay.style.maxWidth = '300px';
  testDisplay.style.maxHeight = '80vh';
  testDisplay.style.overflow = 'auto';
  testDisplay.innerHTML = '<h3>Testing Card Navigation...</h3>';
  document.body.appendChild(testDisplay);

  // Function to test card click
  function testCardClick(card, index) {
    return new Promise(resolve => {
      const id = card.getAttribute('data-id') || card.id;
      const isAquatherm = card.classList.contains('aquatherm-heater');
      const expectedUrl = `/water-heaters/${id}`;

      const resultItem = document.createElement('div');
      resultItem.style.borderBottom = '1px solid #555';
      resultItem.style.padding = '5px 0';
      resultItem.innerHTML = `<div>Testing card ${index+1}/${allCards.length}: ${id}</div>`;
      testDisplay.appendChild(resultItem);

      // Register a click listener to detect navigation
      let navigated = false;
      const navListener = (e) => {
        if (e.detail && e.detail.url === expectedUrl) {
          navigated = true;
          results.passed++;
          resultItem.innerHTML += `<div style="color: #4caf50;">✅ Navigation to ${expectedUrl} confirmed</div>`;
          document.removeEventListener('card-navigation', navListener);
          resolve(true);
        }
      };

      document.addEventListener('card-navigation', navListener);

      // Check if onclick attribute exists and contains the right URL
      const onclickAttr = card.getAttribute('onclick') || '';
      const hasCorrectOnclick = onclickAttr.includes(expectedUrl);

      if (!hasCorrectOnclick) {
        results.failed++;
        resultItem.innerHTML += `<div style="color: #f44336;">❌ No valid onclick attribute</div>`;
        document.removeEventListener('card-navigation', navListener);
        resolve(false);
        return;
      }

      // Simulate click with fallback for timeout
      try {
        // Create and dispatch click event
        const clickEvent = new MouseEvent('click', {
          bubbles: true,
          cancelable: true
        });

        card.dispatchEvent(clickEvent);

        // Set timeout to check if navigation happened
        setTimeout(() => {
          if (!navigated) {
            results.failed++;
            resultItem.innerHTML += `<div style="color: #f44336;">❌ Click did not trigger navigation</div>`;
            document.removeEventListener('card-navigation', navListener);
            resolve(false);
          }
        }, 300);
      } catch (error) {
        results.failed++;
        resultItem.innerHTML += `<div style="color: #f44336;">❌ Error: ${error.message}</div>`;
        document.removeEventListener('card-navigation', navListener);
        resolve(false);
      }
    });
  }

  // Run tests sequentially
  async function runAllClickTests() {
    for (let i = 0; i < allCards.length; i++) {
      results.total++;
      await testCardClick(allCards[i], i);
    }

    // Show final results
    const summaryItem = document.createElement('div');
    summaryItem.style.marginTop = '15px';
    summaryItem.style.fontWeight = 'bold';
    summaryItem.style.borderTop = '2px solid white';
    summaryItem.style.paddingTop = '10px';

    if (results.failed > 0) {
      summaryItem.innerHTML = `❌ FAILED: ${results.failed} of ${results.total} cards have navigation issues`;
      summaryItem.style.color = '#f44336';
    } else {
      summaryItem.innerHTML = `✅ PASSED: All ${results.total} cards navigate correctly`;
      summaryItem.style.color = '#4caf50';
    }

    testDisplay.appendChild(summaryItem);
  }

  // Start the tests with a slight delay to ensure page is ready
  setTimeout(runAllClickTests, 500);
})();
