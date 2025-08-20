# AusLex Testing Analysis and Strategy

## Current Testing Status Assessment

### Existing Test Coverage: **CRITICAL GAPS IDENTIFIED**
- **Frontend**: Zero test files found in React codebase
- **Backend**: Only Python integration tests for legal AI functionality
- **No unit tests** for critical components (CitationParser, AuthModal, ChatInterface)
- **No E2E tests** for user workflows
- **No accessibility tests** despite legal domain requirements
- **No performance tests** for citation parsing or chat functionality

### Test Infrastructure Status
✅ **Already Configured:**
- Jest + React Testing Library (via create-react-app)
- Testing dependencies installed (`@testing-library/jest-dom`, `@testing-library/react`, `@testing-library/user-event`)
- ESLint testing rules configured

❌ **Missing:**
- Test setup file (`setupTests.js`)
- Custom test utilities and mocks
- Playwright E2E test framework
- Test data fixtures
- CI/CD test integration
- Performance testing tools

## Critical User Flows Analysis

### 1. **Authentication Flow** (HIGH PRIORITY)
**Security Critical**: JWT-based auth with localStorage persistence
- Register new account validation
- Login with email/password
- Token persistence across sessions
- Logout and token cleanup
- Error handling for invalid credentials

### 2. **Chat Interface Flow** (HIGH PRIORITY)
**Core Functionality**: Multi-chat with persistence
- Create new chat conversation
- Send messages and receive AI responses
- Message rendering with markdown support
- Chat history management (rename, delete, switch)
- Loading states and error handling

### 3. **Legal Citation Flow** (HIGH PRIORITY - UNIQUE VALUE)
**Legal Domain Critical**: Citation parsing and AustLII integration
- Automatic citation detection in AI responses
- Citation highlighting and clickable behavior
- Modal display with AustLII embedding
- Fallback links when embedding fails
- Complex citation parsing (Acts, Regulations, Cases)

### 4. **Settings Configuration** (MEDIUM PRIORITY)
- API endpoint configuration
- Model parameters adjustment (max_tokens, temperature, top_p)
- Settings persistence
- Validation and error handling

### 5. **Mobile Responsiveness** (MEDIUM PRIORITY)
- Sidebar collapse/expand behavior
- Mobile menu functionality
- Touch interactions for citations
- Responsive chat interface

## Component Testing Strategy

### Testing Philosophy Alignment
Following TDD principles from CLAUDE.md:
- **Behavior-driven testing**: Test through public APIs, not implementation
- **No unit tests**: Focus on user-visible behavior
- **100% coverage expectation**: Through business behavior testing
- **Real schemas/types**: Use actual citation parser types, not mocks

### Priority Testing Categories

#### **TIER 1: Core Security & Legal Accuracy**
1. **CitationParser** (`utils/citationParser.js`)
   - Citation detection accuracy (Australian legal citations)
   - Regex pattern matching for different citation formats
   - AustLII URL generation correctness
   - Edge cases and malformed citations

2. **AuthContext** (`contexts/AuthContext.js`)
   - JWT token handling and validation
   - localStorage persistence behavior
   - Authentication state management
   - Security: token expiration handling

#### **TIER 2: User Experience Critical**
3. **ChatInterface** (`components/ChatInterface.js`)
   - Message sending and receiving flow
   - Markdown rendering with citations
   - Loading states and error handling
   - Message persistence and history

4. **AuthModal** (`components/AuthModal.js`)
   - Form validation (email, password, confirmation)
   - Registration vs login mode switching
   - Error message display
   - Submission handling

#### **TIER 3: Integration & Polish**
5. **CitationModal** (`components/CitationModal.js`)
   - Modal positioning and display
   - AustLII embedding behavior
   - Fallback link handling
   - Keyboard navigation and a11y

6. **Sidebar** (`components/Sidebar.js`)
   - Chat management (create, rename, delete)
   - Navigation state management
   - Mobile responsive behavior

## Test Implementation Examples

### Example 1: CitationParser Behavior Test
```javascript
// src/utils/__tests__/citationParser.test.js
import { describe, it, expect } from '@jest/globals';
import { citationParser, CITATION_TYPES } from '../citationParser';

describe('Citation Parser - Australian Legal Citations', () => {
  describe('Migration Act citations', () => {
    it('should parse section references with jurisdiction', () => {
      const text = "Under Migration Act 1958 (Cth) s 501, the Minister may cancel visas.";
      const citations = citationParser.parseText(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.LEGISLATION,
        actName: 'Migration Act',
        year: '1958',
        jurisdiction: 'Cth',
        provisionType: 'section',
        provision: expect.objectContaining({
          sections: ['501']
        }),
        fullCitation: 'Migration Act 1958 (Cth) s 501'
      });
    });

    it('should generate correct AustLII search queries', () => {
      const text = "Section 359A of the Migration Act 1958 (Cth) applies.";
      const citations = citationParser.parseText(text);
      
      expect(citations[0].searchQuery).toMatchObject({
        actName: 'Migration',
        year: '1958',
        jurisdiction: 'Cth',
        provision: '359A'
      });
    });
  });

  describe('Case citations', () => {
    it('should parse High Court square bracket citations', () => {
      const text = "In Plaintiff M70/2011 v Minister for Immigration [2011] HCA 32, the court held...";
      const citations = citationParser.parseText(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.CASE,
        plaintiff: 'Plaintiff M70/2011',
        defendant: 'Minister for Immigration',
        year: '2011',
        court: 'HCA',
        caseNumber: '32'
      });
    });
  });

  describe('Edge cases and validation', () => {
    it('should handle overlapping citations correctly', () => {
      const text = "Migration Act 1958 (Cth) s 501 and Section 501 of the Migration Act 1958 (Cth)";
      const citations = citationParser.parseText(text);
      
      // Should keep the longer citation and remove the shorter overlapping one
      expect(citations.length).toBeGreaterThan(0);
      citations.forEach((citation, index) => {
        citations.slice(index + 1).forEach(otherCitation => {
          expect(citation.startIndex >= otherCitation.endIndex || 
                 citation.endIndex <= otherCitation.startIndex).toBe(true);
        });
      });
    });

    it('should return empty array for text with no legal citations', () => {
      const text = "This is just regular text with no legal references.";
      const citations = citationParser.parseText(text);
      
      expect(citations).toEqual([]);
    });
  });
});
```

### Example 2: Authentication Flow Test
```javascript
// src/components/__tests__/AuthModal.test.js
import { describe, it, expect, vi, beforeEach } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AuthModal from '../AuthModal';

// Mock fetch for API calls
global.fetch = vi.fn();

describe('AuthModal - Authentication Flow', () => {
  const mockOnClose = vi.fn();
  const mockOnAuthSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    fetch.mockClear();
  });

  describe('Registration flow', () => {
    it('should register new user with valid data', async () => {
      const user = userEvent.setup();
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'mock-jwt-token',
          user: { id: '1', name: 'John Doe', email: 'john@example.com' }
        })
      });

      render(
        <AuthModal 
          isOpen={true} 
          onClose={mockOnClose} 
          onAuthSuccess={mockOnAuthSuccess} 
        />
      );

      // Switch to registration mode
      await user.click(screen.getByText(/create account/i));

      // Fill registration form
      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'password123');

      // Submit form
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Verify API call
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('http://localhost:8000/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'John Doe',
            email: 'john@example.com',
            password: 'password123'
          })
        });
      });

      // Verify success callback
      expect(mockOnAuthSuccess).toHaveBeenCalledWith({
        access_token: 'mock-jwt-token',
        user: { id: '1', name: 'John Doe', email: 'john@example.com' }
      });
    });

    it('should show validation error for password mismatch', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal 
          isOpen={true} 
          onClose={mockOnClose} 
          onAuthSuccess={mockOnAuthSuccess} 
        />
      );

      await user.click(screen.getByText(/create account/i));
      await user.type(screen.getByLabelText(/name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password/i), 'password123');
      await user.type(screen.getByLabelText(/confirm password/i), 'different456');

      await user.click(screen.getByRole('button', { name: /create account/i }));

      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      expect(fetch).not.toHaveBeenCalled();
    });
  });

  describe('Login flow', () => {
    it('should login user with valid credentials', async () => {
      const user = userEvent.setup();
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'mock-jwt-token',
          user: { id: '1', name: 'John Doe', email: 'john@example.com' }
        })
      });

      render(
        <AuthModal 
          isOpen={true} 
          onClose={mockOnClose} 
          onAuthSuccess={mockOnAuthSuccess} 
        />
      );

      await user.type(screen.getByLabelText(/email/i), 'john@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('http://localhost:8000/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'john@example.com',
            password: 'password123'
          })
        });
      });
    });

    it('should handle login error gracefully', async () => {
      const user = userEvent.setup();
      
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' })
      });

      render(
        <AuthModal 
          isOpen={true} 
          onClose={mockOnClose} 
          onAuthSuccess={mockOnAuthSuccess} 
        />
      );

      await user.type(screen.getByLabelText(/email/i), 'wrong@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrongpass');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
      
      expect(mockOnAuthSuccess).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal 
          isOpen={true} 
          onClose={mockOnClose} 
          onAuthSuccess={mockOnAuthSuccess} 
        />
      );

      // Tab through form elements
      await user.tab();
      expect(screen.getByLabelText(/email/i)).toHaveFocus();
      
      await user.tab();
      expect(screen.getByLabelText(/password/i)).toHaveFocus();
      
      await user.tab();
      expect(screen.getByRole('button', { name: /sign in/i })).toHaveFocus();
    });

    it('should handle Escape key to close modal', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal 
          isOpen={true} 
          onClose={mockOnClose} 
          onAuthSuccess={mockOnAuthSuccess} 
        />
      );

      await user.keyboard('{Escape}');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });
});
```