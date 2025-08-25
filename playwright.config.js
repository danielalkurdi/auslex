/**
 * Playwright Configuration for AusLex Legal AI Platform
 * 
 * Configured for testing critical legal workflows with emphasis on:
 * - Cross-browser compatibility for legal professionals
 * - Mobile responsiveness for lawyers on-the-go  
 * - Accessibility compliance
 * - Citation accuracy validation
 */

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  
  // Global test configuration
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['json', { outputFile: 'test-results/results.json' }]
  ],

  // Global test options
  use: {
    // Base URL for testing
    baseURL: 'http://localhost:3000',
    
    // Capture screenshots and traces on failure
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    
    // Timeout settings
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // Test projects for different browsers and devices
  projects: [
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        // Australian legal professionals often use Chrome
        viewport: { width: 1440, height: 900 }
      },
    },

    {
      name: 'firefox-desktop', 
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1440, height: 900 }
      },
    },

    {
      name: 'webkit-desktop',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1440, height: 900 }
      },
    },

    // Mobile testing - lawyers often work on mobile devices
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },

    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },

    // Tablet testing - common in legal settings
    {
      name: 'tablet-chrome',
      use: { ...devices['iPad Pro'] },
    },
  ],

  // Development server configuration
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },

  // Test output directories
  outputDir: 'test-results/',
  
  // Global setup and teardown
  globalSetup: require.resolve('./tests/e2e/global-setup.js'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.js'),
});
