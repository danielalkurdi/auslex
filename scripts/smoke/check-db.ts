import { Client } from "pg";

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL not set");
  const client = new Client({ connectionString: url, ssl: process.env.PG_SSL === 'require' ? { rejectUnauthorized: false } : undefined });
  await client.connect();

  const { rows } = await client.query(`
    SELECT count(*)::int AS n
    FROM auslex.legal_snippets
  `);
  const n = rows?.[0]?.n ?? 0;
  console.log(JSON.stringify({ rows: n }, null, 2));

  const sample = await client.query(`
    SELECT id, jurisdiction, source_type, title, citation, provision, paragraph
    FROM auslex.legal_snippets
    ORDER BY random()
    LIMIT 2
  `);
  console.log("Sample:", sample.rows);
  await client.end();
}

main().catch(e => { console.error(e); process.exit(1); });


