-- Requires pgvector extension on the DB/branch.
-- Create IVFF index for cosine similarity on the embedding column.
CREATE INDEX IF NOT EXISTS legal_snippets_ivff
  ON auslex.legal_snippets USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

ANALYZE auslex.legal_snippets;


