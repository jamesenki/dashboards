/**
 * Combined Test Report Generator for IoTSphere Project
 *
 * This script combines the results from both the standard test report generator
 * and the Python BDD report generator, creating a unified view of all test types.
 *
 * Following the TDD principles where tests are our specification.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const config = {
  projectRoot: path.resolve(__dirname, '..'),
  outputDir: path.resolve(__dirname, '../test-reports'),
  reportScripts: {
    pythonBdd: 'python-bdd-report-v3.js',
    standard: 'test-report-generator.js'
  }
};

// Color formatting for console output
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
 * Run each individual report generator
 */
function generateIndividualReports() {
  console.log(color.bold('Generating individual test reports...'));

  // Run Python BDD report generator
  const pythonBddScript = path.join(__dirname, config.reportScripts.pythonBdd);
  if (fs.existsSync(pythonBddScript)) {
    console.log(`Running ${color.cyan(config.reportScripts.pythonBdd)}...`);
    try {
      execSync(`node ${pythonBddScript}`, {
        cwd: config.projectRoot,
        stdio: 'inherit'
      });
      console.log(`${color.green('✓')} Python BDD report generated successfully.`);
    } catch (error) {
      console.error(`${color.red('✗')} Error generating Python BDD report:`, error.message);
    }
  } else {
    console.warn(`${color.yellow('!')} Python BDD report script not found: ${pythonBddScript}`);
  }

  // Run standard test report generator
  const standardScript = path.join(__dirname, config.reportScripts.standard);
  if (fs.existsSync(standardScript)) {
    console.log(`Running ${color.cyan(config.reportScripts.standard)}...`);
    try {
      execSync(`node ${standardScript}`, {
        cwd: config.projectRoot,
        stdio: 'inherit'
      });
      console.log(`${color.green('✓')} Standard test report generated successfully.`);
    } catch (error) {
      console.error(`${color.red('✗')} Error generating standard test report:`, error.message);
    }
  } else {
    console.warn(`${color.yellow('!')} Standard test report script not found: ${standardScript}`);
  }
}

/**
 * Extract data from the Python BDD report
 */
function extractPythonBddData() {
  console.log(color.bold('Extracting Python BDD report data...'));

  const pythonReportPath = path.join(config.outputDir, 'python-bdd-report.html');

  if (!fs.existsSync(pythonReportPath)) {
    console.warn(`${color.yellow('!')} Python BDD report not found: ${pythonReportPath}`);
    return null;
  }

  try {
    const content = fs.readFileSync(pythonReportPath, 'utf8');

    // Extract key statistics
    const totalStepsMatch = content.match(/Total Step Definitions: <strong>(\d+)<\/strong>/);
    const totalSteps = totalStepsMatch ? parseInt(totalStepsMatch[1]) : 0;

    const neededStepsMatch = content.match(/of <strong>(\d+)<\/strong> needed steps/);
    const neededSteps = neededStepsMatch ? parseInt(neededStepsMatch[1]) : 0;

    const completionMatch = content.match(/Implementation Progress: <strong>(\d+)%<\/strong>/);
    const completionPercentage = completionMatch ? parseInt(completionMatch[1]) : 0;

    const redMatch = content.match(/RED: (\d+)<\/span>/);
    const redPhase = redMatch ? parseInt(redMatch[1]) : 0;

    const greenMatch = content.match(/GREEN: (\d+)<\/span>/);
    const greenPhase = greenMatch ? parseInt(greenMatch[1]) : 0;

    const refactorMatch = content.match(/REFACTOR: (\d+)<\/span>/);
    const refactorPhase = refactorMatch ? parseInt(refactorMatch[1]) : 0;

    // Process category data
    const categoryStats = {};
    const categoryRegex = /<h3>(.+?)<\/h3>[\s\S]*?<p>Steps: (\d+) \/ (\d+) \((\d+)% complete\)<\/p>/g;
    let categoryMatch;

    while ((categoryMatch = categoryRegex.exec(content)) !== null) {
      const category = categoryMatch[1];
      const implemented = parseInt(categoryMatch[2]);
      const needed = parseInt(categoryMatch[3]);
      const completion = parseInt(categoryMatch[4]);

      // Extract phase details for this category
      const categoryContent = content.substring(categoryMatch.index, content.indexOf('</div>', categoryMatch.index));
      const categoryRedMatch = categoryContent.match(/RED: (\d+)<\/span>/);
      const categoryGreenMatch = categoryContent.match(/GREEN: (\d+)<\/span>/);
      const categoryRefactorMatch = categoryContent.match(/REFACTOR: (\d+)<\/span>/);

      categoryStats[category] = {
        total: implemented,
        needed: needed,
        completion: completion,
        red: categoryRedMatch ? parseInt(categoryRedMatch[1]) : 0,
        green: categoryGreenMatch ? parseInt(categoryGreenMatch[1]) : 0,
        refactor: categoryRefactorMatch ? parseInt(categoryRefactorMatch[1]) : 0
      };
    }

    return {
      summary: {
        totalSteps,
        neededSteps,
        completionPercentage,
        redPhase,
        greenPhase,
        refactorPhase
      },
      categories: categoryStats
    };
  } catch (error) {
    console.error(`${color.red('✗')} Error extracting Python BDD data:`, error.message);
    return null;
  }
}

/**
 * Extract data from the standard test report
 */
function extractStandardReportData() {
  console.log(color.bold('Extracting standard test report data...'));

  const standardReportPath = path.join(config.outputDir, 'test_report.html');

  if (!fs.existsSync(standardReportPath)) {
    console.warn(`${color.yellow('!')} Standard test report not found: ${standardReportPath}`);
    return null;
  }

  try {
    const content = fs.readFileSync(standardReportPath, 'utf8');

    // Extract summary statistics (simplified, would need more parsing for complete data)
    const completionMatch = content.match(/Overall Progress: (\d+)%/);
    const overallCompletion = completionMatch ? parseInt(completionMatch[1]) : 0;

    return {
      overallCompletion,
      originalHtml: content
    };
  } catch (error) {
    console.error(`${color.red('✗')} Error extracting standard report data:`, error.message);
    return null;
  }
}

/**
 * Generate the combined HTML report
 */
function generateCombinedReport() {
  // Get data from individual reports
  const pythonData = extractPythonBddData();
  const standardData = extractStandardReportData();

  if (!pythonData && !standardData) {
    console.error(`${color.red('✗')} Could not generate combined report: No data available`);
    return;
  }

  // Calculate overall statistics
  const overallStats = {
    pythonBddCompletion: pythonData ? pythonData.summary.completionPercentage : 0,
    standardReportCompletion: standardData ? standardData.overallCompletion : 0,
    // Simple weighted average (adjust weights as needed)
    overallCompletion: Math.round(
      ((pythonData ? pythonData.summary.completionPercentage : 0) +
       (standardData ? standardData.overallCompletion : 0)) /
      ((pythonData ? 1 : 0) + (standardData ? 1 : 0) || 1)
    )
  };

  // Generate the HTML
  const combinedHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IoTSphere Combined Test Report</title>
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
    .nav-tabs {
      display: flex;
      list-style: none;
      padding: 0;
      margin: 0 0 20px 0;
      border-bottom: 1px solid #dee2e6;
    }
    .nav-tabs li {
      margin-right: 5px;
    }
    .nav-tabs a {
      display: block;
      padding: 10px 15px;
      text-decoration: none;
      color: #495057;
      background-color: #f8f9fa;
      border: 1px solid #dee2e6;
      border-radius: 5px 5px 0 0;
    }
    .nav-tabs a.active {
      background-color: white;
      border-bottom-color: white;
      color: #007bff;
    }
    .tab-content {
      padding: 20px;
      border: 1px solid #dee2e6;
      border-top: none;
    }
    .tab-pane {
      display: none;
    }
    .tab-pane.active {
      display: block;
    }
    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .dashboard-card {
      border: 1px solid #dee2e6;
      border-radius: 5px;
      padding: 15px;
      background: white;
    }
    .dashboard-card h3 {
      margin-top: 0;
      border-bottom: 1px solid #eee;
      padding-bottom: 10px;
    }
    iframe {
      width: 100%;
      height: 800px;
      border: 1px solid #dee2e6;
    }
  </style>
</head>
<body>
  <h1>IoTSphere Combined Test Report</h1>

  <div class="summary">
    <h2>Overall Project Status</h2>
    <p>Test-Driven Development Progress</p>

    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress" style="width: ${overallStats.overallCompletion}%">${overallStats.overallCompletion}% Complete</div>
      </div>
    </div>

    <div class="dashboard-grid">
      ${pythonData ? `
      <div class="dashboard-card">
        <h3>Python BDD Test Status</h3>
        <p>Implementation: <strong>${pythonData.summary.completionPercentage}%</strong></p>
        <div class="progress-bar">
          <div class="progress" style="width: ${pythonData.summary.completionPercentage}%">${pythonData.summary.completionPercentage}%</div>
        </div>
        <p>TDD Phase Breakdown:</p>
        <p>
          <span class="phase-indicator red">RED: ${pythonData.summary.redPhase}</span>
          <span class="phase-indicator green">GREEN: ${pythonData.summary.greenPhase}</span>
          <span class="phase-indicator yellow">REFACTOR: ${pythonData.summary.refactorPhase}</span>
        </p>
      </div>
      ` : ''}

      ${standardData ? `
      <div class="dashboard-card">
        <h3>Standard Test Status</h3>
        <p>Implementation: <strong>${standardData.overallCompletion}%</strong></p>
        <div class="progress-bar">
          <div class="progress" style="width: ${standardData.overallCompletion}%">${standardData.overallCompletion}%</div>
        </div>
      </div>
      ` : ''}
    </div>
  </div>

  <ul class="nav-tabs">
    <li><a href="#combined" class="active">Combined Dashboard</a></li>
    <li><a href="#python-bdd">Python BDD Tests</a></li>
    <li><a href="#standard">Standard Test Report</a></li>
  </ul>

  <div class="tab-content">
    <div id="combined" class="tab-pane active">
      <h2>Combined TDD Progress Dashboard</h2>

      <div class="dashboard-grid">
        ${pythonData ? Object.entries(pythonData.categories).map(([category, stats]) => {
          const completionPercent = stats.completion || 0;
          const greenPercent = stats.needed > 0 ? Math.round((stats.green / stats.needed) * 100) : 0;

          return `
            <div class="dashboard-card">
              <h3>${category}</h3>
              <p>Implementation: <strong>${completionPercent}%</strong></p>
              <div class="progress-bar">
                <div class="progress" style="width: ${completionPercent}%">${completionPercent}%</div>
              </div>
              <p>GREEN Phase: <strong>${greenPercent}%</strong></p>
              <div class="progress-bar">
                <div class="progress green" style="width: ${greenPercent}%">${greenPercent}%</div>
              </div>
              <p>Steps: ${stats.total} / ${stats.needed}</p>
              <p>
                <span class="phase-indicator red">RED: ${stats.red}</span>
                <span class="phase-indicator green">GREEN: ${stats.green}</span>
                <span class="phase-indicator yellow">REFACTOR: ${stats.refactor}</span>
              </p>
            </div>
          `;
        }).join('') : '<p>No Python BDD data available</p>'}
      </div>
    </div>

    <div id="python-bdd" class="tab-pane">
      <h2>Python BDD Test Report</h2>
      <iframe src="python-bdd-report.html" title="Python BDD Test Report"></iframe>
    </div>

    <div id="standard" class="tab-pane">
      <h2>Standard Test Report</h2>
      <iframe src="test_report.html" title="Standard Test Report"></iframe>
    </div>
  </div>

  <script>
    // Simple tab navigation
    document.addEventListener('DOMContentLoaded', function() {
      const tabs = document.querySelectorAll('.nav-tabs a');

      tabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
          e.preventDefault();

          // Remove active class from all tabs and panes
          tabs.forEach(t => t.classList.remove('active'));
          document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

          // Add active class to current tab and pane
          this.classList.add('active');
          const target = this.getAttribute('href').substring(1);
          document.getElementById(target).classList.add('active');
        });
      });
    });
  </script>

  <p><em>Report generated on ${new Date().toLocaleString()}</em></p>
</body>
</html>`;

  // Write the combined report to file
  const outputPath = path.join(config.outputDir, 'combined-test-report.html');
  try {
    fs.writeFileSync(outputPath, combinedHtml);
    console.log(`${color.green('✓')} Combined report generated: ${outputPath}`);
  } catch (error) {
    console.error(`${color.red('✗')} Error writing combined report:`, error.message);
  }
}

/**
 * Main function to run the entire process
 */
function main() {
  console.log(color.bold('=== IoTSphere Combined Test Report Generator ==='));

  // Generate individual reports
  generateIndividualReports();

  // Generate combined report
  generateCombinedReport();

  console.log(color.bold('=== Report Generation Complete ==='));
}

// Run if called directly
if (require.main === module) {
  main();
}
