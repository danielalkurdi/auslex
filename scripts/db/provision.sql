CREATE TABLE IF NOT EXISTS auslex.legal_snippets (
  id TEXT PRIMARY KEY,
  embedding VECTOR(3072),
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

-- Skip ANN indexes in provision to avoid Neon-specific index build issues
CREATE INDEX IF NOT EXISTS legal_snippets_juris_idx
  ON auslex.legal_snippets (jurisdiction);
CREATE UNIQUE INDEX IF NOT EXISTS legal_snippets_hash_uq
  ON auslex.legal_snippets (content_hash);
ANALYZE auslex.legal_snippets;

