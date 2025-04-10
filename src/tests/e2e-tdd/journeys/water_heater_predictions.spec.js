/**
 * @file Water Heater Predictions E2E Test
 * @description Tests the end-to-end flow of a facility manager using predictive maintenance features
 * @phase red - This test defines the expected behavior that is not yet implemented
 */

// Import page objects
import DashboardPage from '../page-objects/DashboardPage';
import WaterHeaterDetailsPage from '../page-objects/WaterHeaterDetailsPage';
import PredictionsPage from '../page-objects/PredictionsPage';

// @red - Test in RED phase of TDD cycle
describe('Water Heater Predictive Maintenance Journey', () => {
  beforeEach(() => {
    // Load and use the facility manager fixture
    cy.fixture('users/facility_manager.json').as('user');
    cy.login('@user');

    // Set up the test data for a water heater with maintenance predictions
    cy.fixture('water_heaters/with_predictions.json').as('waterHeater');
    cy.setupTestWaterHeater('@waterHeater');
  });

  it('allows a facility manager to view predictive maintenance data for a water heater', () => {
    // ======= DASHBOARD NAVIGATION =======
    // User navigates to the dashboard
    DashboardPage.visit();

    // Verify water heaters are displayed
    DashboardPage.getWaterHeaterList().should('be.visible');

    // ======= WATER HEATER SELECTION =======
    // User selects a water heater
    DashboardPage.selectWaterHeater('Main Building Water Heater');

    // Verify we're on the correct water heater details page
    WaterHeaterDetailsPage.getHeaterName().should('contain', 'Main Building Water Heater');

    // ======= PREDICTIONS TAB =======
    // Navigate to the predictions tab
    WaterHeaterDetailsPage.selectTab('predictions');

    // Verify predictions content is loaded
    PredictionsPage.getPredictionsContent().should('be.visible');
    
    // ======= LIFESPAN PREDICTION =======
    // Verify lifespan prediction is displayed
    PredictionsPage.getLifespanPrediction().should('be.visible');
    PredictionsPage.getLifespanRemainingDays().should('be.visible');
    PredictionsPage.getLifespanConfidence().should('be.visible');
    
    // ======= ANOMALY DETECTION =======
    // Verify anomaly detection is displayed
    PredictionsPage.getAnomalyDetection().should('be.visible');
    PredictionsPage.getAnomalyList().should('be.visible');
    
    // ======= USAGE PATTERNS =======
    // Verify usage pattern analysis is displayed
    PredictionsPage.getUsagePatterns().should('be.visible');
    PredictionsPage.getUsagePatternChart().should('be.visible');
    
    // ======= MULTI-FACTOR ANALYSIS =======
    // Verify multi-factor analysis is displayed
    PredictionsPage.getMultiFactorAnalysis().should('be.visible');
    PredictionsPage.getMaintenanceRecommendation().should('be.visible');
    
    // ======= REFRESH PREDICTIONS =======
    // Test refresh functionality
    PredictionsPage.clickRefreshButton();
    PredictionsPage.getRefreshIndicator().should('be.visible');
    // Wait for refresh to complete
    PredictionsPage.getRefreshIndicator().should('not.exist');
  });

  it('displays appropriate maintenance recommendations based on prediction data', () => {
    // ======= DASHBOARD NAVIGATION =======
    DashboardPage.visit();
    DashboardPage.selectWaterHeater('Main Building Water Heater');
    WaterHeaterDetailsPage.selectTab('predictions');
    
    // ======= RECOMMENDATIONS VERIFICATION =======
    // Verify maintenance recommendations are displayed
    PredictionsPage.getMaintenanceRecommendation().should('be.visible');
    PredictionsPage.getMaintenanceRecommendation().should('contain', 'Recommended');
    
    // Verify recommendation details
    PredictionsPage.expandRecommendationDetails();
    PredictionsPage.getRecommendationDetails().should('be.visible');
    PredictionsPage.getRecommendationDetails().should('contain', 'maintenance schedule');
    
    // Verify action buttons
    PredictionsPage.getScheduleMaintenanceButton().should('be.visible');
    PredictionsPage.getDismissRecommendationButton().should('be.visible');
    
    // Test scheduling maintenance
    PredictionsPage.clickScheduleMaintenanceButton();
    PredictionsPage.getMaintenanceSchedulingDialog().should('be.visible');
    PredictionsPage.selectMaintenanceDate('next-available');
    PredictionsPage.confirmMaintenanceScheduling();
    
    // Verify confirmation message
    PredictionsPage.getConfirmationMessage().should('contain', 'Maintenance scheduled');
  });
});
