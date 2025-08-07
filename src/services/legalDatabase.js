/**
 * Mock Legal Database Service
 * 
 * This service simulates integration with Australian legal databases like:
 * - AustLII (http://www.austlii.edu.au/)
 * - Federal Register of Legislation (https://www.legislation.gov.au/)
 * - State and Territory legislation databases
 * 
 * In production, this would make actual API calls to these services.
 * The mock responses are based on real Australian legal provisions.
 */

// Mock database of Australian legal provisions
const MOCK_LEGAL_DATABASE = {
  // Migration Act provisions
  'migration_act_1958_cth_s_55': {
    actName: 'Migration Act 1958',
    jurisdiction: 'Commonwealth',
    section: '55',
    title: 'Visa holders must usually enter before first entry deadline',
    content: `(1) A non-citizen who holds a visa must not travel to Australia, or enter Australia, after the first entry deadline for the visa.

(2) Subsection (1) does not apply if:
    (a) the visa is held by a person who is in Australia; or
    (b) the Minister determines, in writing, that it would be unreasonable to apply subsection (1) to the non-citizen; or
    (c) the visa is a protection visa.

(3) For the purposes of subsection (2), the Minister may have regard to:
    (a) compassionate or compelling circumstances affecting the non-citizen; and
    (b) the circumstances that prevented the non-citizen from entering Australia before the first entry deadline; and
    (c) the length of time that has elapsed since the first entry deadline; and
    (d) any other matter the Minister considers relevant.`,
    lastAmended: '2023-03-15',
    notes: [
      'This provision establishes the first entry deadline requirements for visa holders',
      'Subsection (2) provides important exceptions including for protection visa holders',
      'The Minister has discretionary power under subsection (2)(b)'
    ],
    relatedProvisions: ['s 56', 's 57', 's 58'],
    caseReferences: ['Minister for Immigration v Li (2013) 249 CLR 332'],
    fullActUrl: 'https://www.legislation.gov.au/Details/C2023C00094'
  },

  'migration_act_1958_cth_s_501': {
    actName: 'Migration Act 1958',
    jurisdiction: 'Commonwealth', 
    section: '501',
    title: 'Refusal or cancellation of visa on character grounds',
    content: `(1) The Minister may refuse to grant a visa to a person if the person does not satisfy the Minister that the person passes the character test.

(2) The Minister may cancel a visa that has been granted to a person if:
    (a) the Minister reasonably suspects that the person does not pass the character test; and
    (b) the person does not satisfy the Minister that the person passes the character test.

(3) The Minister may cancel a visa that has been granted to a person if the Minister is satisfied that the person does not pass the character test.

Character test
(6) For the purposes of this section, a person does not pass the character test if:
    (a) the person has a substantial criminal record (as defined by subsection (7)); or
    (b) the person has or has had an association with someone else, or with a group or organisation, whom the Minister reasonably suspects has been or is involved in criminal conduct; or
    (c) having regard to either or both of the following:
        (i) the person's past and present criminal conduct;
        (ii) the person's past and present general conduct;
    the person is not of good character; or
    (d) in the event the person were allowed to enter or to remain in Australia, there is a risk that the person would:
        (i) engage in criminal conduct in Australia; or
        (ii) harass, molest, intimidate or stalk another person in Australia; or
        (iii) vilify a segment of the Australian community; or
        (iv) incite discord in the Australian community or in a segment of that community; or
        (v) represent a danger to the health, safety or good order of the Australian community or a segment of that community.`,
    lastAmended: '2022-12-01',
    notes: [
      'This is one of the most significant discretionary powers in migration law',
      'The character test has been subject to extensive judicial interpretation',
      'Recent amendments have expanded the grounds for character-based cancellation'
    ],
    relatedProvisions: ['s 501A', 's 501B', 's 501C'],
    caseReferences: ['SZTV v Minister for Immigration (2021) 95 ALJR 1077'],
    fullActUrl: 'https://www.legislation.gov.au/Details/C2023C00094'
  },

  // Fair Work Act provisions
  'fair_work_act_2009_cth_s_382': {
    actName: 'Fair Work Act 2009',
    jurisdiction: 'Commonwealth',
    section: '382',
    title: 'What is unfair dismissal',
    content: `A person has been unfairly dismissed if the Fair Work Commission is satisfied that:
    (a) the person has been dismissed; and
    (b) the dismissal was harsh, unjust or unreasonable; and
    (c) the dismissal was not consistent with the Small Business Fair Dismissal Code; and
    (d) the dismissal was not a case of genuine redundancy.

Note: For the definition of consistent with the Small Business Fair Dismissal Code, see section 388.`,
    lastAmended: '2021-06-30',
    notes: [
      'This section establishes the four-element test for unfair dismissal',
      'All elements must be satisfied for a dismissal to be unfair',
      'The Small Business Fair Dismissal Code provides a safe harbour for small businesses'
    ],
    relatedProvisions: ['s 383', 's 384', 's 385'],
    caseReferences: ['Nguyen v Vietnamese Community in Australia (2014) 217 FCR 25'],
    fullActUrl: 'https://www.legislation.gov.au/Details/C2022C00174'
  },

  // Corporations Act provisions
  'corporations_act_2001_cth_s_181': {
    actName: 'Corporations Act 2001',
    jurisdiction: 'Commonwealth',
    section: '181',
    title: 'Good faith—civil obligations',
    content: `(1) A director or other officer of a corporation must exercise their powers and discharge their duties:
    (a) in good faith in the best interests of the corporation; and
    (b) for a proper purpose.

(2) A person who is involved in a contravention of subsection (1) contravenes this subsection.

Note 1: Section 79 defines involved.

Note 2: This section is a civil penalty provision (see section 1317E).`,
    lastAmended: '2020-04-01',
    notes: [
      'This is a fundamental duty of directors and officers',
      'Breach can result in civil penalties and compensation orders',
      'The business judgment rule in s 180(2) provides some protection'
    ],
    relatedProvisions: ['s 180', 's 182', 's 183'],
    caseReferences: ['ASIC v Rich (2009) 236 FLR 1'],
    fullActUrl: 'https://www.legislation.gov.au/Details/C2022C00216'
  },

  // Contract law case
  'carlill_v_carbolic_smoke_ball_1893': {
    type: 'case',
    plaintiff: 'Carlill',
    defendant: 'Carbolic Smoke Ball Co',
    year: '1893',
    court: 'CA',
    citation: 'Carlill v Carbolic Smoke Ball Co [1893] 1 QB 256',
    summary: 'Landmark case establishing principles of unilateral contracts and consideration in advertising.',
    keyPrinciples: [
      'Advertisement can constitute a binding offer',
      'Deposit of money can constitute consideration',
      'Performance of conditions constitutes acceptance'
    ],
    jurisdiction: 'English (adopted in Australia)',
    lastCited: '2023-08-15',
    fullCaseUrl: 'http://www.austlii.edu.au/cgi-bin/viewdoc/au/cases/vic/VSC/2023/123.html'
  }
};

// Simulate network delay for realistic API behavior
const simulateNetworkDelay = (min = 500, max = 2000) => {
  const delay = Math.random() * (max - min) + min;
  return new Promise(resolve => setTimeout(resolve, delay));
};

/**
 * Legal Database Service Class
 */
export class LegalDatabaseService {
  constructor() {
    this.cache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Fetch provision content by citation
   * @param {Object} citation - Parsed citation object
   * @returns {Promise<Object>} Provision content
   */
  async fetchProvision(citation) {
    // Check cache first
    const cacheKey = this.generateCacheKey(citation);
    const cached = this.cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < this.cacheExpiry) {
      await simulateNetworkDelay(100, 300); // Simulate fast cache response
      return cached.data;
    }

    // Simulate network delay
    await simulateNetworkDelay();

    // Generate lookup key
    const lookupKey = this.generateLookupKey(citation);
    
    // Try to find in mock database
    const provisionData = MOCK_LEGAL_DATABASE[lookupKey];
    
    if (provisionData) {
      const result = {
        provisionText: this.formatProvisionText(provisionData.content),
        metadata: {
          title: provisionData.title,
          actName: citation.actName,
          section: citation.provision?.raw,
          jurisdiction: citation.jurisdictionFull,
          lastAmended: provisionData.lastAmended,
          effectiveDate: citation.year
        },
        source: this.getSourceDatabase(citation.jurisdiction),
        fullActUrl: provisionData.fullActUrl,
        notes: provisionData.notes || [],
        relatedProvisions: provisionData.relatedProvisions || [],
        caseReferences: provisionData.caseReferences || []
      };

      // Cache the result
      this.cache.set(cacheKey, {
        data: result,
        timestamp: Date.now()
      });

      return result;
    }

    // If not found, return a generic response
    throw new Error(`Provision not found: ${citation.fullCitation}. This may be because the provision does not exist, has been repealed, or is not available in the database.`);
  }

  /**
   * Search for related provisions
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {Promise<Array>} Search results
   */
  async searchProvisions(query, options = {}) {
    await simulateNetworkDelay();

    // Mock search results
    return [
      {
        title: 'Migration Act 1958 s 55',
        snippet: 'Visa holders must usually enter before first entry deadline...',
        url: '#',
        jurisdiction: 'Commonwealth'
      },
      {
        title: 'Migration Act 1958 s 56',
        snippet: 'Extension of first entry deadline in certain circumstances...',
        url: '#',
        jurisdiction: 'Commonwealth'
      }
    ];
  }

  /**
   * Generate cache key for citation
   * @param {Object} citation - Citation object
   * @returns {string} Cache key
   */
  generateCacheKey(citation) {
    return `${citation.actName}_${citation.year}_${citation.jurisdiction}_${citation.provision?.raw || ''}`
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^\w_]/g, '');
  }

  /**
   * Generate lookup key for mock database
   * @param {Object} citation - Citation object
   * @returns {string} Lookup key
   */
  generateLookupKey(citation) {
    const actName = citation.actName
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^\w]/g, '');
    
    const jurisdiction = citation.jurisdiction.toLowerCase();
    const section = citation.provision?.raw?.toLowerCase() || '';
    
    return `${actName}_${citation.year}_${jurisdiction}_s_${section}`;
  }

  /**
   * Format provision text for display
   * @param {string} text - Raw provision text
   * @returns {string} Formatted HTML
   */
  formatProvisionText(text) {
    return text
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>');
  }

  /**
   * Get source database name
   * @param {string} jurisdiction - Jurisdiction code
   * @returns {string} Database name
   */
  getSourceDatabase(jurisdiction) {
    const databases = {
      'Cth': 'Federal Register of Legislation',
      'NSW': 'NSW Legislation',
      'Vic': 'Victorian Legislation',
      'Qld': 'Queensland Legislation',
      'WA': 'Western Australian Legislation',
      'SA': 'South Australian Legislation',
      'Tas': 'Tasmanian Legislation',
      'NT': 'Northern Territory Legislation',
      'ACT': 'ACT Legislation Register'
    };
    
    return databases[jurisdiction] || 'AustLII';
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache stats
   */
  getCacheStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
}

// Export singleton instance
export const legalDatabase = new LegalDatabaseService();

// Export hook for React components
export const useLegalDatabase = () => {
  const fetchContent = async (citation) => {
    try {
      return await legalDatabase.fetchProvision(citation);
    } catch (error) {
      console.error('Legal database error:', error);
      throw error;
    }
  };

  const searchContent = async (query, options) => {
    try {
      return await legalDatabase.searchProvisions(query, options);
    } catch (error) {
      console.error('Legal database search error:', error);
      throw error;
    }
  };

  return {
    fetchContent,
    searchContent,
    clearCache: () => legalDatabase.clearCache(),
    getCacheStats: () => legalDatabase.getCacheStats()
  };
};

export default legalDatabase;