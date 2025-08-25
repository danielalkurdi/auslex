## AusLex AI — Advanced Australian Legal Assistant

Modern React + FastAPI application for Australian legal research powered by AI vector search and comprehensive legal corpus integration. Features semantic search, legal compliance validation, clickable citation previews (AustLII), and professional-grade legal response generation.

### 🚀 Key Features

#### AI-Powered Legal Research
- 🧠 **Vector Search Engine**: OpenAI embeddings + Pinecone for semantic legal document search
- 📊 **Hybrid Search**: Combines vector similarity with traditional BM25/TF-IDF ranking
- 🎯 **RAG System**: Retrieval-Augmented Generation for accurate, cited legal responses
- 📚 **Australian Legal Corpus**: 229,122+ documents, 1.4B+ tokens from comprehensive legal database
- ⚖️ **Legal Compliance**: Automated validation, risk assessment, and disclaimer injection

#### User Interface & Experience
- 💬 **Chat Interface**: Multi-chat history with create, rename, delete, and switch functionality
- ⚙️ **Configurable Settings**: Adjust `max_tokens`, `temperature`, `top_p`, search methods
- 🔎 **Citation Previews**: Detects Acts, Regulations, Cases - clickable with AustLII integration
- 🎨 **Design System**: Tailwind CSS with custom tokens, responsive layout
- 🔐 **Demo Authentication**: JWT-based email/password system with in-memory store

#### Technical Architecture
- 🚀 **Flexible Backend**: Standalone FastAPI or Vercel serverless functions
- 📈 **Performance Monitoring**: Real-time metrics, search analytics, compliance tracking
- 🧪 **Comprehensive Testing**: Unit, integration, and E2E test coverage
- 🛡️ **Security**: Rate limiting, input validation, compliance safeguards
- 📦 **Production Ready**: Docker support, environment validation, health checks

### 🏗️ Architecture

#### Frontend Stack
- **Framework**: React 18 with Create React App
- **Styling**: Tailwind CSS with custom design tokens
- **UI Components**: Custom components with Lucide React icons
- **Markdown**: react-markdown with remark-gfm for legal document rendering
- **State Management**: React Context (AuthContext) with localStorage persistence

#### Backend Stack
- **API Framework**: FastAPI with Python 3.12
- **AI Integration**: OpenAI GPT-4o-mini + text-embedding-3-small
- **Vector Database**: Pinecone serverless with hybrid search
- **Legal Corpus**: HuggingFace Open Australian Legal Corpus
- **Compliance**: Automated legal validation and disclaimer system
- **Deployment**: Dual mode - standalone or Vercel serverless

#### Key Components
```
Frontend:
├── src/App.js                 # Main app with routing
├── src/components/
│   ├── ChatInterface.js       # Core chat UI
│   ├── Message.js            # Message rendering with citations
│   ├── Sidebar.js            # Chat history management
│   ├── AuthModal.js          # Authentication UI
│   └── CitationModal.js      # Legal citation previews
├── src/utils/
│   └── citationParser.js     # Citation detection and parsing
└── src/contexts/AuthContext.js # Authentication state

Backend:
├── api/index.py              # Vercel serverless functions
├── api/vector_search_engine.py # AI vector search system
├── api/legal_compliance.py   # Compliance validation
├── api/corpus_processor.py   # Legal corpus processing
├── api/performance_monitor.py # Performance tracking
└── backend/main.py           # Standalone FastAPI server
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js 18+** with npm
- **Python 3.12+** (required for Vercel deployment)
- **API Keys**: OpenAI API key (required), Pinecone API key (optional for vector search)

### Environment Setup

1. **Create Environment File**
   ```bash
   # Create from template
   python scripts/setup_environment.py --create-env
   
   # Configure your API keys in .env
   cp .env.example .env
   ```

2. **Required Environment Variables**
   ```bash
   # Required
   OPENAI_API_KEY=sk-your-openai-api-key-here
   
   # Optional (for vector search)
   PINECONE_API_KEY=your-pinecone-api-key-here
   PINECONE_ENVIRONMENT=us-east1-aws
   PINECONE_INDEX_NAME=auslex-legal-corpus
   ```

3. **Validate Setup**
   ```bash
   # Run comprehensive environment validation
   python scripts/setup_environment.py
   ```

### 🖥️ Frontend Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

The app runs at `http://localhost:3000` and uses `REACT_APP_API_ENDPOINT=http://localhost:8000` by default.

### 🔧 Backend Development

#### Option 1: Standalone FastAPI Server
```bash
# Install Python dependencies
pip install -r api/requirements.txt

# Start server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Or using Makefile
make start-backend
```

#### Option 2: Vercel Serverless (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel --prod

# Or for development
vercel dev
```

### 🧠 AI System Setup

#### Phase 1: Basic Setup (Current)
```bash
# Validate Phase 1 completion
python scripts/validate_phase1.py

# If validation passes, system is ready for basic use
```

#### Phase 2: Enhanced AI Capabilities
```bash
# Process legal corpus for vector search
python scripts/process_corpus.py process --batch-size 100 --max-documents 1000

# Monitor processing status
python scripts/process_corpus.py status

# Validate system health
python scripts/process_corpus.py validate
```

---

## 🧪 Testing

### Test Infrastructure
- **Unit Tests**: Jest + React Testing Library (frontend), pytest (backend)
- **Integration Tests**: API endpoint validation, AI system testing
- **E2E Tests**: Playwright for full user journey validation
- **Legal Compliance Tests**: Automated validation testing

### Running Tests

```bash
# Frontend tests
npm test                          # Unit tests
npm run test:coverage            # With coverage report
npm run test:e2e                 # Playwright E2E tests
npm run test:e2e:ui             # E2E with UI
npm run test:all                # All tests

# Backend tests
python -m pytest tests/python/                    # All Python tests
python -m pytest tests/python/test_vector_search.py  # Vector search tests
python -m pytest tests/python/test_legal_compliance.py # Compliance tests

# Integration tests
python tests/python/test_api_endpoints.py http://localhost:8000

# Performance tests
python scripts/validate_phase1.py              # Phase 1 validation
```

### Test Coverage Requirements
- **Frontend**: >90% coverage (enforced by package.json)
- **Backend**: Comprehensive unit and integration coverage
- **E2E**: Critical user journeys and accessibility compliance

---

## 📊 Performance Monitoring

### Built-in Analytics
```bash
# Get search performance metrics
curl http://localhost:8000/api/performance/search?hours=24

# Get compliance analytics  
curl http://localhost:8000/api/performance/compliance?hours=24

# System health status
curl http://localhost:8000/api/health
```

### Key Metrics Tracked
- **Search Performance**: Response times, relevance scores, cache hit rates
- **Compliance Metrics**: Risk assessment, validation accuracy, disclaimer effectiveness
- **System Health**: CPU, memory, error rates, API latencies
- **User Analytics**: Query patterns, success rates, professional adoption

---

## 🛡️ Legal Compliance & Safety

### Automated Compliance System
- **Risk Assessment**: Automatic classification of response risk levels
- **Prohibited Language Detection**: Blocks inappropriate legal advice
- **Domain-Specific Disclaimers**: Tailored warnings for different legal areas
- **Professional Standards**: Compliance with Australian legal professional ethics

### Disclaimer Examples
- **General Legal Information**: Educational purposes disclaimer
- **Immigration Law**: Migration agent consultation recommended
- **Criminal Law**: Immediate legal representation required warning
- **Family Law**: Fact-specific professional advice disclaimer

### Safety Features
- Input sanitization and validation
- Response filtering for harmful content
- Rate limiting and abuse prevention
- Professional liability safeguards

---

## 🚀 Deployment

### Vercel Deployment (Recommended)
```bash
# Install dependencies
npm install
pip install -r api/requirements.txt

# Deploy
vercel --prod

# Environment variables set via Vercel dashboard
```

### Docker Deployment
```bash
# Full stack
docker-compose up --build

# Frontend only
docker build -f Dockerfile.frontend -t auslex-frontend .
docker run -p 3000:80 auslex-frontend

# Backend only  
docker build -f Dockerfile.backend -t auslex-backend .
docker run -p 8000:8000 auslex-backend
```

### Configuration Files
- `vercel.json`: Vercel deployment settings (Python 3.12 runtime)
- `docker-compose.yml`: Full stack Docker setup
- `playwright.config.js`: E2E test configuration
- `tailwind.config.js`: Design system configuration

---

## 📁 Project Structure

```
auslex/
├── 📂 Frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── utils/              # Citation parsing, utilities
│   │   ├── contexts/           # React contexts (auth, etc.)
│   │   └── services/           # API integration services
│   └── public/                 # Static assets
├── 📂 Backend
│   ├── api/                    # Vercel serverless functions
│   │   ├── index.py           # Main API endpoints
│   │   ├── vector_search_engine.py # AI search system
│   │   ├── legal_compliance.py    # Compliance validation
│   │   ├── corpus_processor.py    # Legal corpus processing
│   │   └── performance_monitor.py # Analytics system
│   ├── backend/               # Standalone FastAPI server
│   └── requirements.txt       # Python dependencies
├── 📂 Testing
│   ├── tests/python/          # Backend tests
│   ├── tests/e2e/            # Playwright E2E tests
│   └── src/components/__tests__/ # Frontend tests
├── 📂 Scripts
│   ├── setup_environment.py   # Environment validation
│   ├── process_corpus.py     # Corpus processing
│   └── validate_phase1.py    # Success criteria validation
├── 📂 Documentation
│   ├── IMPLEMENTATION_ROADMAP.md # Development roadmap
│   └── CLAUDE.md             # Development guidelines
└── 📂 Configuration
    ├── vercel.json           # Deployment configuration
    ├── docker-compose.yml   # Docker setup
    └── playwright.config.js # E2E test config
```

---

## 🔧 Development Commands

### Frontend Development
```bash
npm start                    # Development server (localhost:3000)
npm run build               # Production build
npm run build:analyze       # Bundle analysis
npm test                    # Run tests
npm run lint                # ESLint checking
```

### Backend Development
```bash
# Standalone FastAPI
uvicorn backend.main:app --reload

# Vercel development
vercel dev

# Format and lint
black api/ backend/         # Python formatting
ruff check api/ backend/    # Python linting
```

### AI System Management
```bash
# Environment setup
python scripts/setup_environment.py
python scripts/setup_environment.py --create-env

# Corpus processing
python scripts/process_corpus.py validate
python scripts/process_corpus.py process --batch-size 100
python scripts/process_corpus.py status

# System validation
python scripts/validate_phase1.py
python scripts/validate_phase1.py --json-output
```

---

## 🎯 Implementation Roadmap

The system follows a 5-phase implementation roadmap:

### ✅ Phase 1: Foundation (Weeks 1-2) - **COMPLETED**
- Vector search engine with OpenAI + Pinecone
- Legal compliance system with risk assessment
- Comprehensive test infrastructure
- Environment validation and setup scripts

### 🚧 Phase 2: Enhanced Search (Weeks 3-4) - **IN PROGRESS** 
- Corpus processing pipeline for 229,122+ legal documents
- Hybrid search optimization (70% vector + 30% BM25)
- Performance monitoring and analytics
- Query processing enhancements

### 📋 Phase 3: RAG Enhancement (Weeks 5-6)
- Advanced context selection algorithms
- Citation accuracy verification
- Fact-checking layer integration
- Multi-source synthesis capabilities

### 📋 Phase 4: Production Optimization (Weeks 7-8)
- Multi-level caching strategies
- A/B testing framework
- Legal review processes
- 99.9% availability targets

### 📋 Phase 5: Advanced Features (Weeks 9-12)
- Knowledge graph integration (Neo4j)
- Domain-specific expert modes
- Real-time fact-checking
- Legal analytics dashboard

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for detailed specifications.

---

## 🐛 Troubleshooting

### Common Issues

#### Frontend Issues
- **Build failures**: Check Node.js version (18+ required)
- **API connection errors**: Verify `REACT_APP_API_ENDPOINT` in `.env`
- **Citation links broken**: Confirm AustLII service availability

#### Backend Issues
- **Vercel deployment errors**: Ensure Python 3.12 compatibility
- **API key errors**: Verify `OPENAI_API_KEY` configuration
- **Vector search failures**: Check Pinecone configuration or use fallback mode

#### Performance Issues
- **Slow response times**: Monitor with performance analytics
- **High memory usage**: Check corpus processing batch sizes
- **Rate limiting**: Review API usage and implement caching

### Getting Help
- **Environment Issues**: Run `python scripts/setup_environment.py`
- **Phase 1 Validation**: Run `python scripts/validate_phase1.py`
- **System Status**: Check `/api/health` endpoint
- **Logs**: Monitor browser console and server logs

---

## 🤝 Contributing

### Development Workflow
1. **Setup**: Run environment validation and Phase 1 validation
2. **Development**: Follow code style guidelines in `CLAUDE.md`
3. **Testing**: Comprehensive test coverage required
4. **Compliance**: All legal content must pass validation
5. **Documentation**: Update README and implementation docs

### Code Quality Standards
- **Python**: Black formatting, Ruff linting, type hints
- **JavaScript**: ESLint configuration, Prettier formatting
- **Testing**: >90% coverage, E2E validation required
- **Legal**: Professional compliance standards mandatory

---

## 📄 License

This project is developed for educational and research purposes. Legal information provided is for general guidance only and does not constitute professional legal advice. Users should consult qualified legal professionals for specific legal matters.

---

## 🔗 Links

- **AustLII**: https://www.austlii.edu.au (Australian Legal Information Institute)
- **Federal Register of Legislation**: https://www.legislation.gov.au
- **OpenAI API**: https://platform.openai.com/docs
- **Pinecone Vector Database**: https://www.pinecone.io
- **HuggingFace Legal Corpus**: https://huggingface.co/datasets/isaacus/open-australian-legal-corpus

---

*AusLex AI - Advancing Australian Legal Technology with Responsible AI*