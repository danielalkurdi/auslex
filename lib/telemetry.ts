type AskTelemetry = {
  durationMs: number;
  tokenIn?: number;
  tokenOut?: number;
  snippets: number;
  jurisdiction?: string;
  asAt?: string;
  streamed: boolean;
};

export function recordAsk(t: AskTelemetry) {
  // Dev-only logging; sanitize content and secrets
  const payload = {
    durationMs: t.durationMs,
    tokenIn: t.tokenIn,
    tokenOut: t.tokenOut,
    snippets: t.snippets,
    jurisdiction: t.jurisdiction,
    asAt: t.asAt,
    streamed: t.streamed,
  };
  // eslint-disable-next-line no-console
  console.log('[telemetry.ask]', JSON.stringify(payload));
}

