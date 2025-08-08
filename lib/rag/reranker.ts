import { LegalSnippet } from "../types/legal";

export interface Reranker {
  rerank(query: string, snippets: LegalSnippet[], topK: number): Promise<LegalSnippet[]>;
}

export class NoopReranker implements Reranker {
  async rerank(_query: string, snippets: LegalSnippet[], topK: number): Promise<LegalSnippet[]> {
    return snippets.slice(0, topK);
  }
}

