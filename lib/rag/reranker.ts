import { LegalSnippet } from "../types/legal";

export interface Reranker {
  rerank(query: string, candidates: LegalSnippet[]): Promise<LegalSnippet[]>;
}

export class IdentityReranker implements Reranker {
  async rerank(_q: string, c: LegalSnippet[]) { return c; }
}

