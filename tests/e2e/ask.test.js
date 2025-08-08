const request = require('supertest');
const { createServer } = require('../../node-api/server.cjs');

const demoSnippet = {
  id: 'demo_0',
  text: '[45] Character test includes substantial criminal record.',
  meta: {
    jurisdiction: 'Cth',
    sourceType: 'legislation',
    title: 'Migration Act 1958',
    provision: 's 501',
    paragraph: '[45]',
    url: 'https://example.com/migration/s501#45',
    dateInForceFrom: '1958-01-01',
    dateInForceTo: null,
  }
};

function inForceAt(snippet, asAtIso) {
  const asAt = asAtIso ? new Date(asAtIso) : new Date();
  const from = snippet.meta.dateInForceFrom ? new Date(snippet.meta.dateInForceFrom) : undefined;
  const to = snippet.meta.dateInForceTo ? new Date(snippet.meta.dateInForceTo) : undefined;
  if (!from && !to) return true;
  if (from && asAt < from) return false;
  if (to && asAt > to) return false;
  return true;
}

describe('ask API', () => {
  const memoryStore = [];
  const retriever = {
    async search({ query, jurisdiction, asAt, limit = 5 }) {
      const results = memoryStore.filter(s => !jurisdiction || (s.meta.jurisdiction || '').toLowerCase() === jurisdiction.toLowerCase());
      return results.slice(0, limit);
    }
  };
  const app = createServer({ retriever });

  beforeAll(async () => {
    memoryStore.push(demoSnippet);
    process.env.TEST_MODE = '1';
  });

  it('returns JSON schema-compliant answer', async () => {
    const res = await request(app).post('/api/ask').send({ question: 'What is the character test under s 501?', jurisdiction: 'Cth' });
    expect(res.status).toBe(200);
    expect(res.body.answer).toBeTruthy();
    expect(res.body.answer.question).toBeTruthy();
    expect(Array.isArray(res.body.answer.quotes)).toBe(true);
  });

  it('includes AGLC-style citation fields', async () => {
    const res = await request(app).post('/api/ask').send({ question: 'Explain s 501 character test', jurisdiction: 'Cth' });
    const q = res.body.answer.quotes && res.body.answer.quotes[0];
    expect(q).toBeTruthy();
    expect(q.citation.jurisdiction).toBeTruthy();
    expect(q.citation.provision || q.citation.paragraph || q.citation.citation).toBeTruthy();
  });

  it('respects asAt filter (in force)', async () => {
    const res = await request(app).post('/api/ask').send({ question: 'character test', jurisdiction: 'Cth', asAt: '2000-01-01' });
    expect(res.status).toBe(200);
    expect(res.body.snippets.length).toBeGreaterThan(0);
  });
});

