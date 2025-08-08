export const tools = [{
  type: "function",
  function: {
    name: "search_corpus",
    description: "Retrieve top legal paragraphs by relevance with jurisdiction and as-at filtering.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string" },
        jurisdiction: { type: "string", description: "Cth/NSW/VIC/…; omit if unknown" },
        as_at: { type: "string", description: "YYYY-MM-DD; omit to use today" },
        limit: { type: "number", minimum: 1, maximum: 12 }
      },
      required: ["query"]
    }
  }
}] as const;

export type ToolSchema = typeof tools;

