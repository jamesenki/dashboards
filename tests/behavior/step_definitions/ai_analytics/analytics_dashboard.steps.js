/**
 * Step definitions for analytics dashboard display and visualization scenarios
 */
const { Then } = require('@cucumber/cucumber');
// Using async import for Chai (ES module)
let expect;
import('chai').then(chai => {
  expect = chai.expect;
});

/**
 * Verify business intelligence analytics dashboard display content
 */
Then('the business intelligence analytics dashboard should display:', function(dataTable) {
  const dashboardContent = {
    kpis: [
      { name: 'Energy Efficiency', value: '82%', trend: 'up', timeRange: '30 days' },
      { name: 'Maintenance Cost', value: '$12,450', trend: 'down', timeRange: '90 days' },
      { name: 'Uptime', value: '99.2%', trend: 'up', timeRange: '30 days' }
    ],
    charts: [
      {
        type: 'line',
        title: 'Energy Consumption Trends',
        dataPoints: 90,
        hasComparison: true
      },
      {
        type: 'bar',
        title: 'Device Performance by Type',
        dataPoints: 12,
        hasComparison: true
      },
      {
        type: 'pie',
        title: 'Operational Cost Breakdown',
        dataPoints: 6,
        hasComparison: false
      }
    ],
    alerts: [
      {
        type: 'warning',
        message: 'Energy consumption above threshold in Building A',
        timestamp: new Date().toISOString(),
        actionable: true
      },
      {
        type: 'info',
        message: 'Predictive maintenance opportunity identified',
        timestamp: new Date().toISOString(),
        actionable: true
      }
    ]
  };

  // Store the dashboard content in test context
  this.testContext.dashboardContent = dashboardContent;

  // Check that all required elements from the data table are present
  const requirements = dataTable.rowsHash();

  for (const [metricType, description] of Object.entries(requirements)) {
    switch(metricType) {
      case 'keyPerformanceIndicators':
        expect(dashboardContent).to.have.property('kpis');
        expect(dashboardContent.kpis).to.be.an('array').with.length.greaterThan(0);
        break;
      case 'trendCharts':
        expect(dashboardContent).to.have.property('charts');
        expect(dashboardContent.charts).to.be.an('array').with.length.greaterThan(0);
        // Verify we have at least one line chart for trends
        expect(dashboardContent.charts.some(chart => chart.type === 'line')).to.be.true;
        break;
      case 'deviceComparisons':
        expect(dashboardContent).to.have.property('charts');
        // Verify we have at least one chart with comparison capability
        expect(dashboardContent.charts.some(chart => chart.hasComparison)).to.be.true;
        break;
      case 'anomalyAlerts':
        expect(dashboardContent).to.have.property('alerts');
        expect(dashboardContent.alerts).to.be.an('array').with.length.greaterThan(0);
        break;
      case 'actionableInsights':
        expect(dashboardContent).to.have.property('alerts');
        // Verify we have at least one actionable alert/insight
        expect(dashboardContent.alerts.some(alert => alert.actionable)).to.be.true;
        break;
    }
  }

  return 'pending'; // Mark as pending since this is just a stub implementation
});
