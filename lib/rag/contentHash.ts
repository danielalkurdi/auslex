import crypto from 'crypto';

export function hashSnippet(text: string, meta: Record<string, any>) {
  const normText = text.replace(/\s+/g, ' ').trim();
  const minimalMeta = {
    jurisdiction: meta?.jurisdiction ?? '',
    source_type: meta?.source_type ?? meta?.sourceType ?? '',
    citation: meta?.citation ?? '',
    provision: meta?.provision ?? '',
    paragraph: meta?.paragraph ?? '',
    version: meta?.version ?? '',
  };
  const payload = normText + '|' + JSON.stringify(minimalMeta);
  return crypto.createHash('sha256').update(payload).digest('hex');
}

