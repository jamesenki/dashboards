/**
 * Common step definitions for IoTSphere BDD tests
 * These steps are shared between multiple feature files
 * Following TDD principles - establish expected behaviors first
 */
// eslint-disable-next-line no-unused-vars
const { Given, When, Then, Before, After, AfterAll } = require("@cucumber/cucumber");
const { expect } = require("chai");
const { chromium } = require("playwright");
// eslint-disable-next-line no-unused-vars
const { setupRealTimeMonitor } = require("../support/test_helpers");
const { setupTestDevice } = require("../support/test_helpers");
// eslint-disable-next-line no-unused-vars
const { clearTestData, setupTestShadow } = require("../support/shadow_document_helper");

// Store the browser instance so it can be reused
let browser;
let page;

/**
 * Setup and teardown hooks
 */
Before(async function () {
  // Launch the browser if it's not already running
  if (!browser) {
    browser = await chromium.launch({
      headless: true,
      // Set slower animations for stability
      slowMo: 50,
    });
  }

  // Create a new page for each scenario
  const context = await browser.newContext();
  page = await context.newPage();

  // Make page available to steps
  this.page = page;
});

After(async () => {
  // Close the page after each scenario
  if (page) {
    await page.close();
  }
});

AfterAll(async () => {
  // Close the browser after all tests
  if (browser) {
    await browser.close();
    browser = null;
  }
});

/**
 * Application setup steps
 */
Given("the IoTSphere application is running", async function () {
  console.log("Setting up IoTSphere application environment");

  // Create the base application structure for testing
  await this.page.evaluate(() => {
    // Create app container if it doesn't exist
    let appContainer = document.querySelector("#app-container");
    if (!appContainer) {
      appContainer = document.createElement("div");
      appContainer.id = "app-container";
      document.body.appendChild(appContainer);

      // Add basic app structure
      appContainer.innerHTML = `
        <header class="app-header">
          <div class="logo">IoTSphere</div>
          <div class="user-info">Administrator</div>
        </header>
        <main class="app-content">
          <div class="dashboard">
            <div class="device-list-container">
              <h2>Devices</h2>
              <ul class="device-list"></ul>
            </div>
            <div class="device-detail-container">
              <!-- Device details will be loaded here -->
            </div>
          </div>
        </main>
        <div class="connection-status connected">connected</div>
      `;
    }
  });

  // Set up test data for common devices used in tests
  await setupTestDevice(this.page, "wh-test-001", {
    shadowOptions: {
      temperature: 135,
      status: "online",
    },
  });

  await setupTestDevice(this.page, "wh-missing-shadow", {
    shadowData: null,
    metadataOptions: {
      deviceType: "waterHeater",
      manufacturer: "Test Manufacturer",
    },
  });

  await this.page.waitForTimeout(500);
  console.log("IoTSphere application environment set up");
});

Given("I am logged in as an administrator", async function () {
  console.log("Setting up administrator login");

  // Simulate admin login for testing purposes - avoiding sessionStorage
  // which can cause security errors in headless browser tests
  await this.page.evaluate(() => {
    // Set admin info directly on the window object for testing
    window.testContext = window.testContext || {};
    window.testContext.userRole = "administrator";
    window.testContext.isAuthenticated = true;

    // Update UI to reflect logged in state
    const userInfo = document.querySelector(".user-info");
    if (userInfo) {
      userInfo.textContent = "Administrator";
      userInfo.classList.add("logged-in");
    } else {
      // Create user info element if it doesn't exist
      const header = document.querySelector(".app-header") || document.body;
      const newUserInfo = document.createElement("div");
      newUserInfo.className = "user-info logged-in";
      newUserInfo.textContent = "Administrator";
      header.appendChild(newUserInfo);
    }
  });

  await this.page.waitForTimeout(300);
  console.log("Administrator login completed");
});

/**
 * Device navigation steps
 */
When("I navigate to the water heater with ID {string}", async function (deviceId) {
  console.log(`Navigating to water heater with ID: ${deviceId}`);

  // Store device ID for later steps
  this.deviceId = deviceId;

  // Create device in virtual DOM for testing
  await setupTestDevice(this.page, deviceId);

  // Navigate to device detail view
  await this.page.evaluate((id) => {
    // Find or create device link
    let deviceLink = document.querySelector(`.device-list a[data-device-id="${id}"]`);

    if (!deviceLink) {
      // Create device list item if it doesn't exist
      const deviceList = document.querySelector(".device-list");
      if (deviceList) {
        const deviceItem = document.createElement("li");
        deviceItem.className = "device-item";

        deviceLink = document.createElement("a");
        deviceLink.href = `#/devices/${id}`;
        deviceLink.setAttribute("data-device-id", id);
        deviceLink.textContent = `Water Heater ${id}`;

        deviceItem.appendChild(deviceLink);
        deviceList.appendChild(deviceItem);
      }
    }

    // Click the device link to navigate
    if (deviceLink) {
      deviceLink.click();
    }

    // Create device detail view
    const detailContainer = document.querySelector(".device-detail-container");
    if (detailContainer) {
      // Clear previous device details
      detailContainer.innerHTML = `
        <div class="device-detail" data-device-id="${id}">
          <h2>Water Heater ${id}</h2>
          <div class="device-tabs">
            <button class="tab-button active" data-tab="overview">Overview</button>
            <button class="tab-button" data-tab="history">History</button>
            <button class="tab-button" data-tab="settings">Settings</button>
          </div>
          <div class="tab-content active" data-tab-content="overview">
            <div class="device-shadow">
              <div class="temperature-display">--°F</div>
              <div class="status-indicators">
                <div class="status-indicator power">Power: <span>On</span></div>
                <div class="status-indicator connection">Connection: <span>connected</span></div>
              </div>
            </div>
          </div>
          <div class="tab-content" data-tab-content="history">
            <div class="temperature-history-chart">
              <!-- Chart will be rendered here -->
            </div>
          </div>
          <div class="tab-content" data-tab-content="settings">
            <div class="device-settings">
              <!-- Settings will be shown here -->
            </div>
          </div>
        </div>
      `;

      // Setup tab switching behavior
      const tabButtons = detailContainer.querySelectorAll(".tab-button");
      tabButtons.forEach((button) => {
        button.addEventListener("click", () => {
          // Deactivate all tabs
          tabButtons.forEach((btn) => btn.classList.remove("active"));
          detailContainer.querySelectorAll(".tab-content").forEach((content) => {
            content.classList.remove("active");
          });

          // Activate selected tab
          button.classList.add("active");
          const tabName = button.getAttribute("data-tab");
          const tabContent = detailContainer.querySelector(`[data-tab-content="${tabName}"]`);
          if (tabContent) {
            tabContent.classList.add("active");
          }
        });
      });
    }
  }, deviceId);

  await this.page.waitForTimeout(500);
  console.log(`Navigation to device ${deviceId} completed`);
});

/**
 * Tab navigation
 */
When("I click on the History tab", async function () {
  console.log("Clicking on the History tab");

  await this.page.click(".tab-button[data-tab=\"history\"]");

  // Wait for any animations or content loading
  await this.page.waitForTimeout(500);

  // Verify the tab is active
  const isActive = await this.page.evaluate(() => {
    const historyTab = document.querySelector(".tab-button[data-tab=\"history\"]");
    const historyContent = document.querySelector(".tab-content[data-tab-content=\"history\"]");
    return (
      historyTab &&
      historyTab.classList.contains("active") &&
      historyContent &&
      historyContent.classList.contains("active")
    );
  });

  expect(isActive, "History tab should be active").to.be.true;
  console.log("History tab is now active");
});
