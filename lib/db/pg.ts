// Avoid depending on @types/pg at runtime by using minimal local types
type PoolClientLike = { release: () => void } & any;
type PoolLike = { connect: () => Promise<PoolClientLike> } & any;
// Use CommonJS require to prevent TS from resolving module types
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { Pool } = require('pg');

let _pool: PoolLike | undefined;

export function getPool() {
  if (!_pool) {
    if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL not set');
    _pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: Number(process.env.PG_POOL_MAX ?? 5),
      idleTimeoutMillis: Number(process.env.PG_IDLE_TIMEOUT_MS ?? 30000),
      allowExitOnIdle: false,
      ssl: process.env.PG_SSL === 'require' ? { rejectUnauthorized: false } : undefined,
    });
  }
  return _pool;
}

export async function withClient<T>(fn: (c: PoolClientLike) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try { return await fn(client); }
  finally { client.release(); }
}

