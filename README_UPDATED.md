# AusLex-20B - Australian Legal AI Assistant

An optimized React web application for interacting with GPT-20B fine-tuned on Australian legal data.

## Recent Optimizations

- **Performance**: Added React.memo, useCallback, and useMemo optimizations
- **Accessibility**: Improved ARIA labels, keyboard navigation, and screen reader support  
- **Code Quality**: Added PropTypes validation and error handling
- **Security**: Enhanced input validation and API response sanitization

## Quick Start

```bash
npm install
npm start
```

Visit http://localhost:3000 to view the application.

## Deployment

```bash
npm run build
```

## Technology Stack

- React 18 with hooks optimization
- Tailwind CSS for styling
- FastAPI backend (Python) for legacy endpoints
- Node/TypeScript API at `/api/ask` for RAG-first GPT-5 flow
- Docker support included

## License

MIT License
