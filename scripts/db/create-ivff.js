const { Client } = require('pg');

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error("DATABASE_URL not set");
    process.exit(1);
  }
  const client = new Client({ connectionString: url, ssl: process.env.PG_SSL === 'require' ? { rejectUnauthorized: false } : undefined });
  await client.connect();

  // Detect embedding dimension and row count
  const dimRes = await client.query("SELECT vector_dims(embedding) AS dim FROM auslex.legal_snippets LIMIT 1");
  const dim = dimRes.rows?.[0]?.dim ?? null;
  const { rows } = await client.query("SELECT count(*)::int AS n FROM auslex.legal_snippets");
  const n = rows?.[0]?.n ?? 0;

  if (n === 0) {
    console.log("Table auslex.legal_snippets is empty; skipping ANN index.");
    await client.end();
    process.exit(0);
  }
  if (!dim) {
    console.log('Could not determine embedding dimension; skipping ANN index.');
    await client.end();
    process.exit(0);
  }

  if (dim && dim > 2000) {
    console.log(`Rows present (${n}); creating ANN index (HNSW, cosine)...`);
    try {
      await client.query(`
        CREATE INDEX IF NOT EXISTS legal_snippets_hnsw
          ON auslex.legal_snippets USING hnsw (embedding vector_cosine_ops)
          WITH (m = 16, ef_construction = 64);
      `);
      await client.query(`ANALYZE auslex.legal_snippets;`);
      console.log('HNSW index ensured; ANALYZE completed.');
    } catch (e) {
      console.log('HNSW not available on this branch/extension version; skipping ANN index.');
    }
  } else {
    console.log(`Rows present (${n}); creating ANN index (IVFF, cosine)...`);
    await client.query(`
      CREATE INDEX IF NOT EXISTS legal_snippets_ivff
        ON auslex.legal_snippets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    `);
    await client.query(`ANALYZE auslex.legal_snippets;`);
    console.log("IVFF index ensured; ANALYZE completed.");
  }
  await client.end();
}

main().catch(e => { console.error(e); process.exit(1); });


