/**
 * Comprehensive AquaTherm Water Heater Tests
 * Following TDD principles, these tests verify:
 * 1. ALL entries conform to Rheem/AquaTherm models
 * 2. ALL entries are recognized as AquaTherm and properly displayed
 * 3. ALL cards have proper click navigation to their detail pages
 */

const puppeteer = require('puppeteer');

/**
 * Tests to verify AquaTherm water heater integration
 */
class AquaThermTests {
  async runAllTests() {
    console.log('=================================================================');
    console.log('STARTING COMPREHENSIVE AQUATHERM WATER HEATER TESTS');
    console.log('=================================================================');

    // Launch browser for tests
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox']
    });

    try {
      // Run tests in sequence
      await this.testDatabaseEntries();
      await this.testAllCardsAreAquaTherm();
      await this.testCardStylingConsistency();
      await this.testCardClickNavigation();

      console.log('=================================================================');
      console.log('ALL TESTS COMPLETED');
    } catch (error) {
      console.error('TEST EXECUTION FAILED:', error);
    } finally {
      // Cleanup
      await this.browser.close();
    }
  }

  /**
   * Test 1: Verify all database entries conform to Rheem/AquaTherm models
   */
  async testDatabaseEntries() {
    console.log('\n1. TESTING DATABASE ENTRIES CONFORM TO RHEEM/AQUATHERM MODELS');

    const page = await this.browser.newPage();
    try {
      // Fetch all water heaters from API
      await page.goto('http://localhost:8006/api/water-heaters');

      // Get API response
      const apiResponse = await page.evaluate(() => {
        return document.querySelector('pre').textContent;
      });

      const waterHeaters = JSON.parse(apiResponse);
      console.log(`Found ${waterHeaters.length} total water heaters in database`);

      // Check each water heater for AquaTherm/Rheem values
      const nonAquathermHeaters = [];

      waterHeaters.forEach(heater => {
        const manufacturerCheck = heater.manufacturer &&
          (heater.manufacturer.toLowerCase().includes('aqua') ||
           heater.manufacturer.toLowerCase().includes('therm') ||
           heater.manufacturer.toLowerCase().includes('rheem'));

        const modelCheck = heater.model &&
          (heater.model.toLowerCase().includes('aqua') ||
           heater.model.toLowerCase().includes('therm') ||
           heater.model.toLowerCase().includes('rheem'));

        const idCheck = heater.id &&
          (heater.id.toLowerCase().includes('aqua') ||
           heater.id.toLowerCase().includes('rheem'));

        // If it doesn't pass any check, it's not an AquaTherm/Rheem
        if (!manufacturerCheck && !modelCheck && !idCheck) {
          nonAquathermHeaters.push({
            id: heater.id,
            manufacturer: heater.manufacturer,
            model: heater.model
          });
        }
      });

      // Report results
      if (nonAquathermHeaters.length > 0) {
        console.log(`❌ FAILED: Found ${nonAquathermHeaters.length} non-AquaTherm water heaters in database`);
        nonAquathermHeaters.forEach(heater => {
          console.log(`  - ID: ${heater.id}, Manufacturer: ${heater.manufacturer}, Model: ${heater.model}`);
        });
      } else {
        console.log(`✅ PASSED: All ${waterHeaters.length} water heaters in database conform to Rheem/AquaTherm models`);
      }
    } catch (error) {
      console.error('❌ ERROR testing database entries:', error);
    } finally {
      await page.close();
    }
  }

  /**
   * Test 2: Verify ALL cards are identified as AquaTherm
   */
  async testAllCardsAreAquaTherm() {
    console.log('\n2. TESTING ALL CARDS ARE RECOGNIZED AS AQUATHERM');

    const page = await this.browser.newPage();
    try {
      // Load water heaters page
      await page.goto('http://localhost:8006/water-heaters');
      await page.waitForSelector('.heater-card');

      // Count all cards vs AquaTherm cards
      const counts = await page.evaluate(() => {
        const allCards = document.querySelectorAll('.heater-card');
        const aquathermCards = document.querySelectorAll('.heater-card.aquatherm-heater');

        // Count cards by type
        const cardTypes = {};
        allCards.forEach(card => {
          const isAquatherm = card.classList.contains('aquatherm-heater');
          const id = card.getAttribute('data-id') || card.id;
          const manufacturer = card.querySelector('.manufacturer')?.textContent || 'Unknown';
          const model = card.querySelector('.model-name')?.textContent || 'Unknown';

          if (!isAquatherm) {
            cardTypes[id] = { id, manufacturer, model, classes: card.className };
          }
        });

        return {
          total: allCards.length,
          aquatherm: aquathermCards.length,
          nonAquathermCards: Object.values(cardTypes)
        };
      });

      // Report results
      if (counts.total !== counts.aquatherm) {
        console.log(`❌ FAILED: Only ${counts.aquatherm} out of ${counts.total} cards are recognized as AquaTherm`);
        console.log('Non-AquaTherm cards:');
        counts.nonAquathermCards.forEach(card => {
          console.log(`  - ID: ${card.id}, Manufacturer: ${card.manufacturer}, Model: ${card.model}`);
          console.log(`    Classes: ${card.classes}`);
        });
      } else {
        console.log(`✅ PASSED: All ${counts.total} cards are correctly recognized as AquaTherm`);
      }
    } catch (error) {
      console.error('❌ ERROR testing card recognition:', error);
    } finally {
      await page.close();
    }
  }

  /**
   * Test 3: Verify all AquaTherm cards have consistent styling
   */
  async testCardStylingConsistency() {
    console.log('\n3. TESTING CARD STYLING CONSISTENCY');

    const page = await this.browser.newPage();
    try {
      // Load water heaters page
      await page.goto('http://localhost:8006/water-heaters');
      await page.waitForSelector('.heater-card');

      // Check styling consistency
      const stylingResults = await page.evaluate(() => {
        const cards = document.querySelectorAll('.heater-card');

        // Collect style information
        const styles = {
          backgrounds: new Set(),
          borders: new Set(),
          headerBackgrounds: new Set(),
          inconsistentCards: []
        };

        // Expected values
        const expectedBackground = 'rgb(30, 34, 39)';
        const expectedBorder = 'rgb(0, 160, 176)';
        const expectedHeaderBg = 'rgb(40, 44, 52)';

        cards.forEach(card => {
          const cardStyle = window.getComputedStyle(card);
          const headerStyle = window.getComputedStyle(card.querySelector('.card-header'));
          const id = card.getAttribute('data-id') || card.id;

          // Store all observed styles
          styles.backgrounds.add(cardStyle.backgroundColor);

          // Borders can be complex, so we check if it contains our color
          const hasBorderColor = cardStyle.borderLeftColor === expectedBorder ||
                                 cardStyle.borderLeft.includes(expectedBorder);
          if (!hasBorderColor) {
            styles.borders.add(cardStyle.borderLeft);
          }

          styles.headerBackgrounds.add(headerStyle.backgroundColor);

          // Check if inconsistent
          if (cardStyle.backgroundColor !== expectedBackground ||
              !hasBorderColor ||
              headerStyle.backgroundColor !== expectedHeaderBg) {
            styles.inconsistentCards.push({
              id,
              backgroundColor: cardStyle.backgroundColor,
              borderLeft: cardStyle.borderLeft,
              headerBg: headerStyle.backgroundColor
            });
          }
        });

        return {
          totalCards: cards.length,
          uniqueBackgrounds: [...styles.backgrounds],
          uniqueBorders: [...styles.borders],
          uniqueHeaderBgs: [...styles.headerBackgrounds],
          inconsistentCount: styles.inconsistentCards.length,
          inconsistentCards: styles.inconsistentCards
        };
      });

      // Report results
      if (stylingResults.inconsistentCount > 0) {
        console.log(`❌ FAILED: Found ${stylingResults.inconsistentCount} cards with inconsistent styling`);
        console.log(`  - Unique backgrounds: ${stylingResults.uniqueBackgrounds.join(', ')}`);
        console.log(`  - Unique borders: ${stylingResults.uniqueBorders.join(', ')}`);
        console.log(`  - Unique header backgrounds: ${stylingResults.uniqueHeaderBgs.join(', ')}`);

        stylingResults.inconsistentCards.forEach(card => {
          console.log(`  - Card ${card.id}:`);
          console.log(`    Background: ${card.backgroundColor}`);
          console.log(`    Border: ${card.borderLeft}`);
          console.log(`    Header: ${card.headerBg}`);
        });
      } else {
        console.log(`✅ PASSED: All ${stylingResults.totalCards} cards have consistent styling`);
        console.log(`  - Background: ${stylingResults.uniqueBackgrounds[0]}`);
        console.log(`  - Header background: ${stylingResults.uniqueHeaderBgs[0]}`);
      }
    } catch (error) {
      console.error('❌ ERROR testing styling consistency:', error);
    } finally {
      await page.close();
    }
  }

  /**
   * Test 4: Verify clicking on cards navigates to details page
   * NO SHORTCUTS: This test actually clicks the cards and verifies navigation
   * Shows every single card that fails to navigate correctly
   */
  async testCardClickNavigation() {
    console.log('\n4. TESTING CARD CLICK NAVIGATION TO DETAILS PAGE');

    // Use a standard page for testing
    const page = await this.browser.newPage();

    try {
      // Load water heaters page
      await page.goto('http://localhost:8006/water-heaters');
      await page.waitForSelector('.heater-card');

      // Get all cards with their complete details
      const cardDetails = await page.evaluate(() => {
        const cards = document.querySelectorAll('.heater-card');
        return Array.from(cards).map(card => {
          const id = card.getAttribute('data-id') || card.id;
          const isAquaTherm = card.classList.contains('aquatherm-heater');
          const model = card.querySelector('.model-name')?.textContent || 'Unknown';
          const manufacturer = card.querySelector('.manufacturer')?.textContent || 'Unknown';
          const name = card.querySelector('.card-title')?.textContent || 'Unknown';

          return {
            id,
            isAquaTherm,
            model,
            manufacturer,
            name,
            expectedUrl: `/water-heaters/${id}`
          };
        });
      });

      console.log(`Found ${cardDetails.length} cards to test for click navigation`);

      // Keep track of overall test results
      const results = {
        tested: 0,
        passed: 0,
        failed: 0,
        failedCards: []
      };

      // Test each card one by one to avoid interference
      for (let i = 0; i < cardDetails.length; i++) {
        const card = cardDetails[i];
        results.tested++;

        console.log(`\nTesting card ${i+1}/${cardDetails.length}: ${card.id} (${card.isAquaTherm ? 'AquaTherm' : 'Non-AquaTherm'})`);

        try {
          // For each card test, start with a fresh page
          await page.goto('http://localhost:8006/water-heaters');
          await page.waitForSelector('.heater-card');

          // FIRST TEST: Verify card exists and has onclick attribute
          const onclickCheck = await page.evaluate((cardId) => {
            const card = document.querySelector(`.heater-card[data-id="${cardId}"]`);
            if (!card) return { exists: false };

            const onclick = card.getAttribute('onclick');
            return {
              exists: true,
              hasOnclick: !!onclick,
              onclickContent: onclick || ''
            };
          }, card.id);

          if (!onclickCheck.exists) {
            results.failed++;
            results.failedCards.push({
              id: card.id,
              reason: 'Card not found in DOM'
            });
            console.error(`  ❌ Card ${card.id} not found in DOM`);
            continue;
          }

          if (!onclickCheck.hasOnclick) {
            results.failed++;
            results.failedCards.push({
              id: card.id,
              reason: 'No onclick attribute'
            });
            console.error(`  ❌ Card ${card.id} has no onclick attribute`);
            continue;
          }

          // Check if onclick contains the correct URL
          const hasCorrectUrl = onclickCheck.onclickContent.includes(card.expectedUrl);
          if (!hasCorrectUrl) {
            results.failed++;
            results.failedCards.push({
              id: card.id,
              reason: `Onclick doesn't contain expected URL: ${card.expectedUrl}`
            });
            console.error(`  ❌ Card ${card.id} onclick doesn't contain expected URL: ${card.expectedUrl}`);
            console.error(`  Found onclick: ${onclickCheck.onclickContent.substring(0, 100)}...`);
            continue;
          }

          // SECOND TEST: Actually click the card and check if it navigates
          console.log(`  Card has correct onclick attribute with URL: ${card.expectedUrl}`);

          // Set up navigation listener
          let didNavigate = false;
          let navigationError = null;

          // We need to listen for both navigation events and potential console errors
          page.on('console', msg => {
            if (msg.type() === 'error' && msg.text().includes('TypeError:')) {
              navigationError = msg.text();
            }
          });

          // We'll try multiple approaches to test navigation

          // APPROACH 1: Try intercepting the click and navigation
          await page.setRequestInterception(true);

          // Set up request interceptor to detect navigation without actually navigating
          const interceptPromise = new Promise((resolve) => {
            let interceptListener = null;

            interceptListener = request => {
              const url = request.url();

              if (url.includes(card.expectedUrl)) {
                didNavigate = true;
                request.abort();
                page.off('request', interceptListener);
                resolve(true);
              } else {
                request.continue();
              }
            };

            page.on('request', interceptListener);

            // Set timeout in case no navigation happens
            setTimeout(() => {
              page.off('request', interceptListener);
              resolve(false);
            }, 1000);
          });

          // Try clicking the card
          try {
            await page.click(`.heater-card[data-id="${card.id}"]`);
          } catch (clickError) {
            navigationError = `Failed to click card: ${clickError.message}`;
          }

          // Wait for interception result
          await interceptPromise;

          // Disable request interception
          await page.setRequestInterception(false);

          // Now report results for this card
          if (didNavigate) {
            results.passed++;
            console.log(`  ✅ Successfully detected navigation to ${card.expectedUrl}`);
          } else {
            results.failed++;

            const reason = navigationError ?
              `Navigation error: ${navigationError}` :
              'Click did not trigger navigation';

            results.failedCards.push({
              id: card.id,
              reason,
              isAquaTherm: card.isAquaTherm
            });

            console.error(`  ❌ ${reason}`);
          }

        } catch (error) {
          results.failed++;
          results.failedCards.push({
            id: card.id,
            reason: `Test error: ${error.message}`,
            isAquaTherm: card.isAquaTherm
          });
          console.error(`  ❌ Test error for card ${card.id}: ${error.message}`);
        }
      }

      // Show detailed breakdown of failures by card type
      const aquathermFailures = results.failedCards.filter(card => card.isAquaTherm).length;
      const nonAquathermFailures = results.failedCards.filter(card => !card.isAquaTherm).length;

      console.log('\n----- CARD NAVIGATION TEST SUMMARY -----');

      if (results.failed > 0) {
        console.log(`\n❌ FAILED: ${results.failed} out of ${results.tested} cards have navigation issues`);
        console.log(`  • ${aquathermFailures} AquaTherm cards failed`);
        console.log(`  • ${nonAquathermFailures} non-AquaTherm cards failed`);
        console.log('\nDetailed failures:');

        results.failedCards.forEach(card => {
          console.log(`  - Card ${card.id} (${card.isAquaTherm ? 'AquaTherm' : 'Non-AquaTherm'}): ${card.reason}`);
        });
      } else {
        console.log(`\n✅ PASSED: All ${results.tested} cards have proper click navigation to detail pages`);
      }

      return results;
    } catch (error) {
      console.error('❌ ERROR testing card navigation:', error);
      return { tested: 0, passed: 0, failed: 1, failedCards: [{ id: 'test', reason: error.message }] };
    } finally {
      // Clean up
      try {
        await page.close();
      } catch (e) {
        console.error('Error closing page:', e.message);
      }
    }
  }
}

// Run all tests when executed directly
if (require.main === module) {
  const tester = new AquaThermTests();
  tester.runAllTests();
}

module.exports = AquaThermTests;
