const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

async function main() {
  const sql = fs.readFileSync(path.resolve('scripts/db/provision.sql'), 'utf8');
  const client = new Client({ connectionString: process.env.DATABASE_URL, ssl: process.env.PG_SSL === 'require' ? { rejectUnauthorized: false } : undefined });
  await client.connect();
  await client.query(sql);
  await client.end();
  console.log('Provision complete');
}

main().catch(e => { console.error(e); process.exit(1); });

