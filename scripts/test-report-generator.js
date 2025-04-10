/**
 * Test Report Generator for IoTSphere Project
 *
 * This script analyzes test results across different test types:
 * - BDD tests (Cucumber)
 * - E2E tests (Cypress)
 * - Unit tests
 * - Integration tests
 *
 * It generates a report showing test status, TDD phase, and overall project completion.
 * Following the TDD principles where tests are our specification.
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Simple color functions for terminal output
const color = {
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  bold: (text) => `\x1b[1m${text}\x1b[0m`,
  boldBlue: (text) => `\x1b[1m\x1b[34m${text}\x1b[0m`,
  boldRed: (text) => `\x1b[1m\x1b[31m${text}\x1b[0m`,
  boldGreen: (text) => `\x1b[1m\x1b[32m${text}\x1b[0m`,
  boldYellow: (text) => `\x1b[1m\x1b[33m${text}\x1b[0m`
};

// Configuration
const config = {
  projectRoot: path.resolve(__dirname, '..'),
  outputDir: path.resolve(__dirname, '../test-reports'),
  testPatterns: {
    bdd: 'src/tests/bdd/features/**/*.feature',
    e2e: 'src/tests/e2e-tdd/journeys/**/*.spec.js',
    unit: 'src/tests/unit/**/*.py',
    integration: 'src/tests/integration-tdd/**/*.py'
  },
  // Additional paths for Python BDD step implementations and test results
  pythonTestResults: {
    bdd: 'test-reports/bdd_python_report.txt',
    pythonSteps: 'src/tests/bdd/steps/**/*.py',
    junitReports: 'test-reports/junit/*.xml',
    behaveReports: 'src/tests/bdd/reports/*.json'
  },
  // Feature categories (major functionality areas)
  featureCategories: [
    'Water Heater Monitoring',
    'Device Shadow Service',
    'Device Management',
    'Predictive Maintenance',
    'Dashboard & Visualization'
  ],
  // Expected final test counts based on project requirements
  // Following the 70:20:10 ratio for unit:integration:e2e tests
  expectedCounts: {
    bdd: 25,  // BDD features document high-level requirements
    e2e: 15,  // Represents 10% of automated tests (end-to-end)
    unit: 150, // Represents 70% of automated tests (unit)
    integration: 40 // Represents 20% of automated tests (integration)
  }
};

// TDD phase detection patterns
const tddPhaseDetectors = {
  red: /(@red|\/\/ *RED PHASE|# *RED PHASE)/i,
  green: /(@green|\/\/ *GREEN PHASE|# *GREEN PHASE)/i,
  refactor: /(@refactor|\/\/ *REFACTOR PHASE|# *REFACTOR PHASE)/i
};

// Feature category detection patterns
const categoryDetectors = {
  'Water Heater Monitoring': /(water_heater_monitoring|water[-_]heater|monitoring)/i,
  'Device Shadow Service': /(device[-_]shadow|shadow[-_]service|shadow)/i,
  'Device Management': /(device[-_]management|registration|activation|deactivation)/i,
  'Predictive Maintenance': /(predictive[-_]maintenance|maintenance|prediction)/i,
  'Dashboard & Visualization': /(dashboard|visualization|display|gauge)/i
};

/**
 * Main function to generate the test report
 */
async function generateTestReport() {
  console.log(color.boldBlue('Generating IoTSphere Test Report...'));

  const mdOutputPath = path.join(config.outputDir, 'test-report.md');
  const htmlOutputPath = path.join(config.outputDir, 'test-report.html');

  // Ensure output directory exists
  if (!fs.existsSync(config.outputDir)) {
    fs.mkdirSync(config.outputDir, { recursive: true });
  }

  // Get test data
  const testStats = await collectTestStats();
  const mdReport = formatReport(testStats);

  // Write markdown report to file
  fs.writeFileSync(mdOutputPath, mdReport);
  console.log(color.green(`Markdown test report generated at: ${mdOutputPath}`));

  // Generate HTML report
  const htmlReport = formatHtmlReport(testStats);
  fs.writeFileSync(htmlOutputPath, htmlReport);
  console.log(color.green(`HTML test report generated at: ${htmlOutputPath}`));

  // Also print summary to console
  console.log('\n' + formatConsoleReport(testStats));

  return { testStats, mdReportPath: mdOutputPath, htmlReportPath: htmlOutputPath };
}

/**
 * Collect statistics about all test files
 * Includes both JavaScript and Python test files
 */
async function collectTestStats() {
  // Result object will hold all our test statistics
  const result = {
    summary: {
      totalTests: 0,
      redPhase: 0,
      greenPhase: 0,
      refactorPhase: 0,
      completion: 0
    },
    byType: {},
    byCategory: {}
  };

  // Initialize category counters
  config.featureCategories.forEach(category => {
    result.byCategory[category] = {
      total: 0,
      red: 0,
      green: 0,
      refactor: 0
    };
  });

  // Process each test type
  for (const [type, pattern] of Object.entries(config.testPatterns)) {
    const files = glob.sync(pattern, { cwd: config.projectRoot });

    // Special handling for BDD - count both JS and Python implementations
    let totalTests = files.length;
    if (type === 'bdd') {
      // First check for Python step implementation files directly
      const pythonStepFiles = glob.sync(config.pythonTestResults.pythonSteps, { cwd: config.projectRoot });
      let implementedPythonSteps = 0;
      let pythonGreenSteps = 0;
      let pythonRedSteps = 0;
      let pythonRefactorSteps = 0;

      // Process Python step files to count implemented steps
      for (const stepFile of pythonStepFiles) {
        const fullPath = path.join(config.projectRoot, stepFile);
        const content = fs.readFileSync(fullPath, 'utf8');

        // Count step definitions (functions decorated with @given, @when, @then)
        const stepDefinitions = content.match(/\@(given|when|then)/gi) || [];
        implementedPythonSteps += stepDefinitions.length;

        // Check their TDD phase
        if (content.includes('GREEN PHASE')) {
          pythonGreenSteps += stepDefinitions.length;
          result.byType[type].green += stepDefinitions.length;
          result.summary.greenPhase += stepDefinitions.length;
        } else if (content.includes('RED PHASE')) {
          pythonRedSteps += stepDefinitions.length;
          result.byType[type].red += stepDefinitions.length;
          result.summary.redPhase += stepDefinitions.length;
        } else if (content.includes('REFACTOR PHASE')) {
          pythonRefactorSteps += stepDefinitions.length;
          result.byType[type].refactor += stepDefinitions.length;
          result.summary.refactorPhase += stepDefinitions.length;
        } else {
          // Default to GREEN phase if no explicit phase marker but steps are implemented
          pythonGreenSteps += stepDefinitions.length;
          result.byType[type].green += stepDefinitions.length;
          result.summary.greenPhase += stepDefinitions.length;
        }

        // Determine to which feature category this file belongs
        let matchedCategory = false;
        for (const categoryName of config.featureCategories) {
          const lowerCaseCategoryName = categoryName.toLowerCase();
          if (content.toLowerCase().includes(lowerCaseCategoryName) ||
              stepFile.toLowerCase().includes(lowerCaseCategoryName)) {
            // Ensure the category exists in our tracking object
            if (!result.byCategory[categoryName]) {
              result.byCategory[categoryName] = {
                total: 0,
                red: 0,
                green: 0,
                refactor: 0
              };
            }
            // Add step definitions to the appropriate category
            if (content.includes('GREEN PHASE')) {
              result.byCategory[categoryName].green += stepDefinitions.length;
            } else if (content.includes('RED PHASE')) {
              result.byCategory[categoryName].red += stepDefinitions.length;
            } else {
              result.byCategory[categoryName].refactor += stepDefinitions.length;
            }
            result.byCategory[categoryName].total += stepDefinitions.length;
            matchedCategory = true;
            break;
          }
        }

        // If no category matched, put it in a default category
        if (!matchedCategory && stepDefinitions.length > 0) {
          const defaultCategory = 'Uncategorized';
          if (!result.byCategory[defaultCategory]) {
            result.byCategory[defaultCategory] = {
              total: 0,
              red: 0,
              green: 0,
              refactor: 0
            };
          }
          if (content.includes('GREEN PHASE')) {
            result.byCategory[defaultCategory].green += stepDefinitions.length;
          } else if (content.includes('RED PHASE')) {
            result.byCategory[defaultCategory].red += stepDefinitions.length;
          } else {
            result.byCategory[defaultCategory].refactor += stepDefinitions.length;
          }
          result.byCategory[defaultCategory].total += stepDefinitions.length;
        }
      }

      console.log(`Found ${implementedPythonSteps} implemented Python BDD steps (${pythonGreenSteps} GREEN, ${pythonRedSteps} RED, ${pythonRefactorSteps} REFACTOR)`);

      // Add Python steps to total, but avoid double-counting
      totalTests = files.length + implementedPythonSteps;

      // Also check if Python BDD report exists (for backwards compatibility)
      const pythonBddReport = path.join(config.projectRoot, config.pythonTestResults.bdd);
      if (fs.existsSync(pythonBddReport)) {
        const pythonBddContent = fs.readFileSync(pythonBddReport, 'utf8');
        const additionalSteps = (pythonBddContent.match(/implemented|passes|passed/gi) || []).length;
        console.log(`Found ${additionalSteps} additional steps in Python BDD report`);
      }

      // Look for JUnit XML reports from Python tests
      const junitReports = glob.sync(config.pythonTestResults.junitReports, { cwd: config.projectRoot });
      if (junitReports.length > 0) {
        console.log(`Found ${junitReports.length} JUnit reports from Python tests`);
      }

      // Look for Behave JSON reports
      const behaveReports = glob.sync(config.pythonTestResults.behaveReports, { cwd: config.projectRoot });
      if (behaveReports.length > 0) {
        console.log(`Found ${behaveReports.length} Behave JSON reports`);
        for (const reportFile of behaveReports) {
          try {
            const reportContent = fs.readFileSync(path.join(config.projectRoot, reportFile), 'utf8');
            const reportData = JSON.parse(reportContent);
            // Extract additional test information if needed
          } catch (err) {
            console.log(`Error processing Behave report ${reportFile}: ${err.message}`);
          }
        }
      }
    }

    result.byType[type] = {
      total: totalTests,
      red: 0,
      green: 0,
      refactor: 0,
      expected: config.expectedCounts[type],
      completion: 0,
      files: []
    };

    // Process each file
    for (const file of files) {
      const fullPath = path.join(config.projectRoot, file);
      const content = fs.readFileSync(fullPath, 'utf8');

      // Determine TDD phase
      let phase = 'unknown';
      if (tddPhaseDetectors.refactor.test(content)) {
        phase = 'refactor';
        result.byType[type].refactor++;
        result.summary.refactorPhase++;
      } else if (tddPhaseDetectors.green.test(content)) {
        phase = 'green';
        result.byType[type].green++;
        result.summary.greenPhase++;
      } else if (tddPhaseDetectors.red.test(content)) {
        phase = 'red';
        result.byType[type].red++;
        result.summary.redPhase++;
      } else {
        // Default to refactor for files without explicit phase markers
        // This helps account for legacy tests
        phase = 'refactor';
        result.byType[type].refactor++;
        result.summary.refactorPhase++;
      }

      // Determine feature category
      let category = 'Uncategorized';
      for (const [cat, pattern] of Object.entries(categoryDetectors)) {
        if (pattern.test(file)) {
          category = cat;
          break;
        }
      }

      // Add to category stats
      if (result.byCategory[category]) {
        result.byCategory[category].total++;
        result.byCategory[category][phase]++;
      }

      // Add to file details
      result.byType[type].files.push({
        path: file,
        phase,
        category
      });

      result.summary.totalTests++;
    }

    // Calculate completion percentage
    result.byType[type].completion = Math.round((result.byType[type].total / result.byType[type].expected) * 100);
  }

  // Calculate overall completion
  const totalExpected = Object.values(config.expectedCounts).reduce((sum, val) => sum + val, 0);
  result.summary.completion = Math.round((result.summary.totalTests / totalExpected) * 100);

  return result;
}

/**
 * Format the collected data into a detailed Markdown report
 */
function formatReport(stats) {
  let report = `# IoTSphere Test Report\n\n`;
  report += `*Generated on: ${new Date().toLocaleString()}*\n\n`;

  // Overall Summary
  report += `## Overall Progress\n\n`;
  report += `- **Project Completion**: ${stats.summary.completion}% (${stats.summary.totalTests} tests implemented)\n`;
  report += `- **TDD Phase Breakdown**:\n`;

  // Calculate percentages with handling for zero totalTests
  const totalTests = Math.max(1, stats.summary.totalTests); // Avoid division by zero
  const redPercent = Math.round((stats.summary.redPhase / totalTests) * 100);
  const greenPercent = Math.round((stats.summary.greenPhase / totalTests) * 100);
  const refactorPercent = Math.round((stats.summary.refactorPhase / totalTests) * 100);

  report += `  - RED: ${stats.summary.redPhase} tests (${redPercent}%)\n`;
  report += `  - GREEN: ${stats.summary.greenPhase} tests (${greenPercent}%)\n`;
  report += `  - REFACTOR: ${stats.summary.refactorPhase} tests (${refactorPercent}%)\n\n`;

  // Test Type Breakdown
  report += `## Test Type Breakdown\n\n`;
  report += `| Test Type | Implemented | Expected | Completion | RED | GREEN | REFACTOR |\n`;
  report += `|-----------|-------------|----------|------------|-----|-------|----------|\n`;

  for (const [type, data] of Object.entries(stats.byType)) {
    report += `| ${type.toUpperCase()} | ${data.total} | ${data.expected} | ${data.completion}% | `;
    report += `${data.red} | ${data.green} | ${data.refactor} |\n`;
  }

  report += `\n`;

  // Feature Category Breakdown
  report += `## Feature Category Breakdown\n\n`;
  report += `| Feature Category | Total Tests | RED | GREEN | REFACTOR |\n`;
  report += `|------------------|-------------|-----|-------|----------|\n`;

  for (const [category, data] of Object.entries(stats.byCategory)) {
    report += `| ${category} | ${data.total} | ${data.red} | ${data.green} | ${data.refactor} |\n`;
  }

  report += `\n`;

  // Detailed Test Listing by Type
  for (const [type, data] of Object.entries(stats.byType)) {
    report += `## ${type.toUpperCase()} Tests\n\n`;

    if (data.files.length === 0) {
      report += `*No ${type} tests implemented yet.*\n\n`;
      continue;
    }

    report += `| File | Category | TDD Phase |\n`;
    report += `|------|----------|----------|\n`;

    for (const file of data.files) {
      report += `| \`${file.path}\` | ${file.category} | ${file.phase.toUpperCase()} |\n`;
    }

    report += `\n`;
  }

  // Recommendations
  report += `## Recommendations\n\n`;

  // Calculate what to focus on next based on TDD principles
  const redTests = stats.summary.redPhase;
  const greenTests = stats.summary.greenPhase;
  const refactorTests = stats.summary.refactorPhase;

  if (redTests > greenTests && redTests > refactorTests) {
    report += `- **Focus on implementation**: Move ${redTests} RED tests to GREEN by implementing their functionality\n`;
  } else if (greenTests > refactorTests) {
    report += `- **Focus on refactoring**: Improve code quality for ${greenTests} GREEN tests without breaking functionality\n`;
  } else {
    report += `- **Focus on new features**: Add new RED tests for missing functionality\n`;
  }

  // Identify category with least progress
  const lowestCategoryCompletion = Object.entries(stats.byCategory)
    .map(([category, data]) => ({
      category,
      completion: (data.green + data.refactor) / Math.max(1, data.total) * 100
    }))
    .sort((a, b) => a.completion - b.completion)[0];

  if (lowestCategoryCompletion) {
    report += `- **Prioritize ${lowestCategoryCompletion.category}**: This feature area has the lowest implementation completion at ${Math.round(lowestCategoryCompletion.completion)}%\n`;
  }

  return report;
}

/**
 * Format a condensed console-friendly version of the report
 */
function formatConsoleReport(stats) {
  let report = color.boldBlue('\n===== IoTSphere Test Report Summary =====\n');

  // Overall progress
  report += color.bold(`Overall Completion: ${color.green(stats.summary.completion + '%')}\n`);
  report += `Total Tests: ${stats.summary.totalTests}\n`;
  report += `TDD Phases: ${color.red('RED: ' + stats.summary.redPhase)} | `;
  report += `${color.green('GREEN: ' + stats.summary.greenPhase)} | `;
  report += `${color.blue('REFACTOR: ' + stats.summary.refactorPhase)}\n\n`;

  // Test types
  report += color.bold('Test Type Completion:\n');
  for (const [type, data] of Object.entries(stats.byType)) {
    let completionColor = color.red;
    if (data.completion >= 80) completionColor = color.green;
    else if (data.completion >= 40) completionColor = color.yellow;

    report += `${type.toUpperCase()}: ${completionColor(data.completion + '%')} (${data.total}/${data.expected})\n`;
  }

  report += '\n' + color.bold('Feature Category Status:\n');
  for (const [category, data] of Object.entries(stats.byCategory)) {
    const greenPct = Math.round((data.green + data.refactor) / Math.max(1, data.total) * 100);
    let statusColor = color.red;
    if (greenPct >= 80) statusColor = color.green;
    else if (greenPct >= 40) statusColor = color.yellow;

    report += `${category}: ${statusColor(greenPct + '%')} implemented\n`;
  }

  report += '\n' + color.boldBlue('=======================================');
  return report;
}

/**
 * Add this to package.json scripts to run after tests
 */
function addToPackageJson() {
  const packageJsonPath = path.join(config.projectRoot, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    console.log(color.yellow('Could not find package.json to update scripts'));
    return;
  }

  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  packageJson.scripts = packageJson.scripts || {};

  // Add new scripts
  packageJson.scripts['test-report'] = 'node scripts/test-report-generator.js';
  packageJson.scripts['test:bdd-with-report'] = 'cucumber-js --config src/tests/bdd/config/cucumber.js && npm run test-report';
  packageJson.scripts['test:e2e-with-report'] = 'cypress run && npm run test-report';
  packageJson.scripts['test:all-with-report'] = 'npm run test:unit && npm run test:integration && npm run test:e2e && npm run test:bdd && npm run test-report';

  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  console.log(color.green('Added test report scripts to package.json'));
}

/**
 * Format the collected data into an HTML report using the template
 */
function formatHtmlReport(stats) {
  const templatePath = path.join(config.outputDir, 'test-report-template.html');
  if (!fs.existsSync(templatePath)) {
    console.log(color.yellow('HTML template not found. Falling back to markdown only.'));
    return null;
  }

  let template = fs.readFileSync(templatePath, 'utf8');
  const timestamp = new Date().toLocaleString();
  const totalTests = stats.summary.totalTests;
  const expectedTests = Object.values(config.expectedCounts).reduce((sum, val) => sum + val, 0);

  // Calculate completion color based on percentage
  const getCompletionColor = (percentage) => {
    if (percentage >= 80) return '#2ecc71'; // success-color
    if (percentage >= 40) return '#f39c12'; // warning-color
    return '#e74c3c'; // danger-color
  };

  // Calculate TDD phase percentages
  const totalPhaseTests = Math.max(1, totalTests);
  const redPercentage = Math.round((stats.summary.redPhase / totalPhaseTests) * 100);
  const greenPercentage = redPercentage + Math.round((stats.summary.greenPhase / totalPhaseTests) * 100);
  // Note: refactor percentage goes from greenPercentage to 100%

  // Replace template placeholders
  template = template.replace('{{TIMESTAMP}}', timestamp);
  template = template.replace(/{{COMPLETION}}/g, stats.summary.completion);
  template = template.replace('{{COMPLETION_COLOR}}', getCompletionColor(stats.summary.completion));
  template = template.replace('{{TOTAL_TESTS}}', totalTests);
  template = template.replace('{{EXPECTED_TESTS}}', expectedTests);
  template = template.replace('{{RED_PHASE}}', stats.summary.redPhase);
  template = template.replace('{{GREEN_PHASE}}', stats.summary.greenPhase);
  template = template.replace('{{REFACTOR_PHASE}}', stats.summary.refactorPhase);
  template = template.replace('{{RED_PERCENTAGE}}', redPercentage);
  template = template.replace('{{GREEN_PERCENTAGE}}', greenPercentage);

  // Generate table rows for test types
  let testTypeRows = '';
  for (const [type, data] of Object.entries(stats.byType)) {
    const completionClass = data.completion >= 80 ? 'success' : data.completion >= 40 ? 'warning' : 'danger';
    testTypeRows += `<tr>
`;
    testTypeRows += `  <td>${type.toUpperCase()}</td>
`;
    testTypeRows += `  <td>${data.total}</td>
`;
    testTypeRows += `  <td>${data.expected}</td>
`;
    testTypeRows += `  <td>
    <div class="progress-container">
      <div class="progress-bar" style="width: ${data.completion}%; background-color: ${getCompletionColor(data.completion)};">
        ${data.completion}%
      </div>
    </div>
  </td>
`;
    testTypeRows += `  <td>${data.red}</td>
`;
    testTypeRows += `  <td>${data.green}</td>
`;
    testTypeRows += `  <td>${data.refactor}</td>
`;
    testTypeRows += `</tr>
`;
  }
  template = template.replace('{{TEST_TYPE_ROWS}}', testTypeRows);

  // Generate table rows for feature categories
  let featureCategoryRows = '';
  for (const [category, data] of Object.entries(stats.byCategory)) {
    const implementationPct = Math.round((data.green + data.refactor) / Math.max(1, data.total) * 100);
    const implementationClass = implementationPct >= 80 ? 'success' : implementationPct >= 40 ? 'warning' : 'danger';

    featureCategoryRows += `<tr>
`;
    featureCategoryRows += `  <td>${category}</td>
`;
    featureCategoryRows += `  <td>${data.total}</td>
`;
    featureCategoryRows += `  <td>${data.red}</td>
`;
    featureCategoryRows += `  <td>${data.green}</td>
`;
    featureCategoryRows += `  <td>${data.refactor}</td>
`;
    featureCategoryRows += `  <td>
    <div class="progress-container">
      <div class="progress-bar" style="width: ${implementationPct}%; background-color: ${getCompletionColor(implementationPct)};">
        ${implementationPct}%
      </div>
    </div>
  </td>
`;
    featureCategoryRows += `</tr>
`;
  }
  template = template.replace('{{FEATURE_CATEGORY_ROWS}}', featureCategoryRows);

  // Generate BDD test rows
  let bddTestRows = '';
  if (stats.byType.bdd && stats.byType.bdd.files) {
    for (const file of stats.byType.bdd.files) {
      const phaseBadgeClass = file.phase === 'red' ? 'badge-red' :
                              file.phase === 'green' ? 'badge-green' :
                              file.phase === 'refactor' ? 'badge-refactor' : 'badge-unknown';
      bddTestRows += `<tr>
`;
      bddTestRows += `  <td>${file.path}</td>
`;
      bddTestRows += `  <td>${file.category}</td>
`;
      bddTestRows += `  <td><span class="badge ${phaseBadgeClass}">${file.phase.toUpperCase()}</span></td>
`;
      bddTestRows += `</tr>
`;
    }
  }
  template = template.replace('{{BDD_TEST_ROWS}}', bddTestRows || '<tr><td colspan="3">No BDD tests found</td></tr>');

  // Generate E2E test rows
  let e2eTestRows = '';
  if (stats.byType.e2e && stats.byType.e2e.files) {
    for (const file of stats.byType.e2e.files) {
      const phaseBadgeClass = file.phase === 'red' ? 'badge-red' :
                              file.phase === 'green' ? 'badge-green' :
                              file.phase === 'refactor' ? 'badge-refactor' : 'badge-unknown';
      e2eTestRows += `<tr>
`;
      e2eTestRows += `  <td>${file.path}</td>
`;
      e2eTestRows += `  <td>${file.category}</td>
`;
      e2eTestRows += `  <td><span class="badge ${phaseBadgeClass}">${file.phase.toUpperCase()}</span></td>
`;
      e2eTestRows += `</tr>
`;
    }
  }
  template = template.replace('{{E2E_TEST_ROWS}}', e2eTestRows || '<tr><td colspan="3">No E2E tests found</td></tr>');

  // Generate recommendations
  const lowCovFeatures = Object.entries(stats.byCategory)
    .filter(([_, data]) => {
      const implementationPct = Math.round((data.green + data.refactor) / Math.max(1, data.total) * 100);
      return implementationPct < 50;
    })
    .map(([category]) => category);

  let recommendations = '';
  // Check if we need more RED tests
  if (redPercentage < 5) {
    recommendations += `<li>Add more RED tests to define requirements for new features</li>
`;
  }

  // Check if we need to implement GREEN for existing RED tests
  if (stats.summary.redPhase > 0 && redPercentage > greenPercentage) {
    recommendations += `<li>Focus on implementing the ${stats.summary.redPhase} RED tests to move them to GREEN phase</li>
`;
  }

  // Check if we need to refactor existing GREEN tests
  if (stats.summary.greenPhase > 5 && greenPercentage > 50 && stats.summary.refactorPhase < stats.summary.greenPhase) {
    recommendations += `<li>Consider refactoring existing GREEN implementations to improve code quality</li>
`;
  }

  // Add recommendations for low-coverage features
  if (lowCovFeatures.length > 0) {
    recommendations += `<li>Prioritize implementation for these features with low coverage:
      <ul>
`;
    lowCovFeatures.forEach(feature => {
      recommendations += `        <li>${feature}</li>
`;
    });
    recommendations += `      </ul>
    </li>
`;
  }

  // Add recommendation about test balance (70:20:10 ratio)
  const unitPct = stats.byType.unit ? stats.byType.unit.completion : 0;
  const integrationPct = stats.byType.integration ? stats.byType.integration.completion : 0;
  const e2ePct = stats.byType.e2e ? stats.byType.e2e.completion : 0;

  if ((unitPct > 0 && integrationPct > 0 && e2ePct > 0) &&
      (Math.abs(unitPct - 70) > 20 || Math.abs(integrationPct - 20) > 10 || Math.abs(e2ePct - 10) > 5)) {
    recommendations += `<li>Adjust test balance to maintain the recommended 70:20:10 ratio (unit:integration:e2e)</li>
`;
  }

  template = template.replace('{{RECOMMENDATIONS}}', recommendations || '<li>No specific recommendations at this time</li>');

  return template;
}

// If called directly, generate the report
if (require.main === module) {
  console.log('Generating IoTSphere Test Report...');
  // Check for missing dependencies
  try {
    require('glob');
  } catch (err) {
    console.error('Missing dependencies. Please run: npm install --save-dev glob@8.1.0');
    process.exit(1);
  }

  generateTestReport()
    .then(() => {
      // Try to add to package.json
      try {
        addToPackageJson();
      } catch (err) {
        console.log(color.yellow('Could not update package.json:' + err.message));
      }
    })
    .catch(err => {
      console.error('Error generating report:', err);
      process.exit(1);
    });
}

// Export the function for use in other scripts
module.exports = { generateTestReport };
