/**
 * AustLII URL Construction Service
 * 
 * This service constructs direct URLs to AustLII content based on parsed legal citations.
 * It follows AustLII's URL patterns and provides fallback search functionality.
 * 
 * URL Patterns:
 * - Legislation: https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/[jurisdiction]/[type]/[act_id]/s[section].html
 * - Cases: https://www.austlii.edu.au/cgi-bin/viewdoc/au/cases/[jurisdiction]/[court]/[year]/[number].html
 * - Search: https://www.austlii.edu.au/cgi-bin/sinodisp/[search_terms]
 */

// Jurisdiction mappings for AustLII URLs
export const JURISDICTION_MAPPINGS = {
  'Cth': 'cth',
  'Commonwealth': 'cth',
  'NSW': 'nsw',
  'New South Wales': 'nsw',
  'Vic': 'vic', 
  'Victoria': 'vic',
  'Qld': 'qld',
  'Queensland': 'qld',
  'WA': 'wa',
  'Western Australia': 'wa',
  'SA': 'sa',
  'South Australia': 'sa',
  'Tas': 'tas',
  'Tasmania': 'tas',
  'NT': 'nt',
  'Northern Territory': 'nt',
  'ACT': 'act',
  'Australian Capital Territory': 'act'
};

// Act name to AustLII identifier mappings  
export const ACT_MAPPINGS = {
  // Commonwealth Acts
  'Migration Act 1958': 'ma1958118',
  'Privacy Act 1988': 'pa1988108', 
  'Corporations Act 2001': 'ca2001172',
  'Fair Work Act 2009': 'fwa2009114',
  'Competition and Consumer Act 2010': 'caca2010265',
  'Criminal Code Act 1995': 'cca1995115',
  'Income Tax Assessment Act 1997': 'itaa1997143',
  'Family Law Act 1975': 'fla1975114',
  'Bankruptcy Act 1966': 'ba1966142',
  'Evidence Act 1995': 'ea1995114',
  'Administrative Decisions (Judicial Review) Act 1977': 'adjra1977200',
  'Freedom of Information Act 1982': 'foia1982222',
  'Racial Discrimination Act 1975': 'rda1975183',
  'Sex Discrimination Act 1984': 'sda1984209',
  'Disability Discrimination Act 1992': 'dda1992135',
  'Age Discrimination Act 2004': 'ada2004133',
  'Human Rights and Equal Opportunity Commission Act 1986': 'hraeoca1986125',
  'Australian Securities and Investments Commission Act 2001': 'asica2001112',
  'Australian Consumer Law': 'acl2010',
  'Personal Property Securities Act 2009': 'ppsa2009123',
  'Privacy and Personal Information Protection Act 1998': 'ppipa1998133',
  'Biosecurity Act 2015': 'ba201522',
  'Modern Slavery Act 2018': 'msa2018153',
  'National Disability Insurance Scheme Act 2013': 'ndisa201320',
  'Data Availability and Transparency Act 2022': 'data202275',
  'Online Safety Act 2021': 'osa202176',
  'Telecommunications Act 1997': 'ta1997213',
  'Anti-Money Laundering and Counter-Terrorism Financing Act 2006': 'amlctfa2006169',
  'Trade Practices Act 1974': 'tpa1974149',
  'Customs Act 1901': 'ca1901112',
  'Excise Act 1901': 'ea1901107',
  'Social Security Act 1991': 'ssa1991186',
  'Veterans\' Entitlements Act 1986': 'vea1986290',
  'Judiciary Act 1903': 'ja1903112',
  'Federal Court of Australia Act 1976': 'fcoaa1976156',
  'High Court of Australia Act 1979': 'hcoaa1979123',
  
  // Commonwealth Regulations
  'Migration Regulations 1994': 'mr1994227',
  'Corporations Regulations 2001': 'cr2001174',
  'Fair Work Regulations 2009': 'fwr2009115',
  'Privacy Amendment Regulations 2010': 'par2010134',
  'Competition and Consumer Regulations 2010': 'cacr2010267',
  
  // NSW Acts
  'Criminal Procedure Act 1986': 'cpa1986209',
  'Crimes Act 1900': 'ca1900040',
  'Evidence Act 1995 (NSW)': 'ea1995025',
  'Civil Procedure Act 2005': 'cpa2005028',
  'Legal Profession Uniform Law Application Act 2014 (NSW)': 'lpulaa2014014',
  'Property Law Act 1969': 'pla1969046',
  'Conveyancing Act 1919': 'ca1919006',
  'Real Property Act 1900': 'rpa1900025',
  'Residential Tenancies Act 2010': 'rta2010042',
  'Workers Compensation Act 1987': 'wca1987070',
  
  // Victoria Acts
  'Crimes Act 1958': 'ca19586208',
  'Evidence Act 2008': 'ea200819',
  'Civil Procedure Act 2010': 'cpa201016',
  'Legal Profession Uniform Law Application Act 2014 (VIC)': 'lpulaa201476',
  'Property Law Act 1958': 'pla19586344',
  'Sale of Land Act 1962': 'sola19626959',
  'Residential Tenancies Act 1997': 'rta19976042',
  'Workplace Injury Rehabilitation and Compensation Act 2013': 'wircaa201356',
  
  // Queensland Acts
  'Criminal Code Act 1899': 'cca189985',
  'Evidence Act 1977': 'ea1977102',
  'Uniform Civil Procedure Rules 1999': 'ucpr1999430',
  'Legal Profession Act 2007': 'lpa200735',
  'Property Law Act 1974': 'pla197485',
  'Land Act 1994': 'la1994142',
  'Residential Tenancies and Rooming Accommodation Act 2008': 'rtraa200873',
  'Workers\' Compensation and Rehabilitation Act 2003': 'wcra200327',
  
  // Recent Commonwealth Acts (2020-2025)
  'Coronavirus Economic Response Package Omnibus Act 2020': 'cerpo202022',
  'Treasury Laws Amendment (2021 Measures No. 1) Act 2021': 'tlaa202182',
  'Privacy Legislation Amendment Act 2021': 'plaa2021148',
  'Surveillance Legislation Amendment Act 2021': 'slaa202140',
  'Critical Infrastructure Security Act 2022': 'cisa202233',
  'Cyber Security Act 2024': 'csa202456'
};

// Court mappings for case citations
export const COURT_MAPPINGS = {
  'HCA': 'HCA',
  'FCA': 'FCA', 
  'FCAFC': 'FCAFC',
  'FCCA': 'FCC',
  'NSWCA': 'NSWCA',
  'NSWSC': 'NSWSC',
  'NSWCCA': 'NSWCCA',
  'VCA': 'VSCA',
  'VSC': 'VSC',
  'QCA': 'QCA',
  'QSC': 'QSC',
  'WASCA': 'WASCA',
  'WASC': 'WASC',
  'SASCFC': 'SASCFC',
  'SASC': 'SASC',
  'TASCA': 'TASCA',
  'TASSC': 'TASSC',
  'NTCA': 'NTCA',
  'NTSC': 'NTSC',
  'ACTCA': 'ACTCA',
  'ACTSC': 'ACTSC'
};

/**
 * AustLII URL Construction Service
 */
export class AustLIIService {
  constructor() {
    this.baseUrl = 'https://www.austlii.edu.au';
    this.classicBaseUrl = 'https://classic.austlii.edu.au';
  }

  /**
   * Construct AustLII URL for a legal citation
   * @param {Object} citation - Parsed citation object
   * @returns {Object} URL construction result
   */
  constructUrl(citation) {
    try {
      console.log('Constructing URL for citation:', citation);
      
      switch (citation.type) {
        case 'legislation':
          return this.constructLegislationUrl(citation);
        case 'regulation':
          return this.constructRegulationUrl(citation);
        case 'case':
          return this.constructCaseUrl(citation);
        default:
          return this.constructFallbackSearch(citation);
      }
    } catch (error) {
      console.warn('Error constructing AustLII URL:', error);
      return this.constructFallbackSearch(citation);
    }
  }

  /**
   * Construct URL for legislation
   * @param {Object} citation - Citation object
   * @returns {Object} URL result
   */
  constructLegislationUrl(citation) {
    const jurisdiction = JURISDICTION_MAPPINGS[citation.jurisdiction];
    if (!jurisdiction) {
      console.warn(`Unknown jurisdiction: ${citation.jurisdiction}, falling back to search`);
      return this.constructFallbackSearch(citation);
    }

    // Try to find exact match first
    const actKey = `${citation.actName} ${citation.year}`;
    let actId = ACT_MAPPINGS[actKey];
    
    if (!actId) {
      console.warn(`No act mapping found for: ${actKey}, falling back to search`);
      return this.constructFallbackSearch(citation);
    }

    const section = this.formatSectionForUrl(citation.provision?.raw || '1');
    
    // Use classic.austlii.edu.au for legislation
    const url = `${this.classicBaseUrl}/au/legis/${jurisdiction}/consol_act/${actId}/s${section}.html`;
    
    return {
      url,
      type: 'direct',
      title: `${citation.actName} ${citation.year} - Section ${citation.provision?.raw}`,
      fallbackSearch: this.constructFallbackSearch(citation).url
    };
  }

  /**
   * Construct URL for regulations
   * @param {Object} citation - Citation object
   * @returns {Object} URL result
   */
  constructRegulationUrl(citation) {
    const jurisdiction = JURISDICTION_MAPPINGS[citation.jurisdiction];
    if (!jurisdiction) {
      throw new Error(`Unknown jurisdiction: ${citation.jurisdiction}`);
    }

    const regKey = `${citation.actName} ${citation.year}`;
    let regId = ACT_MAPPINGS[regKey];
    
    if (!regId) {
      regId = ACT_MAPPINGS[citation.actName];
    }
    
    if (!regId) {
      regId = this.generateActId(citation.actName, citation.year);
    }

    const section = this.formatSectionForUrl(citation.provision?.raw || '');
    
    const url = `${this.baseUrl}/cgi-bin/viewdoc/au/legis/${jurisdiction}/consol_reg/${regId}/s${section}.html`;
    
    return {
      url,
      type: 'direct',
      title: `${citation.actName} ${citation.year} - ${citation.provisionType} ${citation.provision?.raw}`,
      fallbackSearch: this.constructFallbackSearch(citation).url
    };
  }

  /**
   * Construct URL for case citations
   * @param {Object} citation - Citation object
   * @returns {Object} URL result
   */
  constructCaseUrl(citation) {
    const court = citation.court; // Use the court code directly
    
    // Check if it's a UK case (AC, UKHL, UKSC, etc.) or old case
    const ukCourts = ['AC', 'UKHL', 'UKSC', 'HL', 'PC', 'KB', 'QB'];
    if (ukCourts.includes(court) || parseInt(citation.year) < 1940) {
      // UK cases or very old cases - use search instead
      return this.constructFallbackSearch(citation);
    }
    
    // Determine jurisdiction based on court
    const jurisdiction = this.getJurisdictionFromCourt(court) || 'cth';
    
    // For modern Australian cases (2000+), use the standard pattern
    const url = `${this.baseUrl}/cgi-bin/viewdoc/au/cases/${jurisdiction}/${court}/${citation.year}/${citation.caseNumber}.html`;
    
    console.log('Constructed case URL:', url);
    
    return {
      url,
      type: 'direct',
      title: `${citation.plaintiff} v ${citation.defendant} [${citation.year}] ${citation.court} ${citation.caseNumber}`,
      fallbackSearch: this.constructFallbackSearch(citation).url
    };
  }

  /**
   * Construct fallback search URL
   * @param {Object} citation - Citation object
   * @returns {Object} Search URL result
   */
  constructFallbackSearch(citation) {
    const searchTerms = encodeURIComponent(citation.fullCitation || citation.originalText);
    const url = `${this.baseUrl}/cgi-bin/sinodisp/au/cases/search.html?query=${searchTerms}`;
    
    return {
      url,
      type: 'search',
      title: `Search AustLII for: ${citation.fullCitation || citation.originalText}`,
      isSearch: true
    };
  }

  /**
   * Generate act ID based on name and year
   * @param {string} actName - Act name
   * @param {string} year - Year
   * @returns {string} Generated ID
   */
  generateActId(actName, year) {
    // Simple heuristic: first letters of words + year + estimated number
    const words = actName.toLowerCase().replace(/[^a-z\s]/g, '').split(/\s+/);
    const acronym = words.map(word => word.charAt(0)).join('').substring(0, 6);
    const yearNum = year || '0000';
    const estimatedNum = Math.floor(Math.random() * 999) + 100; // Random 3-digit number
    
    return `${acronym}${yearNum}${estimatedNum}`;
  }

  /**
   * Format section number for URL
   * @param {string} section - Section reference
   * @returns {string} Formatted section
   */
  formatSectionForUrl(section) {
    if (!section) return '1';
    
    // Handle section ranges like "6-8" -> "6"
    if (section.includes('-')) {
      const firstSection = section.split('-')[0];
      return firstSection.toLowerCase();
    }
    
    // Handle complex sections like "359A(1)(a)" -> "359a"
    // Keep letters and numbers, remove brackets
    const cleaned = section.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
    
    return cleaned || '1';
  }

  /**
   * Get jurisdiction code from court abbreviation
   * @param {string} court - Court abbreviation
   * @returns {string} Jurisdiction code
   */
  getJurisdictionFromCourt(court) {
    const courtJurisdictions = {
      'HCA': 'cth',
      'FCA': 'cth',
      'FCAFC': 'cth',
      'FCCA': 'cth',
      'NSWCA': 'nsw',
      'NSWSC': 'nsw',
      'NSWCCA': 'nsw',
      'VCA': 'vic',
      'VSC': 'vic',
      'QCA': 'qld',
      'QSC': 'qld',
      'WASCA': 'wa',
      'WASC': 'wa',
      'SASCFC': 'sa',
      'SASC': 'sa',
      'TASCA': 'tas',
      'TASSC': 'tas',
      'NTCA': 'nt',
      'NTSC': 'nt',
      'ACTCA': 'act',
      'ACTSC': 'act'
    };
    
    return courtJurisdictions[court] || 'cth';
  }

  /**
   * Validate if URL is accessible (basic check)
   * @param {string} url - URL to validate
   * @returns {Promise<boolean>} Whether URL is likely accessible
   */
  async validateUrl(url) {
    try {
      // Simple HEAD request to check if resource exists
      const response = await fetch(url, { 
        method: 'HEAD',
        mode: 'no-cors' // Handle CORS restrictions
      });
      return response.ok || response.status === 0; // 0 for no-cors mode
    } catch (error) {
      console.warn('URL validation failed:', error);
      return false; // Assume it might work in iframe
    }
  }

  /**
   * Get multiple URL options for a citation (primary + alternatives)
   * @param {Object} citation - Citation object
   * @returns {Array} Array of URL options
   */
  getUrlOptions(citation) {
    const primary = this.constructUrl(citation);
    const options = [primary];
    
    // Add alternative patterns for common variations
    if (citation.type === 'legislation') {
      // Try different section formats
      const altSection = citation.provision?.raw?.toLowerCase();
      if (altSection && altSection !== primary.url.match(/s([^.]+)\.html/)?.[1]) {
        const altUrl = primary.url.replace(/s[^.]+\.html/, `s${altSection}.html`);
        options.push({
          url: altUrl,
          type: 'alternative',
          title: `${citation.actName} - Alternative section format`,
          fallbackSearch: primary.fallbackSearch
        });
      }
    }
    
    return options;
  }
}

// Export singleton instance
export const austliiService = new AustLIIService();

// Export hook for React components
export const useAustLII = () => {
  const constructUrl = (citation) => {
    return austliiService.constructUrl(citation);
  };

  const getUrlOptions = (citation) => {
    return austliiService.getUrlOptions(citation);
  };

  const validateUrl = async (url) => {
    return await austliiService.validateUrl(url);
  };

  return {
    constructUrl,
    getUrlOptions,
    validateUrl
  };
};

export default austliiService;