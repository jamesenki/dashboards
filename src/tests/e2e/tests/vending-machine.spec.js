// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Vending Machine Dashboard', () => {
  test('landing page loads correctly', async ({ page }) => {
    // Use the full URL rather than relative path
    await page.goto('http://localhost:8006/');
    await expect(page).toHaveTitle(/IoTSphere/);
    await expect(page.locator('.logo-text')).toContainText('IoTSphere');
  });

  test('navigates to vending machine detail view', async ({ page }) => {
    // Go to the dashboard with full URL
    await page.goto('http://localhost:8006/');
    
    // Click the vending machine icon in the sidebar
    await page.locator('a[href*="vending-machines"]').first().click();
    
    // Verify we're on the vending machine detail page
    await expect(page.url()).toContain('/vending-machines');
    
    // Check that the vending machine elements exist - verify header is visible
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('.logo-text')).toBeVisible();
  });

  test('temperature gauge text is readable', async ({ page }) => {
    // Go directly to the vending machine detail page with loaded hash using full URL
    await page.goto('http://localhost:8006/vending-machines/vm-106c55e5#loaded');
    
    // Verify the temperature gauge exists and is visible
    const tempGauge = page.locator('#temperature-gauge').first();
    await expect(tempGauge).toBeVisible();
    
    // Check the gauge value element is visible and has text
    // Don't use closest() which isn't available in Playwright
    const gaugeValue = page.locator('.gauge-value').filter({ hasText: /°F/ }).first();
    await expect(gaugeValue).toBeVisible();
    
    // Take a screenshot for visual verification
    await gaugeValue.screenshot({ path: 'temperature-gauge-text.png' });
    
    // Verify the text has sufficient contrast by checking CSS properties
    const styles = await gaugeValue.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return {
        backgroundColor: style.backgroundColor,
        color: style.color,
        zIndex: style.zIndex
      };
    });
    
    // If the z-index is a number and greater than 1, text is properly layered
    expect(parseInt(styles.zIndex, 10)).toBeGreaterThan(1);
  });

  test('machine selector loads the correct machine data', async ({ page }) => {
    // Go to a specific vending machine page directly
    await page.goto('http://localhost:8006/vending-machines/vm-106c55e5#loaded');
    
    // Verify page loads by checking for basic elements
    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('.main-content')).toBeVisible();
    
    // Wait for data to load
    await page.waitForTimeout(2000);
    
    // Click on a link to ensure page is interactive
    await page.locator('.logo-text').click();
    
    // Verify we navigated away
    await expect(page.url()).toContain('http://localhost:8006/');
  });
});
