export function rateLimit(req: any, res: any, next: any) {
  const windowMs = Number(process.env.RL_WINDOW_MS || 60000);
  const max = Number(process.env.RL_MAX || 60);
  const key = (req.header('x-auslex-key') || req.ip || 'anon') as string;
  const now = Date.now();
  const start = now - windowMs;
  const buckets: Map<string, number[]> = (global as any).__AUSLEX_BUCKETS__ || new Map();
  (global as any).__AUSLEX_BUCKETS__ = buckets;
  const arr = (buckets.get(key) || []).filter(ts => ts > start);
  if (arr.length >= max) return res.status(429).json({ error: 'Rate limit exceeded' });
  arr.push(now); buckets.set(key, arr);
  next();
}

