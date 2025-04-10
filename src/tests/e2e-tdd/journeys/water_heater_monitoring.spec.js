/**
 * @file Water Heater Monitoring E2E Test
 * @description Tests the end-to-end flow of a facility manager monitoring water heaters
 * @phase green - This test validates the implemented behavior
 */

// Import page objects
import DashboardPage from '../page-objects/DashboardPage';
import WaterHeaterDetailsPage from '../page-objects/WaterHeaterDetailsPage';

// @green - Test in GREEN phase of TDD cycle
describe('Water Heater Monitoring Journey', () => {
  beforeEach(() => {
    // Load and use the facility manager fixture
    cy.fixture('users/facility_manager.json').as('user');
    cy.login('@user');

    // Set up the test data for a water heater with abnormal temperature
    cy.fixture('water_heaters/abnormal_temperature.json').as('waterHeater');
    cy.setupTestWaterHeater('@waterHeater');
  });

  it('allows a facility manager to detect and respond to an abnormal temperature', () => {
    // ======= DASHBOARD NAVIGATION =======
    // User navigates to the dashboard
    DashboardPage.visit();

    // Verify water heaters are displayed with status indicators
    DashboardPage.getWaterHeaterList().should('be.visible');
    DashboardPage.getAlertIndicators().should('have.class', 'warning');

    // ======= WATER HEATER SELECTION =======
    // User selects the water heater with an issue
    DashboardPage.selectWaterHeaterWithIssue('warning');

    // Verify we're on the correct water heater details page
    WaterHeaterDetailsPage.getHeaterName().should('contain', 'Main Building Water Heater');

    // ======= OPERATIONS TAB =======
    // Navigate to the operations tab
    WaterHeaterDetailsPage.selectTab('operations');

    // Verify temperature information is displayed correctly
    WaterHeaterDetailsPage.getTemperatureGauge().should('be.visible');
    WaterHeaterDetailsPage.getTemperatureValue().should('contain', '155°F');
    WaterHeaterDetailsPage.getTemperatureStatus().should('contain', 'Above Normal');

    // ======= TEMPERATURE ADJUSTMENT =======
    // Perform a complete temperature adjustment
    WaterHeaterDetailsPage.adjustTemperature(125);

    // ======= OUTCOME VERIFICATION =======
    // Verify the adjustment was processed correctly
    WaterHeaterDetailsPage.getCommandStatus().should('contain', 'Temperature adjustment sent');
    WaterHeaterDetailsPage.getHeaterStatus().should('contain', 'Adjustment in progress');

    // Wait for adjustment to complete and verify results
    WaterHeaterDetailsPage.waitForAdjustmentComplete();
    WaterHeaterDetailsPage.getTemperatureValue().should('contain', '125°F');
    WaterHeaterDetailsPage.getTemperatureStatus().should('contain', 'Normal');
  });

  it('notifies facility manager of critical temperature conditions requiring immediate attention', () => {
    // Set up a water heater with critical temperature issue
    cy.fixture('water_heaters/critical_temperature.json').as('criticalHeater');
    cy.get('@criticalHeater').then((criticalHeater) => {
      cy.setupTestWaterHeater(criticalHeater);
    });

    // ======= DASHBOARD NAVIGATION =======
    // User navigates to the dashboard
    DashboardPage.visit();

    // Verify water heaters are displayed with critical status indicators
    DashboardPage.getWaterHeaterList().should('be.visible');
    DashboardPage.getAlertIndicators().should('have.class', 'critical');

    // ======= ALERT NOTIFICATION =======
    // Verify critical alert notification is shown
    DashboardPage.getAlertNotifications().should('be.visible');
    DashboardPage.getAlertNotifications().should('contain', 'Critical Temperature');

    // ======= WATER HEATER SELECTION =======
    // User selects the water heater with a critical issue
    DashboardPage.selectWaterHeaterWithIssue('critical');

    // Verify we're on the correct water heater details page
    WaterHeaterDetailsPage.getHeaterName().should('be.visible');
    WaterHeaterDetailsPage.getHeaterStatus().should('contain', 'CRITICAL');

    // ======= EMERGENCY ACTIONS =======
    // Check that emergency action options are available
    WaterHeaterDetailsPage.getEmergencyActions().should('be.visible');

    // Perform emergency shutdown
    WaterHeaterDetailsPage.initiateEmergencyShutdown();

    // Verify confirmation dialog appears
    WaterHeaterDetailsPage.getConfirmationDialog().should('be.visible');
    WaterHeaterDetailsPage.getConfirmationDialog().should('contain', 'Emergency Shutdown');

    // Confirm shutdown
    WaterHeaterDetailsPage.confirmAction();

    // Verify shutdown was initiated
    WaterHeaterDetailsPage.getActionStatus().should('contain', 'Emergency shutdown initiated');
    WaterHeaterDetailsPage.getHeaterStatus().should('contain', 'SHUTTING DOWN');
  });

  // Additional user journey moved to implementation phase
  it('allows facility manager to schedule maintenance based on predictive analytics', () => {
    // ======= DASHBOARD NAVIGATION =======
    // User navigates to the dashboard
    DashboardPage.visit();

    // ======= MAINTENANCE TAB =======
    // Navigate to the maintenance planning section
    DashboardPage.selectMaintenanceTab();

    // Verify predictive analytics section is visible
    DashboardPage.getPredictiveAnalyticsSection().should('be.visible');

    // Check for water heaters with maintenance recommendations
    DashboardPage.getWaterHeatersNeedingMaintenance().should('have.length.at.least', 1);

    // ======= MAINTENANCE SCHEDULING =======
    // Select the first water heater needing maintenance
    DashboardPage.selectWaterHeaterForMaintenance(0);

    // View the maintenance details
    DashboardPage.getMaintenanceRecommendation().should('contain', 'Recommended');

    // Schedule maintenance
    DashboardPage.openMaintenanceScheduler();
    DashboardPage.selectMaintenanceDate('next-week');
    DashboardPage.selectMaintenanceTechnician('John Smith');
    DashboardPage.scheduleMaintenanceTask();

    // Verify the maintenance was scheduled
    DashboardPage.getScheduleConfirmation().should('be.visible');
    DashboardPage.getScheduleConfirmation().should('contain', 'Maintenance scheduled');
  });
});
