/**
 * End-to-end tests for water heater gauge display consistency.
 * This test verifies that gauge displays are consistent and properly rendered.
 */

const puppeteer = require('puppeteer');

// Use dynamic import for Chai as it's an ESM module
let expect;

before(async function() {
  const chai = await import('chai');
  expect = chai.expect;
});

describe('Water Heater Gauge Display Consistency', function() {
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

  it('should display gauges with proper scaling and orientation', async function() {
    // Navigate to the water heaters list page
    await page.goto('http://localhost:8006/water-heaters/', { waitUntil: 'networkidle0' });

    // Get the first water heater ID from the list
    const heaterIds = await page.evaluate(() => {
      const heaterCards = Array.from(document.querySelectorAll('.water-heater-card'));
      return heaterCards.map(card => {
        const link = card.querySelector('a');
        if (link) {
          const href = link.getAttribute('href');
          return href.split('/').pop();
        }
        return null;
      }).filter(id => id);
    });

    if (heaterIds.length === 0) {
      throw new Error('No water heaters found on the page');
    }

    // Navigate to the first water heater details page
    await page.goto(`http://localhost:8006/water-heaters/${heaterIds[0]}`, { waitUntil: 'networkidle0' });

    // Wait for the gauges to be loaded
    await page.waitForSelector('.gauge-container', { timeout: 5000 });

    // Verify temperature gauge display
    const tempGaugeExists = await page.evaluate(() => {
      const tempGauge = document.querySelector('#temperature-gauge-panel');
      return tempGauge !== null;
    });
    expect(tempGaugeExists, 'Temperature gauge should exist').to.be.true;

    // Get all gauge needles and verify their CSS transform properties
    const gaugeNeedleStyles = await page.evaluate(() => {
      const needles = Array.from(document.querySelectorAll('.gauge-needle'));
      return needles.map(needle => {
        const style = window.getComputedStyle(needle);
        return {
          transform: style.transform,
          transformOrigin: style.transformOrigin,
          id: needle.id
        };
      });
    });

    // Verify all gauges have transform properties set
    expect(gaugeNeedleStyles.length).to.be.greaterThan(0, 'Should have gauge needles on the page');
    gaugeNeedleStyles.forEach(style => {
      expect(style.transform, `Gauge needle ${style.id} should have a transform property`).to.not.equal('none');
      expect(style.transformOrigin, `Gauge needle ${style.id} should have a transformOrigin property`).to.include('bottom');
    });

    // Verify gauge values are displayed and formatted correctly
    const gaugeValues = await page.evaluate(() => {
      const values = Array.from(document.querySelectorAll('.gauge-value'));
      return values.map(value => ({
        text: value.textContent.trim(),
        id: value.id
      }));
    });

    expect(gaugeValues.length).to.be.greaterThan(0, 'Should have gauge values on the page');
    gaugeValues.forEach(value => {
      expect(value.text, `Gauge value ${value.id} should not be empty`).to.not.equal('');

      // Check temperature value format (should end with °C)
      if (value.id === 'temperature-gauge-value') {
        expect(value.text, 'Temperature should be formatted with °C').to.include('°C');
      }

      // Check pressure value format (should include 'bar')
      if (value.id === 'pressure-gauge-value') {
        expect(value.text, 'Pressure should be formatted with bar').to.include('bar');
      }

      // Check energy value format (should include 'W')
      if (value.id === 'energy-gauge-value') {
        expect(value.text, 'Energy should be formatted with W').to.include('W');
      }
    });
  });

  it('should have consistent gauge colors and backgrounds', async function() {
    // Navigate to a water heater details page (assuming we already got the ID)
    const heaterIds = await page.evaluate(() => {
      const heaterCards = Array.from(document.querySelectorAll('.water-heater-card'));
      return heaterCards.map(card => {
        const link = card.querySelector('a');
        if (link) {
          const href = link.getAttribute('href');
          return href.split('/').pop();
        }
        return null;
      }).filter(id => id);
    });

    if (heaterIds.length === 0) {
      throw new Error('No water heaters found on the page');
    }

    await page.goto(`http://localhost:8006/water-heaters/${heaterIds[0]}`, { waitUntil: 'networkidle0' });

    // Wait for the gauges to be loaded
    await page.waitForSelector('.gauge-container', { timeout: 5000 });

    // Verify gauge container styling
    const gaugeStyles = await page.evaluate(() => {
      const gaugeContainers = Array.from(document.querySelectorAll('.gauge-container'));
      return gaugeContainers.map(container => {
        const style = window.getComputedStyle(container);
        return {
          borderRadius: style.borderRadius,
          background: style.background,
          id: container.id || 'unknown'
        };
      });
    });

    expect(gaugeStyles.length).to.be.greaterThan(0, 'Should have gauge containers on the page');

    // All gauge containers should have similar styling
    const firstGaugeStyle = gaugeStyles[0];
    gaugeStyles.forEach(style => {
      expect(style.borderRadius, 'Gauge containers should have consistent border radius').to.equal(firstGaugeStyle.borderRadius);

      // We can't strictly compare backgrounds as they may vary by gauge,
      // but they should all have some background set
      expect(style.background, `Gauge ${style.id} should have a background`).to.not.equal('');
    });
  });
});
