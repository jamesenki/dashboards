
 const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Navigate to the water heaters page
    console.log('Navigating to water heaters page...');
    await page.goto('http://localhost:8006/water-heaters', { waitUntil: 'networkidle0' });

    // Wait for the page content to load - use dashboard container instead of specific cards
    console.log('Waiting for page content to load...');
    await page.waitForSelector('#water-heater-list', { timeout: 10000 });

    // Take a screenshot for verification
    await page.screenshot({ path: 'ui_validation_screenshot.png' });
    console.log('Screenshot saved to: ui_validation_screenshot.png');

    // Count the water heater cards (if any)
    const waterHeaterCount = await page.evaluate(() => {
      const cards = document.querySelectorAll('.heater-card');
      console.log(`Found ${cards.length} water heater cards in DOM`);
      return cards.length;
    });

    // Check for empty state message
    const emptyStatePresent = await page.evaluate(() => {
      const emptyState = document.querySelector('.empty-state');
      if (emptyState) {
        console.log('Empty state found with message:', emptyState.textContent);
        return emptyState.textContent;
      }
      return null;
    });

    // Extract detailed information from each card for debugging
    const detailedInfo = await page.evaluate(() => {
      const manufacturers = {};
      const cards = document.querySelectorAll('.heater-card');
      const heaterInfo = [];

      cards.forEach(card => {
        let manufacturer = 'Unknown';
        let id = 'unknown-id';
        let name = 'Unknown Name';

        // Get manufacturer
        const manufacturerElement = card.querySelector('.manufacturer');
        if (manufacturerElement) {
          manufacturer = manufacturerElement.textContent.trim();
        }

        // Try to get ID from href
        const linkElement = card.querySelector('a');
        if (linkElement && linkElement.href) {
          const matches = linkElement.href.match(/\/water-heaters\/([^/]+)/);
          if (matches && matches[1]) {
            id = matches[1];
          }
        }

        // Try to get name
        const nameElement = card.querySelector('.card-title');
        if (nameElement) {
          name = nameElement.textContent.trim();
        }

        // Get card position and dimensions to check for overlapping elements
        const rect = card.getBoundingClientRect();
        const position = {
          top: rect.top,
          left: rect.left,
          bottom: rect.bottom,
          right: rect.right,
          width: rect.width,
          height: rect.height
        };

        // Add to detailed info
        heaterInfo.push({
          id,
          manufacturer,
          name,
          position,
          classes: card.className,
        });

        // Count by manufacturer
        manufacturers[manufacturer] = (manufacturers[manufacturer] || 0) + 1;
      });

      return { manufacturers, heaterInfo };
    });

    // Get page HTML for debugging
    const pageHtml = await page.evaluate(() => {
      const container = document.querySelector('#water-heater-list');
      return container ? container.innerHTML : 'No container found';
    });

    // Output the results as JSON with additional diagnostic information
    const results = {
      waterHeaterCount,
      manufacturerCounts: detailedInfo.manufacturers,
      heaterDetails: detailedInfo.heaterInfo,
      emptyStatePresent,
      pageContentSummary: pageHtml.substring(0, 500) + (pageHtml.length > 500 ? '...' : '')
    };

    console.log(JSON.stringify(results));
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
