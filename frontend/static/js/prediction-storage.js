/**
 * Prediction Storage Service
 * 
 * Manages the storage and retrieval of water heater predictions.
 * This service handles the persistence of prediction data to the backend
 * and provides methods for retrieving historical predictions.
 */

class PredictionStorageService {
  /**
   * Initialize the prediction storage service
   */
  constructor() {
    this.apiBasePath = '/api/predictions';
    this.logger = window.Logger ? new window.Logger('PredictionStorage') : {
      debug: (msg, data) => console.debug(`[PredictionStorage] ${msg}`, data || ''),
      info: (msg, data) => console.log(`[PredictionStorage] ${msg}`, data || ''),
      warn: (msg, data) => console.warn(`[PredictionStorage] ${msg}`, data || ''),
      error: (msg, err) => console.error(`[PredictionStorage] ${msg}`, err || '')
    };
  }

  /**
   * Store a prediction in the database
   * @param {string} deviceId - ID of the water heater
   * @param {string} predictionType - Type of prediction (lifespan, anomaly, usage, multi-factor)
   * @param {Object} predictionData - Prediction data to store
   * @returns {Promise<Object>} Result of the storage operation
   */
  async storePrediction(deviceId, predictionType, predictionData) {
    if (!deviceId || !predictionType || !predictionData) {
      this.logger.error('Missing required parameters for storing prediction');
      throw new Error('Invalid parameters for prediction storage');
    }

    try {
      // Add timestamp and metadata to the prediction
      const enrichedData = {
        ...predictionData,
        metadata: {
          deviceId,
          predictionType,
          timestamp: new Date().toISOString(),
          version: predictionData.version || '1.0.0'
        }
      };

      // Send prediction to the backend for storage
      const response = await fetch(`${this.apiBasePath}/store`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(enrichedData)
      });

      if (!response.ok) {
        throw new Error(`Failed to store prediction: ${response.status}`);
      }

      const result = await response.json();
      this.logger.info(`Successfully stored ${predictionType} prediction for device ${deviceId}`, result);
      return result;
    } catch (error) {
      this.logger.error(`Error storing prediction: ${error.message}`, error);
      // Don't throw here - we want to fail gracefully if storage doesn't work
      return { success: false, error: error.message };
    }
  }

  /**
   * Get historical predictions for a device
   * @param {string} deviceId - ID of the water heater
   * @param {string} predictionType - Type of prediction to retrieve (optional)
   * @param {Object} options - Query options (limit, startDate, endDate)
   * @returns {Promise<Array>} Array of historical predictions
   */
  async getHistoricalPredictions(deviceId, predictionType = null, options = {}) {
    if (!deviceId) {
      this.logger.error('Device ID is required for retrieving historical predictions');
      throw new Error('Device ID is required');
    }

    try {
      // Build query parameters
      const queryParams = new URLSearchParams();
      if (predictionType) queryParams.append('type', predictionType);
      if (options.limit) queryParams.append('limit', options.limit);
      if (options.startDate) queryParams.append('start_date', options.startDate);
      if (options.endDate) queryParams.append('end_date', options.endDate);

      // Request historical predictions from the backend
      const response = await fetch(
        `${this.apiBasePath}/history/${deviceId}?${queryParams.toString()}`
      );

      if (!response.ok) {
        throw new Error(`Failed to retrieve historical predictions: ${response.status}`);
      }

      const predictions = await response.json();
      this.logger.info(`Retrieved ${predictions.length} historical predictions for device ${deviceId}`);
      return predictions;
    } catch (error) {
      this.logger.error(`Error retrieving historical predictions: ${error.message}`, error);
      throw error;
    }
  }

  /**
   * Compare a current prediction with historical data
   * @param {string} deviceId - ID of the water heater
   * @param {string} predictionType - Type of prediction to compare
   * @param {Object} currentPrediction - Current prediction data
   * @returns {Promise<Object>} Comparison results
   */
  async comparePredictions(deviceId, predictionType, currentPrediction) {
    try {
      // Get recent historical predictions for comparison
      const historicalPredictions = await this.getHistoricalPredictions(
        deviceId, 
        predictionType,
        { limit: 5 } // Get the 5 most recent predictions
      );

      if (!historicalPredictions || historicalPredictions.length === 0) {
        return { 
          hasPrevious: false,
          message: 'No historical data available for comparison'
        };
      }

      // Perform comparison based on prediction type
      // This is a simplified example - actual comparison logic would be more sophisticated
      const comparisonResult = {
        hasPrevious: true,
        previousCount: historicalPredictions.length,
        trend: this._calculateTrend(currentPrediction, historicalPredictions, predictionType),
        previousTimestamp: historicalPredictions[0].metadata.timestamp
      };

      this.logger.info(`Prediction comparison completed for ${predictionType}`, comparisonResult);
      return comparisonResult;
    } catch (error) {
      this.logger.error(`Error comparing predictions: ${error.message}`, error);
      return { 
        hasPrevious: false,
        error: error.message,
        message: 'Unable to compare with historical data'
      };
    }
  }

  /**
   * Calculate trend between current and historical predictions
   * @private
   */
  _calculateTrend(currentPrediction, historicalPredictions, predictionType) {
    // Different prediction types have different key metrics to compare
    let currentValue, previousValue;
    
    switch(predictionType) {
      case 'lifespan-estimation':
        currentValue = currentPrediction.remainingLifePercentage;
        previousValue = historicalPredictions[0].remainingLifePercentage;
        break;
      case 'anomaly-detection':
        currentValue = currentPrediction.anomalyScore;
        previousValue = historicalPredictions[0].anomalyScore;
        break;
      case 'usage-patterns':
        currentValue = currentPrediction.efficiencyScore;
        previousValue = historicalPredictions[0].efficiencyScore;
        break;
      case 'multi-factor':
        currentValue = currentPrediction.healthScore;
        previousValue = historicalPredictions[0].healthScore;
        break;
      default:
        return { direction: 'unchanged', percentage: 0 };
    }

    if (currentValue === undefined || previousValue === undefined) {
      return { direction: 'unchanged', percentage: 0 };
    }

    const difference = currentValue - previousValue;
    const percentageChange = previousValue !== 0 
      ? (difference / Math.abs(previousValue)) * 100 
      : 0;

    return {
      direction: difference > 0 ? 'improved' : difference < 0 ? 'declined' : 'unchanged',
      percentage: Math.abs(percentageChange).toFixed(1),
      raw: difference.toFixed(2)
    };
  }
}

// Create a global instance for use throughout the application
window.predictionStorage = new PredictionStorageService();
