/**
 * Jest Configuration for AusLex Testing
 * 
 * Optimized for React + Legal AI testing with comprehensive coverage.
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  
  // Module name mapping for imports
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@services/(.*)$': '<rootDir>/src/services/$1',
    '^@contexts/(.*)$': '<rootDir>/src/contexts/$1'
  },
  
  // Transform files
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
    '^.+\\.css$': 'jest-transform-stub'
  },
  
  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/reportWebVitals.js',
    '!src/**/*.test.{js,jsx}',
    '!src/**/*.spec.{js,jsx}',
    '!src/mocks/**/*'
  ],
  
  // Coverage thresholds - strict for legal accuracy
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    },
    // Critical components require 100% coverage
    'src/utils/citationParser.js': {
      branches: 100,
      functions: 100,
      lines: 100,
      statements: 100
    },
    'src/contexts/AuthContext.js': {
      branches: 95,
      functions: 100,
      lines: 95,
      statements: 95
    }
  },
  
  // Test match patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx}'
  ],
  
  // Test timeout
  testTimeout: 10000,
  
  // Mock file patterns
  moduleFileExtensions: ['js', 'jsx', 'json', 'css'],
  
  // Reporter configuration
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: 'test-results',
      outputName: 'junit.xml'
    }]
  ],
  
  // Verbose output for legal compliance verification
  verbose: true,
  
  // Clear mocks between tests for isolation
  clearMocks: true,
  restoreMocks: true,
  
  // Handle static assets
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(gif|ttf|eot|svg|png)$': 'jest-transform-stub'
  }
};