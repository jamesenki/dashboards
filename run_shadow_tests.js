/**
 * Custom test runner for shadow document tests only
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Generate timestamp for unique report filenames
const timestamp = new Date().toISOString().replace(/[:.]/g, '').substring(0, 15);
const reportFile = `shadow_doc_test_${timestamp}.html`;

// Set up paths
const projectRoot = path.resolve(__dirname);
const featurePath = path.join(projectRoot, 'features', 'shadow_document.feature');
const stepDefPath = path.join(projectRoot, 'features', 'step_definitions', 'shadow_document_steps.js');
const worldPath = path.join(projectRoot, 'features', 'support', 'world.js');
const reportPath = path.join(projectRoot, 'test_reports', reportFile);

// Create the world.js file if it doesn't exist
const worldDir = path.join(projectRoot, 'features', 'support');
if (!fs.existsSync(worldDir)) {
  fs.mkdirSync(worldDir, { recursive: true });
}

if (!fs.existsSync(worldPath)) {
  const worldContent = `
  /**
   * Custom world for shadow document tests
   */
  const { setWorldConstructor } = require('@cucumber/cucumber');
  const { chromium } = require('playwright');
  
  // Custom test world with Playwright setup
  class CustomWorld {
    constructor(options) {
      this.parameters = options.parameters;
    }
    
    async init() {
      this.browser = await chromium.launch({ headless: true });
      this.context = await this.browser.newContext();
      this.page = await this.context.newPage();
    }
    
    async navigate(url) {
      const baseUrl = process.env.TEST_APP_URL || 'http://localhost:4200';
      await this.page.goto(\`\${baseUrl}\${url}\`);
    }
    
    async elementExists(selector) {
      const element = await this.page.$(selector);
      return element !== null;
    }
    
    async close() {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }
  
  setWorldConstructor(CustomWorld);
  `;
  
  fs.writeFileSync(worldPath, worldContent);
  console.log(`Created custom world file at ${worldPath}`);
}

// Create hooks.js for browser setup/teardown
const hooksPath = path.join(projectRoot, 'features', 'support', 'hooks.js');
if (!fs.existsSync(hooksPath)) {
  const hooksContent = `
  /**
   * Hooks for shadow document tests
   */
  const { Before, After } = require('@cucumber/cucumber');
  
  // Setup browser before each scenario
  Before(async function() {
    await this.init();
  });
  
  // Close browser after each scenario
  After(async function() {
    await this.close();
  });
  `;
  
  fs.writeFileSync(hooksPath, hooksContent);
  console.log(`Created hooks file at ${hooksPath}`);
}

// Run Cucumber with the specific feature and step definitions
try {
  const command = [
    'npx cucumber-js',
    featurePath,
    '--require', stepDefPath,
    '--require', worldPath,
    '--require', hooksPath,
    '--format', `html:${reportPath}`,
    '--format', 'summary'
  ].join(' ');
  
  console.log(`Running command: ${command}`);
  execSync(command, { stdio: 'inherit' });
  
  console.log(`\nTest execution complete!`);
  console.log(`Report saved to: ${reportPath}`);
} catch (error) {
  console.error('Test execution failed:', error.message);
  process.exit(1);
}
