const request = require('supertest');
const express = require('express');

function makeApp() {
  const app = express();
  app.get('/api/health', (req, res) => res.json({ ok: true, db: false, vector: 'memory', pool: { max: 5 } }));
  return app;
}

describe('health endpoint', () => {
  it('returns ok and vector info', async () => {
    const app = makeApp();
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.ok).toBe(true);
    expect(res.body.vector).toBeDefined();
  });
});

