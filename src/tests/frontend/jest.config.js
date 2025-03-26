module.exports = {
  testEnvironment: 'jsdom',
  transform: {},
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': '<rootDir>/src/tests/frontend/mocks/styleMock.js',
    '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/src/tests/frontend/mocks/fileMock.js'
  },
  testMatch: ['**/tests/frontend/**/*.test.js'],
  setupFilesAfterEnv: ['<rootDir>/src/tests/frontend/setup.js'],
  testPathIgnorePatterns: ['/node_modules/'],
  collectCoverageFrom: ['frontend/static/js/**/*.js'],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html']
};
