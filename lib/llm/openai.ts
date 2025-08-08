import OpenAI from "openai";
import { MODELS } from "../config";

type Tool = {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
  };
};

export type LLMResponseStreamHandler = (data: string) => void;

export class OpenAIResponsesClient {
  private client: OpenAI;
  private maxRetries = 3;
  private minDelayMs = 250;

  constructor(apiKey?: string) {
    this.client = new OpenAI({ apiKey: apiKey || process.env.OPENAI_API_KEY });
  }

  async embedTexts(texts: string[]): Promise<number[][]> {
    const out: number[][] = [];
    const chunkSize = 128;
    for (let i = 0; i < texts.length; i += chunkSize) {
      const batch = texts.slice(i, i + chunkSize);
      const res = await this.client.embeddings.create({
        model: MODELS.embedding,
        input: batch,
      } as any);
      out.push(...res.data.map((d: any) => d.embedding as number[]));
    }
    return out;
  }

  async respondJSON(params: {
    system: string;
    user: string;
    tools?: Tool[];
    toolChoice?: "auto" | { type: "function"; function: { name: string } };
    responseFormat?: { type: "json_object" };
  }): Promise<{ content: any; toolCalls?: any[] }>{
    return this.withRetries(async () => {
      const res = await this.client.responses.create({
        model: MODELS.reasoner,
        input: [
          { role: "system", content: params.system },
          { role: "user", content: params.user },
        ],
        tools: params.tools as any,
        tool_choice: params.toolChoice as any,
        response_format: params.responseFormat as any,
      } as any);

      const output = res.output?.[0];
      const toolCalls = (output?.content as any[])?.filter((c: any) => c.type === 'tool_call');
      const firstText = (output?.content as any[])?.find((c: any) => c.type === 'output_text');
      let content: any = undefined;
      if (firstText?.text) {
        try { content = JSON.parse(firstText.text); } catch { content = firstText.text; }
      }
      return { content, toolCalls };
    });
  }

  async respondStream(params: {
    system: string;
    user: string;
    tools?: Tool[];
    onDelta: LLMResponseStreamHandler;
  }): Promise<void> {
    await this.withRetries(async () => {
      const stream = await this.client.responses.stream({
        model: MODELS.reasoner,
        input: [
          { role: "system", content: params.system },
          { role: "user", content: params.user },
        ],
        tools: params.tools as any,
      } as any);

      stream.on('text.delta', params.onDelta);
      await stream.finalContent();
    });
  }

  private async withRetries<T>(fn: () => Promise<T>, attempt = 0): Promise<T> {
    try {
      return await fn();
    } catch (err: any) {
      if (attempt >= this.maxRetries) throw err;
      const delay = this.minDelayMs * Math.pow(2, attempt);
      await new Promise(r => setTimeout(r, delay));
      return this.withRetries(fn, attempt + 1);
    }
  }
}

