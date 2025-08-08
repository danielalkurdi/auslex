export const MODELS = {
  reasoner: "gpt-5",
  embedding: "text-embedding-3-large"
} as const;

export const APP_CONFIG = {
  maxSnippets: 8,
  defaultJurisdiction: undefined as string | undefined,
};

