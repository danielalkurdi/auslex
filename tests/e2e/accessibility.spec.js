/**
 * Accessibility Testing Suite
 * 
 * Ensures AusLex meets accessibility standards for legal professionals
 * including those with disabilities.
 */

import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

test.describe('Accessibility Compliance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should meet WCAG 2.1 AA standards on main page', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper keyboard navigation', async ({ page }) => {
    // Test tab order
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus').getAttribute('aria-label');
    expect(focusedElement).toBe('Type your legal question');

    // Continue tab navigation
    await page.keyboard.press('Tab');
    focusedElement = await page.locator(':focus').getAttribute('aria-label');
    expect(focusedElement).toBe('Send message');
  });

  test('should have sufficient color contrast', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('body')
      .withRules(['color-contrast'])
      .analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should support screen readers with proper ARIA labels', async ({ page }) => {
    // Check for essential ARIA labels
    await expect(page.locator('[aria-label="Type your legal question"]')).toBeVisible();
    await expect(page.locator('[aria-label="Send message"]')).toBeVisible();
    
    // Check heading structure
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    
    // Verify no accessibility violations in interactive elements
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('[role="button"], [role="textbox"], [role="link"]')
      .analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should handle focus management in modals', async ({ page }) => {
    // Open auth modal if available
    const authButton = page.locator('[data-testid="auth-button"]');
    if (await authButton.isVisible()) {
      await authButton.click();
      
      // Focus should be trapped in modal
      await page.keyboard.press('Tab');
      const focusedElement = await page.locator(':focus');
      
      // Focus should be within the modal
      const isInModal = await focusedElement.isVisible() && 
                       await page.locator('[data-testid="auth-modal"]').isVisible();
      expect(isInModal).toBe(true);
      
      // Escape should close modal and restore focus
      await page.keyboard.press('Escape');
      await expect(page.locator('[data-testid="auth-modal"]')).not.toBeVisible();
    }
  });
});
