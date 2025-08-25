# AusLex AI Deployment Guide

## Overview

This guide explains how to deploy the AusLex AI legal assistant application to Vercel with proper configuration.

## Prerequisites

- Vercel account
- OpenAI API key (for full functionality)
- Node.js 18+ and Python 3.9+ for local development

## Deployment Steps

### 1. Environment Variables Configuration

Set these environment variables in your Vercel dashboard:

#### Required for Full Functionality:
```
OPENAI_API_KEY=your_openai_api_key_here
```

#### Optional Configuration:
```
OPENAI_ORG=your_openai_org_id
OPENAI_PROJECT=your_openai_project_id
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_FALLBACK_MODEL=gpt-4o-mini
ALLOWED_ORIGINS=https://your-domain.vercel.app
JWT_SECRET_KEY=your_secure_random_jwt_secret
```

### 2. Deploy to Vercel

1. Connect your repository to Vercel
2. Vercel will automatically detect the configuration from `vercel.json`
3. Set the environment variables in the Vercel dashboard
4. Deploy

### 3. Verify Deployment

Test your deployment using the provided test script:

```bash
python test_api_endpoints.py https://your-app.vercel.app
```

Or test individual endpoints:

- Health check: `https://your-app.vercel.app/api/health`
- API root: `https://your-app.vercel.app/api`
- Chat endpoint: `https://your-app.vercel.app/api/chat` (POST)

## Features

### With OpenAI API Key Configured:
- Full AI-powered legal chat assistance
- Legal database integration
- Citation system
- Advanced research capabilities

### Without OpenAI API Key (Demo Mode):
- Basic legal information
- Links to official legal resources
- Educational content
- No AI-powered responses

## Architecture

- **Frontend**: React application served as static files
- **Backend**: FastAPI Python application running as Vercel serverless functions
- **Database**: In-memory storage (suitable for demo/development)
- **Legal Data**: Mock legal database with sample provisions

## File Structure

```
auslex-20b/
├── api/                    # Python FastAPI backend
│   ├── index.py           # Main API endpoints
│   └── requirements.txt   # Python dependencies
├── src/                   # React frontend
├── public/               # Static assets
├── vercel.json          # Vercel configuration
├── package.json         # Node.js dependencies
└── .env.example        # Environment variables template
```

## Troubleshooting

### Common Issues

1. **500 Error on Chat Endpoint**
   - Check if OPENAI_API_KEY is set in Vercel environment variables
   - Verify the API key is valid
   - Check Vercel function logs for detailed error messages

2. **404 Error on API Endpoints**
   - Ensure `vercel.json` is properly configured
   - Check that the API routes are correctly defined in `api/index.py`

3. **CORS Issues**
   - Set ALLOWED_ORIGINS environment variable with your domain
   - Ensure the frontend is using the correct API endpoint

4. **Missing Dependencies**
   - Check that all dependencies are listed in `requirements.txt` and `package.json`
   - Verify Python version compatibility (Python 3.9+ required)

### Debug Steps

1. Check Vercel function logs in the dashboard
2. Test API endpoints individually using curl or the test script
3. Verify environment variables are set correctly
4. Test locally using `uvicorn api.index:app --reload`

## Local Development

1. Install dependencies:
   ```bash
   npm install
   pip install -r api/requirements.txt
   ```

2. Set environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run locally:
   ```bash
   # Frontend
   npm start

   # Backend (in another terminal)
   cd api && python -m uvicorn index:app --reload --host 0.0.0.0 --port 8000
   ```

## Security Considerations

- Never commit API keys to version control
- Use environment variables for all sensitive configuration
- Set CORS origins to specific domains in production
- Use strong JWT secret keys

## Support

For deployment issues:
1. Check the Vercel function logs
2. Test using the provided test script
3. Verify all environment variables are configured
4. Ensure dependencies are properly specified

The application is designed to work in demo mode even without OpenAI configuration, providing educational legal information and links to official resources.