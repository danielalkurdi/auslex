const express = require('express');
const request = require('supertest');
const { rateLimit } = require('../../node-api/middleware/rateLimit.cjs');
const { requireApiKey } = require('../../node-api/middleware/auth.cjs');

function makeApp() {
  const app = express();
  app.use(express.json());
  app.post('/api/ask', requireApiKey, rateLimit, (req, res) => res.json({ ok: true }));
  return app;
}

describe('auth & rate limit', () => {
  const app = makeApp();
  it('rejects without API key when required', async () => {
    process.env.AUSLEX_API_KEY = 'k1';
    const res = await request(app).post('/api/ask').send({});
    expect(res.status).toBe(401);
  });
  it('allows with correct key', async () => {
    const res = await request(app).post('/api/ask').set('x-auslex-key','k1').send({});
    expect(res.status).toBe(200);
  });
  it('rate limits after threshold', async () => {
    process.env.RL_WINDOW_MS = '1000';
    process.env.RL_MAX = '2';
    // reset bucket
    global.__AUSLEX_BUCKETS__ = new Map();
    const ok1 = await request(app).post('/api/ask').set('x-auslex-key','k1').send({});
    const ok2 = await request(app).post('/api/ask').set('x-auslex-key','k1').send({});
    const blocked = await request(app).post('/api/ask').set('x-auslex-key','k1').send({});
    expect(ok1.status).toBe(200);
    expect(ok2.status).toBe(200);
    expect(blocked.status).toBe(429);
  });
});

