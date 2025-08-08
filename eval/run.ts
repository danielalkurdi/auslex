import fs from 'fs';
import path from 'path';
import fetch from 'node-fetch';

type SeedCase = {
  id: string;
  question: string;
  jurisdiction?: string;
  asAt?: string;
  expect?: { mustContainOneOf?: string[]; mustCiteOneOf?: string[] };
  notes?: string;
};

type Result = {
  id: string;
  pass: boolean;
  latencyMs: number;
  snippetCount: number;
  reasons: string[];
};

function median(values: number[]): number {
  if (!values.length) return 0;
  const s = [...values].sort((a,b)=>a-b);
  const mid = Math.floor(s.length/2);
  return s.length % 2 ? s[mid] : (s[mid-1]+s[mid])/2;
}

async function runOne(baseUrl: string, c: SeedCase): Promise<Result> {
  const started = Date.now();
  const url = new URL('/api/ask', baseUrl);
  url.searchParams.set('stream','0');
  const resp = await fetch(url.toString(), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: c.question, jurisdiction: c.jurisdiction, asAt: c.asAt })
  });
  const json = await resp.json();
  const dt = Date.now() - started;
  const answerText = json?.answer?.answer || '';
  const citations = json?.answer?.citations || [];
  const reasons: string[] = [];
  let pass = true;
  if (c.expect?.mustContainOneOf?.length) {
    const ok = c.expect.mustContainOneOf.some(tok => answerText.includes(tok));
    if (!ok) { pass = false; reasons.push('missing_expected_phrase'); }
  }
  if (c.expect?.mustCiteOneOf?.length) {
    const fields = citations.map((ci: any) => [ci.provision, ci.paragraph, ci.citation, ci.title].filter(Boolean).join(' ')).join(' | ');
    const ok = c.expect.mustCiteOneOf.some(tok => fields.includes(tok));
    if (!ok) { pass = false; reasons.push('missing_expected_citation'); }
  }
  const snippetCount = Array.isArray(json?.snippets) ? json.snippets.length : (Array.isArray(json?.answer?.quotes) ? json.answer.quotes.length : 0);
  return { id: c.id, pass, latencyMs: dt, snippetCount, reasons };
}

async function main() {
  const args = process.argv;
  const fileIdx = args.indexOf('--file');
  const filePath = fileIdx !== -1 ? args[fileIdx+1] : 'eval/seed.json';
  const concurrencyIdx = args.indexOf('--concurrency');
  const concurrency = concurrencyIdx !== -1 ? Number(args[concurrencyIdx+1]) : 3;
  const baseUrl = process.env.EVAL_API_BASE || 'http://localhost:8787';
  const data = JSON.parse(fs.readFileSync(path.resolve(filePath), 'utf8')) as SeedCase[];

  const results: Result[] = [];
  let i = 0;
  async function worker() {
    while (i < data.length) {
      const idx = i++;
      const r = await runOne(baseUrl, data[idx]);
      results.push(r);
      // eslint-disable-next-line no-console
      console.log(`[eval] ${r.id} pass=${r.pass} latencyMs=${r.latencyMs} snippets=${r.snippetCount} reasons=${r.reasons.join(',')}`);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, data.length) }, () => worker()));

  const passed = results.filter(r => r.pass).length;
  const acc = (100 * passed / results.length).toFixed(1);
  const latencies = results.map(r => r.latencyMs);
  const med = median(latencies);
  const mean = Math.round(latencies.reduce((a,b)=>a+b,0) / (latencies.length || 1));

  // eslint-disable-next-line no-console
  console.log(`Summary: total=${results.length} passed=${passed} accuracy=${acc}% median=${med}ms mean=${mean}ms`);

  const outDir = path.resolve('eval');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);
  fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify({ results, summary: { total: results.length, passed, accuracy: acc, medianMs: med, meanMs: mean } }, null, 2));
  // CSV
  const header = ['id','pass','latencyMs','snippetCount','reasons'];
  const csv = [header.join(',')].concat(results.map(r => [r.id, r.pass, r.latencyMs, r.snippetCount, r.reasons.join('|')].join(','))).join('\n');
  fs.writeFileSync(path.join(outDir, 'results.csv'), csv);
}

main().catch(err => { console.error(err); process.exit(1); });

