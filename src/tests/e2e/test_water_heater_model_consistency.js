/**
 * End-to-end tests for water heater model consistency.
 * This test verifies that all water heaters are AquaTherm (Rheem) models.
 */

const puppeteer = require('puppeteer');

// Use dynamic import for Chai as it's an ESM module
let expect;

before(async function() {
  const chai = await import('chai');
  expect = chai.expect;
});

describe('Water Heater AquaTherm Model Consistency', function() {
  // Set timeout for Puppeteer tests
  this.timeout(15000);

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

  it('should have 16 AquaTherm water heaters in the database', async function() {
    // Make a direct API call to get all water heaters
    await page.goto('http://localhost:8006/api/water-heaters/', { waitUntil: 'networkidle0' });

    // Extract the JSON response
    const waterHeatersData = await page.evaluate(() => {
      try {
        return JSON.parse(document.querySelector('body').innerText);
      } catch (e) {
        return null;
      }
    });

    // Verify we got water heaters data
    expect(waterHeatersData).to.not.be.null;
    expect(Array.isArray(waterHeatersData)).to.be.true;

    // Count the number of water heaters
    expect(waterHeatersData.length).to.equal(16, 'Should have exactly 16 water heaters');

    // Verify each water heater is of AquaTherm (Rheem) type
    waterHeatersData.forEach(heater => {
      expect(heater.manufacturer.toLowerCase()).to.equal('rheem', `Water heater ${heater.id} should be from Rheem manufacturer`);
      // Check for model names that indicate AquaTherm
      expect(['proterra', 'performance', 'gladiator', 'marathonplus', 'professional'].some(
        modelName => heater.model.toLowerCase().includes(modelName)
      ), `Water heater ${heater.id} should be an AquaTherm model`).to.be.true;
    });
  });

  it('should NOT have any non-AquaTherm water heaters in the database', async function() {
    // Make a direct API call to get all water heaters
    await page.goto('http://localhost:8006/api/water-heaters/', { waitUntil: 'networkidle0' });

    // Extract the JSON response
    const waterHeatersData = await page.evaluate(() => {
      try {
        return JSON.parse(document.querySelector('body').innerText);
      } catch (e) {
        return null;
      }
    });

    // Verify we got water heaters data
    expect(waterHeatersData).to.not.be.null;
    expect(Array.isArray(waterHeatersData)).to.be.true;

    // Print all water heater info for diagnosis
    console.log('Water heaters found:', waterHeatersData.length);
    waterHeatersData.forEach((heater, index) => {
      console.log(`Heater ${index + 1}: ID=${heater.id} | Manufacturer=${heater.manufacturer || 'MISSING'} | Model=${heater.model || 'MISSING'}`);
    });

    // Check for any non-Rheem manufacturers or missing manufacturer
    const nonRheemHeaters = waterHeatersData.filter(heater => {
      if (!heater.manufacturer) {
        return true; // Missing manufacturer is considered non-Rheem
      }
      return heater.manufacturer.toLowerCase() !== 'rheem';
    });

    expect(nonRheemHeaters.length, 'Should NOT have any non-Rheem or missing manufacturer water heaters').to.equal(0);

    // Create a list of known non-AquaTherm model keywords
    const nonAquaThermKeywords = ['generic', 'standard', 'basic', 'old', 'legacy'];

    // Check for any models with non-AquaTherm keywords or missing model
    const potentialNonAquaThermModels = waterHeatersData.filter(heater => {
      if (!heater.model) {
        return true; // Missing model is considered non-AquaTherm
      }

      const modelLower = heater.model.toLowerCase();
      // If model contains any non-AquaTherm keyword or doesn't contain any AquaTherm keyword
      const containsNonAquaThermKeyword = nonAquaThermKeywords.some(keyword => modelLower.includes(keyword));

      // List of AquaTherm model keywords to check for
      const aquaThermKeywords = ['proterra', 'performance', 'gladiator', 'marathon', 'professional', 'hybrid'];
      const containsAquaThermKeyword = aquaThermKeywords.some(keyword => modelLower.includes(keyword));

      return containsNonAquaThermKeyword || !containsAquaThermKeyword;
    });

    expect(potentialNonAquaThermModels.length, 'Should NOT have any non-AquaTherm models').to.equal(0);

    // Extra verification: All water heaters should have AquaTherm-specific attributes
    const heaterWithoutAquaThermAttrs = waterHeatersData.filter(heater => {
      // AquaTherm water heaters should have these attributes
      return !heater.hasOwnProperty('series') ||
             !heater.hasOwnProperty('energy_efficiency_rating') ||
             !heater.hasOwnProperty('smart_enabled');
    });

    expect(heaterWithoutAquaThermAttrs.length, 'All water heaters should have AquaTherm-specific attributes').to.equal(0);
  });

  it('should display AquaTherm model information on the UI', async function() {
    // Navigate to the water heaters list page
    await page.goto('http://localhost:8006/water-heaters/', { waitUntil: 'networkidle0' });

    // Verify all water heater cards display Rheem as manufacturer
    const manufacturers = await page.evaluate(() => {
      const manufacturerElements = Array.from(document.querySelectorAll('.water-heater-manufacturer'));
      return manufacturerElements.map(el => el.textContent.trim().toLowerCase());
    });

    // Check we have manufacturer information displayed
    expect(manufacturers.length).to.be.greaterThan(0, 'Should display manufacturer information');

    // All manufacturers should be Rheem
    manufacturers.forEach(manufacturer => {
      expect(manufacturer).to.include('rheem', 'All water heaters should be from Rheem');
    });

    // Verify the water heater models displayed are AquaTherm models
    const modelNames = await page.evaluate(() => {
      const modelElements = Array.from(document.querySelectorAll('.water-heater-model'));
      return modelElements.map(el => el.textContent.trim().toLowerCase());
    });

    // Check that model names are displayed
    expect(modelNames.length).to.be.greaterThan(0, 'Should display model information');

    // Check that all models are AquaTherm models
    const aquaThermKeywords = ['proterra', 'performance', 'gladiator', 'marathon', 'professional', 'hybrid'];
    modelNames.forEach(model => {
      expect(
        aquaThermKeywords.some(keyword => model.includes(keyword)),
        `Model "${model}" should be an AquaTherm model`
      ).to.be.true;
    });
  });

  it('should have consistent AquaTherm specs on detail pages', async function() {
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

    expect(firstHeaterId).to.not.be.null;

    // Navigate to the water heater details page
    await page.goto(`http://localhost:8006/water-heaters/${firstHeaterId}`, { waitUntil: 'networkidle0' });

    // Verify the details page shows Rheem-specific attributes
    const rheemAttributes = await page.evaluate(() => {
      // Look for Rheem-specific attributes on the page
      const rheemSpecificFields = [
        'series', 'energy_efficiency_rating', 'capacity',
        'smart_enabled', 'leak_detection', 'warranty_info'
      ];

      const attributes = {};

      rheemSpecificFields.forEach(field => {
        const element = document.querySelector(`[data-field="${field}"]`);
        if (element) {
          attributes[field] = element.textContent.trim();
        }
      });

      return attributes;
    });

    // Check for at least some of the Rheem-specific attributes
    expect(Object.keys(rheemAttributes).length).to.be.greaterThan(0, 'Should display Rheem-specific attributes');

    // If the energy efficiency rating is present, it should have a valid UEF value (typically 2.0-4.5)
    if (rheemAttributes.energy_efficiency_rating) {
      const uefValue = parseFloat(rheemAttributes.energy_efficiency_rating);
      expect(isNaN(uefValue)).to.be.false;
      expect(uefValue).to.be.greaterThan(0);
      expect(uefValue).to.be.lessThan(5);
    }

    // If capacity is present, it should be a valid value (typically 30-80 gallons)
    if (rheemAttributes.capacity) {
      const capacityValue = parseFloat(rheemAttributes.capacity);
      expect(isNaN(capacityValue)).to.be.false;
      expect(capacityValue).to.be.greaterThan(0);
      expect(capacityValue).to.be.lessThan(100);
    }
  });
});
