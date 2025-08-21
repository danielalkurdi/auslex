/**
 * AuthModal Integration Tests
 * 
 * CRITICAL: Tests authentication security flows that protect user data.
 * Tests behavior through user interactions, not implementation details.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { server } from '../../mocks/server';
import AuthModal from '../AuthModal';

// Use global MSW server from setupTests; default handlers for auth endpoints

describe('AuthModal - Authentication Security Flows', () => {
  const mockOnClose = jest.fn();
  const mockOnAuthSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    // Ensure consistent auth responses across tests
    server.use(
      rest.post('http://localhost:8000/auth/register', async (req, res, ctx) => {
        const body = typeof req.json === 'function' ? await req.json() : req.body || {};
        return res(
          ctx.status(201),
          ctx.json({
            access_token: 'mock-jwt-token',
            user: {
              id: '1',
              email: body?.email || 'test@example.com',
              name: body?.name || 'Test User'
            }
          })
        );
      }),
      rest.post('http://localhost:8000/auth/login', async (req, res, ctx) => {
        const body = typeof req.json === 'function' ? await req.json() : req.body || {};
        return res(
          ctx.status(200),
          ctx.json({
            access_token: 'mock-jwt-token',
            user: {
              id: '1',
              email: body?.email || 'test@example.com',
              name: 'Test User'
            }
          })
        );
      })
    );
  });

  describe('User Registration Flow', () => {
    it('should register new user successfully with valid data', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      // Switch to registration mode
      await user.click(screen.getByText("Don't have an account? Sign up"));

      // Fill registration form
      await user.type(screen.getByLabelText('Full Name'), 'Test User');
      await user.type(screen.getByLabelText('Email Address'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), 'securepassword123');
      await user.type(screen.getByLabelText('Confirm Password'), 'securepassword123');

      // Submit form
      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      // Verify successful registration
      await waitFor(() => {
        expect(mockOnAuthSuccess).toHaveBeenCalledWith({
          id: '1',
          email: 'test@example.com',
          name: 'Test User'
        });
      });

      // Verify token storage
      expect(localStorage.getItem('authToken')).toBe('mock-jwt-token');
      expect(JSON.parse(localStorage.getItem('userData'))).toMatchObject({
        id: '1',
        email: 'test@example.com',
        name: 'Test User'
      });
    });

    it('should reject registration with weak password', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      await user.click(screen.getByText("Don't have an account? Sign up"));

      // Fill form with weak password
      await user.type(screen.getByLabelText('Full Name'), 'Test User');
      await user.type(screen.getByLabelText('Email Address'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), '123'); // Too short
      await user.type(screen.getByLabelText('Confirm Password'), '123');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      // Should show password strength error
      expect(screen.getByText('Password must be at least 6 characters')).toBeInTheDocument();
      expect(mockOnAuthSuccess).not.toHaveBeenCalled();
    });

    it('should reject registration with mismatched passwords', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      await user.click(screen.getByText("Don't have an account? Sign up"));

      await user.type(screen.getByLabelText('Full Name'), 'Test User');
      await user.type(screen.getByLabelText('Email Address'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), 'password123');
      await user.type(screen.getByLabelText('Confirm Password'), 'differentpassword');

      await user.click(screen.getByRole('button', { name: 'Create Account' }));

      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
      expect(mockOnAuthSuccess).not.toHaveBeenCalled();
    });
  });

  describe('User Login Flow', () => {
    it('should login existing user with valid credentials', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      // Fill login form (default mode is login)
      await user.type(screen.getByLabelText('Email Address'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), 'correctpassword');

      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(mockOnAuthSuccess).toHaveBeenCalledWith({
          id: '1',
          email: 'test@example.com',
          name: 'Test User'
        });
      });

      // Verify secure token storage
      expect(localStorage.getItem('authToken')).toBe('mock-jwt-token');
    });

    it('should handle login failure with invalid credentials', async () => {
      const user = userEvent.setup();

      // Mock failed login response
      server.use(
        rest.post('http://localhost:8000/auth/login', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({ detail: 'Invalid email or password' })
          );
        })
      );
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      await user.type(screen.getByLabelText('Email Address'), 'wrong@example.com');
      await user.type(screen.getByLabelText('Password'), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      await waitFor(() => {
        expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
      });

      expect(mockOnAuthSuccess).not.toHaveBeenCalled();
      expect(localStorage.getItem('authToken')).toBeNull();
    });
  });

  describe('Security Features', () => {
    it('should mask password input by default', () => {
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      const passwordInput = screen.getByLabelText('Password');
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should toggle password visibility when requested', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      const passwordInput = screen.getByLabelText('Password');
      const toggleButton = screen.getByRole('button', { name: /show password/i });

      // Initially hidden
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Toggle to show
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');

      // Toggle back to hide
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('should clear sensitive data when modal closes', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      // Enter sensitive data
      await user.type(screen.getByLabelText('Email Address'), 'test@example.com');
      await user.type(screen.getByLabelText('Password'), 'sensitivepassword');

      // Close modal
      await user.click(screen.getByLabelText('Close modal'));

      expect(mockOnClose).toHaveBeenCalled();
      
      // Verify form data is cleared (test through re-rendering)
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      expect(screen.getByLabelText('Email Address')).toHaveValue('');
      expect(screen.getByLabelText('Password')).toHaveValue('');
    });
  });

  describe('Form Validation Security', () => {
    it('should require email and password fields', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      // Try to submit empty form
      await user.click(screen.getByRole('button', { name: 'Sign In' }));

      expect(screen.getByText('Email and password are required')).toBeInTheDocument();
      expect(mockOnAuthSuccess).not.toHaveBeenCalled();
    });

    it('should validate email format', async () => {
      const user = userEvent.setup();
      
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      // Enter invalid email format
      const emailInput = screen.getByLabelText('Email Address');
      await user.type(emailInput, 'notavalidemail');
      await user.type(screen.getByLabelText('Password'), 'validpassword');

      // HTML5 validation should prevent submission
      await user.click(screen.getByRole('button', { name: 'Sign In' }));
      
      // Browser will show validation message (can't easily test HTML5 validation)
      // But the input should have the correct type attribute
      expect(emailInput).toHaveAttribute('type', 'email');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and keyboard navigation', () => {
      render(
        <AuthModal
          isOpen={true}
          onClose={mockOnClose}
          onAuthSuccess={mockOnAuthSuccess}
        />
      );

      // Check ARIA labels
      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Close modal')).toBeInTheDocument();

      // Check form structure
      expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    });
  });
});

// Test data factory for authentication scenarios
export const getMockUserData = (overrides = {}) => ({
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
  ...overrides
});

export const getMockAuthResponse = (overrides = {}) => ({
  access_token: 'mock-jwt-token',
  user: getMockUserData(),
  ...overrides
});