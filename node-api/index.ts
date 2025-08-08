import express from 'express';
import cors from 'cors';
import { OpenAIResponsesClient } from "../lib/llm/openai";
import { tools } from "../lib/llm/tools";
import { AuslexAnswer } from "../lib/types/answers";
import { VectorBackedRetriever } from "../lib/rag/retriever";
import { initSSE, writeSSE, endSSE } from './sse';
import { recordAsk } from '../lib/telemetry';

const app = express();
app.use(cors());
app.use(express.json());

// Construct retriever per-request to avoid long-lived globals in serverless
const llm = new OpenAIResponsesClient();

app.post('/api/ask', async (req, res) => {
  const { question, jurisdiction, asAt } = req.body || {};
  if (!question || typeof question !== 'string') {
    return res.status(400).json({ error: 'question is required' });
  }
  if (question.length > 2000) {
    return res.status(400).json({ error: 'question too long' });
  }

  const streamed = String(req.query.stream || '') === '1';
  const started = Date.now();

  const system = `You are Auslex, an Australian-law specialist.\n\n- Always answer with AGLC-style citations; pinpoint to paragraph/provision.\n- Never invent authorities; only cite from provided snippets.\n- If retrieval is insufficient, ask a clarifying question or say you cannot answer.\n- Prefer jurisdiction-appropriate sources; respect as_at.\n- Output strictly in the provided JSON schema.`;

  if (streamed) {
    initSSE(res);
    writeSSE(res, 'ready', {});
  }

  // First call: allow tool calling to retrieve snippets (stream if requested)
  const toolResult = await llm.respondJSON({
    system,
    user: `Question: ${question}\nJurisdiction: ${jurisdiction || ''}\nAs at: ${asAt || ''}`,
    tools,
    toolChoice: 'auto',
  });

  // Handle any tool calls (we only support search_corpus)
  let snippets: any[] = [];
  const retriever = new VectorBackedRetriever();
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
      if (streamed) {
        writeSSE(res, 'snippets', results.slice(0, 5).map(s => ({
          id: s.id,
          title: s.meta.title || s.meta.citation || '',
          provision: s.meta.provision,
          paragraph: s.meta.paragraph,
          url: s.meta.url,
          jurisdiction: s.meta.jurisdiction,
        })));
      }
    }
  }

  // Second call: require strict JSON output; stream deltas if requested
  let buffer: any = null;
  let final: any = null;
  if (!streamed) {
    final = await llm.respondJSON({
      system,
      user: JSON.stringify({ question, jurisdiction, asAt, snippets }),
      responseFormat: { type: 'json_object' },
    });
  } else {
    // Use streaming for partial prose (structured partials)
    await llm.respondStream({
      system,
      user: JSON.stringify({ question, jurisdiction, asAt, snippets }),
      tools: tools as any,
      onDelta: (delta: string) => {
        // send partial prose only; full JSON will be validated at the end
        writeSSE(res, 'delta', { proseFragment: delta });
      },
    });
    // After stream, request one-shot JSON to validate
    final = await llm.respondJSON({
      system,
      user: JSON.stringify({ question, jurisdiction, asAt, snippets }),
      responseFormat: { type: 'json_object' },
    });
  }

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

  // Enrich limitations/confidence heuristics
  try {
    if (content) {
      if (Array.isArray(snippets) && snippets.length < 2) {
        content.limitations = Array.from(new Set([...(content.limitations || []), 'insufficient_retrieval']));
        content.confidence = Math.min(content.confidence || 0.5, 0.6);
      }
    }
  } catch {}

  const duration = Date.now() - started;
  recordAsk({ durationMs: duration, snippets: snippets.length, jurisdiction, asAt, streamed: !!streamed });

  if (streamed) {
    writeSSE(res, 'done', { answer: content, snippets });
    writeSSE(res, 'metrics', { durationMs: duration, snippetCount: snippets.length });
    return endSSE(res);
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

