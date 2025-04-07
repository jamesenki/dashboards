/**
 * Dashboard Actions for IoTSphere BDD Tests
 *
 * Provides actions for interacting with the dashboard UI during tests
 * Supports device-agnostic testing approach with water heater reference implementation
 */

// Base app URL - configurable from environment
const BASE_URL = process.env.TEST_APP_URL || 'http://localhost:4200';

/**
 * Navigate to the water heater dashboard
 */
async function navigateToDashboard(page) {
  await page.goto(`${BASE_URL}/dashboard/water-heaters`);
  await page.waitForSelector('app-water-heater-dashboard', { state: 'visible' });
}

/**
 * Select a specific device by its ID
 */
async function selectDevice(page, deviceId) {
  const deviceSelector = `[data-device-id="${deviceId}"]`;
  await page.waitForSelector(deviceSelector);
  await page.click(deviceSelector);

  // Wait for device details page to load
  await page.waitForSelector('.device-details-container', { state: 'visible' });
}

/**
 * Filter the dashboard by manufacturer
 */
async function filterByManufacturer(page, manufacturer) {
  await page.click('.manufacturer-filter');
  await page.waitForSelector('.filter-dropdown', { state: 'visible' });

  // Find and click the manufacturer option
  const optionSelector = `.filter-option:has-text("${manufacturer}")`;
  await page.click(optionSelector);

  // Wait for filter to be applied
  await page.waitForSelector(`.active-filter:has-text("${manufacturer}")`);
}

/**
 * Filter the dashboard by connection status
 */
async function filterByStatus(page, status) {
  await page.click('.status-filter');
  await page.waitForSelector('.filter-dropdown', { state: 'visible' });

  // Find and click the status option
  const optionSelector = `.filter-option:has-text("${status}")`;
  await page.click(optionSelector);

  // Wait for filter to be applied
  await page.waitForSelector(`.active-filter:has-text("${status}")`);
}

/**
 * Clear all filters on the dashboard
 */
async function clearFilters(page) {
  const clearButton = await page.$('.clear-filters');
  if (clearButton) {
    await clearButton.click();
    // Wait for filters to be cleared
    await page.waitForSelector('.active-filters', { state: 'detached' });
  }
}

/**
 * Select a specific tab in the device details view
 */
async function selectTab(page, tabName) {
  const tabSelector = `.tab-button:has-text("${tabName}")`;
  await page.click(tabSelector);

  // Wait for tab content to be visible
  await page.waitForSelector('.tab-content', { state: 'visible' });
}

/**
 * Change the temperature setpoint for a device
 */
async function changeTemperatureSetpoint(page, temperature) {
  // Click the setpoint control to activate it
  await page.click('.temperature-setpoint');

  // Find the input field and clear it
  const input = await page.waitForSelector('input[type="number"]');
  await input.fill(''); // Clear existing value
  await input.fill(temperature); // Set new value

  // Submit the change
  await page.press('input[type="number"]', 'Enter');

  // Wait for confirmation message or UI update
  await page.waitForSelector('.confirmation-message, .target-temp:has-text("' + temperature + '")');
}

/**
 * Toggle the power state of a device
 */
async function togglePowerState(page) {
  const powerButton = await page.waitForSelector('button.power-toggle, button:has-text("Turn On"), button:has-text("Turn Off")');
  await powerButton.click();

  // Wait for command to be processed
  await page.waitForTimeout(500);
}

/**
 * Toggle between temperature units (°F/°C)
 */
async function toggleTemperatureUnit(page) {
  const unitToggle = await page.waitForSelector('button.unit-toggle, button:has-text("°F"), button:has-text("°C")');
  const currentUnit = await unitToggle.textContent();

  await unitToggle.click();

  // Wait for unit to change
  const expectedNewUnit = currentUnit.includes('F') ? '°C' : '°F';
  await page.waitForSelector(`button:has-text("${expectedNewUnit}")`);
}

module.exports = {
  navigateToDashboard,
  selectDevice,
  filterByManufacturer,
  filterByStatus,
  clearFilters,
  selectTab,
  changeTemperatureSetpoint,
  togglePowerState,
  toggleTemperatureUnit
};
