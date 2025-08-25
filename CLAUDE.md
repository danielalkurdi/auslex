# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AusLex is a modern React + FastAPI application for Australian legal research with comprehensive Australian Legal Corpus integration. Features include a chat UI, configurable model settings, clickable legal citation previews (AustLII), accurate section 359A support, and demo authentication.

## Architecture

### Frontend
- **Framework**: React 18 with Create React App
- **Styling**: Tailwind CSS with custom design tokens
- **UI Components**: Custom components with Lucide React icons
- **Markdown**: react-markdown with remark-gfm for legal document rendering
- **State Management**: React Context (AuthContext) with localStorage persistence
- **Legal Citations**: Custom citation parser with AustLII integration

### Backend (Dual Deployment)
- **Standalone**: FastAPI app in `backend/main.py` (runs on port 8000)  
- **Serverless**: Vercel functions in `api/index.py` (deployed under `/api/*`)
- **Runtime**: Python 3.12 for Vercel functions
- **Authentication**: JWT-based demo auth (in-memory user store)
- **Legal Corpus**: Australian legal database integration with semantic search

## Development Commands

### Frontend Development
```bash
npm start                    # Start React dev server (localhost:3000)
npm run build               # Build for production
npm test                    # Run unit tests with Jest
npm run test:coverage       # Run tests with coverage report
npm run test:e2e           # Run Playwright E2E tests
npm run test:e2e:ui        # Run E2E tests with UI
npm run test:all           # Run both unit and E2E tests
```

### Backend Development
```bash
# Standalone FastAPI
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Or via Makefile
make start-backend
```

### Testing
```bash
# Frontend tests
npm test                                    # Jest unit tests
npm run test:e2e                           # Playwright E2E tests

# Python API tests  
python tests/python/test_api_endpoints.py http://localhost:8000

# Docker
docker-compose up --build                  # Full stack
```

### Linting and Formatting
```bash
# Python (configured in pyproject.toml)
black --line-length 100 api/ backend/     # Format Python code
ruff check api/ backend/                   # Lint Python code

# JavaScript/React (uses ESLint from react-scripts)
npm run build                              # Includes linting checks
```

## Key File Locations

### Frontend Architecture
- `src/App.js` - Main app component with routing
- `src/components/ChatInterface.js` - Core chat UI
- `src/components/Message.js` - Message rendering with citations
- `src/components/Sidebar.js` - Chat history management
- `src/components/AuthModal.js` - Authentication UI
- `src/components/CitationModal.js` - Legal citation previews
- `src/utils/citationParser.js` - Citation detection and parsing
- `src/services/austliiService.js` - AustLII integration
- `src/contexts/AuthContext.js` - Authentication state management

### Backend Architecture
- `backend/main.py` - Standalone FastAPI server
- `api/index.py` - Vercel serverless functions (mirrors backend endpoints)
- `api/legal_corpus.py` - Australian legal database
- `api/hardened_endpoints.py` - Production-ready API handlers
- `api/streaming_handler.py` - Real-time response streaming

### Testing
- `src/components/__tests__/` - React component tests
- `src/utils/__tests__/` - Utility function tests  
- `tests/e2e/` - Playwright end-to-end tests
- `tests/python/` - Python API tests

## Configuration Files

### Build & Deploy
- `vercel.json` - Vercel deployment config (Python 3.12 runtime, static build)
- `package.json` - NPM dependencies and scripts
- `playwright.config.js` - E2E test configuration
- `tailwind.config.js` - Tailwind CSS customization

### Python Setup
- `pyproject.toml` - Python formatting/linting (Black, Ruff)
- `api/requirements.txt` - Vercel serverless dependencies
- `backend/requirements.txt` - Standalone server dependencies
- `tests/requirements.txt` - Python testing dependencies

## Environment Variables

### Frontend (.env in project root)
```
REACT_APP_API_ENDPOINT=http://localhost:8000  # Backend URL
```

### Backend (export in shell or deployment platform)
```
JWT_SECRET_KEY=<jwt-secret>              # JWT signing key
ALLOWED_ORIGINS=http://localhost:3000    # CORS origins
OPENAI_API_KEY=<openai-key>              # OpenAI integration
OPENAI_BASE_URL=<custom-url>             # Optional OpenAI routing
```

## Testing Strategy

### Unit Tests (Jest + React Testing Library)
- Components tested through user interactions
- Mock Service Worker (MSW) for API mocking
- High coverage requirements (90%+ per package.json)
- Test files co-located with components

### E2E Tests (Playwright)
- Cross-browser testing (Chrome, Firefox, Safari)
- Mobile/tablet responsive testing
- Legal workflow validation
- Citation accuracy testing
- Accessibility compliance testing

### Python Tests
- API endpoint validation
- Legal corpus integration tests
- Citation parsing accuracy

## Development Patterns

### React Components
- Functional components with hooks
- PropTypes for type checking
- Custom hooks for shared logic
- Context for global state (auth, settings)

### Error Handling
- User-friendly error messages
- Graceful API failure handling
- Citation fallbacks to AustLII search

### Legal Citation Parsing
- Supports Acts, Regulations, Cases
- AustLII URL generation
- Preview modal with embedded content
- Fallback search functionality

## Common Tasks

### Adding a New Component
1. Create component in `src/components/`
2. Add corresponding test file in `__tests__/`
3. Export from component if needed by other modules
4. Update parent components to use new component

### Modifying API Endpoints
1. Update both `backend/main.py` AND `api/index.py` (keep in sync)
2. Add tests in `tests/python/`
3. Update frontend service calls if needed

### Citation Parser Updates
1. Modify `src/utils/citationParser.js`
2. Update tests in `src/utils/__tests__/citationParser.test.js`
3. Test with real legal citations in E2E tests

## Deployment

### Vercel (Recommended)
- Frontend: Static build deployed to CDN
- Backend: Serverless functions under `/api/*`
- Automatic deploys from Git
- Environment variables via Vercel dashboard

### Docker
- Full stack via `docker-compose.yml`
- Frontend served by Nginx
- Backend as separate service
- Good for local development and self-hosting

## Troubleshooting

### Common Issues
- **Vercel Function Timeout**: Check Python runtime version in `vercel.json`
- **CORS Errors**: Verify `ALLOWED_ORIGINS` environment variable
- **Citation Links Broken**: Check AustLII service availability
- **Build Failures**: Ensure all dependencies in package.json and requirements.txt

### Performance Notes
- Frontend build outputs to `build/` directory
- Large bundles can be analyzed with `npm run build:analyze`
- Python dependencies should be minimal for faster cold starts
- Citation parsing is client-side for better performance

## Git Workflow
- Main branch: `main`
- Current branch: `chore/vercel-runtime-fix-and-static-build`
- Use conventional commit format (feat:, fix:, chore:, etc.)
- All tests must pass before merging