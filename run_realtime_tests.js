/**
 * Test runner for real-time updates tests
 * Following TDD principles - we set up proper testing infrastructure first
 */
const fs = require('fs');
const path = require('path');

/**
 * Create Cucumber configuration for running only real-time updates tests
 */
function createTemporaryConfig() {
  // Create a cucumber.js config file that targets only our real-time updates feature
  const config = {
    default: {
      paths: ['./features/realtime_updates.feature'],
      require: [
        './features/support/world.js',
        './features/support/hooks.js',
        './features/step_definitions/shadow_document_steps.js', // We reuse some steps
        './features/step_definitions/realtime_updates_steps.js'
      ],
      format: [
        'progress',
        `html:test_reports/realtime_test_${new Date().toISOString().replace(/:/g, '').replace(/\..+/, '')}.html`
      ]
    }
  };

  // Write configuration to cucumber.js file
  fs.writeFileSync(
    path.join(__dirname, 'cucumber.js'),
    `module.exports = ${JSON.stringify(config, null, 2)};`
  );
  
  console.log('Cucumber configuration created for real-time tests');
}

/**
 * Run the tests using the cucumber command
 */
function runTests() {
  const { execSync } = require('child_process');
  console.log('Running real-time update tests...');
  
  try {
    // Execute cucumber-js with our configuration
    execSync('npx cucumber-js --profile default', { stdio: 'inherit' });
    console.log('Tests completed successfully');
  } catch (error) {
    console.error('Error running tests:', error.message);
    process.exit(1);
  }
}

/**
 * Clean up by removing the temporary config
 */
function cleanup() {
  try {
    fs.unlinkSync(path.join(__dirname, 'cucumber.js'));
    console.log('Temporary configuration removed');
  } catch (error) {
    console.error('Error cleaning up:', error.message);
  }
}

// Main execution
try {
  createTemporaryConfig();
  runTests();
} finally {
  cleanup();
}
