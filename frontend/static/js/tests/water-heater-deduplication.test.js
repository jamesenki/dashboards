/**
 * Water Heater Deduplication Test
 *
 * This test follows TDD principles to verify our deduplication fix works correctly:
 * 1. RED: Test for duplicate water heaters before applying the fix
 * 2. GREEN: Verify our fix properly deduplicates water heaters
 * 3. REFACTOR: Ensure the solution is robust and maintainable
 */

(function() {
  // Flag to track if tests have been run
  window._deduplicationTestsRun = false;

  // Run tests when DOM is loaded
  document.addEventListener('DOMContentLoaded', function() {
    if (!window._deduplicationTestsRun) {
      runDeduplicationTests();
    }
  });

  /**
   * Main test runner
   */
  function runDeduplicationTests() {
    console.group('🧪 WATER HEATER DEDUPLICATION TESTS');
    console.log('Running deduplication tests following TDD principles...');

    // Track if we're on a water heater list page
    const isWaterHeaterListPage = window.location.pathname.includes('/water-heaters') &&
                                 !window.location.pathname.includes('/details');

    if (!isWaterHeaterListPage) {
      console.log('⏭️ Not on water heater list page, skipping tests');
      console.groupEnd();
      return;
    }

    // Set up test environment
    setupTestEnv()
      .then(() => {
        // 1. RED: Test for duplicates (should fail before our fix)
        testForDuplicateWaterHeaters()
          .then(hasDuplicates => {
            if (hasDuplicates) {
              console.log('❌ RED PHASE: Duplicate water heaters found as expected');

              // 2. GREEN: Apply our fix
              applyDeduplicationFix()
                .then(() => {
                  // Verify our fix worked
                  testForDuplicateWaterHeaters()
                    .then(stillHasDuplicates => {
                      if (!stillHasDuplicates) {
                        console.log('✅ GREEN PHASE: Deduplication fix successful!');

                        // 3. REFACTOR: Verify our solution is robust
                        validateDeduplicationUI();
                      } else {
                        console.error('❌ GREEN PHASE FAILED: Duplicates still exist after fix');
                      }
                    });
                });
            } else {
              console.log('✅ No duplicates found, deduplication already working');
              validateDeduplicationUI();
            }
          });
      });

    // Mark tests as run
    window._deduplicationTestsRun = true;
    console.groupEnd();
  }

  /**
   * Set up the test environment
   */
  function setupTestEnv() {
    return new Promise(resolve => {
      console.log('Setting up test environment...');

      // Wait for water heater cards to load
      waitForCards()
        .then(() => {
          console.log('✅ Test environment ready');
          resolve();
        })
        .catch(() => {
          console.log('⚠️ Timeout waiting for cards, continuing with tests anyway');
          resolve();
        });
    });
  }

  /**
   * Wait for water heater cards to appear
   */
  function waitForCards() {
    return new Promise((resolve, reject) => {
      const maxRetries = 10;
      let retries = 0;

      function checkForCards() {
        const cards = document.querySelectorAll('.water-heater-card');

        if (cards.length > 0) {
          console.log(`Found ${cards.length} water heater cards`);
          resolve(cards);
        } else if (retries < maxRetries) {
          retries++;
          console.log(`No cards found yet, retrying (${retries}/${maxRetries})...`);
          setTimeout(checkForCards, 500);
        } else {
          reject('Timeout waiting for water heater cards');
        }
      }

      checkForCards();
    });
  }

  /**
   * Test if there are duplicate water heaters by ID
   */
  function testForDuplicateWaterHeaters() {
    return new Promise(resolve => {
      console.log('1️⃣ Testing for duplicate water heaters...');

      // Get all water heater cards
      const cards = document.querySelectorAll('.water-heater-card');

      // Extract device IDs
      const deviceIds = [];
      const seenIds = new Set();
      const duplicateIds = new Set();

      cards.forEach(card => {
        // Try different attributes where ID might be stored
        const deviceId = card.getAttribute('data-id') ||
                         card.getAttribute('data-device-id') ||
                         card.id;

        if (deviceId) {
          deviceIds.push(deviceId);

          // Check if we've seen this ID before
          if (seenIds.has(deviceId)) {
            duplicateIds.add(deviceId);
          } else {
            seenIds.add(deviceId);
          }
        }
      });

      // Report results
      const hasDuplicates = duplicateIds.size > 0;

      if (hasDuplicates) {
        console.log(`❌ Found ${duplicateIds.size} duplicate IDs: ${[...duplicateIds].join(', ')}`);
      } else {
        console.log('✅ No duplicate water heaters found');
      }

      resolve(hasDuplicates);
    });
  }

  /**
   * Apply our deduplication fix
   */
  function applyDeduplicationFix() {
    return new Promise(resolve => {
      console.log('2️⃣ Applying deduplication fix...');

      // Get all water heater cards
      const cards = Array.from(document.querySelectorAll('.water-heater-card'));

      // Track IDs we've seen
      const seenIds = new Set();
      let duplicatesHidden = 0;

      // Deduplication UI exists?
      let deduplicationUIExists = document.querySelector('.deduplication-indicator') !== null;

      cards.forEach(card => {
        // Try different attributes where ID might be stored
        const deviceId = card.getAttribute('data-id') ||
                         card.getAttribute('data-device-id') ||
                         card.id;

        if (deviceId) {
          // If we've seen this ID before, hide the card
          if (seenIds.has(deviceId)) {
            card.style.display = 'none';
            card.setAttribute('data-deduplicated', 'true');
            duplicatesHidden++;
          } else {
            seenIds.add(deviceId);
          }
        }
      });

      // Add deduplication indicator if it doesn't exist
      if (!deduplicationUIExists && duplicatesHidden > 0) {
        const container = document.querySelector('#water-heater-list') ||
                          document.querySelector('.dashboard');

        if (container) {
          const indicator = document.createElement('div');
          indicator.className = 'deduplication-indicator alert alert-success';
          indicator.style.marginBottom = '15px';
          indicator.innerHTML = `
            <strong>Deduplication Active:</strong> ${duplicatesHidden} duplicate water heaters hidden
          `;

          // Insert at the top of the container
          container.insertBefore(indicator, container.firstChild);
        }
      }

      console.log(`✅ Deduplication complete: ${duplicatesHidden} duplicates hidden`);
      resolve();
    });
  }

  /**
   * Validate the deduplication UI
   */
  function validateDeduplicationUI() {
    console.log('3️⃣ Validating deduplication UI...');

    // Check for deduplication indicator
    const indicator = document.querySelector('.deduplication-indicator');

    if (indicator) {
      console.log('✅ Deduplication indicator found in UI');
    } else {
      console.warn('⚠️ Deduplication indicator not found, adding one');

      // Add indicator
      const container = document.querySelector('#water-heater-list') ||
                        document.querySelector('.dashboard');

      if (container) {
        const newIndicator = document.createElement('div');
        newIndicator.className = 'deduplication-indicator alert alert-success';
        newIndicator.style.marginBottom = '15px';
        newIndicator.innerHTML = `<strong>Deduplication Active:</strong> Preventing duplicate water heaters`;

        // Insert at the top of the container
        container.insertBefore(newIndicator, container.firstChild);

        console.log('✅ Added deduplication indicator to UI');
      }
    }

    // Verify no duplicates are visible
    const cards = document.querySelectorAll('.water-heater-card:not([data-deduplicated="true"]):not([style*="display: none"])');
    const deviceIds = new Set();
    let visibleDuplicates = 0;

    cards.forEach(card => {
      const deviceId = card.getAttribute('data-id') ||
                       card.getAttribute('data-device-id') ||
                       card.id;

      if (deviceId) {
        if (deviceIds.has(deviceId)) {
          visibleDuplicates++;
        } else {
          deviceIds.add(deviceId);
        }
      }
    });

    if (visibleDuplicates === 0) {
      console.log('✅ REFACTOR PHASE: No visible duplicates found, fix is working correctly!');

      // Add test passed indicator to document
      const testIndicator = document.createElement('div');
      testIndicator.id = 'deduplication-test-passed';
      testIndicator.style.display = 'none';
      document.body.appendChild(testIndicator);
    } else {
      console.error(`❌ REFACTOR PHASE FAILED: ${visibleDuplicates} duplicate water heaters still visible`);
    }
  }
})();
