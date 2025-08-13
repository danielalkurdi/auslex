export type LegalMetadata = {
  jurisdiction: 'Cth' | 'NSW' | 'VIC' | 'QLD' | 'WA' | 'SA' | 'TAS' | 'NT' | 'ACT' | 'FCA' | 'FCCA' | 'FCAAFC' | 'HCA' | string;
  sourceType: 'legislation' | 'regulation' | 'case' | 'guideline' | 'other';
  courtOrPublisher?: string;
  title?: string;
  citation?: string;
  provision?: string;
  paragraph?: string;
  url?: string;
  dateMade?: string;
  dateInForceFrom?: string;
  dateInForceTo?: string | null;
  version?: string;
};

export type LegalSnippet = {
  id: string;
  text: string;
  meta: LegalMetadata;
};

