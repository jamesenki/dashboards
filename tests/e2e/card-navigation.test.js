/**
 * Card Navigation End-to-End Test for AquaTherm Cards
 *
 * This is a standalone Puppeteer script to test card navigation.
 * It properly tests actual browser navigation (which can't be tested in-browser).
 * No additional testing frameworks are needed - just runs with Node.js.
 */

const puppeteer = require('puppeteer');

// Test configuration
const config = {
  baseUrl: 'http://localhost:8006',
  navigationTimeout: 5000
};

/**
 * Helper to assert a condition and throw error if it fails
 */
function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

/**
 * Main test function
 */
async function runCardNavigationTests() {
  console.log('\n===== CARD NAVIGATION TEST =====\n');

  // Launch browser in non-headless mode so you can see what's happening
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Log browser console messages
    page.on('console', message => {
      console.log(`Browser console [${message.type()}]: ${message.text()}`);
    });

    // Set navigation timeout
    page.setDefaultNavigationTimeout(config.navigationTimeout);

    // Start at the water heaters page
    console.log('Navigating to water heaters page...');
    await page.goto(`${config.baseUrl}/water-heaters`, { waitUntil: 'networkidle0' });

    // Get all cards
    const cards = await page.$$('.heater-card');
    console.log(`Found ${cards.length} total cards on page`);
    assert(cards.length > 0, 'No cards found on page');

    // Test results tracking
    let successCount = 0;
    let failureCount = 0;
    const failures = [];

    // Test each card
    for (let i = 0; i < cards.length; i++) {
      // For each card, reload the page to get fresh cards
      if (i > 0) {
        await page.goto(`${config.baseUrl}/water-heaters`, { waitUntil: 'networkidle0' });
      }

      // Get fresh cards after page reload
      const freshCards = await page.$$('.heater-card');
      const card = freshCards[i];

      // Get card info
      const cardInfo = await page.evaluate(el => {
        return {
          id: el.getAttribute('data-id') || el.id,
          isAquaTherm: el.classList.contains('aquatherm-heater'),
          hasOnclick: el.hasAttribute('onclick'),
          onclickContent: el.getAttribute('onclick') || ''
        };
      }, card);

      console.log(`\nTesting card ${i+1}/${cards.length}: ${cardInfo.id} (${cardInfo.isAquaTherm ? 'AquaTherm' : 'Standard'})`);

      // CHECK 1: Has onclick attribute
      if (!cardInfo.hasOnclick) {
        console.log('  ❌ Card has no onclick attribute');
        failureCount++;
        failures.push({
          id: cardInfo.id,
          isAquaTherm: cardInfo.isAquaTherm,
          reason: 'No onclick attribute'
        });
        continue;
      }

      // CHECK 2: Correct URL in onclick
      if (!cardInfo.onclickContent.includes(`/water-heaters/${cardInfo.id}`)) {
        console.log(`  ❌ Card onclick doesn't contain correct URL`);
        console.log(`  Found: ${cardInfo.onclickContent.substring(0, 100)}...`);
        failureCount++;
        failures.push({
          id: cardInfo.id,
          isAquaTherm: cardInfo.isAquaTherm,
          reason: 'Incorrect URL in onclick attribute'
        });
        continue;
      }

      console.log(`  ✓ Card has valid onclick with URL: /water-heaters/${cardInfo.id}`);

      // CHECK 3: Actual click navigation
      try {
        console.log('  Clicking card...');

        // Get current URL
        const beforeUrl = page.url();

        // Click card and wait for navigation
        // Use Promise.all to wait for both navigation and click
        await Promise.all([
          page.waitForNavigation({ timeout: config.navigationTimeout }),
          card.click()
        ]);

        // Get new URL after navigation
        const afterUrl = page.url();
        const expectedUrlPattern = `/water-heaters/${cardInfo.id}`;

        if (afterUrl.includes(expectedUrlPattern)) {
          console.log(`  ✅ Successfully navigated to ${afterUrl}`);
          successCount++;
        } else {
          console.log(`  ❌ Navigation failed - went to ${afterUrl} instead of ${expectedUrlPattern}`);
          failureCount++;
          failures.push({
            id: cardInfo.id,
            isAquaTherm: cardInfo.isAquaTherm,
            reason: `Wrong navigation: went to ${afterUrl}`
          });
        }
      } catch (error) {
        console.log(`  ❌ Navigation error: ${error.message}`);
        failureCount++;
        failures.push({
          id: cardInfo.id,
          isAquaTherm: cardInfo.isAquaTherm,
          reason: error.message
        });
      }
    }

    // Show overall test results
    console.log('\n===== CARD NAVIGATION TEST RESULTS =====');

    if (failureCount > 0) {
      console.log(`❌ FAILED: ${failureCount} of ${cards.length} cards have navigation issues`);

      // Group failures by AquaTherm vs Standard
      const aquaThermFailures = failures.filter(f => f.isAquaTherm);
      const standardFailures = failures.filter(f => !f.isAquaTherm);

      console.log(`\n• ${aquaThermFailures.length} AquaTherm cards failed`);
      console.log(`• ${standardFailures.length} Standard cards failed`);

      console.log('\nAll Failures:');
      failures.forEach(failure => {
        console.log(`- Card ${failure.id} (${failure.isAquaTherm ? 'AquaTherm' : 'Standard'}): ${failure.reason}`);
      });
    } else {
      console.log(`✅ PASSED: All ${cards.length} cards navigate correctly when clicked`);
    }
  } catch (error) {
    console.error('\n❌ TEST EXECUTION FAILED:', error);
  } finally {
    // Always close the browser
    await browser.close();
  }
}

// Run the tests if executed directly
if (require.main === module) {
  runCardNavigationTests().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}
