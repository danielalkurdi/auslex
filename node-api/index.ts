import express from 'express';
import cors from 'cors';
import { OpenAIResponsesClient } from "../lib/llm/openai";
import { tools } from "../lib/llm/tools";
import { AuslexAnswer } from "../lib/types/answers";
import { VectorBackedRetriever, InMemoryVectorStore } from "../lib/rag/vectorStore";

const app = express();
app.use(cors());
app.use(express.json());

// ephemeral in-memory store and retriever for dev
const store = new InMemoryVectorStore();
const retriever = new VectorBackedRetriever(store);
const llm = new OpenAIResponsesClient();

app.post('/api/ask', async (req, res) => {
  const { question, jurisdiction, asAt } = req.body || {};
  if (!question || typeof question !== 'string') {
    return res.status(400).json({ error: 'question is required' });
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

function safeParseJSON(input: any): any {
  if (typeof input === 'object') return input;
  if (typeof input !== 'string') return undefined;
  try { return JSON.parse(input); } catch { return undefined; }
}

const port = process.env.PORT || 8787;
app.listen(port, () => console.log(`Node API listening on :${port}`));

