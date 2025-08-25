/**
 * Test Setup Configuration
 * 
 * Global test setup for Jest and MSW integration.
 * Configures mock server and testing utilities.
 */

import '@testing-library/jest-dom';

// Polyfill TextEncoder/TextDecoder for Node test environment (MSW, interceptors)
import { TextEncoder, TextDecoder } from 'util';
if (!global.TextEncoder) {
  global.TextEncoder = TextEncoder;
  // Ensure availability on globalThis in jsdom as well
  globalThis.TextEncoder = TextEncoder;
}
if (!global.TextDecoder) {
  // utf-8 default to match browser behavior
  global.TextDecoder = TextDecoder;
  globalThis.TextDecoder = TextDecoder;
}

// Polyfill Web Streams API (TransformStream, ReadableStream, WritableStream) for Node/JSDOM
try {
  const { TransformStream, ReadableStream, WritableStream } = require('stream/web');
  if (typeof global.TransformStream === 'undefined' && TransformStream) {
    global.TransformStream = TransformStream;
    globalThis.TransformStream = TransformStream;
  }
  if (typeof global.ReadableStream === 'undefined' && ReadableStream) {
    global.ReadableStream = ReadableStream;
    globalThis.ReadableStream = ReadableStream;
  }
  if (typeof global.WritableStream === 'undefined' && WritableStream) {
    global.WritableStream = WritableStream;
    globalThis.WritableStream = WritableStream;
  }
} catch (_) {
  // If stream/web isn't available, leave as-is
}

// Import MSW server AFTER polyfills so interceptors can access TextEncoder/TextDecoder
let server;
try {
  // Use dynamic import for ES modules in Jest environment
  const { server: mswServer } = require('./mocks/server');
  server = mswServer;
} catch (error) {
  console.warn('MSW server could not be loaded:', error.message);
}

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
  if (server) {
    server.listen({
      onUnhandledRequest: 'warn', // Warn but don't fail on unmocked requests
    });
  }
});

afterEach(() => {
  if (server) {
    server.resetHandlers();
  }
});

afterAll(() => {
  if (server) {
    server.close();
  }
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