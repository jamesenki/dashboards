/**
 * Simple Card Navigation Test - Direct Approach
 *
 * Following TDD principles, this test defines the expected behavior:
 * - Clicking on a card should navigate to its detail page
 */

const puppeteer = require('puppeteer');

// Target card ID to test
const TARGET_CARD_ID = 'aqua-wh-tankless-001';

async function runSimpleTest() {
  console.log('====== SIMPLE CARD NAVIGATION TEST ======\n');

  const browser = await puppeteer.launch({
    headless: true, // Run headless to avoid UI issues
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Step 1: Navigate to water heaters page
    console.log('1. Navigating to water heaters page...');
    await page.goto('http://localhost:8006/water-heaters', {
      timeout: 10000,
      waitUntil: 'networkidle0'
    });

    // Step 2: Wait for cards to load
    await page.waitForSelector('.heater-card', { timeout: 10000 });
    console.log('2. Water heaters page loaded');

    // Step 3: Find our target card
    const cardSelector = `[data-id="${TARGET_CARD_ID}"]`;
    const cardExists = await page.evaluate((selector) => {
      return !!document.querySelector(selector);
    }, cardSelector);

    if (!cardExists) {
      console.log(`❌ TEST FAILED: Card with ID ${TARGET_CARD_ID} not found on page`);
      return;
    }

    console.log(`3. Found card: ${TARGET_CARD_ID}`);

    // Step 4: Click the card and track navigation
    console.log('4. Clicking card...');

    try {
      // Use Promise.all to wait for both navigation and click
      await Promise.all([
        page.waitForNavigation({ timeout: 10000 }),
        page.click(cardSelector)
      ]);

      // Check if navigation was successful
      const currentUrl = page.url();
      console.log(`5. Navigation complete. Current URL: ${currentUrl}`);

      if (currentUrl.includes(`/water-heaters/${TARGET_CARD_ID}`)) {
        console.log(`\n✅ TEST PASSED: Successfully navigated to ${currentUrl}`);
      } else {
        console.log(`\n❌ TEST FAILED: Navigated to wrong URL: ${currentUrl}`);
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
runSimpleTest();
