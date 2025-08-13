import { z } from 'zod';

export const CitationAGLC = z.object({
  jurisdiction: z.string(),
  sourceType: z.string(),
  title: z.string().optional(),
  citation: z.string().optional(),
  provision: z.string().optional(),
  paragraph: z.string().optional(),
  url: z.string().url().optional()
});

export const QuoteBlock = z.object({
  text: z.string(),
  citation: CitationAGLC
});

export const AuslexAnswer = z.object({
  question: z.string(),
  answer: z.string(),
  quotes: z.array(QuoteBlock),
  citations: z.array(CitationAGLC),
  reasoning_notes: z.string().optional(),
  limitations: z.array(z.string()).optional(),
  confidence: z.number().min(0).max(1)
});

export type TAuslexAnswer = z.infer<typeof AuslexAnswer>;

