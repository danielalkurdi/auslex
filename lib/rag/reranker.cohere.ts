import { LegalSnippet } from "../types/legal";
import { Reranker } from "./reranker";

export class CohereReranker implements Reranker {
  constructor(private apiKey: string, private model = process.env.COHERE_RERANK_MODEL ?? "rerank-english-v3.0") {}
  async rerank(query: string, candidates: LegalSnippet[]) {
    try {
      // Placeholder: integrate with Cohere rerank API when available in env
      // Keep order for now to avoid external dependency in tests
      return candidates;
    } catch {
      return candidates;
    }
  }
}

