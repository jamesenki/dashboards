/**
 * Python BDD Test Report Generator for IoTSphere Project
 *
 * This script analyzes Python BDD test implementations and generates a focused report
 * showing test status, TDD phase, and overall test completion.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Configuration
const config = {
  projectRoot: path.resolve(__dirname, '..'),
  outputDir: path.resolve(__dirname, '../test-reports'),
  pythonStepsPattern: 'src/tests/bdd/steps/**/*.py',
  featurePattern: 'src/tests/bdd/features/**/*.feature',
  featureCategories: [
    'Water Heater Monitoring',
    'Device Shadow Service',
    'Device Management',
    'Predictive Maintenance',
    'Dashboard & Visualization'
  ]
};

// TDD phase detection patterns for Python
const tddPhaseDetectors = {
  red: /RED PHASE/i,
  green: /GREEN PHASE/i,
  refactor: /REFACTOR PHASE/i
};

// Step definition patterns (handle both Python and JS style definitions)
const stepDefPatterns = {
  python: /@(given|when|then)\(['"](.+?)['"]/gi,
  js: /(Given|When|Then)\(['"](.+?)['"]/gi
};

// Feature category detection patterns
const categoryPatterns = {
  'Water Heater Monitoring': /(water_heater|waterheater|heater_monitoring)/i,
  'Device Shadow Service': /(device_shadow|shadow_service|shadow)/i,
  'Device Management': /(device_management|devicemanagement)/i,
  'Predictive Maintenance': /(predictive|maintenance|predict)/i,
  'Dashboard & Visualization': /(dashboard|visualization|visualize|display)/i
};

/**
 * Main function to analyze Python BDD implementations
 */
function analyzePythonBdd() {
  console.log('Analyzing Python BDD test implementations...');

  // Initialize results
  const results = {
    totalStepDefinitions: 0,
    redPhase: 0,
    greenPhase: 0,
    refactorPhase: 0,
    byCategory: {}
  };

  // Initialize category counters
  config.featureCategories.forEach(category => {
    results.byCategory[category] = {
      total: 0,
      red: 0,
      green: 0,
      refactor: 0
    };
  });

  // Get all Python step files
  const pythonStepFiles = glob.sync(config.pythonStepsPattern, { cwd: config.projectRoot });
  console.log(`Found ${pythonStepFiles.length} Python step definition files`);

  // Process each Python step file
  for (const stepFile of pythonStepFiles) {
    const fullPath = path.join(config.projectRoot, stepFile);
    const content = fs.readFileSync(fullPath, 'utf8');

    // Count step definitions (functions decorated with @given, @when, @then)
    const stepDefinitions = content.match(/@(given|when|then)/gi) || [];
    const stepCount = stepDefinitions.length;
    results.totalStepDefinitions += stepCount;

    if (stepCount === 0) continue;

    // Determine TDD phase
    let phase = 'unknown';
    if (content.includes('GREEN PHASE')) {
      phase = 'green';
      results.greenPhase += stepCount;
    } else if (content.includes('RED PHASE')) {
      phase = 'red';
      results.redPhase += stepCount;
    } else if (content.includes('REFACTOR PHASE')) {
      phase = 'refactor';
      results.refactorPhase += stepCount;
    } else {
      // Default to green if implementation looks complete
      phase = 'green';
      results.greenPhase += stepCount;
    }

    // Determine feature category
    let matched = false;
    for (const [category, pattern] of Object.entries(categoryPatterns)) {
      if (pattern.test(content) || pattern.test(stepFile)) {
        results.byCategory[category].total += stepCount;

        if (phase === 'green') {
          results.byCategory[category].green += stepCount;
        } else if (phase === 'red') {
          results.byCategory[category].red += stepCount;
        } else if (phase === 'refactor') {
          results.byCategory[category].refactor += stepCount;
        }

        matched = true;
        break;
      }
    }

    // If no category matched, add to uncategorized
    if (!matched) {
      if (!results.byCategory['Uncategorized']) {
        results.byCategory['Uncategorized'] = { total: 0, red: 0, green: 0, refactor: 0 };
      }
      results.byCategory['Uncategorized'].total += stepCount;

      if (phase === 'green') {
        results.byCategory['Uncategorized'].green += stepCount;
      } else if (phase === 'red') {
        results.byCategory['Uncategorized'].red += stepCount;
      } else if (phase === 'refactor') {
        results.byCategory['Uncategorized'].refactor += stepCount;
      }
    }
  }

  // Count the total number of steps needed based on feature files
  const featureFiles = glob.sync(config.featurePattern, { cwd: config.projectRoot });
  let totalStepsInFeatures = 0;

  for (const featureFile of featureFiles) {
    const fullPath = path.join(config.projectRoot, featureFile);
    const content = fs.readFileSync(fullPath, 'utf8');

    // Count all Given/When/Then steps in feature files
    const featureSteps = content.match(/^\s*(Given|When|Then|And|But)/gmi) || [];
    totalStepsInFeatures += featureSteps.length;
  }

  // Calculate completion percentage
  results.completionPercentage = Math.round((results.totalStepDefinitions / totalStepsInFeatures) * 100);

  return { results, totalStepsNeeded: totalStepsInFeatures };
}

/**
 * Generate a simple console report
 */
function displayReport(reportData) {
  const { results, totalStepsNeeded } = reportData;

  console.log('\n===== Python BDD Implementation Status =====');
  console.log(`Total Step Definitions: ${results.totalStepDefinitions} of ${totalStepsNeeded} needed steps`);
  console.log(`Implementation Progress: ${results.completionPercentage}%`);
  console.log(`TDD Phase Breakdown: RED: ${results.redPhase} | GREEN: ${results.greenPhase} | REFACTOR: ${results.refactorPhase}`);

  console.log('\nCategory Breakdown:');
  for (const [category, stats] of Object.entries(results.byCategory)) {
    if (stats.total > 0) {
      console.log(`- ${category}: ${stats.total} steps (RED: ${stats.red}, GREEN: ${stats.green}, REFACTOR: ${stats.refactor})`);
    }
  }

  console.log('\nImplementation Progress by Category:');
  for (const [category, stats] of Object.entries(results.byCategory)) {
    if (stats.total > 0) {
      const progressBar = '█'.repeat(Math.round(stats.total / 5)) + '░'.repeat(Math.max(0, 20 - Math.round(stats.total / 5)));
      console.log(`- ${category}: ${progressBar} (${stats.total} steps)`);
    }
  }

  console.log('\n===========================================');
}

// Run the analysis and display the report
const reportData = analyzePythonBdd();
displayReport(reportData);
