# Suggested Commands for AusLex Development

## Development Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server (runs on http://localhost:3000)
npm start

# Build for production
npm run build

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

### Backend Development (Standalone)
```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server (runs on http://localhost:8000)
uvicorn main:app --host 0.0.0.0 --port 8000

# Start with hot reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Backend Development (Serverless/Vercel)
```bash
# API routes served under /api/* when deployed to Vercel
# Local development uses standalone FastAPI instead
# Deploy to Vercel automatically handles serverless functions
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Testing Commands
```bash
# Run Python tests for backend functionality
python test_enhanced_legal_ai.py
python test_legal_corpus.py
python test_section_359a.py

# Run frontend tests (Jest + React Testing Library)
npm test

# Run specific test file
npm test ChatInterface.test.js

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage report
npm test -- --coverage --watchAll=false
```

### Environment Setup
```bash
# Create .env file for frontend
echo "REACT_APP_API_ENDPOINT=http://localhost:8000" > .env

# Backend environment variables (optional)
export JWT_SECRET_KEY="your-secret-key"
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001"
```

### Linting & Formatting
```bash
# ESLint is configured via create-react-app
# Runs automatically with npm start and npm run build

# Check for linting issues
npm run build  # Will fail if linting issues exist
```

### Git Commands (Windows)
```bash
# Basic git operations
git status
git add .
git commit -m "message"
git push

# Branch management
git branch
git checkout -b feature/branch-name
git merge main
```

### Windows-Specific Utilities
```bash
# File system navigation
dir          # List directory contents (equivalent to ls)
cd path      # Change directory
type file    # Display file contents (equivalent to cat)
find "text"  # Search for text in files
copy         # Copy files (equivalent to cp)
del          # Delete files (equivalent to rm)

# Network testing
ping localhost
netstat -an | findstr :3000  # Check if port 3000 is in use
```

### Deployment Commands
```bash
# Vercel deployment
npx vercel

# Build production bundle
npm run build

# Docker production build
docker build -t auslex-app .
docker run -p 3000:80 auslex-app
```