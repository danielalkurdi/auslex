const { Client } = require('pg');

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error("DATABASE_URL not set");
    process.exit(1);
  }
  const client = new Client({ connectionString: url, ssl: process.env.PG_SSL === 'require' ? { rejectUnauthorized: false } : undefined });
  await client.connect();

  // Check row count first; some Neon setups complain on empty tables.
  const { rows } = await client.query("SELECT count(*)::int AS n FROM auslex.legal_snippets");
  const n = rows?.[0]?.n ?? 0;

  if (n === 0) {
    console.log("Table auslex.legal_snippets is empty; skipping IVFF creation for now.");
    await client.end();
    process.exit(0);
  }

  console.log(`Rows present (${n}); creating IVFF index...`);
  await client.query(`
    CREATE INDEX IF NOT EXISTS legal_snippets_ivff
      ON auslex.legal_snippets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
  `);
  await client.query(`ANALYZE auslex.legal_snippets;`);
  console.log("IVFF index ensured and ANALYZE completed.");
  await client.end();
}

main().catch(e => { console.error(e); process.exit(1); });


