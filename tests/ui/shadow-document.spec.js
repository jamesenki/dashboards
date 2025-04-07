// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * UI tests for shadow document display in the IoTSphere interface
 * Following TDD principles - RED phase first
 */

test.describe('Device Shadow Document UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:8006/water-heaters');
  });

  test('details page should show shadow document data', async ({ page }) => {
    // Click on a test water heater
    await page.click('text=WH-TEST-001');
    
    // Wait for page to load
    await page.waitForSelector('.card-header:has-text("Device Status")');
    
    // Check for temperature display from shadow document
    const temperatureElement = page.locator('.temperature-value');
    await expect(temperatureElement).toBeVisible();
    
    // Temperature should be a valid number
    const temperatureText = await temperatureElement.textContent();
    expect(parseFloat(temperatureText.replace('°C', ''))).not.toBeNaN();
    
    // Status indicators should reflect shadow state
    const statusIndicator = page.locator('#realtime-connection-status');
    await expect(statusIndicator).toBeVisible();
    await expect(statusIndicator).toHaveClass(/connected/);
  });

  test('temperature history chart should display when shadow exists', async ({ page }) => {
    // Navigate to a device with shadow data
    await page.click('text=WH-TEST-001');
    
    // Click on the History tab
    await page.click('#history-tab-btn');
    
    // Wait for history tab to become active
    await page.waitForSelector('#history-content.active');
    
    // Temperature chart should be visible
    const tempChart = page.locator('#temperature-chart');
    await expect(tempChart).toBeVisible();
    
    // Canvas element should be present (chart rendered)
    const canvas = page.locator('#temperature-chart canvas');
    await expect(canvas).toBeVisible();
  });

  test('should show error message when shadow document is missing', async ({ page }) => {
    // Navigate to a device without shadow data
    await page.click('text=WH-MISSING-SHADOW');
    
    // Error message should be visible
    const errorMessage = page.locator('.shadow-document-error');
    await expect(errorMessage).toBeVisible();
    
    // Error should explain the issue
    await expect(errorMessage).toContainText('No shadow document exists');
  });
});
