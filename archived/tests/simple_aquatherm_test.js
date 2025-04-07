/**
 * Simple AquaTherm Navigation Test
 *
 * This is a minimal test script that directly checks if an AquaTherm water heater detail
 * page loads correctly. This follows our TDD principles by directly testing the expected behavior.
 */

const puppeteer = require('puppeteer');

async function testAquaThermDetailPage() {
  console.log('Starting Simple AquaTherm Navigation Test...');

  const browser = await puppeteer.launch({
    headless: false,
    args: ['--window-size=1280,800', '--disable-web-security'],
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Listen for console logs and errors
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', err => console.error('PAGE ERROR:', err.message));
    page.on('response', response => {
      if (!response.ok()) {
        console.error(`HTTP ${response.status()}: ${response.url()}`);
      }
    });

    // Set a reasonable timeout
    page.setDefaultNavigationTimeout(20000);

    // Directly navigate to an AquaTherm heater detail page
    console.log('Directly accessing AquaTherm detail page...');
    const heaterID = 'aqua-wh-tank-001';

    await page.goto(`http://localhost:8006/water-heaters/${heaterID}`, {
      waitUntil: 'networkidle0'
    });

    // Check if we reached the correct page
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);

    // Test result
    if (currentUrl.includes(heaterID)) {
      console.log('✅ SUCCESS: Successfully navigated to AquaTherm detail page!');
    } else {
      console.error('❌ FAIL: Navigation to AquaTherm detail page failed.');
      throw new Error(`Expected URL to contain '${heaterID}' but got: ${currentUrl}`);
    }

    // Check if the page has the expected content
    const headerText = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      return h1 ? h1.textContent : 'No header found';
    });

    console.log(`Page title: ${headerText}`);

    // Wait for user to see the result
    await new Promise(resolve => setTimeout(resolve, 3000));

  } catch (error) {
    console.error('Test failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Run the test
testAquaThermDetailPage().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
