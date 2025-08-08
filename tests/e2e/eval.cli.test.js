const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

describe('eval CLI', () => {
  const isWin = process.platform === 'win32';
  (isWin ? it.skip : it)('produces results and CSV', () => {
    const node = process.execPath;
    const cmd = `${node} -e "require('ts-node/register/transpile-only'); require('./eval/run.ts')"`;
    const res = spawnSync(process.platform === 'win32' ? 'cmd' : 'sh', [process.platform === 'win32' ? '/c' : '-c', cmd], { encoding: 'utf-8' });
    expect(res.status).toBe(0);
    const outJson = path.resolve('eval/results.json');
    const outCsv = path.resolve('eval/results.csv');
    expect(fs.existsSync(outJson)).toBe(true);
    expect(fs.existsSync(outCsv)).toBe(true);
    const csv = fs.readFileSync(outCsv, 'utf8');
    expect(csv.split('\n').length).toBeGreaterThan(1);
  });
});

