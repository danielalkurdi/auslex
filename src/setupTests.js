/**
 * Test Setup Configuration
 * 
 * Global test setup for Jest and MSW integration.
 * Configures mock server and testing utilities.
 */

import '@testing-library/jest-dom';
import { server } from './mocks/server';

// Mock IntersectionObserver for React Testing Library
global.IntersectionObserver = jest.fn(() => ({
  disconnect: jest.fn(),
  observe: jest.fn(),
  unobserve: jest.fn(),
}));

// Mock ResizeObserver for responsive components
global.ResizeObserver = jest.fn(() => ({
  disconnect: jest.fn(),
  observe: jest.fn(),
  unobserve: jest.fn(),
}));

// Mock window.matchMedia for responsive testing
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock scrollIntoView for message scrolling tests
Element.prototype.scrollIntoView = jest.fn();

// Set up MSW server
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'error', // Fail tests on unmocked requests
  });
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Console error handling for cleaner test output
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    // Suppress expected React warnings in tests
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render is deprecated') ||
       args[0].includes('Warning: An invalid form control'))
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});