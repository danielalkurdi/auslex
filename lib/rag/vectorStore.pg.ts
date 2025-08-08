import { Client } from 'pg';
import { VectorStore } from './vectorStore';
import { LegalSnippet } from '../types/legal';

const EMBEDDING_DIM = 3072;

export class PgVectorStore implements VectorStore {
  private client: Client;

  constructor(databaseUrl: string) {
    this.client = new Client({ connectionString: databaseUrl });
  }

  async init(): Promise<void> {
    await this.client.connect();
    await this.client.query(`CREATE EXTENSION IF NOT EXISTS vector;`);
    await this.client.query(`CREATE EXTENSION IF NOT EXISTS pg_trgm;`).catch(() => {
      console.warn('pg_trgm not available; hybrid scoring will be disabled.');
    });
    await this.client.query(`
      CREATE TABLE IF NOT EXISTS legal_snippets (
        id TEXT PRIMARY KEY,
        embedding VECTOR(${EMBEDDING_DIM}),
        text TEXT NOT NULL,
        jurisdiction TEXT,
        source_type TEXT,
        court_or_publisher TEXT,
        title TEXT,
        citation TEXT,
        provision TEXT,
        paragraph TEXT,
        url TEXT,
        date_made DATE,
        date_in_force_from DATE,
        date_in_force_to DATE,
        version TEXT
      );
    `);
    await this.client.query(`CREATE INDEX IF NOT EXISTS legal_snippets_ivff ON legal_snippets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`).catch(() => {});
    await this.client.query(`CREATE INDEX IF NOT EXISTS legal_snippets_juris_idx ON legal_snippets (jurisdiction);`).catch(() => {});
  }

  async upsert(snippets: LegalSnippet[], embeddings?: number[][]): Promise<void> {
    if (!embeddings || embeddings.length !== snippets.length) {
      throw new Error('PgVectorStore.upsert requires precomputed embeddings array matching snippets length');
    }
    const text = `
      INSERT INTO legal_snippets (
        id, embedding, text, jurisdiction, source_type, court_or_publisher, title, citation, provision, paragraph, url, date_made, date_in_force_from, date_in_force_to, version
      ) VALUES ${snippets.map((_, i) => `($${i*15+1}, $${i*15+2}, $${i*15+3}, $${i*15+4}, $${i*15+5}, $${i*15+6}, $${i*15+7}, $${i*15+8}, $${i*15+9}, $${i*15+10}, $${i*15+11}, $${i*15+12}, $${i*15+13}, $${i*15+14}, $${i*15+15})`).join(', ')}
      ON CONFLICT (id) DO UPDATE SET
        embedding = EXCLUDED.embedding,
        text = EXCLUDED.text,
        jurisdiction = EXCLUDED.jurisdiction,
        source_type = EXCLUDED.source_type,
        court_or_publisher = EXCLUDED.court_or_publisher,
        title = EXCLUDED.title,
        citation = EXCLUDED.citation,
        provision = EXCLUDED.provision,
        paragraph = EXCLUDED.paragraph,
        url = EXCLUDED.url,
        date_made = EXCLUDED.date_made,
        date_in_force_from = EXCLUDED.date_in_force_from,
        date_in_force_to = EXCLUDED.date_in_force_to,
        version = EXCLUDED.version
    `;
    const values: any[] = [];
    snippets.forEach((s, idx) => {
      const emb = embeddings[idx];
      values.push(
        s.id,
        emb,
        s.text,
        s.meta.jurisdiction || null,
        s.meta.sourceType || null,
        s.meta.courtOrPublisher || null,
        s.meta.title || null,
        s.meta.citation || null,
        s.meta.provision || null,
        s.meta.paragraph || null,
        s.meta.url || null,
        s.meta.dateMade || null,
        s.meta.dateInForceFrom || null,
        s.meta.dateInForceTo || null,
        s.meta.version || null,
      );
    });
    await this.client.query(text, values);
  }

  async similaritySearch(params: { queryEmbedding: number[]; jurisdiction?: string; asAt?: string; limit: number }): Promise<LegalSnippet[]> {
    const { queryEmbedding, jurisdiction, asAt, limit } = params;
    const filters: string[] = [];
    const vals: any[] = [queryEmbedding];
    if (jurisdiction) {
      vals.push(jurisdiction);
      filters.push(`jurisdiction = $${vals.length}`);
    }
    if (asAt) {
      vals.push(asAt);
      const idx = vals.length;
      // only enforce range when both boundaries exist; otherwise include
      filters.push(`(date_in_force_from IS NULL AND date_in_force_to IS NULL OR ($${idx} BETWEEN date_in_force_from AND COALESCE(date_in_force_to, '9999-12-31'))) `);
    }
    const where = filters.length ? `WHERE ${filters.join(' AND ')}` : '';
    // hybrid scoring placeholder using pg_trgm; ignore if not installed
    const sql = `
      SELECT id, text, jurisdiction, source_type, court_or_publisher, title, citation, provision, paragraph, url,
             date_made, date_in_force_from, date_in_force_to, version,
             (1 - (embedding <=> $1)) as sim,
             COALESCE(similarity(text, ' '), 0) as textscore,
             (0.7 * (1 - (embedding <=> $1)) + 0.3 * COALESCE(similarity(text, ' '), 0)) as score
      FROM legal_snippets
      ${where}
      ORDER BY score DESC
      LIMIT ${Math.max(1, Math.min(50, limit))}
    `;
    const res = await this.client.query(sql, vals);
    return res.rows.map(r => ({
      id: r.id,
      text: r.text,
      meta: {
        jurisdiction: r.jurisdiction,
        sourceType: r.source_type,
        courtOrPublisher: r.court_or_publisher,
        title: r.title,
        citation: r.citation,
        provision: r.provision,
        paragraph: r.paragraph,
        url: r.url,
        dateMade: r.date_made ? String(r.date_made) : undefined,
        dateInForceFrom: r.date_in_force_from ? String(r.date_in_force_from) : undefined,
        dateInForceTo: r.date_in_force_to ? String(r.date_in_force_to) : null,
        version: r.version,
      }
    }));
  }

  count(): number {
    // For dev logs only; query when needed
    return -1;
  }
}

export function embeddingDimensions(): number { return EMBEDDING_DIM; }

