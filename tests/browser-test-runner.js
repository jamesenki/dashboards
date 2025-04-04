/**
 * Browser Test Runner for AquaTherm Card Navigation
 * This script uses Puppeteer to run the aquatherm-card-test.js in a real browser
 *
 * Following TDD principles:
 * 1. We're using the test to define the expected behavior (cards should navigate)
 * 2. We're not changing the test to accommodate the implementation
 * 3. We're making the code work to pass the test
 */

const puppeteer = require('puppeteer');

async function runBrowserTest() {
  console.log('Starting AquaTherm Card Navigation Test in browser...');

  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Listen for console messages
    page.on('console', message => {
      const type = message.type();
      const text = message.text();

      // Skip some of the noisy logs
      if (text.includes('API client') || text.includes('component not found')) {
        return;
      }

      // Highlight test results
      if (text.includes('Test execution failed')) {
        console.log('\n❌ TEST FAILED: ' + text);
      } else if (text.includes('PASSED:')) {
        console.log('\n✅ ' + text);
      } else if (type === 'error') {
        console.log('❌ Browser error: ' + text);
      } else if (text.includes('Starting AquaTherm Card Tests')) {
        console.log('\n' + text);
      } else {
        console.log('Browser log: ' + text);
      }
    });

    // Listen for page errors
    page.on('pageerror', error => {
      console.error('\n❌ PAGE ERROR:', error.message);
    });

    // Navigate to the water heaters page
    console.log('Navigating to water heaters page...');
    await page.goto('http://localhost:8006/water-heaters', {
      waitUntil: 'networkidle0',
      timeout: 10000
    });

    // Inject the test script
    console.log('Injecting the AquaTherm card test script...');
    await page.evaluate(() => {
      const script = document.createElement('script');
      script.src = '/static/js/tests/aquatherm-card-test.js';
      document.head.appendChild(script);
    });

    // Wait for test execution and results
    console.log('Waiting for test execution...');

    // Give time for the test to execute and report results
    // Using a Promise-based timeout since waitForTimeout may not be available in this version
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Check if there's a TypeError in the console logs
    const typeErrorExists = await page.evaluate(() => {
      return !!window.testErrorMessage && window.testErrorMessage.includes('TypeError');
    });

    if (typeErrorExists) {
      console.log('\n❌ TypeError detected in test execution');
    } else {
      console.log('\n✅ No TypeError detected in test execution');
    }

    // Test navigation directly
    console.log('\nTesting navigation by clicking on AquaTherm card...');
    const aquaThermCardExists = await page.evaluate(() => {
      return !!document.querySelector('[data-id="aqua-wh-tankless-001"]');
    });

    if (aquaThermCardExists) {
      try {
        console.log('Found AquaTherm tankless card, clicking it...');

        // Click the card and wait for navigation
        await Promise.all([
          page.waitForNavigation({ timeout: 5000 }).catch(e => {
            throw new Error(`Navigation timeout after clicking card: ${e.message}`);
          }),
          page.click('[data-id="aqua-wh-tankless-001"]').catch(e => {
            throw new Error(`Failed to click card: ${e.message}`);
          })
        ]);

        // Check if navigation was successful
        const currentUrl = page.url();
        if (currentUrl.includes('/water-heaters/aqua-wh-tankless-001')) {
          console.log(`\n✅ NAVIGATION SUCCESSFUL: Card click navigated to ${currentUrl}`);
        } else {
          console.log(`\n❌ NAVIGATION FAILED: Card click navigated to wrong URL: ${currentUrl}`);
        }
      } catch (error) {
        console.log(`\n❌ NAVIGATION ERROR: ${error.message}`);
      }
    } else {
      console.log('\n❌ AquaTherm card not found on page');
    }

    // Test if the TypeError occurs on actual click
    if (aquaThermCardExists) {
      console.log('\nTesting for TypeError during card click...');

      // Set up an error handler
      await page.evaluate(() => {
        window.cardClickError = null;
        window.onerror = function(message, source, lineno, colno, error) {
          window.cardClickError = message;
          console.error("Card click error:", message);
          return true; // Prevent default error handling
        };
      });

      // Try to click the card
      try {
        await page.click('[data-id="aqua-wh-tankless-001"]');
        // Using Promise-based timeout for compatibility
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Check if an error occurred
        const clickError = await page.evaluate(() => window.cardClickError);

        if (clickError && clickError.includes('TypeError')) {
          console.log(`\n❌ TypeError detected during card click: ${clickError}`);
        } else if (clickError) {
          console.log(`\n❌ Other error during card click: ${clickError}`);
        } else {
          console.log('\n✅ No TypeError detected during card click');
        }
      } catch (error) {
        console.log(`\n❌ Error testing card click: ${error.message}`);
      }
    }

    console.log('\nTest execution complete');
  } catch (error) {
    console.error('\n❌ TEST RUNNER ERROR:', error.message);
  } finally {
    await browser.close();
  }
}

// Run the test
runBrowserTest().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
