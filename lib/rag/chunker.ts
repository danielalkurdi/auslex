import { LegalMetadata, LegalSnippet } from "../types/legal";

type ChunkerOptions = {
  maxTokens?: number; // approx by words for now
  overlapTokens?: number;
};

const DEFAULT_MAX_TOKENS = 800;
const DEFAULT_OVERLAP = 80;

export function chunkByParagraph(
  docIdPrefix: string,
  text: string,
  meta: LegalMetadata,
  options: ChunkerOptions = {}
): LegalSnippet[] {
  const maxTokens = options.maxTokens ?? DEFAULT_MAX_TOKENS;
  const overlap = options.overlapTokens ?? DEFAULT_OVERLAP;

  const paragraphs = splitIntoParagraphs(text);
  const chunks: LegalSnippet[] = [];
  let current: string[] = [];
  let tokenCount = 0;
  let chunkIndex = 0;

  for (const para of paragraphs) {
    const paraTokens = approximateTokenCount(para);
    if (tokenCount + paraTokens > maxTokens && current.length > 0) {
      // finalize chunk
      chunks.push({ id: `${docIdPrefix}_${chunkIndex++}`, text: current.join('\n\n'), meta });
      // start new with overlap
      const backfill = backfillOverlap(current.join(' '), overlap);
      current = backfill ? [backfill] : [];
      tokenCount = approximateTokenCount(backfill);
    }
    current.push(para);
    tokenCount += paraTokens;
  }

  if (current.length) {
    chunks.push({ id: `${docIdPrefix}_${chunkIndex++}`, text: current.join('\n\n'), meta });
  }

  return chunks;
}

function splitIntoParagraphs(text: string): string[] {
  // Preserve paragraph markers like [45]
  const rawParas = text.split(/\n\s*\n+/g).map(p => p.trim()).filter(Boolean);
  return rawParas;
}

function approximateTokenCount(s: string): number {
  // Rough heuristic ~ 1 token per 0.75 words
  const words = s.split(/\s+/g).filter(Boolean).length;
  return Math.ceil(words / 0.75);
}

function backfillOverlap(s: string, overlapTokens: number): string {
  if (!s) return '';
  const words = s.split(/\s+/g);
  const approxWords = Math.ceil(overlapTokens * 0.75);
  return words.slice(Math.max(0, words.length - approxWords)).join(' ');
}

