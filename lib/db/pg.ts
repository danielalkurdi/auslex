import { Pool, PoolClient } from 'pg';

let _pool: Pool | undefined;

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

export async function withClient<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try { return await fn(client); }
  finally { client.release(); }
}

