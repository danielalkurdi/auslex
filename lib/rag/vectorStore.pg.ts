import { VectorStore } from './vectorStore';
import { LegalSnippet } from '../types/legal';
import { withClient } from '../db/pg';
// Minimal QueryResult to avoid depending on @types/pg at runtime
type QueryResult<T> = { rows: T[] };

const EMBEDDING_DIM = 3072;

type PgSnippetRow = {
  id: string;
  text: string;
  jurisdiction: string | null;
  source_type: string | null;
  court_or_publisher: string | null;
  title: string | null;
  citation: string | null;
  provision: string | null;
  paragraph: string | null;
  url: string | null;
  date_made: string | null;
  date_in_force_from: string | null;
  date_in_force_to: string | null;
  version: string | null;
  score?: number | null;
};

type SourceType = 'legislation' | 'regulation' | 'case' | 'guideline' | 'other';

function coerceSourceType(value: string | null): SourceType {
  switch ((value || '').toLowerCase()) {
    case 'legislation':
    case 'regulation':
    case 'case':
    case 'guideline':
    case 'other':
      return value!.toLowerCase() as SourceType;
    default:
      return 'other';
  }
}

export class PgVectorStore implements VectorStore {
  constructor(databaseUrl?: string) {}

  async init(): Promise<void> {
    await withClient(async c => {
      // Do not create extensions here; assumed ensured earlier
      try {
        await c.query(`
        CREATE TABLE IF NOT EXISTS auslex.legal_snippets (
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
          version TEXT,
          content_hash TEXT,
          embedding_version TEXT
        );
        `);
      } catch (err: any) {
        if (err?.code === '42501') {
          console.warn('No CREATE privilege for schema; skipping table creation.');
        } else {
          throw err;
        }
      }
      try { 
        await c.query(`CREATE UNIQUE INDEX IF NOT EXISTS legal_snippets_hash_uq ON auslex.legal_snippets(content_hash);`); 
      } catch (err: any) {
        console.warn('Failed to create content_hash index:', err?.message);
      }
      // Skip ANN index creation to remain compatible with environments where ivfflat/HNSW may be unavailable
      try { 
        await c.query(`CREATE INDEX IF NOT EXISTS legal_snippets_juris_idx ON auslex.legal_snippets (jurisdiction);`); 
      } catch (err: any) {
        console.warn('Failed to create jurisdiction index:', err?.message);
      }
      try { 
        await c.query(`ANALYZE auslex.legal_snippets;`); 
      } catch (err: any) {
        console.warn('Failed to analyze table:', err?.message);
      }
    });
  }

  async upsert(snippets: LegalSnippet[], embeddings?: number[][]): Promise<void> {
    if (!embeddings || embeddings.length !== snippets.length) {
      throw new Error('PgVectorStore.upsert requires precomputed embeddings array matching snippets length');
    }
    const cols = ['id','embedding','text','jurisdiction','source_type','court_or_publisher','title','citation','provision','paragraph','url','date_made','date_in_force_from','date_in_force_to','version','content_hash','embedding_version'];
    const group = (idx: number) => `(${cols.map((_, j) => `$${idx*cols.length + j + 1}`).join(', ')})`;
    const text = `
      INSERT INTO auslex.legal_snippets (${cols.join(',')})
      VALUES ${snippets.map((_, i) => group(i)).join(', ')}
      ON CONFLICT (content_hash) DO UPDATE SET
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
        version = EXCLUDED.version,
        embedding_version = EXCLUDED.embedding_version
    `;
    const values: any[] = [];
    snippets.forEach((s, idx) => {
      const emb = embeddings[idx];
      values.push(
        s.id,
        // pgvector expects a string like "[v1,v2,...]" when binding as text
        Array.isArray(emb) ? `[${emb.join(',')}]` : emb,
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
        (s as any).content_hash || null,
        process.env.EMBEDDING_MODEL || 'text-embedding-3-large'
      );
    });
    await withClient(c => c.query(text, values));
  }

  async similaritySearch(params: { queryEmbedding: number[]; jurisdiction?: string; asAt?: string; limit: number }): Promise<LegalSnippet[]> {
    const { queryEmbedding, jurisdiction, asAt, limit } = params;
    const filters: string[] = [];
    // Ensure pgvector receives a properly formatted vector literal
    const embParam = Array.isArray(queryEmbedding)
      ? `[${queryEmbedding.join(',')}]`
      : (queryEmbedding as unknown as string);
    const vals: any[] = [embParam];
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
    // Use pure vector similarity by default to avoid requiring pg_trgm extension
    const sql = `
      SELECT id, text, jurisdiction, source_type, court_or_publisher, title, citation, provision, paragraph, url,
             date_made, date_in_force_from, date_in_force_to, version,
             (1 - (embedding <=> $1::vector)) as sim,
             (1 - (embedding <=> $1::vector)) as score
      FROM auslex.legal_snippets
      ${where}
      ORDER BY score DESC
      LIMIT ${Math.max(1, Math.min(50, limit))}
    `;
    const res = await withClient(c => c.query(sql, vals)) as QueryResult<PgSnippetRow>;
    return res.rows.map((r: PgSnippetRow) => ({
      id: r.id,
      text: r.text,
      meta: {
        jurisdiction: r.jurisdiction ?? "",
        sourceType: coerceSourceType(r.source_type),
        courtOrPublisher: r.court_or_publisher ?? undefined,
        title: r.title ?? undefined,
        citation: r.citation ?? undefined,
        provision: r.provision ?? undefined,
        paragraph: r.paragraph ?? undefined,
        url: r.url ?? undefined,
        dateMade: r.date_made ?? undefined,
        dateInForceFrom: r.date_in_force_from ?? undefined,
        dateInForceTo: r.date_in_force_to ?? null,
        version: r.version ?? undefined,
      }
    }));
  }

  count(): number {
    // For dev logs only; query when needed
    return -1;
  }
}

export function embeddingDimensions(): number { return EMBEDDING_DIM; }

