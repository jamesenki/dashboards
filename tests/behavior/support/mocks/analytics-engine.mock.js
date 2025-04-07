/**
 * Mock Analytics Engine
 * 
 * This file provides a mock implementation of the analytics and AI engine
 * for use in BDD tests. It simulates predictive analytics, anomaly detection,
 * and other AI/ML capabilities without requiring the actual implementation.
 */

function mockAnalyticsEngine() {
  // Mock data for device performance insights
  const devicePerformanceInsights = new Map();
  
  // Mock data for anomaly predictions
  const anomalyPredictions = new Map();
  
  // Mock data for performance optimization recommendations
  const optimizationRecommendations = new Map();
  
  // Mock data for predictive maintenance
  const maintenancePredictions = new Map();
  
  // Mock data for maintenance records
  const maintenanceRecords = new Map();
  
  // Mock knowledge base for storing knowledge entries
  const knowledgeBase = {
    entries: [
      {
        id: 'ke-001',
        title: 'Water Heater Diagnostic Procedure',
        category: 'maintenance',
        content: 'Detailed procedure for diagnosing common water heater issues',
        tags: ['diagnostics', 'water-heater', 'maintenance'],
        contributor: 'maintenance-expert-1',
        dateAdded: '2023-06-15',
        lastUpdated: '2023-07-20',
        deviceTypes: ['water-heater'],
        applicableModels: ['WH-1000', 'WH-2000', 'WH-3000'],
        verificationStatus: 'verified',
        usageCount: 47
      },
      {
        id: 'ke-002',
        title: 'Optimal Temperature Settings for Energy Efficiency',
        category: 'energy-optimization',
        content: 'Guidelines for setting optimal temperatures based on usage patterns and environmental conditions',
        tags: ['energy-efficiency', 'temperature', 'optimization'],
        contributor: 'energy-expert-1',
        dateAdded: '2023-05-10',
        lastUpdated: '2023-06-22',
        deviceTypes: ['water-heater', 'hvac'],
        applicableModels: ['WH-1000', 'WH-2000', 'AC-2000', 'AC-3000'],
        verificationStatus: 'verified',
        usageCount: 63
      },
      {
        id: 'ke-003',
        title: 'Vending Machine Restocking Best Practices',
        category: 'operation',
        content: 'Procedures for efficiently restocking vending machines with minimal downtime',
        tags: ['restocking', 'vending-machine', 'operations'],
        contributor: 'operations-manager-2',
        dateAdded: '2023-07-05',
        lastUpdated: '2023-07-05',
        deviceTypes: ['vending-machine'],
        applicableModels: ['VM-100', 'VM-200', 'VM-300'],
        verificationStatus: 'pending-review',
        usageCount: 12
      },
      {
        id: 'ke-004',
        title: 'Robotic Arm Calibration Process',
        category: 'maintenance',
        content: 'Step-by-step guide for calibrating robotic arms after maintenance or redeployment',
        tags: ['calibration', 'robotic-arm', 'precision'],
        contributor: 'robotics-engineer-1',
        dateAdded: '2023-04-18',
        lastUpdated: '2023-08-03',
        deviceTypes: ['robotic-arm'],
        applicableModels: ['RA-500', 'RA-700'],
        verificationStatus: 'verified',
        usageCount: 31
      }
    ],
    categories: [
      'maintenance', 
      'operation', 
      'installation', 
      'troubleshooting',
      'energy-optimization',
      'efficiency-degradation',
      'best-practices'
    ]
  };
  
  // Mock cross-device optimization data
  const fleetOptimizationData = new Map();
  
  // Mock date for maintenance (30 days ago)
  const maintenanceDate = new Date();
  maintenanceDate.setDate(maintenanceDate.getDate() - 30);
  
  return {
    // Anomaly Detection methods
    async predictAnomalies(deviceId, timeframe) {
      const deviceAnomalies = anomalyPredictions.get(deviceId) || [];
      return deviceAnomalies.filter(anomaly => 
        anomaly.predictedTimestamp >= timeframe.start && 
        anomaly.predictedTimestamp <= timeframe.end
      );
    },
    
    async detectCurrentAnomalies(deviceId) {
      const anomalies = anomalyPredictions.get(deviceId) || [];
      const now = new Date();
      
      // Return anomalies predicted to occur within 24 hours of now
      return anomalies.filter(anomaly => {
        const anomalyTime = new Date(anomaly.predictedTimestamp);
        const diffHours = Math.abs(anomalyTime - now) / 36e5; // convert ms to hours
        return diffHours <= 24;
      });
    },
    
    async getAnomalyHistory(deviceId, timeframe) {
      // This would return historical anomalies, different from predictions
      return [];
    },
    
    // Get operational analytics dashboard data for a fleet of devices
    async getOperationalAnalytics(deviceIds) {
      // Return a rich operational analytics object that aligns with the project's device-agnostic vision
      return {
        // Reliability metrics section
        reliabilityMetrics: {
          fleetUptime: 0.982, // 98.2% uptime
          meanTimeBetweenFailures: 4380, // hours (6 months)
          meanTimeToRepair: 3.4, // hours
          failureRates: {
            byDeviceType: {
              'water-heater': 0.021,
              'hvac': 0.024,
              'vending-machine': 0.018
            },
            byManufacturer: {
              'Rheem': 0.020,
              'AO Smith': 0.022,
              'Bradford White': 0.019
            }
          },
          reliabilityTrends: [
            { period: '2023-Q1', value: 0.975 },
            { period: '2023-Q2', value: 0.978 },
            { period: '2023-Q3', value: 0.980 },
            { period: '2023-Q4', value: 0.982 }
          ]
        },
        
        // Maintenance efficiency section
        maintenanceEfficiency: {
          preventiveVsReactive: {
            preventive: 78, // percent
            reactive: 22 // percent
          },
          maintenanceCostTrends: [
            { period: '2023-Q1', planned: 12400, unplanned: 8500 },
            { period: '2023-Q2', planned: 13100, unplanned: 7200 },
            { period: '2023-Q3', planned: 14500, unplanned: 5600 },
            { period: '2023-Q4', planned: 15200, unplanned: 4100 }
          ],
          averageRepairTime: 3.4, // hours
          maintenanceComplianceRate: 0.92, // 92%
          maintenanceEffectivenessScore: 87 // out of 100
        },
        
        // Performance trends section
        performanceTrends: {
          energyEfficiencyTrend: [
            { period: '2023-Q1', value: 0.76 },
            { period: '2023-Q2', value: 0.79 },
            { period: '2023-Q3', value: 0.82 },
            { period: '2023-Q4', value: 0.84 }
          ],
          operationalCapacity: 0.86, // 86% of maximum
          performanceByDeviceAge: [
            { ageGroup: '0-1 years', efficiency: 0.92 },
            { ageGroup: '1-3 years', efficiency: 0.87 },
            { ageGroup: '3-5 years', efficiency: 0.81 },
            { ageGroup: '5+ years', efficiency: 0.72 }
          ],
          keyPerformanceIndicators: {
            energyConsumption: { value: -8.4, trend: 'improving' }, // percent change year-over-year
            outputEfficiency: { value: 6.2, trend: 'improving' }, // percent change year-over-year
            cycleTime: { value: -3.1, trend: 'improving' } // percent change year-over-year
          }
        },
        
        // Cost breakdown section
        costBreakdown: {
          energyCosts: 42, // percent of total
          maintenanceCosts: 23, // percent of total
          replacementParts: 18, // percent of total
          operationalLabor: 12, // percent of total
          other: 5, // percent of total
          costPerOperatingHour: 0.87, // dollars
          costTrends: [
            { period: '2023-Q1', energy: 12400, maintenance: 7200, parts: 5100, labor: 3600 },
            { period: '2023-Q2', energy: 12100, maintenance: 7100, parts: 5000, labor: 3500 },
            { period: '2023-Q3', energy: 11700, maintenance: 6800, parts: 4800, labor: 3400 },
            { period: '2023-Q4', energy: 11200, maintenance: 6500, parts: 4600, labor: 3200 }
          ]
        },
        
        // Data sources and confidence section
        dataSources: {
          telemetryRecords: deviceIds.length * 24 * 180, // 6 months of hourly data per device
          telemetryDataPoints: deviceIds.length * 24 * 180, // Same as telemetryRecords for compatibility
          timeRange: {
            start: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000), // 180 days ago
            end: new Date() // now
          },
          deviceCoverage: 1.0, // 100% of requested devices included
          dataQualityScore: 0.94, // 94% quality score
          confidenceLevel: 0.92, // 92% confidence in analytics
          sources: ['telemetry', 'maintenance_records', 'device_specifications']
        },
        
        // Comparative benchmarks section
        benchmarks: {
          industryComparisons: {
            reliability: {
              industryAverage: 0.94, // 94% uptime
              topQuartile: 0.98, // 98% uptime
              yourFleet: 0.982 // 98.2% uptime
            },
            energyEfficiency: {
              industryAverage: 0.72, // 72% efficiency
              topQuartile: 0.85, // 85% efficiency
              yourFleet: 0.84 // 84% efficiency
            },
            maintenanceCosts: {
              industryAverage: '$0.95 per operating hour',
              topQuartile: '$0.76 per operating hour',
              yourFleet: '$0.82 per operating hour'
            }
          },
          historicalComparisons: {
            yearOverYear: {
              energyUsage: -8.4, // percent change
              maintenanceCosts: -12.8, // percent change
              downtime: -24.6 // percent change
            },
            quarterOverQuarter: {
              energyUsage: -2.1, // percent change
              maintenanceCosts: -3.2, // percent change
              downtime: -5.8 // percent change
            }
          },
          peerGroupComparisons: {
            similar: {
              description: 'Similar size and device mix',
              performanceIndex: 1.12, // 12% better than peers
              costIndex: 0.91 // 9% lower costs than peers
            },
            best: {
              description: 'Best in class',
              performanceGap: 0.05, // 5% below best performers
              improvementAreas: ['Preventive maintenance scheduling', 'Component standardization']
            }
          },
          comparisonSources: [
            'Industry association benchmarks',
            'Anonymized customer data',
            'Third-party research'
          ]
        },
        
        // Recommendations based on analytics
        recommendations: [
          {
            title: 'Optimize Maintenance Scheduling',
            description: 'Shift 10% more maintenance from reactive to preventive to reduce costs',
            potentialSavings: '~$15,000 annually',
            implementation: 'Medium',
            roi: 4.2 // 420% return
          },
          {
            title: 'Replace Aging Components',
            description: 'Replace heating elements in devices over 5 years old',
            potentialSavings: '~$8,500 annually in energy costs',
            implementation: 'Medium-High',
            roi: 2.8 // 280% return
          },
          {
            title: 'Standardize Operating Procedures',
            description: 'Implement temperature set points across all devices',
            potentialSavings: '~$6,200 annually',
            implementation: 'Low',
            roi: 8.5 // 850% return
          }
        ]
      };
    },
    
    addAnomalyPrediction(deviceId, anomaly) {
      if (!anomalyPredictions.has(deviceId)) {
        anomalyPredictions.set(deviceId, []);
      }
      anomalyPredictions.get(deviceId).push(anomaly);
    },
    
    // Performance Insights methods
    async getDevicePerformanceInsights(deviceId) {
      return devicePerformanceInsights.get(deviceId) || {
        efficiency: 0.82,
        utilizationRate: 0.76,
        comparisonToPeers: {
          percentile: 65,
          similarDevicesCount: 120
        },
        trends: {
          weekly: [0.81, 0.83, 0.82, 0.81, 0.82, 0.84, 0.82],
          monthly: [0.79, 0.80, 0.81, 0.82]
        }
      };
    },
    
    async compareDevicePerformance(deviceIds) {
      return deviceIds.map(id => ({
        deviceId: id,
        performance: {
          efficiency: Math.random() * 0.3 + 0.7, // 0.7-1.0
          reliability: Math.random() * 0.2 + 0.8, // 0.8-1.0
          utilization: Math.random() * 0.4 + 0.6  // 0.6-1.0
        }
      }));
    },
    
    setDevicePerformanceInsights(deviceId, insights) {
      devicePerformanceInsights.set(deviceId, insights);
    },
    
    // Optimization methods
    async getOptimizationRecommendations(deviceId) {
      return optimizationRecommendations.get(deviceId) || [
        {
          type: 'operationalHours',
          description: 'Adjust operational hours to match peak efficiency periods',
          potentialSavings: {
            energy: '12%',
            cost: '8.5%'
          },
          confidence: 0.85,
          implementation: 'Medium',
          roi: {
            value: 3.2,
            paybackPeriod: '4 months'
          }
        },
        {
          type: 'temperatureSettings',
          description: 'Optimize temperature settings based on usage patterns',
          potentialSavings: {
            energy: '7%',
            cost: '5.2%'
          },
          confidence: 0.92,
          implementation: 'Easy',
          roi: {
            value: 4.5,
            paybackPeriod: '2 months'
          }
        }
      ];
    },
    
    setOptimizationRecommendations(deviceId, recommendations) {
      optimizationRecommendations.set(deviceId, recommendations);
    },
    
    // Predictive Maintenance methods
    async getPredictiveMaintenance(deviceId) {
      return maintenancePredictions.get(deviceId) || {
        nextMaintenanceDate: (() => {
          const date = new Date();
          date.setDate(date.getDate() + 45);
          return date;
        })(),
        maintenanceType: 'Standard',
        criticalComponents: [
          {
            name: 'Heating Element',
            condition: 'Good',
            estimatedRemainingLife: '2 years'
          },
          {
            name: 'Thermostat',
            condition: 'Fair',
            estimatedRemainingLife: '1 year'
          },
          {
            name: 'Pressure Relief Valve',
            condition: 'Excellent',
            estimatedRemainingLife: '3 years'
          }
        ],
        recommendedActions: [
          'Inspect anode rod',
          'Check temperature and pressure valve',
          'Flush tank to remove sediment'
        ]
      };
    },
    
    setPredictiveMaintenance(deviceId, prediction) {
      maintenancePredictions.set(deviceId, prediction);
    },
    
    /**
     * Save a device health assessment
     * @param {string} deviceId - The ID of the device
     * @param {Object} assessment - The health assessment data
     * @returns {Promise<Object>} The saved assessment
     */
    async saveHealthAssessment(deviceId, assessment) {
      // Create a new health assessment if one doesn't exist
      if (!maintenancePredictions.has(deviceId)) {
        maintenancePredictions.set(deviceId, {
          components: [],
          nextMaintenance: null,
          healthAssessment: null
        });
      }
      
      // Update the existing maintenance prediction with the health assessment
      const prediction = maintenancePredictions.get(deviceId);
      prediction.healthAssessment = {
        ...assessment,
        timestamp: new Date().toISOString(),
        deviceId: deviceId
      };
      
      // Return the updated assessment
      return prediction.healthAssessment;
    },
    
    /**
     * Retrieve a device health assessment
     * @param {string} deviceId - The ID of the device
     * @returns {Promise<Object>} The health assessment data for the device
     */
    async getHealthAssessment(deviceId) {
      // Return the existing health assessment or null if none exists
      if (!maintenancePredictions.has(deviceId)) {
        return null;
      }
      
      const prediction = maintenancePredictions.get(deviceId);
      return prediction.healthAssessment || null;
    },
    
    /**
     * Get maintenance recommendations for a device
     * @param {string} deviceId - The ID of the device
     * @returns {Promise<Array>} List of maintenance recommendations
     */
    async getMaintenanceRecommendations(deviceId) {
      // Get the device's health assessment if it exists
      const assessment = await this.getHealthAssessment(deviceId);
      
      // Generate recommendations based on the health assessment
      // or return default recommendations if no assessment exists
      const recommendations = [];
      
      // Default recommendations any device might need
      recommendations.push({
        action: 'Perform routine inspection',
        priority: 'medium',
        timeframe: '30 days',
        estimatedCost: 150,
        potentialImpact: 'Prevents potential issues before they develop into serious problems'
      });
      
      // Add recommendations based on device health if assessment exists
      if (assessment) {
        const healthScore = assessment.overallScore;
        
        // Add specific recommendations based on health score
        if (healthScore < 50) {
          recommendations.push({
            action: 'Replace critical components',
            priority: 'high',
            timeframe: '7 days',
            estimatedCost: 450,
            potentialImpact: 'Prevents imminent failure and extends device lifespan'
          });
        } else if (healthScore < 70) {
          recommendations.push({
            action: 'Perform preventive maintenance',
            priority: 'medium-high',
            timeframe: '14 days',
            estimatedCost: 250,
            potentialImpact: 'Improves performance and reduces risk of failure'
          });
        }
        
        // Add component-specific recommendations if available
        if (assessment.componentScores) {
          // Check heating element
          if (assessment.componentScores.heatingElement < 60) {
            recommendations.push({
              action: 'Inspect and possibly replace heating element',
              priority: 'high',
              timeframe: '10 days',
              estimatedCost: 200,
              potentialImpact: 'Restores heating efficiency and prevents failure'
            });
          }
          
          // Check thermostat
          if (assessment.componentScores.thermostat < 70) {
            recommendations.push({
              action: 'Calibrate or replace thermostat',
              priority: 'medium',
              timeframe: '21 days',
              estimatedCost: 100,
              potentialImpact: 'Improves temperature regulation and energy efficiency'
            });
          }
          
          // Check pressure relief valve
          if (assessment.componentScores.pressureRelief < 65) {
            recommendations.push({
              action: 'Replace pressure relief valve',
              priority: 'high',
              timeframe: '7 days',
              estimatedCost: 120,
              potentialImpact: 'Critical safety improvement to prevent pressure-related accidents'
            });
          }
          
          // Check tank integrity
          if (assessment.componentScores.tankIntegrity < 60) {
            recommendations.push({
              action: 'Inspect tank for leaks or corrosion',
              priority: 'high',
              timeframe: '14 days',
              estimatedCost: 0,  // Inspection cost only, repair would be additional
              potentialImpact: 'Identifies potential leaks before they cause property damage'
            });
          }
        }
      }
      
      // Sort recommendations by priority (assuming high > medium > low)
      const priorityOrder = {
        'high': 1,
        'medium-high': 2,
        'medium': 3,
        'medium-low': 4,
        'low': 5
      };
      
      recommendations.sort((a, b) => {
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      });
      
      return recommendations;
    },
    
    setMaintenanceRecords(deviceId, hasRecords = true) {
      maintenanceRecords.set(deviceId, hasRecords);
    },
    
    // Add the missing method needed by the test
    async addMaintenanceRecord(record) {
      // Store the record by device ID
      if (!maintenanceRecords.has(record.deviceId)) {
        maintenanceRecords.set(record.deviceId, true);
      }
      
      // In a real implementation, we'd store the actual record
      // For the mock, we just need to mark that this device has maintenance records
      return record;
    },
    
    // This avoids memory issues during test execution
    async getMaintenanceRecords(deviceId) {
      // Return a realistic mock record when maintenance records exist
      const hasRecords = maintenanceRecords.get(deviceId);
      if (hasRecords) {
        return [{
          id: `maint-record-${deviceId}`,
          deviceId: deviceId,
          date: maintenanceDate,
          type: 'Preventive',
          technician: 'John Smith',
          duration: 45, // minutes
          cost: 385.00,
          actions: [
            'Replaced anode rod',
            'Flushed tank',
            'Inspected heating element',
            'Checked pressure relief valve'
          ],
          parts: [
            { name: 'Anode Rod', cost: 40.00 },
            { name: 'Pressure Relief Valve', cost: 65.00 }
          ],
          notes: 'Routine preventive maintenance completed. Device in good condition.'
        }];
      }
      return [];
    },
    
    // Business intelligence calculations
    async calculateMaintenanceROI(deviceId) {
      // This avoids memory issues during test execution
      return {
        // Static ROI values that don't depend on any calculations
        costSavings: 450.00,  
        energySavings: 200.00, 
        lifespanExtension: {
          months: 9,  
          value: 625.00 
        },
        downtimeReduction: {
          hours: 48, 
          value: 300.00 
        },
        totalROI: 4.9, // 490% return on maintenance investment
        paybackPeriod: {
          months: 6,
          confidence: 0.8
        },
        // Add confidence levels required by the test
        confidenceLevels: {
          costSavings: 0.85,
          energySavings: 0.78,
          lifespanExtension: 0.72,
          downtimeReduction: 0.80,
          overallConfidence: 0.82,
          totalROI: 0.88,
          maintenancecosts: 0.95,
          performanceimprovement: 0.90,
          energysavings: 0.78,
          overallROI: 0.88
        },
        // Include maintenance costs and details - Using the exact property names expected by test
        maintenancecosts: 385,
        performanceimprovement: 18.5, // percent
        energysavings: 200.00,   // dollars
        lifespanextension: {
          months: 9,
          value: 625.00
        },
        downtimereduction: {
          hours: 48,
          value: 300.00
        },
        // Add the overall ROI property with the exact name expected by the test
        overallROI: 4.9,
        // Add supporting data that the test expects
        supportingData: {
          beforeAfterComparison: {
            energyConsumption: {
              before: 7.2, // kWh/day
              after: 6.3,  // kWh/day
              change: -12.5 // percent
            },
            uptime: {
              before: 0.94, // 94% 
              after: 0.99,  // 99%
              change: 5.3   // percent
            },
            performanceMetric: {
              before: 82,    // arbitrary score
              after: 94,     // arbitrary score
              change: 14.6   // percent
            }
          },
          costBenefitAnalysis: {
            investmentCost: 385,      // dollars
            annualSavings: 520,       // dollars
            paybackPeriodMonths: 8.9,  // months
            fiveYearReturn: 2210      // dollars over 5 years
          }
        }
      };
    },
    
    /**
     * Compare preventive and reactive maintenance approaches
     * @param {Array<string>} preventiveDeviceIds - Devices following preventive maintenance
     * @param {Array<string>} reactiveDeviceIds - Devices following reactive maintenance
     * @returns {Promise<Object>} The comparison results with ROI analysis
     */
    async compareMaintenanceApproaches(preventiveDeviceIds, reactiveDeviceIds) {
      // Generate realistic maintenance comparison data
      return {
        roi: {
          value: 2.35, // 235% ROI for preventive maintenance
          timeframe: '3 years'
        },
        preventiveCosts: {
          annual: 3200,
          perDevice: 320,
          breakdown: {
            scheduled: 2000,
            parts: 800,
            labor: 400
          }
        },
        reactiveCosts: {
          annual: 7500,
          perDevice: 750,
          breakdown: {
            emergency: 4500,
            parts: 1800,
            labor: 1200
          }
        },
        downtimeComparison: {
          preventive: {
            hoursPerYear: 12,
            costPerHour: 85
          },
          reactive: {
            hoursPerYear: 48,
            costPerHour: 250
          }
        },
        reliabilityImpact: {
          preventive: 0.995, // 99.5% uptime
          reactive: 0.92 // 92% uptime
        },
        projectedSavings: {
          annual: 4300,
          fiveYear: 21500
        },
        recommendedStrategy: 'Preventive maintenance with condition-based monitoring'
      };
    },
    
    // AI-powered operational optimization
    async getOptimalSchedule(deviceId, constraints) {
      return {
        schedule: [
          { day: 'Monday', startTime: '06:00', endTime: '08:30', mode: 'High' },
          { day: 'Monday', startTime: '17:00', endTime: '22:00', mode: 'Medium' },
          { day: 'Tuesday', startTime: '06:00', endTime: '08:30', mode: 'High' },
          { day: 'Tuesday', startTime: '17:00', endTime: '22:00', mode: 'Medium' },
          { day: 'Wednesday', startTime: '06:00', endTime: '08:30', mode: 'High' },
          { day: 'Wednesday', startTime: '17:00', endTime: '22:00', mode: 'Medium' },
          { day: 'Thursday', startTime: '06:00', endTime: '08:30', mode: 'High' },
          { day: 'Thursday', startTime: '17:00', endTime: '22:00', mode: 'Medium' },
          { day: 'Friday', startTime: '06:00', endTime: '08:30', mode: 'High' },
          { day: 'Friday', startTime: '17:00', endTime: '23:00', mode: 'Medium' },
          { day: 'Saturday', startTime: '08:00', endTime: '23:00', mode: 'Low' },
          { day: 'Sunday', startTime: '08:00', endTime: '23:00', mode: 'Low' }
        ],
        estimatedSavings: {
          energy: '18%',
          cost: '22%'
        },
        comfortImpact: 'Minimal',
        constraints: constraints || {
          maxTemperature: 140,
          minTemperature: 120,
          peakAvoidance: true,
          userPreferences: 'Balanced'
        }
      };
    },
    
    // Energy consumption forecasting
    async forecastEnergyConsumption(deviceId, timeframe) {
      const days = Math.ceil((timeframe.end - timeframe.start) / (1000 * 60 * 60 * 24));
      const dailyData = [];
      
      // Generate forecast data points
      let baseline = 6.5; // kWh starting point
      
      for (let i = 0; i < days; i++) {
        // Add some variation to make it look realistic
        const dayVariation = (Math.random() * 0.8) - 0.4; // -0.4 to +0.4
        const weekendAdjustment = (i % 7 === 0 || i % 7 === 6) ? 1.2 : 1.0; // Higher on weekends
        
        const forecast = (baseline + dayVariation) * weekendAdjustment;
        
        const date = new Date(timeframe.start);
        date.setDate(date.getDate() + i);
        
        dailyData.push({
          date: date,
          forecastKwh: forecast.toFixed(2),
          confidence: 0.85 - (i * 0.01) // Confidence decreases further into the future
        });
      }
      
      return {
        deviceId,
        forecastPeriod: {
          start: timeframe.start,
          end: timeframe.end
        },
        dailyForecasts: dailyData,
        aggregates: {
          totalKwh: dailyData.reduce((sum, day) => sum + parseFloat(day.forecastKwh), 0).toFixed(2),
          averageDaily: (dailyData.reduce((sum, day) => sum + parseFloat(day.forecastKwh), 0) / days).toFixed(2),
          estimatedCost: (dailyData.reduce((sum, day) => sum + parseFloat(day.forecastKwh), 0) * 0.15).toFixed(2) // Assuming $0.15/kWh
        },
        confidenceInterval: {
          lower: (dailyData.reduce((sum, day) => sum + parseFloat(day.forecastKwh), 0) * 0.9).toFixed(2),
          upper: (dailyData.reduce((sum, day) => sum + parseFloat(day.forecastKwh), 0) * 1.1).toFixed(2)
        }
      };
    },
    
    // Mock method for water usage pattern analysis
    async analyzeWaterUsagePatterns(deviceId, timeframe) {
      return {
        deviceId,
        period: {
          start: timeframe.start,
          end: timeframe.end
        },
        dailyAverage: {
          weekday: 45.2, // gallons
          weekend: 68.7  // gallons
        },
        peakUsageTimes: [
          { time: '07:00-08:00', averageGallons: 12.5, daysPercent: 92 },
          { time: '18:00-20:00', averageGallons: 18.3, daysPercent: 88 }
        ],
        usageDistribution: {
          morning: 35, // percent
          afternoon: 25, // percent
          evening: 38, // percent
          night: 2     // percent
        },
        seasonalVariation: {
          winter: '+5%',
          summer: '-8%'
        },
        efficiencyOpportunities: [
          {
            description: 'Reduce water temperature during low-usage periods',
            potentialSavings: '9%',
            implementation: 'Configure schedule to reduce temperature between 10:00-16:00'
          },
          {
            description: 'Install low-flow fixtures',
            potentialSavings: '12%',
            implementation: 'Replace shower heads and faucet aerators'
          }
        ]
      };
    },
    
    // Cross-device learning and optimization
    async getFleetWideInsights(deviceIds, metrics) {
      return {
        fleetSize: deviceIds.length,
        aggregatePerformance: {
          efficiency: 0.82,
          reliability: 0.94,
          costEffectiveness: 0.78
        },
        outliers: {
          topPerformers: deviceIds.slice(0, 3).map(id => ({
            deviceId: id,
            efficiency: 0.95,
            reliability: 0.98
          })),
          underperformers: deviceIds.slice(-3).map(id => ({
            deviceId: id,
            efficiency: 0.68,
            reliability: 0.88,
            recommendedActions: [
              'Schedule maintenance',
              'Verify temperature settings',
              'Check for scaling buildup'
            ]
          }))
        },
        correlations: [
          {
            factors: ['age', 'maintenance frequency'],
            strength: 0.72,
            description: 'Older units with less frequent maintenance show significantly lower efficiency'
          },
          {
            factors: ['usage patterns', 'energy consumption'],
            strength: 0.85,
            description: 'Units with consistent daily usage have better efficiency than those with erratic usage'
          }
        ],
        learningInsights: [
          'Fleet-wide efficiency improves with regular maintenance every 6 months',
          'Units installed in basement locations show 5% better energy efficiency',
          'Vacation mode usage reduces wear and extends unit lifespan'
        ]
      };
    },
    
    // AI-driven business intelligence
    async analyzeBizROI(implementation, customerSegment) {
      return {
        implementationCost: 850000,
        projectedReturns: {
          year1: 280000,
          year2: 560000,
          year3: 720000
        },
        paybackPeriod: 1.8, // years
        roi5Year: 2.4, // 240%
        customerBenefits: {
          costSavings: {
            average: 420, // $ per customer per year
            varianceBySegment: {
              residential: 320,
              commercial: 2200,
              industrial: 15800
            }
          },
          energySavings: {
            average: '18%',
            varianceBySegment: {
              residential: '14%',
              commercial: '22%',
              industrial: '19%'
            }
          }
        },
        marketDifferentiation: {
          competitiveAdvantage: 'High',
          uniqueValueProposition: 'Integrated efficiency solution with demonstrable ROI',
          customerLoyaltyImpact: '+24% retention rate'
        },
        sustainabilityMetrics: {
          carbonReduction: '18,500 tons CO2 per year',
          waterConservation: '12.6 million gallons per year',
          energyConservation: '28,400 MWh per year'
        },
        risks: [
          {
            type: 'Adoption rate lower than projected',
            probability: 'Medium',
            mitigation: 'Enhance onboarding experience and provide clear efficiency metrics'
          },
          {
            type: 'Competitive response',
            probability: 'High',
            mitigation: 'Accelerate feature development and lock in key customers with long-term contracts'
          }
        ]
      };
    },
    
    // Knowledge extraction and response
    async getKnowledgeResponse(query, context) {
      // Mock of a large language model responding to user queries
      const responses = {
        'efficiency tips': {
          content: 'To improve water heater efficiency: 1) Insulate the tank and pipes, 2) Lower the temperature to 120°F, 3) Install a timer to operate only when needed, 4) Use vacation mode when away, 5) Flush the tank annually to remove sediment.',
          confidence: 0.95,
          sources: ['Efficiency Guide v3.2', 'Customer Best Practices']
        },
        'troubleshooting': {
          content: 'Common water heater issues include: insufficient hot water, unusual noises, leaks, or discolored water. For insufficient hot water, check the thermostat setting. For unusual noises, the heating element may need cleaning. Leaks require immediate attention. Discolored water often indicates corrosion in the anode rod.',
          confidence: 0.92,
          sources: ['Technical Manual', 'Support Database']
        },
        'installation requirements': {
          content: 'Installation requires: 1) Adequate space with 2ft clearance on all sides, 2) Properly sized electrical circuit (typically 240V, 30A dedicated circuit), 3) Pressure relief valve and drain, 4) Expansion tank in closed systems, 5) Compliance with local building codes.',
          confidence: 0.97,
          sources: ['Installation Guide', 'Building Code Reference']
        }
      };
      
      // Default response if no match
      return responses[query.toLowerCase()] || {
        content: 'The IoTSphere system optimizes water heater performance through advanced analytics and machine learning. It monitors energy usage, water temperature, and maintenance needs to provide personalized recommendations for efficiency improvements.',
        confidence: 0.85,
        sources: ['Product Documentation', 'User Manual']
      };
    },
    
    /**
     * Add a knowledge entry to the knowledge base
     * @param {Object} entry - The knowledge entry to add
     * @returns {Promise<string>} The ID of the added entry
     */
    async addKnowledgeEntry(entry) {
      // Generate an ID if not provided
      if (!entry.id) {
        entry.id = `entry-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
      }
      
      // Add timestamp if not provided
      if (!entry.dateAdded) {
        entry.dateAdded = new Date();
      }
      
      // Initialize metrics if not provided
      if (!entry.appliedCount) entry.appliedCount = 0;
      if (entry.successRate === undefined) entry.successRate = 1.0;
      
      // Add to knowledge base
      knowledgeBase.entries.push(entry);
      
      return entry.id;
    },
    
    /**
     * Get all knowledge entries from the knowledge base
     * @param {Object} filters - Optional filters for retrieving entries
     * @returns {Promise<Array>} The knowledge entries
     */
    async getKnowledgeEntries(filters = {}) {
      let entries = [...knowledgeBase.entries];
      
      // Apply category filter if provided
      if (filters.category) {
        entries = entries.filter(entry => entry.category === filters.category);
      }
      
      // Apply search term filter if provided
      if (filters.searchTerm) {
        const term = filters.searchTerm.toLowerCase();
        entries = entries.filter(entry => 
          entry.title.toLowerCase().includes(term) ||
          entry.content.toLowerCase().includes(term)
        );
      }
      
      // Apply date filter if provided
      if (filters.dateFrom) {
        entries = entries.filter(entry => 
          entry.dateAdded >= filters.dateFrom
        );
      }
      
      return entries;
    },
    
    /**
     * Get all available knowledge categories
     * @returns {Promise<Array<string>>} The knowledge categories
     */
    async getKnowledgeCategories() {
      return [...knowledgeBase.categories];
    },
    
    /**
     * Analyze the knowledge base to identify operational improvement opportunities
     * @returns {Promise<Object>} Analysis results with improvement opportunities
     */
    async analyzeKnowledgeBase() {
      // Create a mock analysis result based on the knowledge entries
      return {
        improvementOpportunities: {
          trainingOpportunities: {
            title: 'Staff Training Opportunities',
            description: 'Areas where additional staff training could improve operational efficiency',
            items: [
              {
                area: 'Preventive Maintenance',
                description: 'Training on identifying early warning signs of device failure',
                impact: 'High',
                implementationEffort: 'Medium',
                estimatedImpact: {
                  downtimeReduction: '35%',
                  costSavings: '$12,500 annually'
                }
              },
              {
                area: 'Installation Procedures',
                description: 'Standardized training on optimal installation configuration',
                impact: 'Medium',
                implementationEffort: 'Low',
                estimatedImpact: {
                  callbackReduction: '42%',
                  customerSatisfaction: '+18%'
                }
              }
            ]
          },
          processImprovements: {
            title: 'Maintenance Process Improvements',
            description: 'Opportunities to streamline maintenance workflows',
            items: [
              {
                area: 'Maintenance Scheduling',
                description: 'Implement route optimization for maintenance visits',
                impact: 'High',
                implementationEffort: 'Medium',
                estimatedImpact: {
                  technicianEfficiency: '+28%',
                  fuelSavings: '15%'
                }
              },
              {
                area: 'Parts Management',
                description: 'Predictive inventory management for maintenance parts',
                impact: 'Medium-High',
                implementationEffort: 'Medium',
                estimatedImpact: {
                  partAvailability: '+95%',
                  inventoryCost: '-22%'
                }
              }
            ]
          },
          commonIssues: {
            title: 'Frequently Occurring Problems',
            description: 'Recurring issues that could be addressed systematically',
            items: [
              {
                issue: 'Temperature Sensor Calibration',
                frequency: 'High',
                rootCause: 'Environmental factors affecting calibration',
                recommendedFix: 'Implement monthly automatic calibration routine',
                estimatedImpact: {
                  accuracyImprovement: '95%',
                  maintenanceReduction: '40%'
                }
              },
              {
                issue: 'Control Board Firmware Compatibility',
                frequency: 'Medium',
                rootCause: 'Inconsistent firmware update processes',
                recommendedFix: 'Standardize OTA update procedure with validation',
                estimatedImpact: {
                  errorReduction: '85%',
                  deviceReliability: '+12%'
                }
              }
            ]
          },
          bestPractices: {
            title: 'Operational Best Practices',
            description: 'Recommended practices from successful implementations',
            items: [
              {
                practice: 'Preventive Maintenance Scheduling',
                description: 'Align maintenance with seasonal demand patterns',
                benefit: 'Reduces peak-season failures by 42%',
                implementationGuidance: 'Schedule major preventive maintenance during shoulder seasons'
              },
              {
                practice: 'Energy Efficiency Optimization',
                description: 'Adjust settings based on usage patterns',
                benefit: 'Reduces energy consumption by 18-22%',
                implementationGuidance: 'Implement adaptive temperature control based on historical usage data'
              }
            ]
          }
        },
        knowledgeGaps: [
          {
            area: 'Energy Efficiency Comparison',
            description: 'Limited data on real-world efficiency comparisons between models',
            recommendedAction: 'Initiate structured data collection across model types'
          },
          {
            area: 'Installation Environment Factors',
            description: 'Insufficient knowledge about environmental impact on performance',
            recommendedAction: 'Add environmental factor fields to installation documentation'
          }
        ],
        implementationRoadmap: {
          shortTerm: [
            'Update maintenance technician training materials',
            'Implement parts inventory prediction system'
          ],
          mediumTerm: [
            'Develop standardized preventive maintenance schedule generator',
            'Create knowledge sharing platform for field technicians'
          ],
          longTerm: [
            'Implement AI-driven maintenance optimization',
            'Develop cross-device failure prediction system'
          ]
        }
      };
    },
    
    /**
     * Perform fleet-wide optimization analysis
     * @param {Array<string>} deviceIds - Array of device IDs to analyze
     * @returns {Promise<Object>} Fleet optimization analysis results
     */
    async performFleetOptimizationAnalysis(deviceIds) {
      // Create a mock optimization analysis result
      return {
        opportunities: [
          {
            type: 'Energy Efficiency',
            description: 'Standardize temperature settings across similar devices',
            potentialImpact: {
              financial: 15000,
              operational: 'Energy savings of 12%',
              environmental: 'Carbon reduction of 22 tons CO2/year'
            },
            implementationEffort: 'Low',
            confidenceLevel: 0.92,
            timeToBenefit: '2 weeks',
            implementationGuidance: 'Update temperature profiles through central management console.',
            affectedDevices: [
              { id: 'device-123', type: 'water-heater', model: 'WH-5000', facility: 'Facility A' },
              { id: 'device-456', type: 'water-heater', model: 'WH-4500', facility: 'Facility B' },
              { id: 'device-789', type: 'chiller', model: 'CH-1000', facility: 'Facility A' }
            ]
          },
          {
            type: 'Maintenance Scheduling',
            description: 'Align maintenance schedules to optimize technician routing',
            potentialImpact: {
              financial: 32000,
              operational: 'Labor efficiency improvement of 24%',
              environmental: 'Reduced travel and emissions from optimized routing'
            },
            implementationEffort: 'Medium',
            confidenceLevel: 0.87,
            timeToBenefit: '1 month',
            implementationGuidance: 'Use the maintenance scheduling tool to group devices by location and maintenance type.',
            affectedDevices: [
              { id: 'device-234', type: 'vending-machine', model: 'VM-200', facility: 'Facility C' },
              { id: 'device-567', type: 'water-heater', model: 'WH-5000', facility: 'Facility B' },
              { id: 'device-890', type: 'hvac', model: 'AC-3000', facility: 'Facility A' }
            ]
          },
          {
            type: 'Load Balancing',
            description: 'Stagger operating cycles to reduce peak demand',
            potentialImpact: {
              financial: 25000,
              operational: 'Peak demand reduction of 18%',
              environmental: 'Improved grid stability and reduced carbon footprint'
            },
            implementationEffort: 'Medium',
            confidenceLevel: 0.89,
            timeToBenefit: '2 months',
            implementationGuidance: 'Program coordinated cycles using the fleet management API.',
            affectedDevices: [
              { id: 'device-321', type: 'robotic-arm', model: 'RA-500', facility: 'Facility D' },
              { id: 'device-654', type: 'conveyor-belt', model: 'CB-200', facility: 'Facility C' },
              { id: 'device-987', type: 'water-heater', model: 'WH-6000', facility: 'Facility A' }
            ]
          }
        ],
        crossDeviceInsights: {
          performanceVariance: '23%',
          outlierDevices: ['device-342', 'device-198', 'device-871'],
          bestPerformingConfiguration: {
            settings: {
              temperatureRange: '120-130°F',
              standbyMode: 'Eco',
              maintenanceFrequency: 'Quarterly'
            },
            deviceIds: ['device-456', 'device-789', 'device-234']
          }
        },
        prioritizedRecommendations: [
          {
            id: 'rec-001',
            name: 'Load Balancing Implementation',
            priority: 'High',
            rationale: 'Highest ROI with moderate implementation effort',
            financialImpact: 45000,
            implementationEffort: 'Medium',
            confidenceLevel: 0.93,
            timeToBenefit: '1 month'
          },
          {
            id: 'rec-002',
            name: 'Temperature Standardization',
            priority: 'Medium-High',
            rationale: 'Quick implementation with good ROI',
            financialImpact: 30000,
            implementationEffort: 'Low',
            confidenceLevel: 0.95,
            timeToBenefit: '2 weeks'
          },
          {
            id: 'rec-003',
            name: 'Maintenance Rescheduling',
            priority: 'Medium',
            rationale: 'Significant benefit but requires coordination with field teams',
            financialImpact: 32000,
            implementationEffort: 'Medium',
            confidenceLevel: 0.87,
            timeToBenefit: '3 months'
          }
        ]
      };
    },
    
    /**
     * Generate scenario projection model based on input parameters
     * @param {Object} parameters - Scenario parameters
     * @returns {Promise<Object>} Projection model for the scenario
     */
    async generateScenarioProjection(parameters) {
      // Return a mock scenario projection
      return {
        scenarioName: 'Efficiency Optimization Scenario',
        parameters: parameters || {
          deviceReplacementRate: '15% per year',
          energyCosts: 'Projected to increase 8% annually',
          maintenanceApproach: 'Predictive with 80% compliance',
          operationalHours: 'Extended by 2 hours daily'
        },
        projectionPeriod: '5 years',
        projectionYears: 5,
        projectionData: {
          year1: {
            capitalexpenditure: 250000,
            operationalcosts: 380000,
            reliability: { uptime: '95.2%', failures: 42 },
            energyconsumption: { kWh: 840000, cost: 126000 },
            totalcostofownership: 756000
          },
          year2: {
            capitalexpenditure: 220000,
            operationalcosts: 360000,
            reliability: { uptime: '96.8%', failures: 34 },
            energyconsumption: { kWh: 798000, cost: 129000 },
            totalcostofownership: 709000
          },
          year3: {
            capitalexpenditure: 210000,
            operationalcosts: 342000,
            reliability: { uptime: '97.5%', failures: 28 },
            energyconsumption: { kWh: 758000, cost: 132000 },
            totalcostofownership: 684000
          },
          year4: {
            capitalexpenditure: 200000,
            operationalcosts: 325000,
            reliability: { uptime: '98.2%', failures: 22 },
            energyconsumption: { kWh: 720000, cost: 134000 },
            totalcostofownership: 659000
          },
          year5: {
            capitalexpenditure: 190000,
            operationalcosts: 309000,
            reliability: { uptime: '98.8%', failures: 18 },
            energyconsumption: { kWh: 684000, cost: 137000 },
            totalcostofownership: 636000
          },
          summary: {
            capitalexpenditure: {
              total: 1070000,
              trend: 'Declining 5% annually after year 1'
            },
            operationalcosts: {
              total: 1716000,
              trend: 'Declining 5% annually'
            },
            reliability: {
              trend: 'Improving steadily with newer devices and better maintenance'
            },
            energyconsumption: {
              trend: 'Consumption decreasing 5% annually, costs rising due to rate increases'
            },
            totalcostofownership: {
              fiveYearTotal: 3444000,
              averageAnnual: 688800
            }
          }
        },
        baselineComparison: {
          totalSavings: 620000,
          carbonReduction: '250 tons CO2',
          roi: 1.8,
          paybackPeriod: '2.7 years',
          costDifference: 135000,
          reliabilityDifference: 0.15
        },
        sensitivityanalysis: [
          {
            parameter: 'Energy Cost Inflation',
            scenarios: [
              { value: '5% annual', tcodelta: '-$120,000' },
              { value: '8% annual', tcodelta: '$0' },
              { value: '12% annual', tcodelta: '+$180,000' }
            ]
          },
          {
            parameter: 'Device Replacement Rate',
            scenarios: [
              { value: '10% annual', tcodelta: '-$150,000' },
              { value: '15% annual', tcodelta: '$0' },
              { value: '20% annual', tcodelta: '+$175,000' }
            ]
          }
        ],
        implementationroadmap: {
          phases: [
            {
              name: 'Initial Optimization',
              timeline: 'Months 1-3',
              key5tasks: [
                'Standardize temperature settings',
                'Implement basic scheduling',
                'Train maintenance staff on system'
              ]
            },
            {
              name: 'Advanced Implementation',
              timeline: 'Months 4-9',
              key5tasks: [
                'Deploy load balancing across all compatible devices',
                'Transition to predictive maintenance model',
                'Integrate with building management systems'
              ]
            },
            {
              name: 'Continuous Improvement',
              timeline: 'Months 10+',
              key5tasks: [
                'Refine ML models with accumulated data',
                'Optimize replacement scheduling',
                'Expand to additional device types'
              ]
            }
          ]
        }
      };
    },

    // Knowledge Management methods
    async addKnowledgeEntry(entry) {
      // Create a new entry with an ID if one doesn't exist
      const newEntry = {
        ...entry,
        id: entry.id || 'ke-' + Math.random().toString(36).substring(2, 10),
        dateAdded: entry.dateAdded || new Date().toISOString().split('T')[0],
        lastUpdated: new Date().toISOString().split('T')[0],
        usageCount: entry.usageCount || 0,
        verificationStatus: entry.verificationStatus || 'pending-review'
      };
      
      // Add the entry to the knowledge base
      knowledgeBase.entries.push(newEntry);
      
      return newEntry;
    },
    
    async getKnowledgeEntries(filters = {}) {
      let results = [...knowledgeBase.entries];
      
      // Apply filters if provided
      if (filters.category) {
        results = results.filter(entry => 
          entry.category && entry.category.toLowerCase() === filters.category.toLowerCase());
      }
      
      if (filters.deviceType) {
        results = results.filter(entry => 
          entry.deviceTypes && entry.deviceTypes.includes(filters.deviceType));
      }
      
      if (filters.tags && Array.isArray(filters.tags) && filters.tags.length > 0) {
        results = results.filter(entry => 
          entry.tags && filters.tags.some(tag => entry.tags.includes(tag)));
      }
      
      if (filters.searchTerm) {
        const searchTermLower = filters.searchTerm.toLowerCase();
        results = results.filter(entry => 
          (entry.title && entry.title.toLowerCase().includes(searchTermLower)) || 
          (entry.content && entry.content.toLowerCase().includes(searchTermLower)));
      }
      
      // Apply sorting if specified
      if (filters.sortBy && filters.sortDirection) {
        const direction = filters.sortDirection.toLowerCase() === 'desc' ? -1 : 1;
        results.sort((a, b) => {
          if (a[filters.sortBy] < b[filters.sortBy]) return -1 * direction;
          if (a[filters.sortBy] > b[filters.sortBy]) return 1 * direction;
          return 0;
        });
      } else {
        // Default sort by lastUpdated (newest first)
        results.sort((a, b) => {
          if (a.lastUpdated < b.lastUpdated) return 1;
          if (a.lastUpdated > b.lastUpdated) return -1;
          return 0;
        });
      }
      
      return results;
    },
    
    async getKnowledgeCategories() {
      return knowledgeBase.categories;
    }
  };
}

module.exports = { mockAnalyticsEngine };
