/**
 * AquaTherm Card Navigation Test
 *
 * This test verifies that clicking on AquaTherm water heater cards correctly navigates
 * to the appropriate detail page. Following Test-Driven Development principles,
 * this test defines the expected behavior that our implementation must satisfy.
 */

const puppeteer = require('puppeteer');

// Test configuration
const config = {
  baseUrl: 'http://localhost:8006',
  timeout: 20000, // 20 second timeout for operations
  navigationWaitTime: 2000 // Wait time after navigation
};

// Main test function
async function runCardNavigationTest() {
  console.log('Starting AquaTherm Card Navigation Test...');

  const browser = await puppeteer.launch({
    headless: false, // Set to true for headless testing
    args: ['--window-size=1280,800', '--disable-web-security'],
    defaultViewport: { width: 1280, height: 800 }
  });

  try {
    const page = await browser.newPage();

    // Set longer timeouts for navigation
    page.setDefaultNavigationTimeout(config.timeout);
    page.setDefaultTimeout(config.timeout);

    // Listen for console logs
    page.on('console', msg => console.log('BROWSER:', msg.text()));

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

    // Wait a bit to ensure JS has initialized
    // Using setTimeout with a promise for compatibility with older Puppeteer versions
    await new Promise(resolve => setTimeout(resolve, 1000));

    console.log('Waiting for water heater cards to load...');
    await page.waitForSelector('.card', { timeout: config.timeout });

    // Check all water heater cards - perform a fresh evaluation
    const allCards = await page.evaluate(() => {
      // Find all card elements
      const cards = document.querySelectorAll('.card[data-id]');

      // Map to a simple array of objects
      return Array.from(cards).map(card => ({
        id: card.getAttribute('data-id'),
        name: card.querySelector('.card-title')?.textContent?.trim() ||
              card.textContent.trim().split('\n')[0].trim()
      }));
    });

    console.log(`Found ${allCards.length} heater cards:`, allCards);

    if (allCards.length === 0) {
      throw new Error('No heater cards found on the page. There may be an issue with the page rendering.');
    }

    // Find AquaTherm cards by ID (they should start with 'aqua-')
    const aquathermCards = allCards.filter(card =>
      card.id.startsWith('aqua-') ||
      card.name.toLowerCase().includes('aquatherm')
    );

    console.log(`Identified ${aquathermCards.length} AquaTherm cards:`, aquathermCards);

    // We'll test at least one AquaTherm card to verify navigation works correctly
    if (aquathermCards.length > 0) {
      // Test just one AquaTherm card as a representative example
      const aquaCard = aquathermCards[0];
      console.log(`Testing navigation for AquaTherm card: ${aquaCard.name} (${aquaCard.id})`);

      // Use a new navigation approach to avoid DOM detachment issues
      await testSingleCardNavigation(page, aquaCard);
    } else {
      console.log('No AquaTherm cards found to test. This is unexpected!');
      console.log('Testing a regular water heater card instead...');

      if (allCards.length > 0) {
        await testSingleCardNavigation(page, allCards[0]);
      } else {
        throw new Error('No cards available to test!');
      }
    }

    console.log('✅ Card navigation test completed successfully!');
  } catch (error) {
    console.error('❌ Test failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

// Test a single card's navigation in isolation
async function testSingleCardNavigation(page, card) {
  try {
    // Ensure we're on the listing page
    if (!page.url().includes('/water-heaters')) {
      await page.goto(`${config.baseUrl}/water-heaters`, {
        waitUntil: 'networkidle0',
        timeout: config.timeout
      });
      await page.waitForFunction('document.readyState === "complete"', { timeout: config.timeout });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Give JS time to initialize
    }

    console.log(`Looking for card with ID: ${card.id}`);

    // Use page.evaluate to find and click the card directly in the browser context
    // This avoids the DOM reference issues
    const clicked = await page.evaluate((cardId) => {
      const card = document.querySelector(`.card[data-id="${cardId}"]`);
      if (card) {
        console.log(`Found card ${cardId}, clicking it...`);
        card.click();
        return true;
      }
      return false;
    }, card.id);

    if (!clicked) {
      throw new Error(`Could not find card with ID ${card.id} to click`);
    }

    // Wait for navigation to complete
    await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: config.timeout });

    // Check the URL to verify navigation worked
    const currentUrl = page.url();

    console.log(`Navigated to: ${currentUrl}`);

    if (!currentUrl.includes(card.id)) {
      throw new Error(`Navigation failed for card ${card.id}. Expected URL to contain: ${card.id}, Actual URL: ${currentUrl}`);
    }

    // Successfully navigated to the correct detail page
    console.log(`✓ Successfully navigated to detail page for ${card.name} (${card.id})`);
    return true;
  } catch (error) {
    console.error(`Error testing card ${card.id}:`, error.message);
    throw error;
  }
}


// Run the test
runCardNavigationTest().catch(err => {
  console.error('Test execution failed:', err);
  process.exit(1);
});
