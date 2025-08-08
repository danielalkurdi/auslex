/**
 * Australian Legal Citation Parser
 * 
 * This utility parses Australian legal citations and converts them into structured data.
 * Supports various Australian legal citation formats including:
 * - Acts: "Migration Act 1958 (Cth) s 55"
 * - Regulations: "Migration Regulations 1994 r 4.01"
 * - Case citations: "R v Smith [2020] HCA 15"
 * - Complex provisions: "s 55(1)(a)", "ss 55-60"
 */

// Australian jurisdictions mapping
export const JURISDICTIONS = {
  'Cth': 'Commonwealth',
  'NSW': 'New South Wales', 
  'Vic': 'Victoria',
  'Qld': 'Queensland',
  'WA': 'Western Australia',
  'SA': 'South Australia',
  'Tas': 'Tasmania',
  'NT': 'Northern Territory',
  'ACT': 'Australian Capital Territory'
};

// Citation types
export const CITATION_TYPES = {
  LEGISLATION: 'legislation',
  REGULATION: 'regulation', 
  CASE: 'case',
  UNKNOWN: 'unknown'
};

/**
 * Main citation parser class
 */
export class CitationParser {
  constructor() {
    // Fixed regex patterns for Australian legal citations
    
    // Case citation patterns
    // Pattern 1: Square bracket citations like "[2025] HCA 29"
    this.casePatternSquare = /\b((?:[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?|[A-Z][A-Za-z0-9]+)(?:\s+(?:and|&|of|for)?\s+[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?)*?(?:\s+Commission)?)\s+v\s+((?:[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?|[A-Z][A-Za-z0-9]+)(?:\s+(?:and|&|of|for)?\s+[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?)*?)\s*\[(\d{4})\]\s*([A-Z]+[A-Z0-9]*)\s*(\d+)\b/g;
    
    // Pattern 2: Parenthetical citations like "(2001) 207 CLR 562"
    this.casePatternParen = /\b((?:[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?|[A-Z][A-Za-z0-9]+)(?:\s+(?:and|&|of|for)?\s+[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?)*?(?:\s+Commission)?)\s+v\s+((?:[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?|[A-Z][A-Za-z0-9]+)(?:\s+(?:and|&|of|for)?\s+[A-Z][A-Za-z0-9'.-]+(?:\s+(?:Pty\s+)?Ltd|Inc|Corp|LLC|Co)?)*?)\s*\((\d{4})\)\s*(\d+)\s+([A-Z]+)\s+(\d+)\b/g;
    
    // Legislation pattern 1: "Section X of the Act Name Year (Jurisdiction)"
    // Matches: "Section 359A of the Migration Act 1958 (Cth)"
    this.sectionFirstPattern = /\bSection\s+(\d+[A-Z]?(?:\(\d+\))?(?:\([a-z]+\))?)\s+of\s+the\s+([A-Z][A-Za-z\s]+(?:Act|Code|Law))\s+(\d{4})\s*\(([^)]+)\)/gi;
    
    // Legislation pattern 2: "Act Name Year (Jurisdiction) s X"
    // Matches: "Migration Act 1958 (Cth) s 359A", "Privacy Act 1988 (Cth) ss 6-8"
    // More restrictive to avoid capturing too much text
    this.sectionLastPattern = /\b([A-Z][A-Za-z\s]+(?:Act|Code|Law))\s+(\d{4})\s*\(([^)]+)\)\s+(ss?)\s+([\d\-A-Za-z()]+)\b/gi;
    
    // Additional pattern for regulations
    this.regulationPattern = /([^(]+?(?:Regulations?|Rules?))\s+(\d{4})\s*\(([^)]+)\)\s+(reg?|r|rule)\s+([\d\-A-Za-z().]+)/gi;
    
    // Pattern for Act citations without section references (e.g., "Privacy Act 1988 (Cth)")
    // Start with "the" or capital letter to avoid capturing preceding text
    this.actOnlyPattern = /\b(?:the\s+)?([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*\s+(?:Act|Code|Law))\s+(\d{4})\s*\(([^)]+)\)(?!\s*s)/gi;
  }

  /**
   * Parse all citations from text content
   * @param {string} text - The text to parse
   * @param {Object} context - Optional context (current act, jurisdiction)
   * @returns {Array} Array of parsed citation objects
   */
  parseText(text, context = {}) {
    const citations = [];
    
    // Find case citations - square bracket format
    const caseMatchesSquare = [...text.matchAll(this.casePatternSquare)];
    for (const match of caseMatchesSquare) {
      const citation = this.parseCaseCitationSquare(match);
      if (citation) {
        citation.originalText = match[0];
        citation.startIndex = match.index;
        citation.endIndex = match.index + match[0].length;
        citations.push(citation);
      }
    }
    
    // Find case citations - parenthetical format
    const caseMatchesParen = [...text.matchAll(this.casePatternParen)];
    for (const match of caseMatchesParen) {
      const citation = this.parseCaseCitationParen(match);
      if (citation) {
        citation.originalText = match[0];
        citation.startIndex = match.index;
        citation.endIndex = match.index + match[0].length;
        citations.push(citation);
      }
    }
    
    // Find "Section X of the Act" pattern
    const sectionFirstMatches = [...text.matchAll(this.sectionFirstPattern)];
    for (const match of sectionFirstMatches) {
      const citation = this.parseSectionFirstCitation(match);
      if (citation) {
        citation.originalText = match[0];
        citation.startIndex = match.index;
        citation.endIndex = match.index + match[0].length;
        citations.push(citation);
      }
    }
    
    // Find "Act Name s X" pattern
    const sectionLastMatches = [...text.matchAll(this.sectionLastPattern)];
    for (const match of sectionLastMatches) {
      const citation = this.parseSectionLastCitation(match);
      if (citation) {
        citation.originalText = match[0];
        citation.startIndex = match.index;
        citation.endIndex = match.index + match[0].length;
        citations.push(citation);
      }
    }
    
    // Find regulation citations
    const regulationMatches = [...text.matchAll(this.regulationPattern)];
    for (const match of regulationMatches) {
      const citation = this.parseRegulationCitation(match);
      if (citation) {
        citation.originalText = match[0];
        citation.startIndex = match.index;
        citation.endIndex = match.index + match[0].length;
        citations.push(citation);
      }
    }
    
    // Find Act citations without sections (e.g., "Privacy Act 1988 (Cth)")
    const actOnlyMatches = [...text.matchAll(this.actOnlyPattern)];
    for (const match of actOnlyMatches) {
      const citation = this.parseActOnlyCitation(match);
      if (citation) {
        citation.originalText = match[0];
        citation.startIndex = match.index;
        citation.endIndex = match.index + match[0].length;
        citations.push(citation);
      }
    }
    
    // Remove overlapping citations (keep longer ones)
    const filteredCitations = this.removeOverlappingCitations(citations);
    
    // Sort citations by position in text (reverse order for replacement)
    filteredCitations.sort((a, b) => b.startIndex - a.startIndex);
    
    return filteredCitations;
  }

  /**
   * Parse "Section X of the Act Name Year (Jurisdiction)" citation
   * @param {Array} match - Regex match array
   * @returns {Object} Parsed citation object
   */
  parseSectionFirstCitation(match) {
    try {
      return {
        id: this.generateId(),
        type: CITATION_TYPES.LEGISLATION,
        actName: match[2].trim(),
        year: match[3],
        jurisdiction: match[4],
        jurisdictionFull: JURISDICTIONS[match[4]] || match[4],
        provisionType: 'section',
        provision: this.parseProvision(match[1]),
        fullCitation: `${match[2].trim()} ${match[3]} (${match[4]}) s ${match[1]}`,
        searchQuery: this.buildSearchQuery({
          actName: match[2].trim(),
          year: match[3],
          jurisdiction: match[4],
          provision: match[1]
        })
      };
    } catch (error) {
      console.warn('Failed to parse section-first citation:', match[0], error);
      return null;
    }
  }

  /**
   * Parse "Act Name Year (Jurisdiction) s X" citation
   * @param {Array} match - Regex match array
   * @returns {Object} Parsed citation object
   */
  parseSectionLastCitation(match) {
    try {
      return {
        id: this.generateId(),
        type: CITATION_TYPES.LEGISLATION,
        actName: match[1].trim(),
        year: match[2],
        jurisdiction: match[3],
        jurisdictionFull: JURISDICTIONS[match[3]] || match[3],
        provisionType: this.normalizeProvisionType(match[4]),
        provision: this.parseProvision(match[5]),
        fullCitation: `${match[1].trim()} ${match[2]} (${match[3]}) ${match[4]} ${match[5]}`,
        searchQuery: this.buildSearchQuery({
          actName: match[1].trim(),
          year: match[2],
          jurisdiction: match[3],
          provision: match[5]
        })
      };
    } catch (error) {
      console.warn('Failed to parse section-last citation:', match[0], error);
      return null;
    }
  }

  /**
   * Parse regulation citation
   * @param {Array} match - Regex match array  
   * @returns {Object} Parsed citation object
   */
  parseRegulationCitation(match) {
    try {
      return {
        id: this.generateId(),
        type: CITATION_TYPES.REGULATION,
        actName: match[1].trim(),
        year: match[2] || null,
        jurisdiction: match[3] || 'Cth',
        jurisdictionFull: JURISDICTIONS[match[3] || 'Cth'] || match[3] || 'Commonwealth',
        provisionType: this.normalizeProvisionType(match[4]),
        provision: this.parseProvision(match[5]),
        fullCitation: `${match[1].trim()}${match[2] ? ' ' + match[2] : ''}${match[3] ? ' (' + match[3] + ')' : ''} ${match[4]} ${match[5]}`,
        searchQuery: this.buildSearchQuery({
          actName: match[1].trim(),
          year: match[2],
          jurisdiction: match[3] || 'Cth',
          provision: match[5]
        })
      };
    } catch (error) {
      console.warn('Failed to parse regulation citation:', match[0], error);
      return null;
    }
  }

  /**
   * Parse Act-only citation (no section reference)
   * @param {Array} match - Regex match array
   * @returns {Object} Parsed citation object
   */
  parseActOnlyCitation(match) {
    try {
      return {
        id: this.generateId(),
        type: CITATION_TYPES.LEGISLATION,
        actName: match[1].trim(),
        year: match[2],
        jurisdiction: match[3],
        jurisdictionFull: JURISDICTIONS[match[3]] || match[3],
        provisionType: null,
        provision: null,
        fullCitation: `${match[1].trim()} ${match[2]} (${match[3]})`,
        searchQuery: this.buildSearchQuery({
          actName: match[1].trim(),
          year: match[2],
          jurisdiction: match[3],
          provision: ''
        })
      };
    } catch (error) {
      console.warn('Failed to parse act-only citation:', match[0], error);
      return null;
    }
  }

  /**
   * Parse case citation with square brackets [Year] Court Number
   * @param {Array} match - Regex match array
   * @returns {Object} Parsed citation object  
   */
  parseCaseCitationSquare(match) {
    try {
      return {
        id: this.generateId(),
        type: CITATION_TYPES.CASE,
        plaintiff: match[1].trim(),
        defendant: match[2].trim(),
        year: match[3],
        court: match[4],
        caseNumber: match[5],
        jurisdiction: 'cth', // All Australian federal courts map to cth
        jurisdictionFull: 'Commonwealth',
        fullCitation: `${match[1].trim()} v ${match[2].trim()} [${match[3]}] ${match[4]} ${match[5]}`,
        searchQuery: this.buildCaseSearchQuery({
          plaintiff: match[1].trim(),
          defendant: match[2].trim(),
          year: match[3],
          court: match[4],
          caseNumber: match[5]
        })
      };
    } catch (error) {
      console.warn('Failed to parse case citation:', match[0], error);
      return null;
    }
  }

  /**
   * Parse case citation with parentheses (Year) Volume Court Page
   * @param {Array} match - Regex match array
   * @returns {Object} Parsed citation object  
   */
  parseCaseCitationParen(match) {
    try {
      return {
        id: this.generateId(),
        type: CITATION_TYPES.CASE,
        plaintiff: match[1].trim(),
        defendant: match[2].trim(),
        year: match[3],
        volume: match[4], // Volume number
        court: match[5],
        caseNumber: match[6], // Page number
        jurisdiction: 'cth',
        jurisdictionFull: 'Commonwealth',
        fullCitation: `${match[1].trim()} v ${match[2].trim()} (${match[3]}) ${match[4]} ${match[5]} ${match[6]}`,
        searchQuery: this.buildCaseSearchQuery({
          plaintiff: match[1].trim(),
          defendant: match[2].trim(),
          year: match[3],
          court: match[5],
          caseNumber: match[6]
        })
      };
    } catch (error) {
      console.warn('Failed to parse parenthetical case citation:', match[0], error);
      return null;
    }
  }

  /**
   * Remove overlapping citations, keeping the longer ones
   * @param {Array} citations - Array of citation objects
   * @returns {Array} Filtered citations
   */
  removeOverlappingCitations(citations) {
    const filtered = [];
    
    for (const citation of citations) {
      let isOverlapping = false;
      
      for (let i = 0; i < filtered.length; i++) {
        const existing = filtered[i];
        
        // Check if citations overlap
        const citationStart = citation.startIndex;
        const citationEnd = citation.endIndex;
        const existingStart = existing.startIndex;
        const existingEnd = existing.endIndex;
        
        const hasOverlap = (citationStart < existingEnd && citationEnd > existingStart);
        
        if (hasOverlap) {
          // Keep the longer citation
          const citationLength = citationEnd - citationStart;
          const existingLength = existingEnd - existingStart;
          
          if (citationLength > existingLength) {
            filtered[i] = citation; // Replace with longer citation
          }
          isOverlapping = true;
          break;
        }
      }
      
      if (!isOverlapping) {
        filtered.push(citation);
      }
    }
    
    return filtered;
  }

  /**
   * Parse provision reference (handles complex provisions like "55(1)(a)" or "55-60")
   * @param {string} provisionText - The provision text to parse
   * @returns {Object} Parsed provision object
   */
  parseProvision(provisionText) {
    const provision = {
      raw: provisionText,
      sections: [],
      subsections: [],
      paragraphs: []
    };

    // Handle range provisions (e.g., "55-60")
    const rangeMatch = provisionText.match(/^(\d+)-(\d+)$/);
    if (rangeMatch) {
      const start = parseInt(rangeMatch[1]);
      const end = parseInt(rangeMatch[2]);
      for (let i = start; i <= end; i++) {
        provision.sections.push(i.toString());
      }
      return provision;
    }

    // Handle complex provisions (e.g., "55(1)(a)")
    const complexMatch = provisionText.match(/^(\d+)(?:\(([^)]+)\))?(?:\(([^)]+)\))?/);
    if (complexMatch) {
      provision.sections.push(complexMatch[1]);
      if (complexMatch[2]) {
        provision.subsections.push(complexMatch[2]);
      }
      if (complexMatch[3]) {
        provision.paragraphs.push(complexMatch[3]);
      }
      return provision;
    }

    // Simple provision
    provision.sections.push(provisionText);
    return provision;
  }

  /**
   * Normalize provision types to standard format
   * @param {string} type - Raw provision type
   * @returns {string} Normalized type
   */
  normalizeProvisionType(type) {
    const typeMap = {
      's': 'section',
      'ss': 'sections', 
      'section': 'section',
      'sections': 'sections',
      'para': 'paragraph',
      'paragraph': 'paragraph',
      'reg': 'regulation',
      'regulation': 'regulation',
      'r': 'regulation',
      'rule': 'rule'
    };
    return typeMap[type.toLowerCase()] || type;
  }

  /**
   * Build search query for legislation/regulation lookup
   * @param {Object} params - Citation parameters
   * @returns {string} Search query string
   */
  buildSearchQuery({ actName, year, jurisdiction, provision }) {
    // Clean act name for search
    const cleanActName = actName
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/\b(Act|Regulations?|Rules?)\b/gi, '');

    return {
      actName: cleanActName,
      year,
      jurisdiction,
      provision: provision,
      queryString: `${cleanActName} ${year} ${jurisdiction} ${provision}`
    };
  }

  /**
   * Build search query for case lookup
   * @param {Object} params - Case citation parameters  
   * @returns {string} Search query string
   */
  buildCaseSearchQuery({ plaintiff, defendant, year, court, caseNumber }) {
    return {
      plaintiff,
      defendant,
      year,
      court,
      caseNumber,
      queryString: `${plaintiff} v ${defendant} [${year}] ${court} ${caseNumber}`
    };
  }

  /**
   * Generate unique ID for citation
   * @returns {string} Unique identifier
   */
  generateId() {
    return `citation_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Convert text with citations to React-renderable format
   * @param {string} text - Original text
   * @param {Array} citations - Parsed citations
   * @returns {Array} Array of text chunks and citation objects
   */
  textToRenderableChunks(text, citations) {
    if (citations.length === 0) {
      return [{ type: 'text', content: text }];
    }

    const chunks = [];
    let lastIndex = 0;

    // Sort citations by start index
    const sortedCitations = [...citations].sort((a, b) => a.startIndex - b.startIndex);

    for (const citation of sortedCitations) {
      // Add text before citation
      if (citation.startIndex > lastIndex) {
        chunks.push({
          type: 'text',
          content: text.slice(lastIndex, citation.startIndex)
        });
      }

      // Add citation
      chunks.push({
        type: 'citation',
        citation: citation,
        content: citation.originalText
      });

      lastIndex = citation.endIndex;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      chunks.push({
        type: 'text',
        content: text.slice(lastIndex)
      });
    }

    return chunks;
  }
}

// Export singleton instance
export const citationParser = new CitationParser();

// Utility functions for common operations
export const parseCitations = (text, context) => {
  return citationParser.parseText(text, context);
};

export const renderableText = (text) => {
  const citations = parseCitations(text);
  return citationParser.textToRenderableChunks(text, citations);
};

export default citationParser;