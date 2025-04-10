/**
 * Python BDD Test Report Generator for IoTSphere Project (v2)
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

// Color functions for console output
const color = {
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  magenta: (text) => `\x1b[35m${text}\x1b[0m`,
  cyan: (text) => `\x1b[36m${text}\x1b[0m`,
  bold: (text) => `\x1b[1m${text}\x1b[0m`
};

/**
 * Main function to analyze Python BDD implementations
 */
function analyzePythonBdd() {
  console.log(color.bold('Analyzing Python BDD test implementations...'));

  // Initialize results
  const results = {
    totalStepDefinitions: 0,
    redPhase: 0,
    greenPhase: 0,
    refactorPhase: 0,
    unknownPhase: 0,
    byCategory: {},
    stepDefinitions: [] // Store all step definitions for reporting
  };

  // Initialize category counters
  config.featureCategories.forEach(category => {
    results.byCategory[category] = {
      total: 0,
      red: 0,
      green: 0,
      refactor: 0,
      unknown: 0
    };
  });

  // Get all Python step files
  const pythonStepFiles = glob.sync(config.pythonStepsPattern, { cwd: config.projectRoot });
  console.log(`Found ${pythonStepFiles.length} Python step definition files`);

  // Process each Python step file
  for (const stepFile of pythonStepFiles) {
    const fullPath = path.join(config.projectRoot, stepFile);
    const content = fs.readFileSync(fullPath, 'utf8');
    const fileName = path.basename(stepFile);

    console.log(`\nProcessing file: ${color.cyan(fileName)}`);

    // Extract lines with @given, @when, @then to find step definitions
    const lines = content.split('\n');
    const stepDefs = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('@given') || line.includes('@when') || line.includes('@then')) {
        // Found a step definition decorator, get the step text
        const match = line.match(/@(given|when|then)\(['"](.+?)['"]/);
        if (match) {
          const type = match[1]; // given, when, then
          const stepText = match[2]; // the step text pattern

          // Get the method name from the next line
          let methodName = '';
          if (i + 1 < lines.length) {
            const nextLine = lines[i + 1];
            const methodMatch = nextLine.match(/def\s+(\w+)/);
            if (methodMatch) {
              methodName = methodMatch[1];
            }
          }

          // Determine TDD phase
          let phase = 'unknown';
          // Check docstring for phase information
          for (let j = i + 1; j < Math.min(i + 10, lines.length); j++) {
            const docLine = lines[j];
            if (docLine.includes('RED PHASE')) {
              phase = 'red';
              break;
            } else if (docLine.includes('GREEN PHASE')) {
              phase = 'green';
              break;
            } else if (docLine.includes('REFACTOR PHASE')) {
              phase = 'refactor';
              break;
            }
          }

          // Store the step definition
          stepDefs.push({
            type,
            text: stepText,
            method: methodName,
            phase,
            file: fileName
          });

          // Count by phase
          if (phase === 'red') {
            results.redPhase++;
          } else if (phase === 'green') {
            results.greenPhase++;
          } else if (phase === 'refactor') {
            results.refactorPhase++;
          } else {
            results.unknownPhase++;
          }
        }
      }
    }

    // Log found steps
    if (stepDefs.length > 0) {
      console.log(`  Found ${color.green(stepDefs.length)} step definitions:`);
      stepDefs.forEach(step => {
        const phaseColor =
          step.phase === 'red' ? color.red(step.phase) :
          step.phase === 'green' ? color.green(step.phase) :
          step.phase === 'refactor' ? color.yellow(step.phase) :
          color.magenta(step.phase);

        console.log(`  - @${step.type}('${step.text}') [${phaseColor}]`);
      });

      // Add steps to results
      results.stepDefinitions.push(...stepDefs);
      results.totalStepDefinitions += stepDefs.length;

      // Categorize steps
      for (const step of stepDefs) {
        let matchedCategory = false;

        // Try to categorize based on file name and step text
        for (const category of config.featureCategories) {
          const categoryLower = category.toLowerCase();
          if (
            fileName.toLowerCase().includes(categoryLower.replace(/\\s+/g, '_')) ||
            step.text.toLowerCase().includes(categoryLower) ||
            (categoryLower.includes('shadow') && fileName.includes('shadow'))
          ) {
            if (!results.byCategory[category]) {
              results.byCategory[category] = { total: 0, red: 0, green: 0, refactor: 0, unknown: 0 };
            }

            results.byCategory[category].total++;

            if (step.phase === 'red') {
              results.byCategory[category].red++;
            } else if (step.phase === 'green') {
              results.byCategory[category].green++;
            } else if (step.phase === 'refactor') {
              results.byCategory[category].refactor++;
            } else {
              results.byCategory[category].unknown++;
            }

            matchedCategory = true;
            break;
          }
        }

        // If no category matched, use "Uncategorized"
        if (!matchedCategory) {
          if (!results.byCategory['Uncategorized']) {
            results.byCategory['Uncategorized'] = { total: 0, red: 0, green: 0, refactor: 0, unknown: 0 };
          }

          results.byCategory['Uncategorized'].total++;

          if (step.phase === 'red') {
            results.byCategory['Uncategorized'].red++;
          } else if (step.phase === 'green') {
            results.byCategory['Uncategorized'].green++;
          } else if (step.phase === 'refactor') {
            results.byCategory['Uncategorized'].refactor++;
          } else {
            results.byCategory['Uncategorized'].unknown++;
          }
        }
      }
    } else {
      console.log(`  ${color.yellow('No step definitions found in this file')}`);
    }
  }

  // Count steps in feature files to estimate total needed
  let totalStepsInFeatures = 0;
  let categorizedStepsInFeatures = {};

  // Initialize categories
  config.featureCategories.forEach(category => {
    categorizedStepsInFeatures[category] = 0;
  });

  // Process feature files
  const featureFiles = glob.sync(config.featurePattern, { cwd: config.projectRoot });
  console.log(`\nFound ${featureFiles.length} feature files`);

  for (const featureFile of featureFiles) {
    const fullPath = path.join(config.projectRoot, featureFile);
    const content = fs.readFileSync(fullPath, 'utf8');
    const fileName = path.basename(featureFile);

    // Extract scenario steps (Given, When, Then, And, But)
    const stepLines = content.match(/^\\s*(Given|When|Then|And|But) (.+?)$/gim) || [];
    totalStepsInFeatures += stepLines.length;

    // Categorize the feature
    let matchedCategory = false;
    for (const category of config.featureCategories) {
      const categoryLower = category.toLowerCase();
      if (
        fileName.toLowerCase().includes(categoryLower.replace(/\\s+/g, '_')) ||
        content.toLowerCase().includes(categoryLower)
      ) {
        categorizedStepsInFeatures[category] += stepLines.length;
        matchedCategory = true;
        break;
      }
    }

    // If no category matched, use "Uncategorized"
    if (!matchedCategory) {
      if (!categorizedStepsInFeatures['Uncategorized']) {
        categorizedStepsInFeatures['Uncategorized'] = 0;
      }
      categorizedStepsInFeatures['Uncategorized'] += stepLines.length;
    }
  }

  // Calculate completion percentage
  results.completionPercentage = totalStepsInFeatures > 0
    ? Math.round((results.totalStepDefinitions / totalStepsInFeatures) * 100)
    : 0;

  return {
    results,
    totalStepsNeeded: totalStepsInFeatures,
    categorizedStepsInFeatures
  };
}

/**
 * Generate a simple console report
 */
function displayReport(reportData) {
  const { results, totalStepsNeeded, categorizedStepsInFeatures } = reportData;

  console.log('\n' + color.bold('===== Python BDD Implementation Status ====='));
  console.log(`Total Step Definitions: ${color.green(results.totalStepDefinitions)} of ${color.cyan(totalStepsNeeded)} needed steps`);
  console.log(`Implementation Progress: ${color.yellow(results.completionPercentage + '%')}`);
  console.log(`TDD Phase Breakdown: RED: ${color.red(results.redPhase)} | GREEN: ${color.green(results.greenPhase)} | REFACTOR: ${color.yellow(results.refactorPhase)} | UNKNOWN: ${color.magenta(results.unknownPhase)}`);

  console.log('\n' + color.bold('Category Breakdown:'));
  for (const [category, stats] of Object.entries(results.byCategory)) {
    if (stats.total > 0) {
      const totalNeeded = categorizedStepsInFeatures[category] || 0;
      const completion = totalNeeded > 0 ? Math.round((stats.total / totalNeeded) * 100) : 0;

      console.log(`- ${color.cyan(category)}: ${color.green(stats.total)} steps (${completion}% complete)`);
      console.log(`  RED: ${color.red(stats.red)}, GREEN: ${color.green(stats.green)}, REFACTOR: ${color.yellow(stats.refactor)}, UNKNOWN: ${color.magenta(stats.unknown)}`);
    }
  }

  console.log('\n' + color.bold('Implementation Progress by Category:'));
  for (const [category, stats] of Object.entries(results.byCategory)) {
    if (stats.total > 0) {
      const totalNeeded = categorizedStepsInFeatures[category] || 0;
      const completion = totalNeeded > 0 ? Math.round((stats.total / totalNeeded) * 100) : 0;

      // Create progress bar
      const barLength = 30;
      const completedLength = Math.round((completion / 100) * barLength);
      const progressBar = '█'.repeat(completedLength) + '░'.repeat(barLength - completedLength);

      console.log(`- ${color.cyan(category)}: ${progressBar} ${color.yellow(completion + '%')} (${color.green(stats.total)}/${color.cyan(totalNeeded)} steps)`);
    }
  }

  console.log('\n' + color.bold('==========================================='));
}

// Run the analysis and display the report
const reportData = analyzePythonBdd();
displayReport(reportData);
