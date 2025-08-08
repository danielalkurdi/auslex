import crypto from 'crypto';
import { MODELS } from "../config";
import { LegalMetadata, LegalSnippet } from "../types/legal";

export interface VectorStore {
  upsert(snippets: LegalSnippet[]): Promise<void>;
  similaritySearch(queryEmbedding: number[], limit: number): Promise<LegalSnippet[]>;
  count(): number;
}

export interface EmbeddingProvider {
  embed(texts: string[]): Promise<number[][]>;
}

export class InMemoryVectorStore implements VectorStore {
  private items: { id: string; vector: number[]; snippet: LegalSnippet }[] = [];

  async upsert(snippets: LegalSnippet[]): Promise<void> {
    for (const snip of snippets) {
      const vector = await fakeLocalEmbedding(snip.text);
      const existingIndex = this.items.findIndex(i => i.id === snip.id);
      if (existingIndex >= 0) this.items.splice(existingIndex, 1);
      this.items.push({ id: snip.id, vector, snippet: snip });
    }
  }

  async similaritySearch(queryEmbedding: number[], limit: number): Promise<LegalSnippet[]> {
    const scored = this.items.map(it => ({
      score: cosineSimilarity(queryEmbedding, it.vector),
      snippet: it.snippet,
    }));
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map(s => s.snippet);
  }

  count(): number {
    return this.items.length;
  }
}

// Placeholder for local embeddings to keep dev offline deterministic
async function fakeLocalEmbedding(text: string): Promise<number[]> {
  const hash = crypto.createHash('sha256').update(text).digest();
  // Convert 32 bytes into 64-dim pseudo-vector by repeating bytes
  const arr: number[] = Array.from(hash).flatMap(b => [b / 255, (255 - b) / 255]);
  return arr.slice(0, 64);
}

export function cosineSimilarity(a: number[], b: number[]): number {
  const len = Math.min(a.length, b.length);
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < len; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-8);
}

export class VectorBackedRetriever {
  constructor(private store: VectorStore) {}

  async search(params: { query: string; jurisdiction?: string; asAt?: string; limit?: number }): Promise<LegalSnippet[]> {
    const limit = params.limit ?? 8;
    const qVec = await fakeLocalEmbedding(params.query);
    let results = await this.store.similaritySearch(qVec, limit * 2);
    // Jurisdiction filter (soft)
    if (params.jurisdiction) {
      results = results.filter(r => r.meta.jurisdiction?.toLowerCase().includes(params.jurisdiction!.toLowerCase()));
    }
    // Time-travel filter
    if (params.asAt) {
      const asAtDate = new Date(params.asAt);
      results = results
        .map(s => ({ s, penalty: missingForcePenalty(s) }))
        .filter(({ s }) => inForceAt(s, asAtDate))
        .sort((a, b) => a.penalty - b.penalty)
        .map(({ s }) => s);
    }
    return results.slice(0, limit);
  }
}

function inForceAt(snippet: LegalSnippet, asAt: Date): boolean {
  const from = snippet.meta.dateInForceFrom ? new Date(snippet.meta.dateInForceFrom) : undefined;
  const to = snippet.meta.dateInForceTo ? new Date(snippet.meta.dateInForceTo) : undefined;
  if (!from && !to) return true;
  if (from && asAt < from) return false;
  if (to && asAt > to) return false;
  return true;
}

function missingForcePenalty(snippet: LegalSnippet): number {
  return snippet.meta.dateInForceFrom || snippet.meta.dateInForceTo ? 0 : 0.05;
}

