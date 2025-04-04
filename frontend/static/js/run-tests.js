/**
 * Test Runner - Manually executes the AquaTherm card tests
 * Following TDD principles: Red → Green → Refactor
 */
console.log('======= MANUAL TEST EXECUTION =======');
console.log('Running AquaTherm card tests...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
  // Wait a bit for all data to load
  setTimeout(function() {
    console.log('======= STARTING TESTS =======');

    // Create and run test instance
    const tester = new AquaThermCardTest();
    tester.runTests();

    console.log('Tests complete - check results above');
  }, 2000);
});

// Also run if DOM is already loaded
if (document.readyState !== 'loading') {
  setTimeout(function() {
    console.log('DOM already loaded, running tests now...');
    const tester = new AquaThermCardTest();
    tester.runTests();
  }, 2000);
}
