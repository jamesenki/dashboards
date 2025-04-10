/**
 * Shadow Tasks for Cypress E2E Tests
 * 
 * These tasks allow E2E tests to interact with MongoDB shadow documents
 * directly for testing the complete data flow from database to UI.
 */
const { MongoClient } = require('mongodb');

// MongoDB connection settings - use the same as the application
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/';
const DB_NAME = process.env.DB_NAME || 'iotsphere';
const SHADOWS_COLLECTION = 'device_shadows';
const HISTORY_COLLECTION = 'shadow_history';

let mongoClient = null;
let db = null;

/**
 * Initialize MongoDB connection
 */
async function initMongoDB() {
  if (mongoClient) {
    return;
  }
  
  try {
    console.log(`Connecting to MongoDB at ${MONGODB_URI}`);
    mongoClient = new MongoClient(MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      connectTimeoutMS: 5000,
      serverSelectionTimeoutMS: 5000
    });
    
    await mongoClient.connect();
    db = mongoClient.db(DB_NAME);
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('Failed to connect to MongoDB:', error);
    throw error;
  }
}

/**
 * Reset test data to initial state
 */
async function resetTestData() {
  await initMongoDB();
  
  try {
    // Load fixtures for test water heaters
    const testHeaters = [
      {
        _id: 'wh-12347',
        name: 'Main Building Water Heater - Critical',
        model: 'IoTSphere Pro 5000',
        location: 'Basement Utility Room',
        status: {
          operational: true,
          alert_level: 'normal',
          condition: 'normal'
        },
        metrics: {
          current_temperature: 120,
          target_temperature: 120,
          units: 'fahrenheit',
          pressure: 75,
          flow_rate: 8.5,
          energy_usage: 5.2
        },
        telemetry: {
          temperature: 120,
          target_temperature: 120,
          heating_status: 'standby',
          power_status: 'on',
          water_flow: 8.5,
          timestamp: new Date().toISOString()
        },
        last_updated: new Date().toISOString()
      }
    ];
    
    // Replace test heaters with clean versions
    const shadows = db.collection(SHADOWS_COLLECTION);
    for (const heater of testHeaters) {
      await shadows.replaceOne(
        { _id: heater._id },
        heater,
        { upsert: true }
      );
    }
    
    console.log('Reset test data complete');
    return { success: true };
  } catch (error) {
    console.error('Failed to reset test data:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Update device shadow
 * 
 * @param {Object} params Parameters for the update
 * @param {string} params.deviceId Device ID
 * @param {Object} params.update Update content
 * @returns {Object} Update result
 */
async function updateDeviceShadow({ deviceId, update }) {
  await initMongoDB();
  
  try {
    console.log(`Updating shadow for device ${deviceId}:`, update);
    
    // Prepare update document
    const updateDoc = {
      $set: {
        ...update,
        last_updated: new Date().toISOString()
      }
    };
    
    // Update shadow
    const shadows = db.collection(SHADOWS_COLLECTION);
    const result = await shadows.updateOne(
      { _id: deviceId },
      updateDoc,
      { upsert: false }
    );
    
    console.log('Shadow update result:', result);
    
    if (result.matchedCount === 0) {
      return {
        success: false,
        error: `No shadow found for device ID: ${deviceId}`
      };
    }
    
    // Add entry to shadow history
    const history = db.collection(HISTORY_COLLECTION);
    await history.insertOne({
      device_id: deviceId,
      timestamp: new Date(),
      changes: update,
      user_id: 'e2e-test'
    });
    
    return {
      success: true,
      deviceId,
      modified: result.modifiedCount > 0
    };
  } catch (error) {
    console.error('Failed to update shadow:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Register shadow tasks with Cypress
 * 
 * @param {Object} on Cypress 'on' function
 */
function registerShadowTasks(on) {
  on('task', {
    resetTestData,
    updateDeviceShadow
  });
}

module.exports = {
  registerShadowTasks
};
