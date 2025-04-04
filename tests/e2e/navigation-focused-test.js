/**
 * Focused Card Navigation Test - Specifically for AquaTherm Tankless-001 Card
 *
 * This test identifies the specific navigation issue by focusing on a single card
 * that's known to have problems. It follows TDD principles by defining how navigation
 * should work and testing against that spec.
 */

const puppeteer = require('puppeteer');

// Target card that has known navigation issues
const PROBLEM_CARD_ID = 'aqua-wh-tankless-001';

async function runFocusedNavigationTest() {
  console.log('====== FOCUSED CARD NAVIGATION TEST ======\n');
  console.log(`Testing navigation specifically for card ID: ${PROBLEM_CARD_ID}\n`);

  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Only log errors, not all console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Browser error: ${msg.text()}`);
      }
    });

    // Step 1: Navigate to the water heaters page
    console.log('1. Navigating to water heaters listing page...');
    await page.goto('http://localhost:8006/water-heaters', { waitUntil: 'networkidle0' });

    // Step 2: Find our specific problem card
    console.log(`2. Looking for card with ID: ${PROBLEM_CARD_ID}...`);
    const cardExists = await page.evaluate((cardId) => {
      const card = document.querySelector(`[data-id="${cardId}"]`);
      return !!card;
    }, PROBLEM_CARD_ID);

    if (!cardExists) {
      throw new Error(`Card with ID ${PROBLEM_CARD_ID} not found on page!`);
    }

    console.log('   Card found on page.');

    // Step 3: Check for onclick attribute
    const onclickCheck = await page.evaluate((cardId) => {
      const card = document.querySelector(`[data-id="${cardId}"]`);
      if (!card) return { exists: false };

      return {
        onclick: card.getAttribute('onclick') || '',
        hasOnclick: card.hasAttribute('onclick')
      };
    }, PROBLEM_CARD_ID);

    if (!onclickCheck.hasOnclick) {
      console.log('   ❌ Card has NO onclick attribute!');
      throw new Error('Card is missing onclick attribute');
    }

    console.log('   Card has onclick attribute.');
    console.log(`   Onclick content: ${onclickCheck.onclick.substring(0, 100)}...`);

    // Step 4: Try clicking the card with error catching
    console.log('\n3. Attempting to click the card...');

    try {
      // First try with standard click
      await Promise.all([
        page.waitForNavigation({ timeout: 5000 }).catch(e => {
          throw new Error(`Navigation failed: ${e.message}`);
        }),
        page.click(`[data-id="${PROBLEM_CARD_ID}"]`).catch(e => {
          throw new Error(`Click failed: ${e.message}`);
        })
      ]);

      // If we get here, navigation worked!
      const currentUrl = page.url();
      console.log(`   ✅ Navigation successful! Current URL: ${currentUrl}`);

      if (currentUrl.includes(`/water-heaters/${PROBLEM_CARD_ID}`)) {
        console.log('\n✅ TEST PASSED: Card successfully navigated to detail page');
      } else {
        console.log(`\n❌ TEST FAILED: Card navigated to wrong URL: ${currentUrl}`);
      }
    } catch (error) {
      console.log(`   ❌ Navigation error: ${error.message}`);

      // Step 5: Alternative approach - inject and execute click
      console.log('\n4. Trying alternative click approach...');

      try {
        // Get current URL before click
        const beforeUrl = page.url();

        // Inject a special click handler that captures errors
        const result = await page.evaluate((cardId) => {
          try {
            const card = document.querySelector(`[data-id="${cardId}"]`);
            if (!card) return { success: false, error: 'Card not found' };

            // Create and dispatch a click event
            const clickEvent = new MouseEvent('click', {
              bubbles: true,
              cancelable: true,
              view: window
            });

            // Track any errors during click
            let clickError = null;
            window.onerror = (message) => {
              clickError = message;
              return true; // Prevent default error handling
            };

            // Dispatch click
            card.dispatchEvent(clickEvent);

            return {
              success: true,
              error: clickError,
              onclickContent: card.getAttribute('onclick') || ''
            };
          } catch (e) {
            return { success: false, error: e.toString() };
          }
        }, PROBLEM_CARD_ID);

        if (result.error) {
          console.log(`   ❌ Error during click: ${result.error}`);

          // Look for TypeError in the onclick attribute
          if (result.onclickContent && result.onclickContent.includes('window.location')) {
            console.log('\n🔍 ROOT CAUSE IDENTIFIED:');
            console.log('   The card\'s onclick handler is directly setting window.location.href');
            console.log('   This causes the TypeError: Cannot redefine property: location/href');
            console.log('   This is a known browser security restriction that prevents redefinition');
          }
        }

        // Check if URL changed despite error
        const afterUrl = page.url();
        if (afterUrl !== beforeUrl) {
          console.log(`   Navigation occurred to: ${afterUrl}`);
        } else {
          console.log('   No navigation occurred after click');
        }

        console.log('\n❌ TEST FAILED: Card click does not reliably navigate to detail page');
      } catch (altError) {
        console.log(`   ❌ Alternative testing approach also failed: ${altError.message}`);
        console.log('\n❌ TEST FAILED: Unable to test card navigation due to errors');
      }
    }
  } catch (error) {
    console.error(`\n❌ TEST EXECUTION FAILED: ${error.message}`);
  } finally {
    // Always close the browser
    await browser.close();
  }
}

// Run the test
runFocusedNavigationTest().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
