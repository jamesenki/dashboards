/**
 * Final Card Navigation Test - Properly Waits for Application Load
 *
 * This test follows TDD principles:
 * 1. Tests define the expected behavior (clicking a card should navigate to detail page)
 * 2. Code is modified to make tests pass, not vice versa
 */

const puppeteer = require('puppeteer');

// Target card that has known navigation issues
const TARGET_CARD_ID = 'aqua-wh-tankless-001';

async function runCardTest() {
  console.log('====== FINAL CARD NAVIGATION TEST ======\n');

  const browser = await puppeteer.launch({
    headless: true, // Use headless mode for test stability
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Increase timeouts for stability
    page.setDefaultNavigationTimeout(30000);
    page.setDefaultTimeout(30000);

    // Add extra logging for page errors and console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`Browser error: ${msg.text()}`);
      }
    });

    page.on('pageerror', err => {
      console.log(`Page error: ${err.message}`);
    });

    // First ensure a clean start by navigating to the home page
    console.log('1. Navigating to home page first...');
    await page.goto('http://localhost:8006', { waitUntil: 'networkidle0' });

    // Sleep to ensure full page load
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Now navigate to the water heaters page
    console.log('2. Navigating to water heaters page...');
    await page.goto('http://localhost:8006/water-heaters', { waitUntil: 'networkidle0' });

    // Wait longer for all scripts to load and execute
    console.log('3. Waiting for page to fully stabilize...');
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Ensure our card is on the page
    console.log(`4. Looking for card: ${TARGET_CARD_ID}...`);
    const cardExists = await page.evaluate((cardId) => {
      return !!document.querySelector(`[data-id="${cardId}"]`);
    }, TARGET_CARD_ID);

    if (!cardExists) {
      console.log(`❌ TEST FAILED: Card ${TARGET_CARD_ID} not found on page`);
      return;
    }

    console.log('   ✅ Card found on page');

    // Wait again to ensure all handlers are attached
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Check if card already has proper navigation setup
    console.log('5. Testing navigation by clicking card...');

    try {
      // Click on the card and wait for navigation
      const navigationPromise = page.waitForNavigation({
        timeout: 10000,
        waitUntil: 'networkidle0'
      });

      // Perform the click
      await page.click(`[data-id="${TARGET_CARD_ID}"]`);

      // Wait for navigation to complete
      await navigationPromise;

      // Check if we're on the correct detail page
      const finalUrl = page.url();
      console.log(`6. Navigation complete, final URL: ${finalUrl}`);

      if (finalUrl.includes(TARGET_CARD_ID)) {
        console.log(`\n✅ TEST PASSED: Card navigation works correctly!`);
      } else {
        console.log(`\n❌ TEST FAILED: Navigated to wrong URL: ${finalUrl}`);
      }
    } catch (error) {
      console.log(`\n❌ TEST FAILED: ${error.message}`);
    }
  } catch (error) {
    console.log(`\n❌ TEST EXECUTION ERROR: ${error.message}`);
  } finally {
    await browser.close();
  }
}

// Run the test
runCardTest();
