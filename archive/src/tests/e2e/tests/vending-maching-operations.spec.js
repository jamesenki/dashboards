// @ts-check
const { test, expect } = require('@playwright/test');

test('Vending Machine Operations Test', async ({ page }) => {
  // Navigate to the vending machine details page
  await page.goto('/vending-machines');
  await expect(page).toHaveTitle(/Vending Machines/i);

  // Create a test machine if none exists
  const machineCount = await page.locator('.machine-item').count();
  if (machineCount === 0) {
    await page.locator('a:has-text("Add New")').click();
    await page.fill('[name="name"]', 'Test Operations Machine');
    await page.fill('[name="location"]', 'Test Location');
    await page.fill('[name="temperature"]', '-5');
    await page.click('button:has-text("Save")');
    await page.waitForNavigation();
  }

  // Click on first machine to view details
  await page.locator('.machine-item').first().click();
  await page.waitForLoadState('networkidle');

  // Test 1: Operations Summary Tab (Analytics)
  // Verify that operations analytics data is correctly displayed
  await page.locator('.tab:has-text("Operations Summary")').click();
  await expect(page.locator('.tab.active')).toHaveText('Operations Summary');
  await expect(page.locator('#operations-summary-content')).toBeVisible();

  // Wait for data to load
  await page.waitForTimeout(1000);

  // Verify operations analytics elements are visible
  await expect(page.locator('.operations-summary-container h2')).toBeVisible();
  await expect(page.locator('.operations-summary-container')).not.toContainText('Loading operations data...');

  // Check for specific analytics sections that should be present
  await expect(page.locator('.analytics-section h3:has-text("Sales Data")')).toBeVisible();
  await expect(page.locator('.analytics-section h3:has-text("Usage Patterns")')).toBeVisible();
  await expect(page.locator('.analytics-section h3:has-text("Maintenance History")')).toBeVisible();
  await expect(page.locator('.analytics-section h3:has-text("Temperature Trends")')).toBeVisible();

  // Test 2: Remote Operations Cockpit Tab (Real-time)
  // Verify that real-time operations data is correctly displayed
  await page.locator('.tab:has-text("Remote Operations Cockpit")').click();
  await expect(page.locator('.tab.active')).toHaveText('Remote Operations Cockpit');
  await expect(page.locator('#remote-operations-content')).toBeVisible();

  // Wait for data to load
  await page.waitForTimeout(1000);

  // Verify real-time operations elements are visible
  await expect(page.locator('.remote-operations-container h2')).toBeVisible();
  await expect(page.locator('.remote-operations-container')).not.toContainText('Loading real-time operations data...');

  // Check for specific real-time sections that should be present
  await expect(page.locator('.operations-status-section h3:has-text("Current Status")')).toBeVisible();
  await expect(page.locator('.operations-gauges-section h3:has-text("Performance Metrics")')).toBeVisible();
  await expect(page.locator('.operations-inventory-section h3:has-text("Freezer Inventory")')).toBeVisible();

  // Verify gauge elements are displayed
  await expect(page.locator('#rt-asset-health-gauge')).toBeVisible();
  await expect(page.locator('#rt-temperature-gauge')).toBeVisible();
  await expect(page.locator('#rt-dispense-force-gauge')).toBeVisible();
  await expect(page.locator('#rt-cycle-time-gauge')).toBeVisible();

  // Verify status indicators are displayed
  await expect(page.locator('.status-item:has(.status-label:has-text("Machine Status"))')).toBeVisible();
  await expect(page.locator('.status-item:has(.status-label:has-text("POD Code"))')).toBeVisible();
  await expect(page.locator('.status-item:has(.status-label:has-text("Cup Detect"))')).toBeVisible();
  await expect(page.locator('.status-item:has(.status-label:has-text("POD Bin Door"))')).toBeVisible();
  await expect(page.locator('.status-item:has(.status-label:has-text("Customer Door"))')).toBeVisible();
});
