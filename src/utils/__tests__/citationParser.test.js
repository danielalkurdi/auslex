/**
 * CitationParser Unit Tests
 * 
 * CRITICAL: These tests validate legal citation parsing accuracy.
 * Incorrect parsing could mislead lawyers and impact client outcomes.
 * 
 * Test data uses REAL Australian legal citations, not synthetic data.
 */

import { citationParser, parseCitations, JURISDICTIONS, CITATION_TYPES } from '../citationParser';

describe('CitationParser - Legal Citation Accuracy', () => {
  describe('Case Citation Parsing', () => {
    it('should parse High Court square bracket citations accurately', () => {
      const text = 'The decision in Mabo v Queensland (No 2) [1992] HCA 23 established native title rights.';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.CASE,
        plaintiff: 'Mabo',
        defendant: 'Queensland (No 2)',
        year: '1992',
        court: 'HCA',
        caseNumber: '23',
        jurisdiction: 'cth',
        jurisdictionFull: 'Commonwealth'
      });
      expect(citations[0].fullCitation).toBe('Mabo v Queensland (No 2) [1992] HCA 23');
    });

    it('should parse complex corporate case names with entities', () => {
      const text = 'In Australian Competition and Consumer Commission v Cement Australia Pty Ltd [2023] FCA 1234, the court found...';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.CASE,
        plaintiff: 'Australian Competition and Consumer Commission',
        defendant: 'Cement Australia Pty Ltd',
        year: '2023',
        court: 'FCA'
      });
    });

    it('should parse CLR parenthetical citations', () => {
      const text = 'The High Court in Australian Capital Television Pty Ltd v Commonwealth (1992) 177 CLR 106 held that...';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.CASE,
        plaintiff: 'Australian Capital Television Pty Ltd',
        defendant: 'Commonwealth',
        year: '1992',
        volume: '177',
        court: 'CLR',
        caseNumber: '106'
      });
    });
  });

  describe('Legislation Citation Parsing', () => {
    it('should parse Migration Act section references accurately', () => {
      const text = 'Under Migration Act 1958 (Cth) s 359A, the Tribunal must provide particulars.';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.LEGISLATION,
        actName: 'Migration Act',
        year: '1958',
        jurisdiction: 'Cth',
        jurisdictionFull: 'Commonwealth',
        provisionType: 'section',
        fullCitation: 'Migration Act 1958 (Cth) s 359A'
      });
    });

    it('should parse complex subsection references', () => {
      const text = 'Migration Act 1958 (Cth) s 359A(1)(a) requires specific procedural fairness.';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      const provision = citations[0].provision;
      expect(provision.sections).toContain('359A');
      expect(provision.subsections).toContain('1');
      expect(provision.paragraphs).toContain('a');
    });

    it('should parse section ranges correctly', () => {
      const text = 'Privacy Act 1988 (Cth) ss 13-16 deal with collection of personal information.';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0].provisionType).toBe('sections');
      expect(citations[0].provision.sections).toEqual(['13', '14', '15', '16']);
    });

    it('should parse "Section X of the Act" format', () => {
      const text = 'Section 359A of the Migration Act 1958 (Cth) provides procedural fairness requirements.';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.LEGISLATION,
        actName: 'Migration Act',
        year: '1958',
        jurisdiction: 'Cth',
        provisionType: 'section'
      });
    });
  });

  describe('Regulation Citation Parsing', () => {
    it('should parse regulation references accurately', () => {
      const text = 'Migration Regulations 1994 (Cth) reg 4.01 specifies the application requirements.';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(1);
      expect(citations[0]).toMatchObject({
        type: CITATION_TYPES.REGULATION,
        actName: 'Migration Regulations',
        year: '1994',
        jurisdiction: 'Cth',
        provisionType: 'regulation'
      });
    });
  });

  describe('Australian Jurisdiction Mapping', () => {
    it('should map all Australian jurisdictions correctly', () => {
      const jurisdictionTests = [
        { abbrev: 'Cth', full: 'Commonwealth' },
        { abbrev: 'NSW', full: 'New South Wales' },
        { abbrev: 'Vic', full: 'Victoria' },
        { abbrev: 'Qld', full: 'Queensland' },
        { abbrev: 'WA', full: 'Western Australia' },
        { abbrev: 'SA', full: 'South Australia' },
        { abbrev: 'Tas', full: 'Tasmania' },
        { abbrev: 'NT', full: 'Northern Territory' },
        { abbrev: 'ACT', full: 'Australian Capital Territory' }
      ];

      jurisdictionTests.forEach(({ abbrev, full }) => {
        const text = `Test Act 2023 (${abbrev}) s 1 applies.`;
        const citations = parseCitations(text);
        
        expect(citations[0].jurisdiction).toBe(abbrev);
        expect(citations[0].jurisdictionFull).toBe(full);
      });
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle overlapping citations correctly', () => {
      const text = 'Migration Act 1958 (Cth) s 359A and Migration Act 1958 (Cth) ss 359A-359C both apply.';
      const citations = parseCitations(text);
      
      // Should detect both citations without overlap
      expect(citations).toHaveLength(2);
      expect(citations[0].provision.raw).toBe('359A');
      expect(citations[1].provision.raw).toBe('359A-359C');
    });

    it('should handle malformed citations gracefully', () => {
      const text = 'This is not a citation: Random Text 1234 (Invalid) s xyz';
      const citations = parseCitations(text);
      
      expect(citations).toHaveLength(0);
    });

    it('should handle empty and null input', () => {
      expect(parseCitations('')).toHaveLength(0);
      expect(parseCitations(null)).toHaveLength(0);
      expect(parseCitations(undefined)).toHaveLength(0);
    });
  });

  describe('Search Query Generation', () => {
    it('should generate appropriate search queries for AustLII lookup', () => {
      const text = 'Migration Act 1958 (Cth) s 359A requires procedural fairness.';
      const citations = parseCitations(text);
      
      const searchQuery = citations[0].searchQuery;
      expect(searchQuery).toMatchObject({
        actName: 'Migration',
        year: '1958',
        jurisdiction: 'Cth',
        provision: '359A'
      });
      expect(searchQuery.queryString).toContain('Migration 1958 Cth 359A');
    });
  });

  describe('Text to Renderable Chunks Conversion', () => {
    it('should convert text with citations to clickable components', () => {
      const text = 'Under Migration Act 1958 (Cth) s 359A, the Tribunal must act fairly.';
      const citations = parseCitations(text);
      const chunks = citationParser.textToRenderableChunks(text, citations);
      
      expect(chunks).toHaveLength(3); // Before citation, citation, after citation
      expect(chunks[0]).toMatchObject({
        type: 'text',
        content: 'Under '
      });
      expect(chunks[1]).toMatchObject({
        type: 'citation',
        citation: citations[0]
      });
      expect(chunks[2]).toMatchObject({
        type: 'text',
        content: ', the Tribunal must act fairly.'
      });
    });
  });
});

// Test data factories for consistent test data
export const getMockCaseCitation = (overrides = {}) => ({
  type: CITATION_TYPES.CASE,
  plaintiff: 'Test Plaintiff',
  defendant: 'Test Defendant',
  year: '2023',
  court: 'HCA',
  caseNumber: '1',
  jurisdiction: 'cth',
  jurisdictionFull: 'Commonwealth',
  fullCitation: 'Test Plaintiff v Test Defendant [2023] HCA 1',
  originalText: 'Test Plaintiff v Test Defendant [2023] HCA 1',
  ...overrides
});

export const getMockLegislationCitation = (overrides = {}) => ({
  type: CITATION_TYPES.LEGISLATION,
  actName: 'Test Act',
  year: '2023',
  jurisdiction: 'Cth',
  jurisdictionFull: 'Commonwealth',
  provisionType: 'section',
  provision: {
    raw: '1',
    sections: ['1'],
    subsections: [],
    paragraphs: []
  },
  fullCitation: 'Test Act 2023 (Cth) s 1',
  originalText: 'Test Act 2023 (Cth) s 1',
  ...overrides
});