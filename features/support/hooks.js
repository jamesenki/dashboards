/**
 * Hooks and World setup for BDD tests following TDD principles
 */
const { Before, After, AfterAll, setWorldConstructor } = require("@cucumber/cucumber");
const { chromium } = require("playwright");
const { expect } = require("chai");
const { setupTestDevice } = require("./test_helpers");

/**
 * Custom world object that provides context for steps
 */
class IoTSphereWorld {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.testData = {};
  }

  async initBrowser() {
    // Launch the browser if it doesn't exist
    if (!this.browser) {
      this.browser = await chromium.launch({
        headless: true,
        slowMo: 50,
      });
    }

    // Create a new context and page
    this.context = await this.browser.newContext();
    this.page = await this.context.newPage();

    // Make chai available
    this.expect = expect;
  }

  async closeBrowser() {
    if (this.page) {
      await this.page.close();
      this.page = null;
    }

    if (this.context) {
      await this.context.close();
      this.context = null;
    }
  }

  async setupTestDevice(deviceId, options = {}) {
    return setupTestDevice(this.page, deviceId, options);
  }
}

// Register our custom world
setWorldConstructor(IoTSphereWorld);

// Setup before each scenario
Before(async function () {
  await this.initBrowser();
});

// Cleanup after each scenario
After(async function () {
  await this.closeBrowser();
});

// Global browser cleanup
AfterAll(async function () {
  // Clean up any resources
  // Note: We don't need to explicitly connect to browsers since we're using
  // the browser instance created in the Before hook
  // Just ensure all browser instances are closed
  try {
    if (this.browser) {
      await this.browser.close();
      this.browser = null;
    }
  } catch (error) {
    console.error("Error during browser cleanup:", error);
  }
});
