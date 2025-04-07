/**
 * World configuration for Cucumber.js
 * Following TDD principles - provides the environment for BDD tests
 */
const { setWorldConstructor } = require("@cucumber/cucumber");
const { chromium } = require("playwright");

/**
 * Custom world class for shadow document testing
 */
class ShadowDocumentWorld {
  constructor() {
    this.browser = null;
    this.page = null;
    this.deviceId = null;
    this.baseUrl = "http://localhost:8006";
  }

  /**
   * Initialize the browser for testing
   */
  async initBrowser() {
    this.browser = await chromium.launch({
      headless: true,
    });
    const context = await this.browser.newContext();
    this.page = await context.newPage();
    return this.page;
  }

  /**
   * Close the browser after testing
   */
  async closeBrowser() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  /**
   * Navigate to a page
   * @param {string} path - URL path
   */
  async navigate(path) {
    const url = `${this.baseUrl}${path}`;
    await this.page.goto(url);
  }

  /**
   * Get element by selector
   * @param {string} selector - CSS selector
   */
  async getElement(selector) {
    return await this.page.$(selector);
  }

  /**
   * Check if element exists
   * @param {string} selector - CSS selector
   */
  async elementExists(selector) {
    const element = await this.getElement(selector);
    return element !== null;
  }

  /**
   * Check if element is visible
   * @param {string} selector - CSS selector
   */
  async elementIsVisible(selector) {
    const element = await this.getElement(selector);
    if (!element) return false;

    return await this.page.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.display !== "none" && style.visibility !== "hidden";
    }, element);
  }

  /**
   * Get text content of element
   * @param {string} selector - CSS selector
   */
  async getElementText(selector) {
    const element = await this.getElement(selector);
    if (!element) return null;

    return await this.page.evaluate((el) => el.textContent, element);
  }
}

// Set our custom world as the World constructor
setWorldConstructor(ShadowDocumentWorld);
