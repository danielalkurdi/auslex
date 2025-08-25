# Repository Guidelines

## Project Structure & Modules
- `src/`: React app (components, contexts, services, utils, styles).
- `backend/`: Standalone FastAPI service (`main.py`).
- `api/`: Vercel serverless FastAPI entry (`index.py`) mirroring backend routes under `/api/*`.
- `public/`: Static assets. `build/`: production output.
- `tests/e2e/`: Playwright tests.
- `scripts/`: Utility scripts (API smoke tests, demos).

## Build, Test, and Development
- `npm start`: Run React dev server at `http://localhost:3000`.
- `npm run build`: Create production build in `build/`.
- `npm test`: Run Jest unit tests (watch mode).
- `npm run test:coverage`: Jest with coverage (thresholds: 90% global).
- `npm run test:e2e`: Run Playwright E2E tests.
- Backend (standalone): `cd backend && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 8000`.
- Docker (both services): `docker-compose up --build`.

## Coding Style & Naming
- JavaScript/React: CRA defaults with `eslintConfig: react-app`.
- Indentation: 2 spaces; use semicolons; JSX props in camelCase.
- Components: `PascalCase` filenames (e.g., `CitationModal.js`); variables/functions `camelCase`.
- Python (API): Follow PEP 8; type hints preferred in FastAPI models and endpoints.

## Testing Guidelines
- Unit: Jest in `src/`. Name tests `*.test.js(x)` near code or in `__tests__/`.
- E2E: Playwright specs in `tests/e2e/` (`npm run test:e2e`).
- API smoke: `python tests/python/test_api_endpoints.py http://localhost:8000`.
- Coverage: Maintained at 90% global (branches/functions/lines/statements).

## Commit & Pull Requests
- Commits: Use conventional types (emoji optional): `feat:`, `fix:`, `chore:`, `test:`, `ci:`, `docs:` (e.g., `✨ feat: add citation previews`).
- PRs: Include purpose/summary, linked issues, screenshots for UI changes, test plan (unit/E2E), and any env or migration notes.
- Keep PRs focused; update related docs when behavior changes.

## Security & Configuration
- Environment: Copy `.env.example` → `.env` for frontend. Backend reads env directly (e.g., `JWT_SECRET_KEY`, `OPENAI_API_KEY`, `ALLOWED_ORIGINS`).
- Never commit secrets; prefer local `.env` and host-level variables in deployment.
- Local API URL: `REACT_APP_API_ENDPOINT=http://localhost:8000`.
