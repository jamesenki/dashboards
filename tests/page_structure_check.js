/**
 * Page Structure Check Script
 *
 * This script examines the HTML structure of the water heaters page
 * to identify the correct selectors for our navigation test.
 */

const puppeteer = require('puppeteer');

// Test configuration
const config = {
  baseUrl: 'http://localhost:8006',
  timeout: 15000 // 15 second timeout
};

async function checkPageStructure() {
  console.log('Starting page structure analysis...');

  const browser = await puppeteer.launch({
    headless: false,
    args: ['--window-size=1280,800'],
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Navigate to the water heaters list page
    console.log('Navigating to water heaters list page...');
    await page.goto(`${config.baseUrl}/water-heaters`, {
      waitUntil: 'networkidle0',
      timeout: config.timeout
    });

    // Wait for the DOM to be fully loaded
    await page.waitForFunction('document.readyState === "complete"', {
      timeout: config.timeout
    });

    console.log('Page loaded, analyzing structure...');

    // Check if any cards exist with various possible selectors
    const selectors = [
      '.water-heater-card',
      '.card',
      '[data-heater-id]',
      '[data-id]',
      '.col-md-4',
      '.device-card'
    ];

    for (const selector of selectors) {
      const count = await page.$$eval(selector, elements => elements.length).catch(() => 0);
      console.log(`Found ${count} elements with selector: ${selector}`);

      if (count > 0) {
        // Get more details about the first element with this selector
        const details = await page.$$eval(selector, elements => {
          const el = elements[0];
          return {
            id: el.id,
            classes: el.className,
            attributes: {
              'data-id': el.getAttribute('data-id'),
              'data-heater-id': el.getAttribute('data-heater-id'),
              'data-manufacturer': el.getAttribute('data-manufacturer')
            },
            html: el.outerHTML.substring(0, 500) + '...' // First 500 chars only
          };
        }).catch(e => ({ error: e.toString() }));

        console.log(`Details for first ${selector}:`, details);
      }
    }

    // Check the full page HTML to see what we're working with
    const bodyHtml = await page.$eval('body', el => el.innerHTML.substring(0, 2000));
    console.log('\nPage body HTML (first 2000 chars):\n', bodyHtml, '\n');

    // Check specifically for water heater container elements
    const containerHtml = await page.$eval('#water-heaters-container', el => el.innerHTML.substring(0, 1000))
      .catch(() => 'Container not found');
    console.log('\nWater heaters container HTML (first 1000 chars):\n', containerHtml, '\n');

    console.log('Structure analysis complete.');
  } catch (error) {
    console.error('Analysis failed:', error);
  } finally {
    await browser.close();
  }
}

// Run the analysis
checkPageStructure().catch(err => {
  console.error('Script execution failed:', err);
  process.exit(1);
});
