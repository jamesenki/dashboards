const { test, expect } = require('@playwright/test');

test.describe('Vending Machine Tab Navigation', () => {
  // Navigate to the vending machine detail page before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8006/vending-machines/vm-001');
    // Wait for page to fully load
    await page.waitForSelector('.dashboard-tabs');
  });

  test('should start with Asset Health tab active', async ({ page }) => {
    // Verify initial tab is active
    await expect(page.locator('.tab.active')).toHaveText('Asset Health');
    await expect(page.locator('#asset-health-content')).toBeVisible();
  });

  test('should switch to Operations Summary tab when clicked', async ({ page }) => {
    // Click on Operations Summary tab
    await page.locator('.tab:has-text("Operations Summary")').click();
    
    // Verify tab is active
    await expect(page.locator('.tab.active')).toHaveText('Operations Summary');
    await expect(page.locator('#operations-summary-content')).toBeVisible();
    
    // Verify other content is hidden
    await expect(page.locator('#asset-health-content')).not.toBeVisible();
  });

  test('should switch to Predictions tab when clicked', async ({ page }) => {
    // Click on Predictions tab
    await page.locator('.tab:has-text("Predictions")').click();
    
    // Verify tab is active
    await expect(page.locator('.tab.active')).toHaveText('Predictions');
    await expect(page.locator('#predictions-content')).toBeVisible();
  });

  test('should switch to Insights tab when clicked', async ({ page }) => {
    // Click on Insights tab
    await page.locator('.tab:has-text("Insights")').click();
    
    // Verify tab is active
    await expect(page.locator('.tab.active')).toHaveText('Insights');
    await expect(page.locator('#insights-content')).toBeVisible();
  });

  test('should switch to Remote Operations Cockpit tab when clicked', async ({ page }) => {
    // Click on Remote Operations Cockpit tab
    await page.locator('.tab:has-text("Remote Operations Cockpit")').click();
    
    // Verify tab is active
    await expect(page.locator('.tab.active')).toHaveText('Remote Operations Cockpit');
    await expect(page.locator('#remote-operations-content')).toBeVisible();
  });

  test('should maintain selected tab when refreshing page', async ({ page }) => {
    // Click on Operations Summary tab
    await page.locator('.tab:has-text("Operations Summary")').click();
    
    // Reload the page
    await page.reload();
    await page.waitForSelector('.dashboard-tabs');
    
    // Verify Operations Summary tab is still active
    await expect(page.locator('.tab.active')).toHaveText('Operations Summary');
    await expect(page.locator('#operations-summary-content')).toBeVisible();
  });
});