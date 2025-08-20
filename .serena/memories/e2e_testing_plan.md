# E2E Testing Plan with Playwright - AusLex Legal AI Platform

## Playwright Setup and Configuration

### Installation and Initial Setup
```bash
# Install Playwright
npm install --save-dev @playwright/test

# Install browsers
npx playwright install

# Generate Playwright config
npx playwright install --with-deps
```

### Playwright Configuration (`playwright.config.js`)
```javascript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['json', { outputFile: 'test-results/results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox', 
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: [
    {
      command: 'npm start',
      port: 3000,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd backend && uvicorn main:app --port 8000',
      port: 8000,
      timeout: 60 * 1000,
      reuseExistingServer: !process.env.CI,
    }
  ],
});
```

## Page Object Models

### Base Page Object
```javascript
// e2e/pages/BasePage.js
export class BasePage {
  constructor(page) {
    this.page = page;
  }

  async waitForNetworkIdle() {
    await this.page.waitForLoadState('networkidle');
  }

  async waitForDOMStable() {
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForTimeout(500); // Small buffer for React rendering
  }

  async takeScreenshot(name) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    });
  }
}
```

### Authentication Page Object
```javascript
// e2e/pages/AuthPage.js
import { BasePage } from './BasePage.js';

export class AuthPage extends BasePage {
  constructor(page) {
    super(page);
    
    // Selectors using data-testid (recommended pattern)
    this.signInButton = '[data-testid="auth-sign-in-button"]';
    this.emailInput = '[data-testid="auth-email-input"]';
    this.passwordInput = '[data-testid="auth-password-input"]';
    this.nameInput = '[data-testid="auth-name-input"]';
    this.confirmPasswordInput = '[data-testid="auth-confirm-password-input"]';
    this.createAccountButton = '[data-testid="auth-create-account-button"]';
    this.switchToRegisterLink = '[data-testid="auth-switch-to-register"]';
    this.switchToLoginLink = '[data-testid="auth-switch-to-login"]';
    this.errorMessage = '[data-testid="auth-error-message"]';
    this.closeButton = '[data-testid="auth-modal-close"]';
  }

  async openSignInModal() {
    await this.page.click('[data-testid="sidebar-auth-button"]');
    await this.waitForDOMStable();
  }

  async loginUser(email, password) {
    await this.page.fill(this.emailInput, email);
    await this.page.fill(this.passwordInput, password);
    await this.page.click(this.signInButton);
    await this.waitForNetworkIdle();
  }

  async registerUser(name, email, password) {
    await this.page.click(this.switchToRegisterLink);
    await this.page.fill(this.nameInput, name);
    await this.page.fill(this.emailInput, email);
    await this.page.fill(this.passwordInput, password);
    await this.page.fill(this.confirmPasswordInput, password);
    await this.page.click(this.createAccountButton);
    await this.waitForNetworkIdle();
  }

  async getErrorMessage() {
    return await this.page.textContent(this.errorMessage);
  }

  async isModalVisible() {
    return await this.page.isVisible('[data-testid="auth-modal"]');
  }
}
```

### Chat Page Object
```javascript
// e2e/pages/ChatPage.js
import { BasePage } from './BasePage.js';

export class ChatPage extends BasePage {
  constructor(page) {
    super(page);
    
    this.messageInput = '[data-testid="chat-message-input"]';
    this.sendButton = '[data-testid="chat-send-button"]';
    this.messagesList = '[data-testid="chat-messages-list"]';
    this.newChatButton = '[data-testid="sidebar-new-chat-button"]';
    this.chatItem = '[data-testid="sidebar-chat-item"]';
    this.loadingIndicator = '[data-testid="chat-loading-indicator"]';
  }

  async sendMessage(message) {
    await this.page.fill(this.messageInput, message);
    await this.page.click(this.sendButton);
    await this.waitForNetworkIdle();
  }

  async waitForResponse() {
    await this.page.waitForSelector(this.loadingIndicator, { state: 'hidden' });
    await this.waitForDOMStable();
  }

  async getLastMessage() {
    const messages = this.page.locator(`${this.messagesList} [data-testid="message"]`);
    const lastMessage = messages.last();
    return await lastMessage.textContent();
  }

  async getMessageCount() {
    const messages = this.page.locator(`${this.messagesList} [data-testid="message"]`);
    return await messages.count();
  }

  async createNewChat() {
    await this.page.click(this.newChatButton);
    await this.waitForDOMStable();
  }

  async getCitations() {
    const citations = this.page.locator('[data-testid="citation-link"]');
    return await citations.all();
  }

  async clickCitation(index = 0) {
    const citations = this.page.locator('[data-testid="citation-link"]');
    await citations.nth(index).click();
    await this.waitForDOMStable();
  }
}
```

## Critical E2E Test Flows

### 1. Authentication Flow Tests
```javascript
// e2e/tests/auth.spec.js
import { test, expect } from '@playwright/test';
import { AuthPage } from '../pages/AuthPage.js';
import { testUsers } from '../fixtures/testData.js';

test.describe('Authentication Flow', () => {
  let authPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    await page.goto('/');
  });

  test('should register new user successfully', async ({ page }) => {
    const newUser = testUsers.validNewUser;
    
    await authPage.openSignInModal();
    await authPage.registerUser(newUser.name, newUser.email, newUser.password);

    // Verify successful registration
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-name"]')).toContainText(newUser.name);
  });

  test('should login existing user successfully', async ({ page }) => {
    const existingUser = testUsers.validExistingUser;
    
    await authPage.openSignInModal();
    await authPage.loginUser(existingUser.email, existingUser.password);

    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await authPage.openSignInModal();
    await authPage.loginUser('invalid@email.com', 'wrongpassword');

    const errorMessage = await authPage.getErrorMessage();
    expect(errorMessage).toContain('Invalid credentials');
  });

  test('should persist authentication across page refresh', async ({ page }) => {
    const user = testUsers.validExistingUser;
    
    // Login
    await authPage.openSignInModal();
    await authPage.loginUser(user.email, user.password);
    
    // Refresh page
    await page.reload();
    await authPage.waitForDOMStable();
    
    // Verify still authenticated
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });

  test('should support keyboard navigation in auth modal', async ({ page }) => {
    await authPage.openSignInModal();
    
    // Tab through form elements
    await page.keyboard.press('Tab');
    await expect(page.locator(authPage.emailInput)).toBeFocused();
    
    await page.keyboard.press('Tab'); 
    await expect(page.locator(authPage.passwordInput)).toBeFocused();
    
    await page.keyboard.press('Tab');
    await expect(page.locator(authPage.signInButton)).toBeFocused();
    
    // Escape to close
    await page.keyboard.press('Escape');
    expect(await authPage.isModalVisible()).toBeFalsy();
  });
});
```

### 2. Legal Citation Tests
```javascript
// e2e/tests/citations.spec.js
import { test, expect } from '@playwright/test';
import { AuthPage } from '../pages/AuthPage.js';
import { ChatPage } from '../pages/ChatPage.js';
import { testUsers } from '../fixtures/testData.js';

test.describe('Legal Citation Flow', () => {
  let authPage, chatPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    chatPage = new ChatPage(page);
    
    // Setup authenticated session
    await page.goto('/');
    await authPage.openSignInModal();
    await authPage.loginUser(testUsers.validExistingUser.email, testUsers.validExistingUser.password);
  });

  test('should detect and highlight legal citations in AI responses', async ({ page }) => {
    // Send message that triggers citation response
    await chatPage.sendMessage('Tell me about section 501 of the Migration Act');
    await chatPage.waitForResponse();

    // Verify citations are detected and highlighted
    const citations = await chatPage.getCitations();
    expect(citations.length).toBeGreaterThan(0);
    
    // Verify citation styling
    const firstCitation = page.locator('[data-testid="citation-link"]').first();
    await expect(firstCitation).toHaveClass(/citation/);
  });

  test('should open citation modal with correct content', async ({ page }) => {
    await chatPage.sendMessage('What does Migration Act 1958 (Cth) s 501 say?');
    await chatPage.waitForResponse();

    // Click first citation
    await chatPage.clickCitation(0);
    
    // Verify modal opens with correct content
    await expect(page.locator('[data-testid="citation-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="citation-title"]')).toContainText('Migration Act 1958');
    await expect(page.locator('[data-testid="citation-provision"]')).toContainText('501');
  });

  test('should provide AustLII fallback when embedding fails', async ({ page }) => {
    // Mock network to simulate AustLII embedding failure
    await page.route('**/austlii/**', route => route.abort());
    
    await chatPage.sendMessage('Show me Fair Work Act 2009 s 394');
    await chatPage.waitForResponse();
    await chatPage.clickCitation(0);

    // Verify fallback link is available
    await expect(page.locator('[data-testid="austlii-fallback-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="citation-search-link"]')).toBeVisible();
  });

  test('should handle complex citations correctly', async ({ page }) => {
    const complexCitationQuery = 'Tell me about Plaintiff M70/2011 v Minister for Immigration [2011] HCA 32';
    
    await chatPage.sendMessage(complexCitationQuery);
    await chatPage.waitForResponse();

    const citations = await chatPage.getCitations();
    expect(citations.length).toBeGreaterThan(0);
    
    await chatPage.clickCitation(0);
    
    // Verify case citation modal content
    await expect(page.locator('[data-testid="citation-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="case-citation-title"]')).toContainText('Plaintiff M70/2011 v Minister for Immigration');
  });

  test('should support keyboard navigation in citation modal', async ({ page }) => {
    await chatPage.sendMessage('Tell me about Privacy Act 1988 (Cth) s 6');
    await chatPage.waitForResponse();
    
    // Use keyboard to navigate to citation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter'); // Should open modal
    
    await expect(page.locator('[data-testid="citation-modal"]')).toBeVisible();
    
    // Escape should close modal
    await page.keyboard.press('Escape');
    await expect(page.locator('[data-testid="citation-modal"]')).not.toBeVisible();
  });
});
```

### 3. Chat Functionality Tests
```javascript
// e2e/tests/chat.spec.js
import { test, expect } from '@playwright/test';
import { AuthPage } from '../pages/AuthPage.js';
import { ChatPage } from '../pages/ChatPage.js';
import { testUsers } from '../fixtures/testData.js';

test.describe('Chat Interface Flow', () => {
  let authPage, chatPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    chatPage = new ChatPage(page);
    
    await page.goto('/');
    await authPage.openSignInModal();
    await authPage.loginUser(testUsers.validExistingUser.email, testUsers.validExistingUser.password);
  });

  test('should create new chat and send messages', async ({ page }) => {
    await chatPage.createNewChat();
    
    const testMessage = 'What is unfair dismissal under Australian law?';
    await chatPage.sendMessage(testMessage);
    await chatPage.waitForResponse();

    // Verify message appears in chat
    const messageCount = await chatPage.getMessageCount();
    expect(messageCount).toBe(2); // User message + AI response

    // Verify response contains relevant content
    const lastMessage = await chatPage.getLastMessage();
    expect(lastMessage).toContain('Fair Work Act'); // Expected legal reference
  });

  test('should persist chat history', async ({ page }) => {
    await chatPage.createNewChat();
    await chatPage.sendMessage('Test message for persistence');
    await chatPage.waitForResponse();

    // Refresh page
    await page.reload();
    await authPage.waitForDOMStable();

    // Verify message still exists
    expect(await chatPage.getMessageCount()).toBeGreaterThan(0);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/chat', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' })
      });
    });

    await chatPage.sendMessage('Test error handling');
    await chatPage.waitForResponse();

    // Verify error message is shown
    const lastMessage = await chatPage.getLastMessage();
    expect(lastMessage).toContain('error');
  });

  test('should support markdown rendering in messages', async ({ page }) => {
    await chatPage.sendMessage('Show me content with **bold** and *italic* text');
    await chatPage.waitForResponse();

    // Verify markdown is rendered as HTML
    const messageContent = page.locator('[data-testid="message-content"]').last();
    await expect(messageContent.locator('strong')).toBeVisible();
    await expect(messageContent.locator('em')).toBeVisible();
  });
});
```

## Mobile and Responsive Testing

### Mobile-Specific Tests
```javascript
// e2e/tests/mobile.spec.js
import { test, expect, devices } from '@playwright/test';

test.describe('Mobile Responsiveness', () => {
  test.use({ ...devices['iPhone 12'] });

  test('should display mobile menu correctly', async ({ page }) => {
    await page.goto('/');
    
    // Mobile menu button should be visible
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    
    // Sidebar should be collapsed by default
    await expect(page.locator('[data-testid="sidebar"]')).not.toBeVisible();
  });

  test('should handle touch interactions for citations', async ({ page }) => {
    await page.goto('/');
    // ... setup authenticated session
    
    await chatPage.sendMessage('Tell me about section 394 Fair Work Act');
    await chatPage.waitForResponse();

    // Tap citation (touch event)
    await page.locator('[data-testid="citation-link"]').first().tap();
    
    // Verify modal opens
    await expect(page.locator('[data-testid="citation-modal"]')).toBeVisible();
  });

  test('should maintain usability on small screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto('/');
    
    // Verify critical elements are accessible
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="chat-message-input"]')).toBeVisible();
  });
});
```

## Accessibility Testing

### A11y Test Implementation
```javascript
// e2e/tests/accessibility.spec.js
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Compliance', () => {
  test('should pass axe accessibility tests on main page', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should maintain focus management in modals', async ({ page }) => {
    await page.goto('/');
    
    // Open auth modal
    await page.click('[data-testid="sidebar-auth-button"]');
    
    // Focus should be trapped in modal
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');
    const isInModal = await focusedElement.evaluate(el => 
      el.closest('[data-testid="auth-modal"]') !== null
    );
    expect(isInModal).toBe(true);
  });

  test('should provide proper ARIA labels', async ({ page }) => {
    await page.goto('/');
    
    // Verify critical elements have proper ARIA labels
    await expect(page.locator('[data-testid="chat-message-input"]')).toHaveAttribute('aria-label');
    await expect(page.locator('[data-testid="chat-send-button"]')).toHaveAttribute('aria-label');
  });

  test('should support screen reader navigation', async ({ page }) => {
    await page.goto('/');
    
    // Verify heading structure
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);
    
    // Verify landmark regions
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('nav')).toBeVisible();
  });
});
```

## Performance Testing

### Performance Test Suite
```javascript
// e2e/tests/performance.spec.js
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('should load initial page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(3000); // 3 second threshold
  });

  test('should handle citation parsing efficiently', async ({ page }) => {
    await page.goto('/');
    // ... setup authenticated session
    
    const longTextWithCitations = `
      This text contains multiple citations: Migration Act 1958 (Cth) s 501,
      Fair Work Act 2009 (Cth) s 394, Privacy Act 1988 (Cth) s 6, and
      Plaintiff M70/2011 v Minister for Immigration [2011] HCA 32.
      ${' '.repeat(1000)} // Large text block
    `;
    
    const startTime = Date.now();
    await chatPage.sendMessage(`Analyze this legal text: ${longTextWithCitations}`);
    await chatPage.waitForResponse();
    const processingTime = Date.now() - startTime;
    
    expect(processingTime).toBeLessThan(5000); // 5 second threshold
  });
});
```

## Test Data Management

### Test Fixtures
```javascript
// e2e/fixtures/testData.js
export const testUsers = {
  validExistingUser: {
    email: 'test@example.com',
    password: 'password123',
    name: 'Test User'
  },
  validNewUser: {
    email: 'newuser@example.com', 
    password: 'newpass123',
    name: 'New Test User'
  }
};

export const testQueries = {
  migrationLaw: 'What is section 501 of the Migration Act?',
  employmentLaw: 'Tell me about unfair dismissal under Fair Work Act',
  caseLaw: 'Explain Plaintiff M70/2011 v Minister for Immigration',
  withCitations: 'Analyze Migration Act 1958 (Cth) s 359A and Fair Work Act 2009 s 394'
};

export const expectedCitations = {
  migrationAct501: {
    actName: 'Migration Act',
    year: '1958',
    jurisdiction: 'Cth',
    provision: '501'
  }
};
```

## CI/CD Integration Commands

### GitHub Actions Workflow
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Install Playwright
        run: npx playwright install --with-deps
        
      - name: Start servers
        run: |
          npm start &
          cd backend && uvicorn main:app --port 8000 &
          
      - name: Wait for servers
        run: |
          npx wait-on http://localhost:3000 --timeout 60000
          npx wait-on http://localhost:8000 --timeout 30000
          
      - name: Run E2E tests
        run: npx playwright test
        
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

### Test Execution Commands
```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test auth.spec.js

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run tests on specific browser
npx playwright test --project=chromium

# Debug tests
npx playwright test --debug

# Generate test report
npx playwright show-report

# Update snapshots
npx playwright test --update-snapshots
```