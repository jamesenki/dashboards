module.exports = {
  // Root directory for tests
  rootDir: '../../',
  
  // The test environment that will be used for testing
  testEnvironment: 'jsdom',
  
  // Only run tests from the unit folder
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.js'
  ],
  
  // Enable ESM support with Babel
  transform: {
    '^.+\\.js$': ['babel-jest', { configFile: './babel.config.js' }]
  },
  
  // Module file extensions to handle
  moduleFileExtensions: ['js', 'json'],
  
  // Coverage reporting configuration
  collectCoverage: true,
  coverageDirectory: '<rootDir>/coverage/micro-frontend',
  
  // Verbose output
  verbose: true
};
