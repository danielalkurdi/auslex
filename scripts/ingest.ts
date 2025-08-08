import fs from 'fs';
import path from 'path';
import { InMemoryVectorStore } from "../lib/rag/vectorStore";
import { PgVectorStore } from "../lib/rag/vectorStore.pg";
import { chunkByParagraph } from "../lib/rag/chunker";
import { LegalMetadata } from "../lib/types/legal";
import { OpenAIResponsesClient } from "../lib/llm/openai";
import { hashSnippet } from "../lib/rag/contentHash";

async function main() {
  const dbUrl = process.env.DATABASE_URL;
  const usingPg = !!dbUrl;
  if (process.env.VERCEL === '1' && !process.argv.includes('--force')) {
    console.error('Refusing to ingest on Vercel runtime. Run locally or pass --force.');
    process.exit(1);
  }
  const argIdx = process.argv.indexOf('--path');
  const custom = argIdx !== -1 ? process.argv[argIdx + 1] : undefined;
  const rebuild = process.argv.includes('--rebuild');
  let dryRun = process.argv.includes('--dry-run');

  // If no API key but not explicitly dry-run, fall back to dry-run mode
  if (!dryRun && !process.env.OPENAI_API_KEY) {
    console.warn('OPENAI_API_KEY not set; proceeding with --dry-run (no embeddings will be created).');
    dryRun = true;
  }

  let memStore: InMemoryVectorStore | undefined;
  let pgStore: PgVectorStore | undefined;
  if (usingPg) {
    pgStore = new PgVectorStore(dbUrl!);
    // Ensure DB schema exists before any embedding work
    await pgStore.init();
  } else {
    memStore = new InMemoryVectorStore();
  }

  // Only instantiate the OpenAI client when not in dry-run mode
  const embedder = dryRun ? undefined : new OpenAIResponsesClient();

  // Small sample ingestion from a local seed if present
  const sampleDir = path.join(process.cwd(), custom || 'sample-corpus');
  if (!fs.existsSync(sampleDir)) {
    console.log('No sample-corpus directory found; creating with a tiny demo file.');
    fs.mkdirSync(sampleDir);
    fs.writeFileSync(path.join(sampleDir, 'migration_act_demo.txt'), `
[1] Migration Act 1958 (Cth) s 501 character test notes.\n\n[2] The Minister may refuse to grant a visa if not satisfied the person passes the character test.\n\n[3] Character test includes substantial criminal record.\n`);
  }

  const files = fs.readdirSync(sampleDir).filter(f => f.endsWith('.txt'));
  let skipped = 0, embedded = 0, reembedded = 0;
  const t0 = Date.now();
  for (const file of files) {
    const content = fs.readFileSync(path.join(sampleDir, file), 'utf8');
    const meta: LegalMetadata = {
      jurisdiction: 'Cth',
      sourceType: 'legislation',
      title: 'Migration Act 1958',
      citation: undefined,
      provision: 's 501',
      paragraph: undefined,
      url: undefined,
      dateMade: '1958-01-01',
      dateInForceFrom: '1958-01-01',
      dateInForceTo: null,
      version: 'demo'
    };
    const chunks = chunkByParagraph(path.basename(file, '.txt'), content, meta);
    chunks.forEach(c => (c as any).content_hash = hashSnippet(c.text, c.meta));
    const textArr = chunks.map(c => c.text);
    const embeddings = dryRun ? [] : await embedder!.embedTexts(textArr);
    if (!dryRun) {
      if (pgStore) {
        await pgStore.upsert(chunks, embeddings);
        embedded += chunks.length; // simplified; real tracking would diff by hash
      } else if (memStore) {
        await memStore.upsert(chunks, embeddings);
        embedded += chunks.length;
      }
    } else {
      skipped += chunks.length;
    }
  }
  const dt = Date.now() - t0;
  if (pgStore) {
    console.log(`Ingest complete (pgvector). embedded=${embedded} skipped=${skipped} reembedded=${reembedded} in ${dt}ms`);
  } else if (memStore) {
    console.log(`Ingested ${memStore.count()} chunks into in-memory store. embedded=${embedded} skipped=${skipped} in ${dt}ms`);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

