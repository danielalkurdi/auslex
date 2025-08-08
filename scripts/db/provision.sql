CREATE EXTENSION IF NOT EXISTS vector;
CREATE INDEX IF NOT EXISTS legal_snippets_ivff ON legal_snippets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS legal_snippets_juris_idx ON legal_snippets (jurisdiction);
ANALYZE legal_snippets;

