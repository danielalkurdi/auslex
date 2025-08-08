export const runtime = 'nodejs';
export const preferredRegion = 'home';

import { NextRequest } from 'next/server';
import { OpenAIResponsesClient } from '../../../lib/llm/openai';
import { tools } from '../../../lib/llm/tools';
import { VectorBackedRetriever } from '../../../lib/rag/retriever';
import { AuslexAnswer } from '../../../lib/types/answers';

export async function POST(req: NextRequest) {
  const url = new URL(req.url);
  const stream = url.searchParams.get('stream') === '1';
  const body = await req.json();
  const { question, jurisdiction, asAt } = body || {};
  if (!question || typeof question !== 'string' || question.length > 2000) {
    return new Response(JSON.stringify({ error: 'invalid question' }), { status: 400 });
  }
  const llm = new OpenAIResponsesClient();
  const retriever = new VectorBackedRetriever();
  const system = `You are Auslex, an Australian-law specialist.\n\n- Always answer with AGLC-style citations; pinpoint to paragraph/provision.\n- Never invent authorities; only cite from provided snippets.\n- If retrieval is insufficient, ask a clarifying question or say you cannot answer.\n- Prefer jurisdiction-appropriate sources; respect as_at.\n- Output strictly in the provided JSON schema.`;

  if (!stream) {
    const toolResult = await llm.respondJSON({ system, user: `Question: ${question}\nJurisdiction: ${jurisdiction || ''}\nAs at: ${asAt || ''}`, tools, toolChoice: 'auto' });
    let snippets: any[] = [];
    for (const call of toolResult.toolCalls || []) {
      if (call?.name === 'search_corpus') {
        const args = typeof call.arguments === 'string' ? JSON.parse(call.arguments) : call.arguments || {};
        const results = await retriever.search({ query: args.query || question, jurisdiction: args.jurisdiction || jurisdiction, asAt: args.as_at || asAt, limit: Math.min(12, Math.max(1, Number(args.limit) || 8)) });
        snippets = results;
      }
    }
    const final = await llm.respondJSON({ system, user: JSON.stringify({ question, jurisdiction, asAt, snippets }), responseFormat: { type: 'json_object' } });
    let content: any = final.content;
    const parsed = AuslexAnswer.safeParse(content);
    if (!parsed.success) {
      const correction = await llm.respondJSON({ system, user: `Return ONLY a JSON object that satisfies this Zod schema: ${AuslexAnswer.toString()}\nPrevious invalid output:\n${JSON.stringify(content)}`, responseFormat: { type: 'json_object' } });
      content = correction.content;
    }
    return Response.json({ answer: content, snippets });
  }

  const streamResp = new ReadableStream({
    async start(controller) {
      const enc = new TextEncoder();
      const write = (event: string, data: any) => {
        controller.enqueue(enc.encode(`event: ${event}\n`));
        controller.enqueue(enc.encode(`data: ${typeof data === 'string' ? data : JSON.stringify(data)}\n\n`));
      };
      write('ready', {});
      try {
        const toolResult = await llm.respondJSON({ system, user: `Question: ${question}\nJurisdiction: ${jurisdiction || ''}\nAs at: ${asAt || ''}`, tools, toolChoice: 'auto' });
        let snippets: any[] = [];
        for (const call of toolResult.toolCalls || []) {
          if (call?.name === 'search_corpus') {
            const args = typeof call.arguments === 'string' ? JSON.parse(call.arguments) : call.arguments || {};
            const results = await retriever.search({ query: args.query || question, jurisdiction: args.jurisdiction || jurisdiction, asAt: args.as_at || asAt, limit: Math.min(12, Math.max(1, Number(args.limit) || 8)) });
            snippets = results;
          }
        }
        write('snippets', snippets.slice(0,5).map(s => ({ id: s.id, title: s.meta.title || s.meta.citation || '', provision: s.meta.provision, paragraph: s.meta.paragraph, url: s.meta.url, jurisdiction: s.meta.jurisdiction })));
        await llm.respondStream({ system, user: JSON.stringify({ question, jurisdiction, asAt, snippets }), tools: tools as any, onDelta: (d) => write('delta', { proseFragment: d }) });
        const final = await llm.respondJSON({ system, user: JSON.stringify({ question, jurisdiction, asAt, snippets }), responseFormat: { type: 'json_object' } });
        write('done', { answer: final.content, snippets });
      } catch (e: any) {
        write('error', { error: e?.message || 'stream_error' });
      } finally {
        controller.close();
      }
    }
  });
  return new Response(streamResp, { headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache, no-transform', 'Connection': 'keep-alive' } });
}

