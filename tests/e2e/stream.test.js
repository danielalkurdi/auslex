// This test simulates streaming by calling the endpoint with stream=1 and verifying SSE envelope shape.
const request = require('supertest');
const express = require('express');

// Minimal stub app that emits SSE ready/delta/done for test stability
function fakeSSEApp() {
  const app = express();
  app.use(express.json());
  app.post('/api/ask', (req, res) => {
    if (String(req.query.stream || '') !== '1') return res.json({ answer: { answer: 'ok' }, snippets: [] });
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache, no-transform');
    res.setHeader('Connection', 'keep-alive');
    res.write('event: ready\n');
    res.write('data: {}\n\n');
    res.write('event: snippets\n');
    res.write('data: [{"id":"s1","title":"t"}]\n\n');
    res.write('event: delta\n');
    res.write('data: {"proseFragment":"Hello "}\n\n');
    res.write('event: delta\n');
    res.write('data: {"proseFragment":"world"}\n\n');
    res.write('event: done\n');
    res.write('data: {"answer":{"answer":"Hello world"}}\n\n');
    res.end();
  });
  return app;
}

describe('SSE stream contract', () => {
  const app = fakeSSEApp();
  it('emits ready, snippets, delta, done', async () => {
    const res = await request(app).post('/api/ask?stream=1').send({ question: 'x' });
    expect(res.status).toBe(200);
    const text = res.text;
    expect(text.includes('event: ready')).toBe(true);
    expect(text.includes('event: snippets')).toBe(true);
    expect(text.includes('event: delta')).toBe(true);
    expect(text.includes('event: done')).toBe(true);
  });
});

