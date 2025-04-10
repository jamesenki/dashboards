/**
 * Python BDD Test Report Generator for IoTSphere Project (v3)
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
  ],
  // Add category mapping for files and patterns
  categoryMappings: {
    'Water Heater Monitoring': ['water_heater', 'waterheater', 'heater_monitoring', 'dashboard/water_heater'],
    'Device Shadow Service': ['device_shadow', 'shadow_service', 'shadow'],
    'Device Management': ['device_management', 'devicemanagement'],
    'Predictive Maintenance': ['predictive', 'maintenance', 'predict'],
    'Dashboard & Visualization': ['dashboard', 'visualization', 'visualize', 'display']
  }
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
 * Determines which category a file or step belongs to
 */
function determineCategory(fileName, stepText) {
  for (const [category, patterns] of Object.entries(config.categoryMappings)) {
    for (const pattern of patterns) {
      if (
        fileName.toLowerCase().includes(pattern.toLowerCase()) ||
        (stepText && stepText.toLowerCase().includes(pattern.toLowerCase()))
      ) {
        return category;
      }
    }
  }
  return 'Uncategorized';
}

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
  results.byCategory['Uncategorized'] = { total: 0, red: 0, green: 0, refactor: 0, unknown: 0 };

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
            file: fileName,
            filePath: stepFile
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
        const category = determineCategory(step.filePath, step.text);

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
  categorizedStepsInFeatures['Uncategorized'] = 0;

  // Process feature files
  const featureFiles = glob.sync(config.featurePattern, { cwd: config.projectRoot });
  console.log(`\nFound ${featureFiles.length} feature files`);

  for (const featureFile of featureFiles) {
    const fullPath = path.join(config.projectRoot, featureFile);
    const content = fs.readFileSync(fullPath, 'utf8');
    const fileName = path.basename(featureFile);

    console.log(`Processing feature: ${color.cyan(featureFile)}`);

    // Extract scenario steps (Given, When, Then, And, But)
    const stepRegex = /^\s*(Given|When|Then|And|But)\s+(.+)$/gim;
    let match;
    let stepCount = 0;

    while ((match = stepRegex.exec(content)) !== null) {
      stepCount++;
    }

    // Count from content again since the regex consumes the matches
    const allSteps = content.match(/^\s*(Given|When|Then|And|But)\s+.+$/gim) || [];
    stepCount = allSteps.length;

    console.log(`  Found ${color.green(stepCount)} steps in feature file`);
    totalStepsInFeatures += stepCount;

    // Determine the category for this feature file
    const category = determineCategory(featureFile, content);
    categorizedStepsInFeatures[category] += stepCount;

    console.log(`  Categorized as: ${color.cyan(category)}`);
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

      console.log(`- ${color.cyan(category)}: ${color.green(stats.total)} / ${color.yellow(totalNeeded)} steps (${completion}% complete)`);
      console.log(`  RED: ${color.red(stats.red)}, GREEN: ${color.green(stats.green)}, REFACTOR: ${color.yellow(stats.refactor)}, UNKNOWN: ${color.magenta(stats.unknown)}`);
    }
  }

  console.log('\n' + color.bold('Implementation Progress by Category:'));
  for (const [category, stats] of Object.entries(results.byCategory)) {
    if (stats.total > 0 || categorizedStepsInFeatures[category] > 0) {
      const totalNeeded = categorizedStepsInFeatures[category] || 0;
      const completion = totalNeeded > 0 ? Math.round((stats.total / totalNeeded) * 100) : 0;

      // Create progress bar
      const barLength = 30;
      const completedLength = Math.round((completion / 100) * barLength);
      const progressBar = '█'.repeat(completedLength) + '░'.repeat(barLength - completedLength);

      console.log(`- ${color.cyan(category)}: ${progressBar} ${color.yellow(completion + '%')} (${color.green(stats.total)}/${color.cyan(totalNeeded)} steps)`);

      // Show the GREEN phase percentage separately
      const greenPercentage = totalNeeded > 0 ? Math.round((stats.green / totalNeeded) * 100) : 0;
      console.log(`  GREEN Phase: ${color.green(stats.green)}/${color.cyan(totalNeeded)} (${color.green(greenPercentage + '%')})`);
    }
  }

  console.log('\n' + color.bold('==========================================='));

  // Generate an HTML report with more details
  generateHtmlReport(reportData);
}

/**
 * Generate an HTML report file
 */
function generateHtmlReport(reportData) {
  const { results, totalStepsNeeded, categorizedStepsInFeatures } = reportData;

  // Create the output directory if it doesn't exist
  if (!fs.existsSync(config.outputDir)) {
    fs.mkdirSync(config.outputDir, { recursive: true });
  }

  const reportFilePath = path.join(config.outputDir, 'python-bdd-report.html');

  // Generate HTML content
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IoTSphere Python BDD Test Report</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    h1, h2, h3 {
      color: #2c3e50;
    }
    .summary {
      background-color: #f8f9fa;
      border-radius: 5px;
      padding: 15px;
      margin-bottom: 20px;
    }
    .progress-container {
      margin-top: 10px;
      margin-bottom: 30px;
    }
    .progress-bar {
      height: 25px;
      background-color: #e9ecef;
      border-radius: 5px;
      overflow: hidden;
      margin-bottom: 5px;
    }
    .progress {
      height: 100%;
      background-color: #007bff;
      color: white;
      text-align: center;
      line-height: 25px;
    }
    .green { background-color: #28a745; }
    .red { background-color: #dc3545; }
    .yellow { background-color: #ffc107; color: #333; }
    .table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
    }
    .table th, .table td {
      padding: 12px 15px;
      border: 1px solid #ddd;
      text-align: left;
    }
    .table th {
      background-color: #f8f9fa;
    }
    .table tr:nth-child(even) {
      background-color: #f2f2f2;
    }
    .phase-indicator {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 3px;
      color: white;
      font-weight: bold;
      margin-right: 5px;
    }
  </style>
</head>
<body>
  <h1>IoTSphere Python BDD Test Report</h1>

  <div class="summary">
    <h2>Overall Summary</h2>
    <p>Total Step Definitions: <strong>${results.totalStepDefinitions}</strong> of <strong>${totalStepsNeeded}</strong> needed steps</p>
    <p>Implementation Progress: <strong>${results.completionPercentage}%</strong></p>

    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress" style="width: ${results.completionPercentage}%">${results.completionPercentage}%</div>
      </div>
    </div>

    <h3>TDD Phase Breakdown</h3>
    <p>
      <span class="phase-indicator red">RED: ${results.redPhase}</span>
      <span class="phase-indicator green">GREEN: ${results.greenPhase}</span>
      <span class="phase-indicator yellow">REFACTOR: ${results.refactorPhase}</span>
    </p>
  </div>

  <h2>Category Implementation Progress</h2>

  <div class="progress-container">
    ${Object.entries(results.byCategory)
      .filter(([category, stats]) => stats.total > 0 || categorizedStepsInFeatures[category] > 0)
      .map(([category, stats]) => {
        const totalNeeded = categorizedStepsInFeatures[category] || 0;
        const completion = totalNeeded > 0 ? Math.round((stats.total / totalNeeded) * 100) : 0;
        const greenPercentage = totalNeeded > 0 ? Math.round((stats.green / totalNeeded) * 100) : 0;

        return `
          <h3>${category}</h3>
          <p>Steps: ${stats.total} / ${totalNeeded} (${completion}% complete)</p>
          <div class="progress-bar">
            <div class="progress" style="width: ${completion}%">${completion}%</div>
          </div>
          <p>GREEN Phase: ${stats.green} / ${totalNeeded} (${greenPercentage}%)</p>
          <div class="progress-bar">
            <div class="progress green" style="width: ${greenPercentage}%">${greenPercentage}%</div>
          </div>
          <p>Phase Breakdown:
            <span class="phase-indicator red">RED: ${stats.red}</span>
            <span class="phase-indicator green">GREEN: ${stats.green}</span>
            <span class="phase-indicator yellow">REFACTOR: ${stats.refactor}</span>
          </p>
        `;
      }).join('')}
  </div>

  <h2>Step Definition Details</h2>
  <table class="table">
    <thead>
      <tr>
        <th>Type</th>
        <th>Step Text</th>
        <th>File</th>
        <th>Phase</th>
      </tr>
    </thead>
    <tbody>
      ${results.stepDefinitions.map(step => {
        const phaseClass =
          step.phase === 'red' ? 'red' :
          step.phase === 'green' ? 'green' :
          step.phase === 'refactor' ? 'yellow' : '';

        return `
          <tr>
            <td>${step.type}</td>
            <td>${step.text}</td>
            <td>${step.file}</td>
            <td><span class="phase-indicator ${phaseClass}">${step.phase.toUpperCase()}</span></td>
          </tr>
        `;
      }).join('')}
    </tbody>
  </table>

  <p><em>Report generated on ${new Date().toLocaleString()}</em></p>
</body>
</html>`;

  // Write to file
  fs.writeFileSync(reportFilePath, html);
  console.log(`\nHTML report generated at: ${color.cyan(reportFilePath)}`);
}

// Run the analysis and display the report
const reportData = analyzePythonBdd();
displayReport(reportData);
