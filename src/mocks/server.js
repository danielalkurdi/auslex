/**
 * Mock Service Worker Server Configuration
 * 
 * Sets up MSW for testing environment to intercept and mock API calls.
 */

const { setupServer } = require('msw/node');
const { handlers } = require('./handlers.js');

// Setup MSW server with default handlers
const server = setupServer(...handlers);

// Server lifecycle for tests
const startServer = () => {
  server.listen({
    onUnhandledRequest: 'warn', // Warn about unmocked requests
  });
};

const stopServer = () => {
  server.close();
};

const resetServerHandlers = () => {
  server.resetHandlers();
};

// Helper to override handlers for specific tests
const useServerHandlers = (...newHandlers) => {
  server.use(...newHandlers);
};

module.exports = {
  server,
  startServer,
  stopServer,
  resetServerHandlers,
  useServerHandlers
};