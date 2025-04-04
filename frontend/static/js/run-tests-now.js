/**
 * IMMEDIATE TEST EXECUTION
 * This script will run the tests as soon as it's loaded
 */
console.clear();
console.log('======= RUNNING TESTS NOW =======');

// Create and run test instance immediately
const tester = new AquaThermCardTest();
tester.runTests();

// Also output to the page for visibility
setTimeout(() => {
  const testDiv = document.createElement('div');
  testDiv.id = 'test-results';
  testDiv.style.position = 'fixed';
  testDiv.style.top = '0';
  testDiv.style.left = '0';
  testDiv.style.right = '0';
  testDiv.style.padding = '10px';
  testDiv.style.backgroundColor = 'rgba(0,0,0,0.8)';
  testDiv.style.color = 'white';
  testDiv.style.zIndex = '10000';
  testDiv.innerHTML = '<h3>Running AquaTherm Card Tests...</h3><p>Check console for detailed results</p>';
  document.body.appendChild(testDiv);
}, 500);
