/**
 * Simple HTML Structure Check - Verify cards are structured correctly
 *
 * Following TDD principles - checking if the implementation matches the expected structure
 */

const puppeteer = require('puppeteer');

async function checkCardStructure() {
  console.log('====== CHECKING CARD HTML STRUCTURE ======\n');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Navigate to water heaters page
    console.log('1. Navigating to water heaters page...');
    await page.goto('http://localhost:8006/water-heaters', {
      timeout: 10000,
      waitUntil: 'networkidle0'
    });

    // Check regular water heater card structure
    console.log('\n2. Checking structure of regular water heater card...');
    const regularCardStructure = await page.evaluate(() => {
      const regularCards = Array.from(document.querySelectorAll('.heater-card:not(.aquatherm-heater)'));
      if (regularCards.length === 0) return null;

      const card = regularCards[0];
      const cardId = card.getAttribute('data-id');
      const isWrappedInAnchor = card.parentElement.tagName === 'A';
      const anchorHref = isWrappedInAnchor ? card.parentElement.getAttribute('href') : null;
      const hasOnClick = card.hasAttribute('onclick');
      const onClickValue = hasOnClick ? card.getAttribute('onclick').substring(0, 50) + '...' : '';

      return {
        cardId,
        isWrappedInAnchor,
        anchorHref,
        hasOnClick,
        onClickValue,
        parentNodeType: card.parentElement.tagName
      };
    });

    if (regularCardStructure) {
      console.log('Regular card structure:');
      console.log(JSON.stringify(regularCardStructure, null, 2));

      if (regularCardStructure.isWrappedInAnchor) {
        console.log('✅ Regular card is properly wrapped in anchor tag');
      } else {
        console.log('❌ Regular card is NOT properly wrapped in anchor tag');
      }
    } else {
      console.log('No regular water heater cards found');
    }

    // Check AquaTherm card structure
    console.log('\n3. Checking structure of AquaTherm water heater card...');
    const aquaThermCardStructure = await page.evaluate(() => {
      const aquaThermCards = Array.from(document.querySelectorAll('.aquatherm-heater'));
      if (aquaThermCards.length === 0) return null;

      const card = aquaThermCards[0];
      const cardId = card.getAttribute('data-id');
      const isWrappedInAnchor = card.parentElement.tagName === 'A';
      const anchorHref = isWrappedInAnchor ? card.parentElement.getAttribute('href') : null;
      const hasOnClick = card.hasAttribute('onclick');
      const onClickValue = hasOnClick ? card.getAttribute('onclick').substring(0, 50) + '...' : '';

      // Get full node structure
      let structure = '';
      let node = card;
      while (node && node.tagName !== 'BODY') {
        structure = node.tagName + (structure ? ' > ' + structure : '');
        node = node.parentElement;
      }

      return {
        cardId,
        isWrappedInAnchor,
        anchorHref,
        hasOnClick,
        onClickValue,
        nodeStructure: structure,
        parentNodeType: card.parentElement.tagName
      };
    });

    if (aquaThermCardStructure) {
      console.log('AquaTherm card structure:');
      console.log(JSON.stringify(aquaThermCardStructure, null, 2));

      if (aquaThermCardStructure.isWrappedInAnchor) {
        console.log('✅ AquaTherm card is properly wrapped in anchor tag');
      } else {
        console.log('❌ AquaTherm card is NOT properly wrapped in anchor tag');
      }
    } else {
      console.log('No AquaTherm water heater cards found');
    }

    // Compare implementations
    if (regularCardStructure && aquaThermCardStructure) {
      console.log('\n4. Comparing implementations...');

      if (regularCardStructure.isWrappedInAnchor === aquaThermCardStructure.isWrappedInAnchor) {
        console.log('✅ Both card types have the same anchor wrapping implementation');
      } else {
        console.log('❌ Cards have different anchor wrapping implementations');
      }

      if (regularCardStructure.hasOnClick === aquaThermCardStructure.hasOnClick) {
        console.log('✅ Both card types have the same onclick attribute implementation');
      } else {
        console.log('❌ Cards have different onclick attribute implementations');
      }
    }

  } catch (error) {
    console.log(`\n❌ TEST EXECUTION ERROR: ${error.message}`);
  } finally {
    await browser.close();
  }
}

// Run the check
checkCardStructure();
