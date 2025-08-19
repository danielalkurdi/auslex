## AusLex AI — Australian Legal Assistant

Modern React + FastAPI app for Australian legal research with comprehensive Australian Legal Corpus integration. Features include a chat UI, configurable model settings, clickable legal citation previews (AustLII), accurate section 359A support, and a simple authentication flow for demo purposes. You can run the backend as a standalone FastAPI service or as a serverless function on Vercel.

### Key Features

- 💬 **Chat interface with multi-chat history**: Create, rename, delete, and switch between chats in the `Sidebar`. Messages render with Markdown and citation-aware content.
- ⚙️ **Configurable settings**: Adjust `max_tokens`, `temperature`, and `top_p` in `Settings`. Change API endpoint at runtime.
- 🔎 **Legal citation parsing & previews**: Detects Acts, Regulations, and Case citations in responses, turns them into clickable links, and shows a preview modal with direct AustLII links and fallbacks.
- 📚 **Australian Legal Corpus**: Comprehensive legal database integration with semantic search and section 359A Migration Act support.
- 🔐 **Demo authentication**: Email/password register/login modal; JWT stored in `localStorage`. In-memory user store for demo (not production-grade).
- 🎨 **Design system**: Tailwind tokens for color, spacing, typography; responsive layout and subtle micro-interactions.
- 🚀 **Flexible backend**: Same API available under root paths (standalone) and `/api/*` (Vercel serverless).

### Architecture

- Frontend: React 18, Tailwind CSS, `react-markdown`, `lucide-react`.
- Backend: FastAPI (see two options below).
  - Standalone: `backend/main.py`
  - Vercel serverless: `api/index.py` (exposes identical endpoints with `/api` prefix)

Relevant code:
- Chat UI: `src/App.js`, `src/components/ChatInterface.js`, `src/components/Message.js`, `src/components/Sidebar.js`
- Settings: `src/components/SettingsPanel.js`
- Auth: `src/components/AuthModal.js`, `src/contexts/AuthContext.js`
- Citations: `src/utils/citationParser.js`, `src/components/CitationText.js`, `src/components/CitationModal.js`, `src/services/austliiService.js`
- Styles & tokens: `tailwind.config.js`, `src/index.css`

---

## Getting Started

### Prerequisites

- Node.js 18+
- npm
- Python 3.9+

### 1) Frontend setup

```bash
npm install
npm start
```

By default the app uses `REACT_APP_API_ENDPOINT=http://localhost:8000`. You can override it in a `.env` file at the repo root:

```env
REACT_APP_API_ENDPOINT=http://localhost:8000
```

The UI runs at `http://localhost:3000`.

### 2) Backend — Option A: Standalone FastAPI

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Environment variables (optional):
- `JWT_SECRET_KEY` — secret for signing JWTs
- `ALLOWED_ORIGINS` — comma-separated origins (defaults to `http://localhost:3000,http://localhost:3001` in `api/index.py`; `backend/main.py` defaults to `http://localhost:3000`)

### 2) Backend — Option B: Vercel serverless

The repository includes `vercel.json` and `api/index.py`. When deployed to Vercel:
- API routes are served under `/api/*` (e.g., `/api/chat`, `/api/auth/login`).
- Frontend is built as a static site (`build/`).

For local development you can continue using the standalone FastAPI server instead.

### Alternative: Docker Compose

```bash
docker-compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## API

All endpoints exist at root (standalone FastAPI) and under `/api/*` (Vercel). Examples below show the root paths.

### POST /chat
Request:
```json
{
  "message": "Your legal question here",
  "max_tokens": 2048,
  "temperature": 0.7,
  "top_p": 0.9
}
```

Response:
```json
{
  "response": "...",
  "tokens_used": 123,
  "processing_time": 1.42
}
```

Notes:
- The backend currently returns mock responses keyed to certain keywords (e.g., “citation”, “negligence”, etc.) and a generic legal disclaimer otherwise.

### POST /legal/provision
Request:
```json
{
  "act_name": "Migration Act",
  "year": "1958",
  "jurisdiction": "Cth",
  "provision_type": "section",
  "provision": "55",
  "full_citation": "Migration Act 1958 (Cth) s 55"
}
```

Response:
```json
{
  "provision_text": "<p>...</p>",
  "metadata": { "title": "...", "lastAmended": "...", "effectiveDate": "..." },
  "source": "Federal Register of Legislation",
  "full_act_url": "https://...",
  "notes": ["..."],
  "related_provisions": ["..."],
  "case_references": ["..."]
}
```

### Auth
Demo-only in-memory auth suitable for local testing.

- POST `/auth/register` → `{ name, email, password }`
- POST `/auth/login` → `{ email, password }`

Response shape:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": { "id": "user_1", "name": "...", "email": "..." }
}
```

The frontend stores `authToken` and `userData` in `localStorage`. Chat history is persisted to `localStorage` when authenticated.

---

## Using the app

- Open the app and start a new chat from the `Sidebar`.
- Type any prompt. To see citation previews, include legal citations or the word “citation” (triggers a sample response with clickable citations).
- Click highlighted citations to open the `CitationModal` with an embedded AustLII view and links.
- Configure API endpoint and model parameters in `Settings`.
- Use the `Sign In` button for demo auth. This uses the local FastAPI auth endpoints.

---

## Styling & Design

- Tailwind tokens and scales live in `tailwind.config.js`.
- Global styles and responsive behaviors in `src/index.css`.

---

## Build & Deploy

### Static build
```bash
npm run build
```
Outputs to `build/`.

### Vercel
- `vercel.json` configures a static build for the frontend and Python serverless function at `api/index.py`.
- Routes `/api/*` are forwarded to the Python function.

### Docker
- `Dockerfile` builds the frontend and serves it with Nginx.
- `docker-compose.yml` runs both frontend and backend together for local use.

---

## Notes & Limitations

- The backend does not call a real LLM by default; responses are mock/demo. Wire your own model behind `/chat` or adapt the handler.
- The auth layer is in-memory and for demonstration only.
- AustLII embedding may be restricted by remote headers in some cases; the modal provides direct links and a search fallback.

---

## License

MIT — see `LICENSE`.

## Contributing

PRs welcome. Please:
1) Fork the repo
2) Create a feature branch
3) Add tests or thorough manual validation
4) Open a pull request

