import React, { useState } from 'react';

export default function AdminHealth() {
  // Simple guard: require AUSLEX_ADMIN_KEY in query or localStorage
  if (typeof window !== 'undefined') {
    const required = new URLSearchParams(window.location.search).get('AUSLEX_ADMIN_KEY') || localStorage.getItem('AUSLEX_ADMIN_KEY');
    if (!required) {
      return <div className="p-4">Not found</div>;
    }
  }
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');

  const run = async () => {
    setError('');
    try {
      const res = await fetch('/api/health');
      const json = await res.json();
      setHealth(json);
    } catch (e) { setError(String(e)); }
  };

  const pool = health?.pool || {};

  return (
    <div className="p-4 max-w-3xl mx-auto">
      <h1 className="text-xl font-semibold mb-3">Admin Health</h1>
      <div className="flex gap-3 mb-3">
        <div className="p-3 border rounded">API: {health ? 'up' : 'unknown'}</div>
        <div className="p-3 border rounded">DB: {health?.db ? 'connected' : 'none'}</div>
        <div className="p-3 border rounded">Vector: {health?.vector || 'unknown'}</div>
        <div className="p-3 border rounded">Pool max: {pool.max || '-'}</div>
      </div>
      <button onClick={run} className="px-3 py-1 rounded bg-accent text-white">Run health checks</button>
      {error && <div className="mt-3 text-status-warning">{error}</div>}
      {health && (
        <pre className="mt-3 bg-background-secondary p-2 rounded text-xs overflow-auto">{JSON.stringify(health, null, 2)}</pre>
      )}
      <div className="mt-4">
        <a className="text-accent underline" href="/eval">Go to Eval</a>
      </div>
    </div>
  );
}

