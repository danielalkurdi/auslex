import express from 'express';
import cors from 'cors';
import { OpenAIResponsesClient } from "../lib/llm/openai";
import { tools } from "../lib/llm/tools";
import { AuslexAnswer } from "../lib/types/answers";
import { VectorBackedRetriever } from "../lib/rag/vectorStore";
import { Retriever } from "../lib/rag/retriever";

export function createServer(deps?: { retriever?: Retriever; llm?: OpenAIResponsesClient }) {
  const app = express();
  app.use(cors());
  app.use(express.json());

  const retriever = deps?.retriever!;
  const llm = deps?.llm || new OpenAIResponsesClient();

  app.post('/api/ask', async (req, res) => {
    const { question, jurisdiction, asAt } = req.body || {};
    if (!question || typeof question !== 'string') {
      return res.status(400).json({ error: 'question is required' });
    }

    // TEST_MODE path avoids external LLM for CI
    if (process.env.TEST_MODE === '1' || !process.env.OPENAI_API_KEY) {
      const snippets = await retriever.search({ query: question, jurisdiction, asAt, limit: 5 });
      const first = snippets[0];
      const answer = {
        question,
        answer: first ? `As at ${asAt || 'today'}, relevant authority includes: ${first.meta.title || first.meta.citation || ''}.` : "I cannot answer with confidence.",
        quotes: first ? [{ text: first.text.slice(0, 200), citation: {
          jurisdiction: first.meta.jurisdiction || 'Cth',
          sourceType: first.meta.sourceType || 'legislation',
          title: first.meta.title,
          citation: first.meta.citation,
          provision: first.meta.provision,
          paragraph: first.meta.paragraph,
          url: first.meta.url,
        }}] : [],
        citations: snippets.slice(0, 3).map(s => ({
          jurisdiction: s.meta.jurisdiction || 'Cth',
          sourceType: s.meta.sourceType || 'legislation',
          title: s.meta.title,
          citation: s.meta.citation,
          provision: s.meta.provision,
          paragraph: s.meta.paragraph,
          url: s.meta.url,
        })),
        reasoning_notes: first ? 'Used top snippet and supporting citations.' : 'Insufficient retrieval.',
        limitations: first ? [] : ['insufficient_retrieval'],
        confidence: first ? 0.6 : 0.2
      };
      const valid = AuslexAnswer.safeParse(answer);
      if (!valid.success) {
        return res.status(500).json({ error: 'schema_invalid', issues: valid.error.issues });
      }
      return res.json({ answer, snippets });
    }

    const system = `You are Auslex, an Australian-law specialist.\n\n- Always answer with AGLC-style citations; pinpoint to paragraph/provision.\n- Never invent authorities; only cite from provided snippets.\n- If retrieval is insufficient, ask a clarifying question or say you cannot answer.\n- Prefer jurisdiction-appropriate sources; respect as_at.\n- Output strictly in the provided JSON schema.`;

    // First call: allow tool calling to retrieve snippets
    const toolResult = await llm.respondJSON({
      system,
      user: `Question: ${question}\nJurisdiction: ${jurisdiction || ''}\nAs at: ${asAt || ''}`,
      tools,
      toolChoice: 'auto',
    });

    // Handle any tool calls (we only support search_corpus)
    let snippets: any[] = [];
    for (const call of toolResult.toolCalls || []) {
      if (call?.name === 'search_corpus') {
        const args = safeParseJSON(call.arguments) || {};
        const results = await retriever.search({
          query: args.query || question,
          jurisdiction: args.jurisdiction || jurisdiction,
          asAt: args.as_at || asAt,
          limit: Math.min(12, Math.max(1, Number(args.limit) || 8)),
        });
        snippets = results;
      }
    }

    // Second call: require strict JSON output
    const final = await llm.respondJSON({
      system,
      user: JSON.stringify({ question, jurisdiction, asAt, snippets }),
      responseFormat: { type: 'json_object' },
    });

    // Validate against schema; if invalid, nudge once
    let content = final.content;
    const parsed = AuslexAnswer.safeParse(content);
    if (!parsed.success) {
      const correction = await llm.respondJSON({
        system,
        user: `Return ONLY a JSON object that satisfies this Zod schema: ${AuslexAnswer.toString()}\nPrevious invalid output:\n${JSON.stringify(content)}`,
        responseFormat: { type: 'json_object' },
      });
      content = correction.content;
    }

    return res.json({ answer: content, snippets });
  });

  return app;
}

function safeParseJSON(input: any): any {
  if (typeof input === 'object') return input;
  if (typeof input !== 'string') return undefined;
  try { return JSON.parse(input); } catch { return undefined; }
}

