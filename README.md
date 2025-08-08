# AusLex AI - Australian Legal Assistant

A modern web application for interacting with a GPT-20B model fine-tuned on Australian legal data. This application provides a professional interface for legal research, case law analysis, and legal assistance.

## Features

- 🤖 **AI-Powered Legal Assistant**: Powered by GPT-20B fine-tuned on Australian legal datasets
- 💬 **Interactive Chat Interface**: Clean, professional chat interface with message history
- ⚙️ **Configurable Settings**: Adjustable model parameters (temperature, max tokens, top-p)
- 📋 **Copy to Clipboard**: Easy copying of AI responses
- 🎨 **Modern UI/UX**: Professional design with Tailwind CSS
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🔧 **API Integration**: Ready to connect to your deployed model endpoint

## Screenshots

The application features a clean, professional interface with:
- Header with branding and navigation controls
- Main chat area with message bubbles
- Sidebar with information about the AI assistant
- Settings panel for model configuration
- Responsive design for all screen sizes

## Getting Started

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn
- Your deployed GPT-20B model endpoint

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd auslex-20b-webapp
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the root directory:
```env
REACT_APP_API_ENDPOINT=http://localhost:8000
```

4. Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`.

### Configuration

The application expects your GPT-20B model to be deployed with a REST API endpoint that accepts POST requests at `/chat` with the following format:

**Request:**
```json
{
  "message": "Your legal question here",
  "max_tokens": 2048,
  "temperature": 0.7,
  "top_p": 0.9
}
```

**Response:**
```json
{
  "response": "AI response here"
}
```

## Deployment

### Build for Production

```bash
npm run build
```

This creates a `build` folder with optimized production files.

### Environment Variables

Set the following environment variables for production:

- `REACT_APP_API_ENDPOINT`: The URL of your deployed model API

### Deployment Options

1. **Vercel**: Connect your GitHub repository and deploy automatically
2. **Netlify**: Drag and drop the `build` folder or connect your repository
3. **AWS S3 + CloudFront**: Upload the `build` folder to S3 and serve via CloudFront
4. **Docker**: Use the provided Dockerfile for containerized deployment

## API Integration

The application is designed to work with any REST API that follows the expected format. You can modify the API integration in `src/App.js` if your endpoint has different requirements.

### Example API Endpoints

- **Local Development**: `http://localhost:8000`
- **Cloud Deployment**: `https://your-model-api.com`
- **Docker Container**: `http://your-container:8000`

## Customization

### Styling

The application uses Tailwind CSS for styling. You can customize the design by modifying:

- `tailwind.config.js` - Color schemes and theme configuration
- `src/index.css` - Custom CSS classes and component styles

### Branding

Update the branding by modifying:

- `public/index.html` - Page title and meta tags
- `src/components/Header.js` - Application name and logo
- `src/App.js` - Welcome messages and descriptions

## Legal Disclaimer

This application is designed for educational and research purposes. The AI responses should not be considered as legal advice. Always consult with qualified legal professionals for actual legal matters.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions about the application, please open an issue in the repository.

## Roadmap

- [ ] Document upload and analysis
- [ ] Case law citation tracking
- [ ] Export conversations to PDF
- [ ] User authentication and conversation history
- [ ] Integration with legal databases
- [ ] Multi-language support 

## RAG Quickstart

Environment
- Create `.env` in project root:
  - `OPENAI_API_KEY=...`
  - `DATABASE_URL=...` (optional, Postgres with pgvector)

Node API
- Start the Node RAG API: `npm run dev:node`
- Default endpoint: `http://localhost:8787/api/ask`

Ingestion
- Use in-memory (default): `npm run ingest -- --path ./sample-corpus`
- Use pgvector: set `DATABASE_URL` then run the same ingest command

pgvector setup (Neon/Supabase)
- Ensure `CREATE EXTENSION IF NOT EXISTS vector;` and optionally `pg_trgm` are enabled.

Store selection
- If `DATABASE_URL` is set, pgvector is used; otherwise an in-memory store is used for development.

### Auth & Rate limiting
- Set `AUSLEX_API_KEY` to enforce an API key via `x-auslex-key` header.
- Rate limiting envs: `RL_WINDOW_MS` (default 60000), `RL_MAX` (default 60).