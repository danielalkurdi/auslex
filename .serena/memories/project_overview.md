# AusLex Australian Legal AI Platform - Project Overview

## Purpose
AusLex AI is a modern React + FastAPI application designed for Australian legal research. It serves as an AI-powered legal assistant with comprehensive Australian Legal Corpus integration, featuring chat-based interactions, legal citation parsing, and AustLII integration for accurate legal references.

## Key Features
- **Chat Interface**: Multi-chat history with create, rename, delete, and switch capabilities
- **Legal Citation Parsing**: Detects Acts, Regulations, and Case citations; converts to clickable links with AustLII previews  
- **Australian Legal Corpus**: Comprehensive legal database integration with semantic search
- **Authentication**: Demo JWT-based auth with email/password (in-memory for demo)
- **Settings Configuration**: Adjustable max_tokens, temperature, top_p parameters
- **Design System**: Tailwind CSS with ochre (#C9A063) and jet black (#0D0D0D) color scheme
- **Responsive Layout**: Mobile-first design with collapsible sidebar

## Tech Stack
- **Frontend**: React 18, Tailwind CSS, react-markdown, lucide-react
- **Backend**: FastAPI (dual deployment: standalone + Vercel serverless)
- **Testing**: Jest, React Testing Library (configured but no existing tests)
- **Authentication**: JWT with localStorage storage
- **Legal Data**: AustLII integration, custom citation parser
- **Deployment**: Docker Compose, Vercel, Nginx

## Architecture
- Frontend: React SPA with context-based state management
- Backend: FastAPI with two deployment options:
  - Standalone: `backend/main.py` 
  - Serverless: `api/index.py` (identical endpoints with `/api` prefix)
- Legal Services: Citation parsing, AustLII lookup, corpus search
- Authentication: Context-based auth with JWT tokens

## File Structure
```
src/
├── components/          # React components
│   ├── ChatInterface.js
│   ├── AuthModal.js
│   ├── CitationModal.js
│   ├── CitationText.js
│   └── ...
├── contexts/           # React context providers
│   └── AuthContext.js
├── services/          # External service integrations
│   ├── austliiService.js
│   └── legalDatabase.js
└── utils/            # Utility functions
    └── citationParser.js
```

## Critical Components
1. **Citation Parser** (`utils/citationParser.js`): Complex regex-based parser for Australian legal citations
2. **Chat Interface** (`components/ChatInterface.js`): Real-time messaging with legal context
3. **Auth System** (`contexts/AuthContext.js`): JWT-based authentication with persistence
4. **Legal Database** (`services/legalDatabase.js`): Corpus search and semantic matching