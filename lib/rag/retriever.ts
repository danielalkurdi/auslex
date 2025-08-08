import { LegalSnippet } from "../types/legal";
import { InMemoryVectorStore, cosineSimilarity } from "./vectorStore";
import { PgVectorStore } from "./vectorStore.pg";
import { OpenAIResponsesClient } from "../llm/openai";

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

export class VectorBackedRetriever implements Retriever {
  private memStore?: InMemoryVectorStore;
  private pgStore?: PgVectorStore;
  private embedder: OpenAIResponsesClient;

  constructor() {
    this.embedder = new OpenAIResponsesClient();
    const dbUrl = process.env.DATABASE_URL;
    if (dbUrl) {
      this.pgStore = new PgVectorStore(dbUrl);
      // init lazily
      this.pgStore.init().catch(err => console.error('pgvector init failed', err));
    } else {
      this.memStore = new InMemoryVectorStore();
    }
  }

  async search(params: { query: string; jurisdiction?: string; asAt?: string; limit?: number }): Promise<LegalSnippet[]> {
    const limit = params.limit ?? 8;
    const [qEmbedding] = await this.embedder.embedTexts([params.query]);
    if (this.pgStore) {
      return this.pgStore.similaritySearch({ queryEmbedding: qEmbedding, jurisdiction: params.jurisdiction, asAt: params.asAt, limit });
    }
    // in-memory fallback
    return this.memStore!.similaritySearch({ queryEmbedding: qEmbedding, jurisdiction: params.jurisdiction, asAt: params.asAt, limit });
  }
}

