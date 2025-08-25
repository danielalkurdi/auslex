/**
 * Playwright Global Setup
 * 
 * Sets up test environment and authentication state for legal AI testing.
 */

import { chromium } from '@playwright/test';

async function globalSetup() {
  console.log('🚀 Setting up AusLex E2E test environment...');
  
  // Create a browser instance for setup
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Navigate to application
    await page.goto('http://localhost:3000');
    
    // Wait for app to load - wait for main chat interface
    await page.waitForSelector('textarea[aria-label="Type your legal question"]', { 
      timeout: 30000,
      state: 'attached'
    }).catch(() => {
      // Fallback: wait for any chat interface element
      return page.waitForSelector('.h-full.flex.flex-col', { timeout: 10000 });
    });
    
    console.log('✅ Application successfully loaded');
    
    // Create authenticated user state for tests that need it
    await setupAuthenticatedUser(page);
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

async function setupAuthenticatedUser(page) {
  try {
    // Register test user for authenticated scenarios
    await page.goto('http://localhost:3000');
    
    // Open auth modal
    await page.click('[aria-label="Sign in"]').catch(() => {
      console.log('Auth button not found, skipping authenticated user setup');
      return;
    });
    
    // Switch to registration
    await page.click('text="Don\'t have an account? Sign up"');
    
    // Fill registration form
    await page.fill('[name="name"]', 'Test Lawyer');
    await page.fill('[name="email"]', 'test.lawyer@auslex.test');
    await page.fill('[name="password"]', 'SecurePassword123');
    await page.fill('[name="confirmPassword"]', 'SecurePassword123');
    
    // Submit registration
    await page.click('button[type="submit"]');
    
    // Wait for successful authentication - look for the sign out button
    await page.waitForSelector('[aria-label="Sign out"]', { timeout: 10000 });
    
    // Save authentication state for reuse
    await page.context().storageState({ path: 'tests/e2e/auth-state.json' });
    
    console.log('✅ Authenticated user state created');
    
  } catch (error) {
    console.log('⚠️  Could not create authenticated user state:', error.message);
    // Not critical - tests can still run without pre-authenticated state
  }
}

export default globalSetup;
