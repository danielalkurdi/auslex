/**
 * Mock Service Worker Server Configuration
 * 
 * Sets up MSW for testing environment to intercept and mock API calls.
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers.js';

// Setup MSW server with default handlers
export const server = setupServer(...handlers);

// Server lifecycle for tests
export const startServer = () => {
  server.listen({
    onUnhandledRequest: 'warn', // Warn about unmocked requests
  });
};

export const stopServer = () => {
  server.close();
};

export const resetServerHandlers = () => {
  server.resetHandlers();
};

// Helper to override handlers for specific tests
export const useServerHandlers = (...newHandlers) => {
  server.use(...newHandlers);
};

export default server;