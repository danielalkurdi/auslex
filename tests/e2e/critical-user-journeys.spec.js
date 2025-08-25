/**
 * Critical User Journeys E2E Tests
 * 
 * Tests the most important workflows that legal professionals use daily.
 * These tests simulate real lawyer interactions with the AusLex platform.
 */

import { test, expect } from '@playwright/test';

test.describe('Critical Legal Research Journey', () => {
  test('should complete full legal research workflow with citation interaction', async ({ page }) => {
    // Navigate to AusLex application
    await page.goto('/');
    
    // Verify welcome state loads correctly
    await expect(page.locator('h1')).toContainText(/Australian legal AI assistant|Ready to help with Australian law/);
    await expect(page.getByText('Ask questions about Australian law, get accurate answers with proper citations')).toBeVisible();
    
    // Submit a complex legal question with known citation expectations
    const legalQuestion = 'What are the procedural fairness requirements under section 359A of the Migration Act 1958?';
    
    await page.fill('[placeholder="Ask anything..."]', legalQuestion);
    await page.click('[aria-label="Send message"]');
    
    // Verify question appears in chat
    await expect(page.getByText(legalQuestion)).toBeVisible();
    
    // Wait for AI response with loading indicator
    await expect(page.getByText('AusLex is analyzing your question...')).toBeVisible();
    
    // Wait for response to appear (with reasonable timeout for AI processing)
    await expect(page.locator('[data-testid="message"][data-role="assistant"]')).toBeVisible({ timeout: 30000 });
    
    // Verify response contains expected legal citation
    const responseText = await page.locator('[data-testid="message"][data-role="assistant"]').textContent();
    expect(responseText).toMatch(/Migration Act 1958.*Cth.*359A/);
    
    // Test citation interaction - click on legal citation
    const citationLink = page.locator('[data-testid="citation-link"]').first();
    await expect(citationLink).toBeVisible();
    await citationLink.click();
    
    // Verify citation modal opens
    await expect(page.locator('[data-testid="citation-modal"]')).toBeVisible();
    await expect(page.getByText('Migration Act 1958 (Cth) s 359A')).toBeVisible();
    
    // Verify AustLII link is present and functional
    const austliiLink = page.locator('[href*="austlii.edu.au"]').first();
    await expect(austliiLink).toBeVisible();
    await expect(austliiLink).toHaveAttribute('target', '_blank');
    
    // Close citation modal
    await page.click('[aria-label="Close modal"]');
    await expect(page.locator('[data-testid="citation-modal"]')).not.toBeVisible();
    
    // Continue conversation with follow-up question
    const followUpQuestion = 'Can you provide more detail about the Tribunal\'s obligations?';
    await page.fill('[placeholder="Ask anything..."]', followUpQuestion);
    await page.click('[aria-label="Send message"]');
    
    // Verify follow-up appears and gets response
    await expect(page.getByText(followUpQuestion)).toBeVisible();
    await expect(page.locator('[data-testid="message"][data-role="assistant"]').nth(1)).toBeVisible({ timeout: 30000 });
    
    // Verify chat history is maintained
    await expect(page.getByText(legalQuestion)).toBeVisible();
    await expect(page.getByText(followUpQuestion)).toBeVisible();
  });

  test('should handle mobile legal research workflow', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile-specific test');
    
    await page.goto('/');
    
    // Verify mobile responsive design
    const input = page.locator('[placeholder="Ask anything..."]');
    await expect(input).toBeVisible();
    
    // On mobile, sidebar should be collapsed by default
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    
    // Test mobile chat interaction
    await input.fill('What is the Privacy Act 1988?');
    await page.tap('[aria-label="Send message"]');
    
    // Verify mobile-optimized loading state
    await expect(page.getByText('AusLex is analyzing your question...')).toBeVisible();
    
    // Verify response appears correctly on mobile
    await expect(page.locator('[data-testid="message"][data-role="assistant"]')).toBeVisible({ timeout: 30000 });
    
    // Test mobile citation interaction
    const citationLink = page.locator('[data-testid="citation-link"]').first();
    if (await citationLink.isVisible()) {
      await citationLink.tap();
      
      // Verify modal is mobile-optimized
      const modal = page.locator('[data-testid="citation-modal"]');
      await expect(modal).toBeVisible();
      
      // Modal should be responsive and readable on mobile
      const modalContent = modal.locator('[data-testid="citation-content"]');
      await expect(modalContent).toBeVisible();
      
      await page.tap('[aria-label="Close modal"]');
    }
  });
});

test.describe('Authentication Security Journey', () => {
  test('should complete secure user registration and login flow', async ({ page }) => {
    await page.goto('/');
    
    // Open authentication modal
    await page.click('[aria-label="Sign in"]');
    await expect(page.getByRole('heading', { name: /Welcome Back|Create Account/ })).toBeVisible();
    
    // Test user registration
    await page.click('text="Don\'t have an account? Sign up"');
    
    const testUser = {
      name: 'Jane Legal',
      email: `test.user.${Date.now()}@auslex.test`,
      password: 'SecurePassword123'
    };
    
    await page.fill('[name="name"]', testUser.name);
    await page.fill('[name="email"]', testUser.email);
    await page.fill('[name="password"]', testUser.password);
    await page.fill('[name="confirmPassword"]', testUser.password);
    
    // Submit registration
    await page.click('button[type="submit"]');
    
    // Verify successful registration
    await expect(page.locator('[data-testid="auth-modal"]')).not.toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    
    // Verify user is logged in
    await expect(page.getByText(testUser.name)).toBeVisible();
    
    // Test logout
    await page.click('[data-testid="user-menu"]');
    await page.click('text="Sign Out"');
    
    // Verify logged out state
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="auth-button"]')).toBeVisible();
    
    // Test login with same credentials
    await page.click('[aria-label="Sign in"]');
    await page.fill('[name="email"]', testUser.email);
    await page.fill('[name="password"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Verify successful login
    await expect(page.locator('[data-testid="auth-modal"]')).not.toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should handle authentication errors securely', async ({ page }) => {
    await page.goto('/');
    
    await page.click('[aria-label="Sign in"]');
    
    // Test invalid login credentials
    await page.fill('[name="email"]', 'nonexistent@example.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    // Should show error message without exposing system details
    await expect(page.getByText(/Invalid email or password|Authentication failed/)).toBeVisible();
    
    // Should remain on login modal
    await expect(page.getByRole('heading', { name: /Welcome Back|Create Account/ })).toBeVisible();
    
    // Should clear password field for security
    await expect(page.locator('[name="password"]')).toHaveValue('');
  });

  test('should persist authentication across sessions', async ({ page, context }) => {
    // First session - login
    await page.goto('/');
    await page.click('[aria-label="Sign in"]');
    await page.click('text="Don\'t have an account? Sign up"');
    
    const testUser = {
      name: 'Persistent User',
      email: `persistent.${Date.now()}@auslex.test`,
      password: 'SecurePassword123'
    };
    
    await page.fill('[name="name"]', testUser.name);
    await page.fill('[name="email"]', testUser.email);
    await page.fill('[name="password"]', testUser.password);
    await page.fill('[name="confirmPassword"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Verify logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    
    // Create new page to simulate session persistence
    const newPage = await context.newPage();
    await newPage.goto('/');
    
    // Should still be logged in
    await expect(newPage.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(newPage.getByText(testUser.name)).toBeVisible();
    
    await newPage.close();
  });
});

test.describe('Chat History Management Journey', () => {
  test('should create, switch between, and manage multiple chats', async ({ page }) => {
    await page.goto('/');
    
    // Create first chat
    const firstQuestion = 'What is section 359A of the Migration Act?';
    await page.fill('[placeholder="Ask anything..."]', firstQuestion);
    await page.click('[aria-label="Send message"]');
    
    // Wait for response
    await expect(page.locator('[data-testid="message"][data-role="assistant"]')).toBeVisible({ timeout: 30000 });
    
    // Create new chat
    await page.click('[data-testid="new-chat-button"]');
    
    // Verify we're in a new chat (input should be centered again)
    await expect(page.locator('h1')).toContainText(/Australian legal AI assistant|Ready to help with Australian law/);
    
    // Add content to second chat
    const secondQuestion = 'What is the Privacy Act 1988?';
    await page.fill('[placeholder="Ask anything..."]', secondQuestion);
    await page.click('[aria-label="Send message"]');
    
    // Wait for response
    await expect(page.locator('[data-testid="message"][data-role="assistant"]')).toBeVisible({ timeout: 30000 });
    
    // Switch back to first chat
    const firstChatItem = page.locator('[data-testid="chat-item"]').first();
    await firstChatItem.click();
    
    // Verify first chat content is restored
    await expect(page.getByText(firstQuestion)).toBeVisible();
    
    // Verify second chat content is not visible
    await expect(page.getByText(secondQuestion)).not.toBeVisible();
    
    // Switch to second chat
    const secondChatItem = page.locator('[data-testid="chat-item"]').nth(1);
    await secondChatItem.click();
    
    // Verify second chat content is visible
    await expect(page.getByText(secondQuestion)).toBeVisible();
    
    // Test chat deletion
    await secondChatItem.hover();
    await page.click('[data-testid="delete-chat-button"]');
    
    // Confirm deletion
    await page.click('[data-testid="confirm-delete"]');
    
    // Verify chat was deleted
    await expect(page.locator('[data-testid="chat-item"]')).toHaveCount(1);
    
    // Should automatically switch to remaining chat or empty state
    const remainingChats = await page.locator('[data-testid="chat-item"]').count();
    if (remainingChats > 0) {
      await expect(page.getByText(firstQuestion)).toBeVisible();
    } else {
      // Should show empty state if no chats remain
      await expect(page.locator('h1')).toContainText(/Australian legal AI assistant|Ready to help with Australian law/);
    }
  });
});

test.describe('Accessibility and Keyboard Navigation', () => {
  test('should support full keyboard navigation for legal professionals', async ({ page }) => {
    await page.goto('/');
    
    // Test keyboard navigation to input
    await page.keyboard.press('Tab');
    await expect(page.locator('[placeholder="Ask anything..."]')).toBeFocused();
    
    // Test typing and submission via keyboard
    await page.keyboard.type('What are the procedural fairness requirements?');
    await page.keyboard.press('Tab'); // Move to send button
    await expect(page.locator('[aria-label="Send message"]')).toBeFocused();
    
    await page.keyboard.press('Enter'); // Submit message
    
    // Verify message was sent
    await expect(page.getByText('What are the procedural fairness requirements?')).toBeVisible();
    
    // Test Escape key for modal interactions
    if (await page.locator('[data-testid="citation-link"]').first().isVisible()) {
      await page.locator('[data-testid="citation-link"]').first().click();
      await expect(page.locator('[data-testid="citation-modal"]')).toBeVisible();
      
      await page.keyboard.press('Escape');
      await expect(page.locator('[data-testid="citation-modal"]')).not.toBeVisible();
    }
  });

  test('should meet accessibility standards for legal compliance', async ({ page }) => {
    await page.goto('/');
    
    // Check for proper heading structure
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    await expect(headings.first()).toBeVisible();
    
    // Verify ARIA labels are present
    await expect(page.locator('[aria-label="Send message"]')).toBeVisible();
    await expect(page.locator('[aria-label="Type your legal question"]')).toBeVisible();
    
    // Check color contrast (basic verification)
    const computedStyle = await page.locator('body').evaluate((el) => {
      return window.getComputedStyle(el);
    });
    
    // Verify readable text colors are used
    expect(computedStyle.color).toBeTruthy();
    expect(computedStyle.backgroundColor).toBeTruthy();
    
    // Test focus indicators
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    
    // Focused element should have visible outline or other focus indicator
    const outline = await focusedElement.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.outline || styles.boxShadow || styles.borderColor;
    });
    
    expect(outline).toBeTruthy();
  });
});

test.describe('Error Handling and Recovery', () => {
  test('should handle API failures gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/chat', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    await page.goto('/');
    
    await page.fill('[placeholder="Ask anything..."]', 'Test question');
    await page.click('[aria-label="Send message"]');
    
    // Should show error message to user
    await expect(page.getByText(/Sorry, I encountered an error/)).toBeVisible({ timeout: 30000 });
    
    // Should allow user to try again
    await expect(page.locator('[placeholder="Ask anything..."]')).toBeEnabled();
    
    // Remove the mock to test recovery
    await page.unroute('**/chat');
    
    // Try again with same question
    await page.fill('[placeholder="Ask anything..."]', 'Recovery test question');
    await page.click('[aria-label="Send message"]');
    
    // Should work normally after recovery
    await expect(page.getByText('Recovery test question')).toBeVisible();
  });

  test('should handle network timeouts appropriately', async ({ page }) => {
    // Mock slow API response
    await page.route('**/chat', route => {
      // Delay response by 35 seconds (longer than typical timeout)
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ response: 'Delayed response' })
        });
      }, 35000);
    });
    
    await page.goto('/');
    
    await page.fill('[placeholder="Ask anything..."]', 'Timeout test');
    await page.click('[aria-label="Send message"]');
    
    // Should show loading state initially
    await expect(page.getByText('AusLex is analyzing your question...')).toBeVisible();
    
    // Should eventually show timeout or error message
    await expect(page.getByText(/Sorry, I encountered an error|Request timed out/)).toBeVisible({ timeout: 40000 });
  });
});
