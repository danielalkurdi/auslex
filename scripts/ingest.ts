import fs from 'fs';
import path from 'path';
import { InMemoryVectorStore } from "../lib/rag/vectorStore";
import { chunkByParagraph } from "../lib/rag/chunker";
import { LegalMetadata } from "../lib/types/legal";

async function main() {
  const store = new InMemoryVectorStore();

  // Small sample ingestion from a local seed if present
  const sampleDir = path.join(process.cwd(), 'sample-corpus');
  if (!fs.existsSync(sampleDir)) {
    console.log('No sample-corpus directory found; creating with a tiny demo file.');
    fs.mkdirSync(sampleDir);
    fs.writeFileSync(path.join(sampleDir, 'migration_act_demo.txt'), `
[1] Migration Act 1958 (Cth) s 501 character test notes.\n\n[2] The Minister may refuse to grant a visa if not satisfied the person passes the character test.\n\n[3] Character test includes substantial criminal record.\n`);
  }

  const files = fs.readdirSync(sampleDir).filter(f => f.endsWith('.txt'));
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
    await store.upsert(chunks);
  }

  console.log(`Ingested ${store.count()} chunks into in-memory store.`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

