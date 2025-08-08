export const runtime = 'nodejs';
export const preferredRegion = 'home';

import { getPool } from '../../../lib/db/pg';

export async function GET() {
  const status: any = { ok: true, db: false, vector: process.env.DATABASE_URL ? 'pg' : 'memory', pool: {} };
  try {
    if (process.env.DATABASE_URL) {
      const pool = getPool();
      status.db = true;
      status.pool = { max: (pool as any).options?.max ?? Number(process.env.PG_POOL_MAX || 5) };
    }
  } catch {
    status.db = false;
  }
  return Response.json(status);
}

