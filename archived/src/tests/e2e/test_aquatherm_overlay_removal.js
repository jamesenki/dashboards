/**
 * End-to-end tests to verify the AquaTherm test results overlay has been removed.
 */

const puppeteer = require('puppeteer');

// Use dynamic import for Chai as it's an ESM module
let expect;

before(async function() {
  const chai = await import('chai');
  expect = chai.expect;
});

describe('AquaTherm Test Results Overlay Verification', function() {
  // Set timeout for Puppeteer tests
  this.timeout(10000);

  let browser;
  let page;

  before(async function() {
    // Launch browser
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    page = await browser.newPage();
  });

  after(async function() {
    // Close browser
    if (browser) {
      await browser.close();
    }
  });

  it('should not display AquaTherm test results overlay', async function() {
    // Navigate to the water heaters list page
    await page.goto('http://localhost:8006/water-heaters/', { waitUntil: 'networkidle0' });

    // Check if the AquaTherm Test Results overlay exists
    const overlayExists = await page.evaluate(() => {
      return document.querySelector('.aquatherm-test-results') !== null;
    });

    // The overlay should not exist
    expect(overlayExists, 'AquaTherm test results overlay should not be present').to.be.false;

    // Also check for any elements with "AquaTherm Test" in their text content
    const aquaThermTestElements = await page.evaluate(() => {
      const allElements = Array.from(document.querySelectorAll('*'));
      return allElements.filter(el =>
        el.textContent &&
        el.textContent.includes('AquaTherm Test Results')
      ).length;
    });

    expect(aquaThermTestElements, 'No elements should display AquaTherm Test Results text').to.equal(0);
  });

  it('should not have AquaTherm test results section on dashboard pages', async function() {
    // Navigate to the main dashboard
    await page.goto('http://localhost:8006/dashboard', { waitUntil: 'networkidle0' });

    // Check if any AquaTherm test results section exists on the dashboard
    const testResultsSectionExists = await page.evaluate(() => {
      // Check for various potential selectors that might indicate test results
      const selectors = [
        '.aquatherm-test-results',
        '#aquatherm-test-results',
        '[data-testid="aquatherm-test-results"]',
        '.test-results-overlay'
      ];

      return selectors.some(selector => document.querySelector(selector) !== null);
    });

    expect(testResultsSectionExists, 'AquaTherm test results section should not exist on dashboard').to.be.false;
  });

  it('should not have AquaTherm test results section on water heater detail pages', async function() {
    // Navigate to the water heaters list page
    await page.goto('http://localhost:8006/water-heaters/', { waitUntil: 'networkidle0' });

    // Get the first water heater ID
    const firstHeaterId = await page.evaluate(() => {
      const firstCard = document.querySelector('.water-heater-card a');
      if (firstCard) {
        const href = firstCard.getAttribute('href');
        return href.split('/').pop();
      }
      return null;
    });

    if (!firstHeaterId) {
      throw new Error('No water heaters found on the page');
    }

    // Navigate to the water heater details page
    await page.goto(`http://localhost:8006/water-heaters/${firstHeaterId}`, { waitUntil: 'networkidle0' });

    // Check if any test results overlay or section exists
    const testResultsExists = await page.evaluate(() => {
      // Check for various selectors related to test results
      const selectors = [
        '.aquatherm-test-results',
        '#aquatherm-test-results',
        '[data-testid="aquatherm-test-results"]',
        '.test-results-container',
        '#test-results-section'
      ];

      // Also check for headings or text content that mentions test results
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, .section-title'));
      const testResultHeading = headings.some(h =>
        h.textContent && h.textContent.toLowerCase().includes('test results')
      );

      return {
        bySelector: selectors.some(selector => document.querySelector(selector) !== null),
        byHeading: testResultHeading
      };
    });

    expect(testResultsExists.bySelector, 'AquaTherm test results section should not exist on detail page').to.be.false;
    expect(testResultsExists.byHeading, 'No headings should mention test results').to.be.false;
  });
});
