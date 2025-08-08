const { Client } = require('pg');

async function main() {
  const client = new Client({ connectionString: process.env.DATABASE_URL, ssl: process.env.PG_SSL === 'require' ? { rejectUnauthorized: false } : undefined });
  await client.connect();
  await client.query('ANALYZE legal_snippets;');
  await client.end();
  console.log('Analyze complete');
}

main().catch(e => { console.error(e); process.exit(1); });

