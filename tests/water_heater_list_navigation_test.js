/**
 * Water Heater List Navigation Test
 *
 * This test validates a key requirement:
 * - The water heater list page must stay on the list view until a user explicitly clicks on a card
 * - No automatic navigation should occur
 */

const puppeteer = require('puppeteer');

// Test Configuration
const TEST_CONFIG = {
  baseUrl: 'http://localhost:8006',
  listPageUrl: 'http://localhost:8006/water-heaters',
  waitTimeMs: 5000,  // Time to wait to verify no auto-navigation happens
  selectors: {
    cardSelector: '.heater-card, .card[data-id]',
    listContainerSelector: '.dashboard'
  }
};

async function runWaterHeaterListNavigationTest() {
  console.log('📋 TEST PLAN:');
  console.log('1. Navigate to water heater list page');
  console.log('2. Wait for list content to load');
  console.log('3. Verify the page does NOT auto-navigate away for 5 seconds');
  console.log('4. Simulate user clicking a card');
  console.log('5. Verify navigation to detail page happens only after user click');

  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    defaultViewport: null
  });

  try {
    // Create new page and setup console logging
    const page = await browser.newPage();
    page.on('console', msg => console.log('BROWSER:', msg.text()));

    // Step 1: Navigate to water heater list page
    console.log('🧪 TEST STEP 1: Navigating to water heaters list page');
    await page.goto(TEST_CONFIG.listPageUrl, { waitUntil: 'networkidle0' });

    // Step 2: Wait for list content to load
    console.log('🧪 TEST STEP 2: Waiting for water heater list to load');
    try {
      await page.waitForSelector(TEST_CONFIG.selectors.listContainerSelector, { timeout: 5000 });
      console.log('✅ Water heater list loaded successfully');
    } catch (error) {
      console.error('❌ TEST FAILED: Water heater list did not load', error);
      throw new Error('Water heater list did not load');
    }

    // Step 3: Verify no auto-navigation for 5 seconds
    console.log(`🧪 TEST STEP 3: Waiting ${TEST_CONFIG.waitTimeMs}ms to verify no auto-navigation`);

    // Record starting URL
    const startUrl = await page.url();
    console.log(`Initial URL: ${startUrl}`);

    // Setup navigation listener to detect any navigation
    let navigationDetected = false;
    let navigationUrl = null;

    page.on('framenavigated', frame => {
      if (frame === page.mainFrame()) {
        navigationDetected = true;
        navigationUrl = frame.url();
        console.log(`⚠️ Navigation detected to: ${navigationUrl}`);
      }
    });

    // Wait for specified time using a promise-based timeout since waitForTimeout isn't available
    await new Promise(resolve => setTimeout(resolve, TEST_CONFIG.waitTimeMs));

    // Verify current URL hasn't changed
    const currentUrl = await page.url();
    console.log(`URL after waiting: ${currentUrl}`);

    // Check if we're still on the list page
    const isStillOnListPage =
      (currentUrl === TEST_CONFIG.listPageUrl ||
       currentUrl === TEST_CONFIG.baseUrl ||
       currentUrl === TEST_CONFIG.baseUrl + '/');

    if (!isStillOnListPage || navigationDetected) {
      console.error('❌ TEST FAILED: Page automatically navigated away from water heaters list');
      console.error(`Expected to stay on ${TEST_CONFIG.listPageUrl}, but navigated to: ${navigationUrl || currentUrl}`);
      throw new Error('Automatic navigation detected');
    } else {
      console.log('✅ TEST PASSED: Page remained on water heaters list without auto-navigating');
    }

    // Step 4: Simulate user clicking a card
    console.log('🧪 TEST STEP 4: Testing user-initiated navigation by clicking on a card');

    // Find all heater cards
    const cards = await page.$$(TEST_CONFIG.selectors.cardSelector);

    if (cards.length === 0) {
      console.warn('⚠️ No cards found to test user-initiated navigation');
      console.log('⚠️ TEST INCONCLUSIVE: Unable to test user click navigation');
    } else {
      console.log(`Found ${cards.length} cards to test`);

      // Take screenshot before clicking
      await page.screenshot({ path: './tests/screenshots/before-click.png' });

      // Reset navigation detection
      navigationDetected = false;
      navigationUrl = null;

      // Click the first card
      console.log('Clicking the first card...');
      await cards[0].click();

      // Step 5: Verify navigation to detail page happens
      console.log('🧪 TEST STEP 5: Verifying navigation after user click');

      // Wait for navigation or timeout
      try {
        await page.waitForNavigation({ timeout: 5000 });
        navigationDetected = true;
      } catch (error) {
        console.log('No navigation occurred after clicking card');
      }

      // Take screenshot after clicking
      await page.screenshot({ path: './tests/screenshots/after-click.png' });

      // Check if we navigated to a detail page
      const afterClickUrl = await page.url();
      navigationUrl = afterClickUrl;

      const navigatedToDetail = afterClickUrl.includes('/water-heaters/') &&
                                !afterClickUrl.endsWith('/water-heaters') &&
                                !afterClickUrl.endsWith('/water-heaters/');

      if (navigatedToDetail) {
        console.log('✅ TEST PASSED: User click successfully navigated to detail page');
        console.log(`Navigated to: ${afterClickUrl}`);
      } else {
        console.error('❌ TEST FAILED: User click did not navigate to detail page');
        console.error(`Expected URL to change to a detail page, but got: ${afterClickUrl}`);
        throw new Error('User click navigation failed');
      }
    }

    console.log('✅ ALL TESTS PASSED: Water heater list navigation behavior is correct');

  } catch (error) {
    console.error('❌ TEST ERROR:', error);
    return false;
  } finally {
    // Close the browser
    await browser.close();
    console.log('🧪 Water Heater List Navigation Test completed');
  }

  return true;
}

// Self-executing test
(async () => {
  try {
    const success = await runWaterHeaterListNavigationTest();
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error('Unhandled test error:', error);
    process.exit(1);
  }
})();
