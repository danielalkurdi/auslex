/**
 * Playwright Global Teardown
 * 
 * Cleanup after E2E test execution.
 */

import fs from 'fs/promises';
import path from 'path';

async function globalTeardown() {
  console.log('🧹 Cleaning up AusLex E2E test environment...');
  
  try {
    // Clean up authentication state file
    const authStatePath = path.join(__dirname, 'auth-state.json');
    await fs.unlink(authStatePath).catch(() => {
      // File may not exist, ignore error
    });
    
    // Clean up any temporary test data files
    const tempFiles = ['test-data.json', 'mock-responses.json'];
    for (const file of tempFiles) {
      await fs.unlink(path.join(__dirname, file)).catch(() => {
        // Files may not exist, ignore errors
      });
    }
    
    console.log('✅ Cleanup completed successfully');
    
  } catch (error) {
    console.error('❌ Cleanup failed:', error);
    // Don't throw - cleanup failures shouldn't fail the entire test suite
  }
}

export default globalTeardown;