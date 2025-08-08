import React, { useMemo, useState } from 'react';
import seed from '../../eval/seed.json';

function csvFrom(results) {
  const header = ['id','pass','latencyMs','snippetCount','reasons'];
  const rows = results.map(r => [r.id, r.pass, r.latencyMs, r.snippetCount, (r.reasons||[]).join('|')]);
  return [header, ...rows].map(r => r.join(',')).join('\n');
}

export default function EvalPage() {
  const [filter, setFilter] = useState('all');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState([]);

  const filtered = useMemo(() => results.filter(r => filter==='all' ? true : (filter==='pass' ? r.pass : !r.pass)), [results, filter]);
  const acc = useMemo(() => results.length ? Math.round(100 * results.filter(r=>r.pass).length / results.length) : 0, [results]);
  const latencies = results.map(r => r.latencyMs).sort((a,b)=>a-b);
  const med = latencies.length ? (latencies.length%2? latencies[(latencies.length-1)/2] : Math.round((latencies[latencies.length/2-1]+latencies[latencies.length/2])/2)) : 0;
  const mean = latencies.length ? Math.round(latencies.reduce((a,b)=>a+b,0)/latencies.length) : 0;

  const runAll = async () => {
    setRunning(true); setResults([]);
    const base = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8787';
    const out = [];
    for (const c of seed) {
      const t0 = performance.now();
      const url = new URL(base + '/api/ask'); url.searchParams.set('stream','0');
      const resp = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ question: c.question, jurisdiction: c.jurisdiction, asAt: c.asAt }) });
      const json = await resp.json();
      const dt = Math.round(performance.now()-t0);
      const answerText = json?.answer?.answer || '';
      const citations = json?.answer?.citations || [];
      let pass = true; const reasons = [];
      if (c.expect?.mustContainOneOf?.length) {
        const ok = c.expect.mustContainOneOf.some(tok => answerText.includes(tok));
        if (!ok) { pass=false; reasons.push('missing_expected_phrase'); }
      }
      if (c.expect?.mustCiteOneOf?.length) {
        const fields = citations.map(ci => [ci.provision, ci.paragraph, ci.citation, ci.title].filter(Boolean).join(' ')).join(' | ');
        const ok = c.expect.mustCiteOneOf.some(tok => fields.includes(tok));
        if (!ok) { pass=false; reasons.push('missing_expected_citation'); }
      }
      const snippetCount = Array.isArray(json?.snippets) ? json.snippets.length : (Array.isArray(json?.answer?.quotes) ? json.answer.quotes.length : 0);
      out.push({ id: c.id, pass, latencyMs: dt, snippetCount, reasons, jurisdiction: c.jurisdiction, asAt: c.asAt, notes: c.notes });
      setResults([...out]);
    }
    setRunning(false);
  };

  const exportCsv = () => {
    const blob = new Blob([csvFrom(results)], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'eval-results.csv';
    a.click();
  };

  return (
    <div className="p-4 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <button disabled={running} onClick={runAll} className="px-3 py-1 rounded bg-accent text-white disabled:opacity-50">Run All</button>
        <select value={filter} onChange={e=>setFilter(e.target.value)} className="border rounded px-2 py-1">
          <option value="all">All</option>
          <option value="pass">Pass</option>
          <option value="fail">Fail</option>
        </select>
        <button onClick={exportCsv} className="px-3 py-1 rounded bg-background-secondary border">Export CSV</button>
      </div>
      <div className="mb-3 text-sm">Accuracy: {acc}% • Median: {med}ms • Mean: {mean}ms • Total: {results.length}</div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b"><th>ID</th><th>Jurisdiction</th><th>As at</th><th>Pass</th><th>Latency</th><th>Snippets</th><th>Notes</th></tr>
        </thead>
        <tbody>
          {filtered.map(r => (
            <tr key={r.id} className="border-b hover:bg-border-subtle/20">
              <td>{r.id}</td>
              <td>{r.jurisdiction}</td>
              <td>{r.asAt}</td>
              <td>{r.pass ? 'pass' : 'fail'}</td>
              <td>{r.latencyMs}</td>
              <td>{r.snippetCount}</td>
              <td className="text-text-secondary">{r.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

