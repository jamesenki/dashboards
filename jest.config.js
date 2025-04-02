/**
 * Jest configuration for IoTSphere frontend tests
 */
module.exports = {
  // The root directory where Jest should scan for tests
  roots: ['<rootDir>/src/tests/frontend'],

  // The test environment that will be used for testing
  testEnvironment: 'jsdom',

  // Files to match for tests
  testMatch: [
    '**/test_*.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Transform files with babel for ES6+ features
  transform: {},

  // Setup files to run before each test
  setupFiles: [],

  // Module file extensions to handle
  moduleFileExtensions: ['js', 'json'],

  // Path mappings for module resolution
  moduleNameMapper: {
    // Static assets mocking
    '\\.(css|less|scss|sass)$': '<rootDir>/src/tests/frontend/mocks/styleMock.js',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/src/tests/frontend/mocks/fileMock.js'
  },

  // Coverage reporting configuration
  collectCoverage: true,
  coverageDirectory: '<rootDir>/coverage',
  coverageReporters: ['json', 'lcov', 'text', 'clover'],

  // Verbose output
  verbose: true
};
