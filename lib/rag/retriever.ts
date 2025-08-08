import { LegalSnippet } from "../types/legal";

export interface Retriever {
  search(params: {
    query: string;
    jurisdiction?: string;
    asAt?: string;
    limit?: number;
  }): Promise<LegalSnippet[]>;
}

export class NoopRetriever implements Retriever {
  async search(): Promise<LegalSnippet[]> {
    return [];
  }
}

