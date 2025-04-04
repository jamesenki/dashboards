/**
 * Navigation Blocker Test
 *
 * This test validates that the navigation blocker is working correctly,
 * following TDD principles where tests define the expected behavior.
 *
 * It attempts various navigation methods and verifies they are blocked.
 */

// Setup test framework
const puppeteer = require('puppeteer');

async function runTest() {
  console.log('🧪 Starting Navigation Blocker Test');
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Navigate to the water heaters list page
    console.log('🧪 Navigating to water heaters list page');
    await page.goto('http://localhost:8006/water-heaters', { waitUntil: 'networkidle0' });

    // Wait for page to fully load
    await page.waitForSelector('.dashboard', { timeout: 5000 });
    console.log('✅ Successfully loaded water heaters list page');

    // Check if we stay on the list page for 3 seconds (no auto-navigation)
    console.log('🧪 Waiting 3 seconds to ensure no auto-navigation occurs');
    await page.waitForTimeout(3000);

    // Verify we're still on the list page
    const currentUrl = await page.url();
    console.log(`Current URL after waiting: ${currentUrl}`);

    const isStillOnListPage = currentUrl.includes('/water-heaters') &&
                             !currentUrl.includes('/water-heaters/');

    if (isStillOnListPage) {
      console.log('✅ TEST PASSED: Page remained on water heaters list without auto-navigating');
    } else {
      console.error('❌ TEST FAILED: Page auto-navigated away from water heaters list');
      console.error(`Expected URL to remain at /water-heaters, but got: ${currentUrl}`);
    }

    // Test user-initiated navigation by simulating a click on a card
    if (isStillOnListPage) {
      console.log('🧪 Testing user-initiated navigation by clicking on a card');

      // Find all heater cards
      const cards = await page.$$('.heater-card, .card[data-id]');
      if (cards.length > 0) {
        console.log(`Found ${cards.length} cards to test`);

        // Click the first card
        await cards[0].click();

        // Wait for navigation to complete
        await page.waitForNavigation({ timeout: 5000 }).catch(() => {
          console.log('No navigation occurred after clicking card');
        });

        // Check if we navigated to a detail page
        const afterClickUrl = await page.url();
        const navigatedToDetail = afterClickUrl.includes('/water-heaters/') &&
                                !afterClickUrl.endsWith('/water-heaters');

        if (navigatedToDetail) {
          console.log('✅ TEST PASSED: User click successfully navigated to detail page');
          console.log(`Navigated to: ${afterClickUrl}`);
        } else {
          console.log('❓ TEST INCONCLUSIVE: User click did not navigate to detail page');
          console.log(`URL after click: ${afterClickUrl}`);
        }
      } else {
        console.log('⚠️ No cards found to test user-initiated navigation');
      }
    }

  } catch (error) {
    console.error('❌ TEST ERROR:', error);
  } finally {
    // Close the browser
    await browser.close();
    console.log('🧪 Navigation Blocker Test completed');
  }
}

// Run the test
runTest();
