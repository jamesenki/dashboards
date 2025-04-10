/**
 * Test Report Patch for IoTSphere Project
 *
 * This script fixes integration issues with Python BDD test reporting
 * and provides a way to combine all test reports into a single unified view
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Import the Python BDD report data
function importPythonBddReport() {
  console.log('Importing Python BDD report data...');

  // Check if Python BDD HTML report exists
  const pythonReportPath = path.resolve(__dirname, '../test-reports/python-bdd-report.html');
  if (!fs.existsSync(pythonReportPath)) {
    console.log('Python BDD report not found. Run python-bdd-report-v3.js first.');
    return null;
  }

  // Parse the report to extract data (simplified version)
  const content = fs.readFileSync(pythonReportPath, 'utf8');

  // Extract key statistics using regex
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
  const categoryRegex = /<h3>(.+?)<\/h3>\s*<p>Steps: (\d+) \/ (\d+) \((\d+)% complete\)<\/p>/g;
  let categoryMatch;

  while ((categoryMatch = categoryRegex.exec(content)) !== null) {
    const category = categoryMatch[1];
    const implemented = parseInt(categoryMatch[2]);
    const needed = parseInt(categoryMatch[3]);
    const completion = parseInt(categoryMatch[4]);

    categoryStats[category] = {
      total: implemented,
      needed: needed,
      completion: completion,
      // Simplified, would need more parsing for precise numbers
      red: 0,
      green: 0,
      refactor: 0
    };
  }

  // Parse phase details for each category (simplified)
  Object.keys(categoryStats).forEach(category => {
    const categoryRegexPhase = new RegExp(`<h3>${category}<\/h3>[\\s\\S]*?RED: (\\d+), GREEN: (\\d+), REFACTOR: (\\d+)`, 'i');
    const phaseMatch = content.match(categoryRegexPhase);

    if (phaseMatch) {
      categoryStats[category].red = parseInt(phaseMatch[1]);
      categoryStats[category].green = parseInt(phaseMatch[2]);
      categoryStats[category].refactor = parseInt(phaseMatch[3]);
    }
  });

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
}

// Generate an integrated report using both Python and JS data
function generateIntegratedReport() {
  console.log('Generating integrated test report...');

  // Get Python BDD data
  const pythonData = importPythonBddReport();
  if (!pythonData) {
    console.log('Cannot continue without Python BDD data');
    return;
  }

  // Create a directory for the integrated report
  const outputDir = path.resolve(__dirname, '../test-reports');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Generate the HTML report
  const htmlReport = generateIntegratedHtml(pythonData);

  // Write the HTML report
  const reportPath = path.resolve(outputDir, 'integrated-test-report.html');
  fs.writeFileSync(reportPath, htmlReport);

  console.log(`Integrated test report generated at: ${reportPath}`);

  // Also generate a console summary
  generateConsoleSummary(pythonData);
}

// Generate a console summary of the integrated report
function generateConsoleSummary(pythonData) {
  console.log('\n===== IoTSphere Integrated Test Report =====');
  console.log('\nPython BDD Tests:');
  console.log(`- Total Steps: ${pythonData.summary.totalSteps} / ${pythonData.summary.neededSteps} (${pythonData.summary.completionPercentage}% complete)`);
  console.log(`- TDD Phase: RED: ${pythonData.summary.redPhase}, GREEN: ${pythonData.summary.greenPhase}, REFACTOR: ${pythonData.summary.refactorPhase}`);

  console.log('\nCategory Breakdown:');
  Object.entries(pythonData.categories).forEach(([category, stats]) => {
    console.log(`- ${category}: ${stats.total} / ${stats.needed} steps (${stats.completion}% complete)`);
    console.log(`  RED: ${stats.red}, GREEN: ${stats.green}, REFACTOR: ${stats.refactor}`);
  });

  console.log('\n==========================================');
}

// Generate HTML for the integrated report
function generateIntegratedHtml(pythonData) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IoTSphere Integrated Test Report</title>
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
  </style>
</head>
<body>
  <h1>IoTSphere Integrated Test Report</h1>

  <div class="summary">
    <h2>Overall Project Status</h2>
    <p>Test-Driven Development Progress</p>

    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress" style="width: ${pythonData.summary.completionPercentage}%">${pythonData.summary.completionPercentage}% Complete</div>
      </div>
    </div>

    <h3>TDD Phase Breakdown</h3>
    <p>
      <span class="phase-indicator red">RED: ${pythonData.summary.redPhase}</span>
      <span class="phase-indicator green">GREEN: ${pythonData.summary.greenPhase}</span>
      <span class="phase-indicator yellow">REFACTOR: ${pythonData.summary.refactorPhase}</span>
    </p>
  </div>

  <ul class="nav-tabs">
    <li><a href="#python-bdd" class="active">Python BDD Tests</a></li>
    <li><a href="#js-bdd">JavaScript BDD Tests</a></li>
    <li><a href="#e2e">E2E Tests</a></li>
    <li><a href="#unit">Unit Tests</a></li>
    <li><a href="#integration">Integration Tests</a></li>
  </ul>

  <div class="tab-content">
    <div id="python-bdd" class="tab-pane active">
      <h2>Python BDD Test Status</h2>
      <p>Total Steps: <strong>${pythonData.summary.totalSteps}</strong> of <strong>${pythonData.summary.neededSteps}</strong> needed steps</p>
      <p>Implementation Progress: <strong>${pythonData.summary.completionPercentage}%</strong></p>

      <h3>Category Implementation Progress</h3>
      ${Object.entries(pythonData.categories)
        .map(([category, stats]) => {
          const completionPercent = stats.completion || 0;
          const greenPercent = stats.needed > 0 ? Math.round((stats.green / stats.needed) * 100) : 0;

          return `
            <div class="category-section">
              <h4>${category}</h4>
              <p>Steps: ${stats.total} / ${stats.needed} (${completionPercent}% complete)</p>
              <div class="progress-bar">
                <div class="progress" style="width: ${completionPercent}%">${completionPercent}%</div>
              </div>
              <p>GREEN Phase: ${stats.green} / ${stats.needed} (${greenPercent}%)</p>
              <div class="progress-bar">
                <div class="progress green" style="width: ${greenPercent}%">${greenPercent}%</div>
              </div>
              <p>Phase Breakdown:
                <span class="phase-indicator red">RED: ${stats.red}</span>
                <span class="phase-indicator green">GREEN: ${stats.green}</span>
                <span class="phase-indicator yellow">REFACTOR: ${stats.refactor}</span>
              </p>
            </div>
          `;
        }).join('')}
    </div>

    <div id="js-bdd" class="tab-pane">
      <h2>JavaScript BDD Test Status</h2>
      <p>Data will be imported from original test report</p>
      <!-- This section would be populated with JavaScript BDD test data -->
    </div>

    <div id="e2e" class="tab-pane">
      <h2>E2E Test Status</h2>
      <p>Data will be imported from original test report</p>
      <!-- This section would be populated with E2E test data -->
    </div>

    <div id="unit" class="tab-pane">
      <h2>Unit Test Status</h2>
      <p>Data will be imported from original test report</p>
      <!-- This section would be populated with unit test data -->
    </div>

    <div id="integration" class="tab-pane">
      <h2>Integration Test Status</h2>
      <p>Data will be imported from original test report</p>
      <!-- This section would be populated with integration test data -->
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
}

// Run the report generation if this file is executed directly
if (require.main === module) {
  generateIntegratedReport();
}
