/**
 * ChatInterface Component Tests
 * 
 * Tests core chat functionality through user behavior patterns.
 * Focuses on lawyer workflow scenarios and legal question handling.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInterface from '../ChatInterface';

// Mock the Message component to focus on ChatInterface behavior
jest.mock('../Message', () => {
  return function MockMessage({ message }) {
    return <div data-testid="message" data-role={message.role}>{message.content}</div>;
  };
});

describe('ChatInterface - Core Chat Functionality', () => {
  const mockOnSendMessage = jest.fn();
  const mockMessagesEndRef = { current: null };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Empty Chat State (Welcome Experience)', () => {
    it('should display welcome message for new users', () => {
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      // Should show typewriter welcome message
      expect(screen.getByText(/Your Australian legal AI assistant is ready|Australian law made accessible|Ready to help with Australian law/)).toBeInTheDocument();
      
      // Should show descriptive subtitle
      expect(screen.getByText('Ask questions about Australian law, get accurate answers with proper citations')).toBeInTheDocument();
    });

    it('should show centered input field for first question', () => {
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('autoFocus');
    });

    it('should handle first message submission correctly', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      const submitButton = screen.getByRole('button', { name: 'Send message' });

      await user.type(input, 'What is the Migration Act 1958?');
      await user.click(submitButton);

      expect(mockOnSendMessage).toHaveBeenCalledWith('What is the Migration Act 1958?');
    });
  });

  describe('Active Chat State (Conversation Mode)', () => {
    const mockMessages = [
      {
        id: '1',
        content: 'What is section 359A of the Migration Act?',
        role: 'user',
        timestamp: '2023-01-01T10:00:00Z'
      },
      {
        id: '2',
        content: 'Section 359A of the Migration Act 1958 (Cth) requires the Tribunal to provide particulars of adverse information.',
        role: 'assistant',
        timestamp: '2023-01-01T10:00:05Z'
      }
    ];

    it('should display conversation messages correctly', () => {
      render(
        <ChatInterface
          messages={mockMessages}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      // Should show all messages
      const messages = screen.getAllByTestId('message');
      expect(messages).toHaveLength(2);
      
      expect(screen.getByText('What is section 359A of the Migration Act?')).toBeInTheDocument();
      expect(screen.getByText(/Section 359A of the Migration Act 1958/)).toBeInTheDocument();
    });

    it('should position input at bottom during conversation', () => {
      render(
        <ChatInterface
          messages={mockMessages}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      const inputContainer = input.closest('.sticky');
      
      expect(inputContainer).toHaveClass('bottom-0');
    });
  });

  describe('Message Input Behavior', () => {
    it('should enable send button only when message is entered', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      const submitButton = screen.getByRole('button', { name: 'Send message' });

      // Initially disabled
      expect(submitButton).toBeDisabled();

      // Enable after typing
      await user.type(input, 'Test message');
      expect(submitButton).not.toBeDisabled();

      // Disable after clearing
      await user.clear(input);
      expect(submitButton).toBeDisabled();
    });

    it('should clear input after successful message send', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      
      await user.type(input, 'What is procedural fairness?');
      await user.click(screen.getByRole('button', { name: 'Send message' }));

      expect(input).toHaveValue('');
    });

    it('should handle Enter key submission', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      
      await user.type(input, 'Test legal question');
      await user.keyboard('{Enter}');

      expect(mockOnSendMessage).toHaveBeenCalledWith('Test legal question');
    });

    it('should allow Shift+Enter for line breaks without sending', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      
      await user.type(input, 'Multi-line question');
      await user.keyboard('{Shift>}{Enter}{/Shift}');
      await user.type(input, 'Second line');

      // Should not send message on Shift+Enter
      expect(mockOnSendMessage).not.toHaveBeenCalled();
      expect(input).toHaveValue('Multi-line question\nSecond line');
    });
  });

  describe('Loading States', () => {
    it('should disable input and show loading indicator while processing', () => {
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={true}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      const submitButton = screen.getByRole('button', { name: 'Processing...' });

      expect(input).toBeDisabled();
      expect(submitButton).toBeDisabled();
      expect(screen.getByText('AusLex is analyzing your question...')).toBeInTheDocument();
    });

    it('should show loading spinner icon during processing', () => {
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={true}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      // Check for loading spinner (Loader2 icon with animation)
      const loadingButton = screen.getByRole('button', { name: 'Processing...' });
      const spinner = loadingButton.querySelector('.animate-slow-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Legal Question Context Awareness', () => {
    it('should handle complex legal terminology input', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const complexLegalQuestion = 'What are the procedural fairness requirements under section 359A of the Migration Act 1958 (Cth) when the Tribunal considers adverse country information?';
      
      const input = screen.getByPlaceholderText('Ask anything...');
      await user.type(input, complexLegalQuestion);
      await user.click(screen.getByRole('button', { name: 'Send message' }));

      expect(mockOnSendMessage).toHaveBeenCalledWith(complexLegalQuestion);
    });

    it('should prevent empty message submission', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      
      // Try to send whitespace-only message
      await user.type(input, '   ');
      await user.click(screen.getByRole('button', { name: 'Send message' }));

      expect(mockOnSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility and Keyboard Navigation', () => {
    it('should have proper ARIA labels for screen readers', () => {
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByLabelText('Type your legal question');
      const submitButton = screen.getByLabelText('Send message');

      expect(input).toBeInTheDocument();
      expect(submitButton).toBeInTheDocument();
    });

    it('should support keyboard-only navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <ChatInterface
          messages={[]}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      const input = screen.getByPlaceholderText('Ask anything...');
      
      // Tab to input, type, tab to button, activate
      await user.tab();
      expect(input).toHaveFocus();
      
      await user.type(input, 'Keyboard navigation test');
      await user.tab();
      
      const submitButton = screen.getByRole('button', { name: 'Send message' });
      expect(submitButton).toHaveFocus();
      
      await user.keyboard('{Enter}');
      expect(mockOnSendMessage).toHaveBeenCalledWith('Keyboard navigation test');
    });
  });

  describe('Error Message Handling', () => {
    it('should display error messages appropriately', () => {
      const errorMessages = [
        {
          id: '1',
          content: 'What is section 359A?',
          role: 'user',
          timestamp: '2023-01-01T10:00:00Z'
        },
        {
          id: '2',
          content: 'Sorry, I encountered an error while processing your request.',
          role: 'assistant',
          timestamp: '2023-01-01T10:00:05Z',
          isError: true
        }
      ];

      render(
        <ChatInterface
          messages={errorMessages}
          onSendMessage={mockOnSendMessage}
          isLoading={false}
          messagesEndRef={mockMessagesEndRef}
        />
      );

      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument();
    });
  });
});

// Test data factories for chat scenarios
export const getMockUserMessage = (overrides = {}) => ({
  id: '1',
  content: 'What is section 359A of the Migration Act?',
  role: 'user',
  timestamp: '2023-01-01T10:00:00Z',
  ...overrides
});

export const getMockAssistantMessage = (overrides = {}) => ({
  id: '2',
  content: 'Section 359A of the Migration Act 1958 (Cth) requires the Tribunal to provide procedural fairness.',
  role: 'assistant',
  timestamp: '2023-01-01T10:00:05Z',
  ...overrides
});

export const getMockErrorMessage = (overrides = {}) => ({
  id: '3',
  content: 'Sorry, I encountered an error while processing your request.',
  role: 'assistant',
  timestamp: '2023-01-01T10:00:10Z',
  isError: true,
  ...overrides
});