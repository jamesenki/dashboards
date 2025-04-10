/**
 * E2E Test for Shadow Data Flow
 * 
 * This test validates the complete user journey for shadow data flow from 
 * MongoDB to the UI through the message broker pattern.
 * 
 * Following Clean Architecture principles, this test operates at the UI level
 * and verifies business outcomes rather than implementation details.
 * 
 * @red - Initial implementation; test should fail until message broker pattern is fully integrated
 */

import { DashboardPage } from '../page-objects/DashboardPage';
import { WaterHeaterDetailsPage } from '../page-objects/WaterHeaterDetailsPage';

describe('Device Shadow Real-Time Updates', () => {
  before(() => {
    // Reset any mock data to ensure clean test environment
    cy.task('resetTestData', { timeout: 10000 });
  });

  it('updates temperature in real-time when shadow document changes', () => {
    // ======= ARRANGE: Start with baseline state =======
    // Visit the water heater dashboard
    DashboardPage.visit();
    
    // Select the test water heater
    const testHeaterId = 'wh-12347';
    DashboardPage.getWaterHeaterById(testHeaterId).should('be.visible');
    DashboardPage.getWaterHeaterById(testHeaterId).click();
    
    // Verify we're on the details page
    WaterHeaterDetailsPage.getHeaterName().should('contain', 'Main Building Water Heater');
    
    // Get initial temperature
    WaterHeaterDetailsPage.getTemperatureValue().then($temp => {
      const initialTemp = parseFloat($temp.text());
      cy.log(`Initial temperature: ${initialTemp}°C`);
      
      // ======= ACT: Trigger a shadow update =======
      // Use a custom task to update the shadow in MongoDB
      // This simulates an external device sending telemetry data
      const newTemp = initialTemp + 5.0;
      cy.task('updateDeviceShadow', {
        deviceId: testHeaterId,
        update: {
          telemetry: {
            temperature: newTemp
          }
        }
      }, { timeout: 10000 });
      
      // ======= ASSERT: Verify UI updates in real-time =======
      // The UI should update within 3 seconds via WebSocket without page refresh
      cy.log('Waiting for WebSocket update...');
      
      // Wait for the temperature value to change
      WaterHeaterDetailsPage.getTemperatureValue().should('not.have.text', initialTemp, { timeout: 5000 });
      
      // Verify the new temperature appears
      WaterHeaterDetailsPage.getTemperatureValue().should('contain', newTemp, { timeout: 5000 });
      
      // Verify the gauge updates
      WaterHeaterDetailsPage.getTemperatureGauge().should('be.visible');
    });
  });

  it('updates alert status in real-time when critical condition occurs', () => {
    // ======= ARRANGE: Start with baseline state =======
    // Visit the water heater dashboard
    DashboardPage.visit();
    
    // Select a test water heater
    const testHeaterId = 'wh-12347';
    DashboardPage.getWaterHeaterById(testHeaterId).should('be.visible');
    
    // Get initial alert state
    DashboardPage.getAlertIndicatorForHeater(testHeaterId).then($alert => {
      const initialAlertClass = $alert.attr('class');
      cy.log(`Initial alert class: ${initialAlertClass}`);
      
      // ======= ACT: Trigger a shadow update with critical status =======
      cy.task('updateDeviceShadow', {
        deviceId: testHeaterId,
        update: {
          status: {
            operational: true,
            alert_level: 'critical',
            condition: 'critical_temperature'
          },
          telemetry: {
            temperature: 190,
            target_temperature: 120
          }
        }
      }, { timeout: 10000 });
      
      // ======= ASSERT: Verify UI updates in real-time =======
      // Alert indicator should change to critical without page refresh
      cy.log('Waiting for WebSocket update to alert status...');
      
      // Wait for alert class to change
      DashboardPage.getAlertIndicatorForHeater(testHeaterId)
        .should('have.class', 'critical', { timeout: 5000 });
    });
  });

  it('maintains shadow updates across page navigation', () => {
    // ======= ARRANGE: Start with updated shadow =======
    // Visit the water heater dashboard
    DashboardPage.visit();
    
    // Verify updated temperature is still showing for our test heater
    const testHeaterId = 'wh-12347';
    DashboardPage.getWaterHeaterById(testHeaterId).should('be.visible');
    DashboardPage.getTemperatureForHeater(testHeaterId).should('contain', '190');
    
    // ======= ACT: Navigate away and back =======
    // Navigate to another page
    cy.visit('/diagnostic');
    
    // Navigate back to dashboard
    DashboardPage.visit();
    
    // ======= ASSERT: Verify data persistence =======
    // Verify the updated values are still shown
    DashboardPage.getWaterHeaterById(testHeaterId).should('be.visible');
    DashboardPage.getTemperatureForHeater(testHeaterId).should('contain', '190');
    DashboardPage.getAlertIndicatorForHeater(testHeaterId).should('have.class', 'critical');
  });
});
