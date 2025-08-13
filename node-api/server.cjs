const express = require('express');
const cors = require('cors');
// Note: This CommonJS server is only used for tests. In dev, use node-api/index.ts.

function createServer(deps) {
  const app = express();
  app.use(cors());
  app.use(express.json());

  const retriever = deps.retriever;

  app.post('/api/ask', async (req, res) => {
    const { question, jurisdiction, asAt } = req.body || {};
    if (!question || typeof question !== 'string') {
      return res.status(400).json({ error: 'question is required' });
    }

    // Test-mode simplified path: no LLM, no TS imports
    if (process.env.TEST_MODE === '1' || !process.env.OPENAI_API_KEY) {
      // Minimal in-test retriever interface: expect .search on deps
      const snippets = await retriever.search({ query: question, jurisdiction, asAt, limit: 5 });
      const first = snippets[0];
      const answer = {
        question,
        answer: first ? `As at ${asAt || 'today'}, relevant authority includes: ${first.meta.title || first.meta.citation || ''}.` : "I cannot answer with confidence.",
        quotes: first ? [{ text: first.text.slice(0, 200), citation: {
          jurisdiction: first.meta.jurisdiction || 'Cth',
          sourceType: first.meta.sourceType || 'legislation',
          title: first.meta.title,
          citation: first.meta.citation,
          provision: first.meta.provision,
          paragraph: first.meta.paragraph,
          url: first.meta.url,
        }}] : [],
        citations: snippets.slice(0, 3).map(s => ({
          jurisdiction: s.meta.jurisdiction || 'Cth',
          sourceType: s.meta.sourceType || 'legislation',
          title: s.meta.title,
          citation: s.meta.citation,
          provision: s.meta.provision,
          paragraph: s.meta.paragraph,
          url: s.meta.url,
        })),
        reasoning_notes: first ? 'Used top snippet and supporting citations.' : 'Insufficient retrieval.',
        limitations: first ? [] : ['insufficient_retrieval'],
        confidence: first ? 0.6 : 0.2
      };
      // Skip schema validation in CJS test shim
      return res.json({ answer, snippets });
    }
    // Non-test mode not supported in CJS shim
    return res.status(500).json({ error: 'not_supported', message: 'Use node-api/index.ts in dev/prod.' });
  });

  return app;
}

module.exports = { createServer };

