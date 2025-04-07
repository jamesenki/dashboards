/**
 * IoTSphere BDD Test Tags
 *
 * This file defines the tag system used to categorize and filter BDD test scenarios.
 * Tags help determine which tests are run in different environments and track the status
 * of features.
 */

const TAGS = {
  // Implementation Status Tags
  CURRENT: '@current',       // Currently implemented features
  PLANNED: '@planned',       // Features planned for the near future
  FUTURE: '@future',         // Long-term vision features
  WIP: '@wip',               // Work in progress features

  // Device Type Tags
  DEVICE_AGNOSTIC: '@device-agnostic',
  DEVICE_WATERHEATER: '@device-waterheater',
  DEVICE_VENDINGMACHINE: '@device-vendingmachine',
  DEVICE_ROBOT: '@device-robot',
  DEVICE_VEHICLE: '@device-vehicle',

  // Persona Tags
  PERSONA_FACILITYMAN: '@persona-facilityman',
  PERSONA_TECHNICIAN: '@persona-technician',
  PERSONA_ENDUSER: '@persona-enduser',
  PERSONA_SYSADMIN: '@persona-sysadmin',
  PERSONA_ENERGYMAN: '@persona-energyman',
  PERSONA_MANUFACTURER: '@persona-manufacturer',
  PERSONA_BMSINTEGRATOR: '@persona-bmsintegrator',

  // Domain Context Tags
  CONTEXT_DEVICEMGMT: '@context-devicemgmt',
  CONTEXT_DEVICEOP: '@context-deviceop',
  CONTEXT_MAINTENANCE: '@context-maintenance',
  CONTEXT_ENERGY: '@context-energy',
  CONTEXT_ANALYTICS: '@context-analytics',

  // AI Capability Tags
  AI_CAPABILITY: '@ai-capability',
  AI_PREDICTIVE: '@ai-predictive',
  AI_LEARNING: '@ai-learning',
  AI_BI: '@ai-business-intelligence',
  AI_CROSSDEVICE: '@ai-cross-device',

  // Test Type Tags
  SMOKE: '@smoke',           // Quick smoke tests
  REGRESSION: '@regression', // Full regression suite
  PERFORMANCE: '@performance', // Performance testing
};

module.exports = TAGS;
