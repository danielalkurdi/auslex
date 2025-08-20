"""
Lightweight Australian Legal Corpus Integration
Fallback version that works without heavy dependencies
"""

import os
import json
import logging
from typing import List, Dict, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalCorpusLite:
    """
    Lightweight legal corpus that provides fallback functionality
    """
    
    def __init__(self):
        self.is_initialized = False
        self.fallback_data = self._create_fallback_data()
        
    def _create_fallback_data(self):
        """Create comprehensive fallback data including section 359A"""
        return [
            {
                'id': 'migration_act_1958_cth_s_359a',
                'citation': 'Migration Act 1958 (Cth) s 359A',
                'text': '''Information and invitation given in writing by Tribunal

(1) Subject to subsections (2) and (3), if:
    (a) in the course of the review of an MRT-reviewable decision, the Tribunal gets any information; and
    (b) the Tribunal considers that the information would be the reason, or a part of the reason, for affirming the decision that is under review; and
    (c) the information was not given by the applicant for the purposes of the application for review;
then the Tribunal must:

(d) give to the applicant, in the way that the Tribunal considers appropriate in the circumstances, particulars of any such information, other than non-disclosable information; and
(e) ensure, as far as is reasonably practicable, that the applicant understands why it is relevant to the review, and the consequences of it being relied on in affirming the decision that is under review; and
(f) invite the applicant to comment on or respond to it.

This provision codifies procedural fairness requirements for the Migration Review Tribunal. It requires the Tribunal to disclose adverse information before making a decision, implementing the principle of natural justice - the right to be heard. Failure to comply with s 359A constitutes jurisdictional error.''',
                'jurisdiction': 'Commonwealth',
                'type': 'primary_legislation',
                'date': '2024-07-01',
                'url': 'https://www.legislation.gov.au/Details/C2023C00094',
                'relevance_score': 0.9
            },
            {
                'id': 'migration_act_1958_cth_s_501',
                'citation': 'Migration Act 1958 (Cth) s 501',
                'text': '''Character test provisions - The Minister may refuse to grant a visa to a person if the person does not satisfy the Minister that the person passes the character test. The Minister may cancel a visa if the person does not pass the character test. For the purposes of this section, a person does not pass the character test if the person has a substantial criminal record, has criminal associations, or is not of good character.''',
                'jurisdiction': 'Commonwealth',
                'type': 'primary_legislation',
                'date': '2022-12-01',
                'url': 'https://www.legislation.gov.au/Details/C2023C00094',
                'relevance_score': 0.8
            },
            {
                'id': 'fair_work_act_2009_cth_s_382',
                'citation': 'Fair Work Act 2009 (Cth) s 382',
                'text': '''Unfair dismissal occurs when the Fair Work Commission is satisfied that a person has been dismissed and the dismissal was harsh, unjust or unreasonable, was not consistent with the Small Business Fair Dismissal Code, and was not a case of genuine redundancy.''',
                'jurisdiction': 'Commonwealth',
                'type': 'primary_legislation',
                'date': '2021-06-30',
                'url': 'https://www.legislation.gov.au/Details/C2022C00174',
                'relevance_score': 0.7
            },
            {
                'id': 'corporations_act_2001_cth_s_181',
                'citation': 'Corporations Act 2001 (Cth) s 181',
                'text': '''Good faith duties - A director or other officer of a corporation must exercise their powers and discharge their duties in good faith in the best interests of the corporation and for a proper purpose. This is a fundamental duty of directors and officers, with breach resulting in civil penalties and compensation orders.''',
                'jurisdiction': 'Commonwealth',
                'type': 'primary_legislation',
                'date': '2020-04-01',
                'url': 'https://www.legislation.gov.au/Details/C2022C00216',
                'relevance_score': 0.6
            }
        ]
    
    def initialize(self):
        """Initialize the lite corpus"""
        logger.info("Initializing Legal Corpus Lite (fallback mode)")
        self.is_initialized = True
    
    def search_provisions(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search provisions using simple text matching"""
        query_lower = query.lower()
        results = []
        
        for provision in self.fallback_data:
            score = 0
            
            # Simple keyword matching
            text_lower = provision['text'].lower()
            citation_lower = provision['citation'].lower()
            
            # Score based on keyword matches
            for word in query_lower.split():
                if len(word) > 2:  # Skip very short words
                    if word in text_lower:
                        score += 2
                    if word in citation_lower:
                        score += 3
            
            # Section number matching
            section_matches = re.findall(r'\b(?:section|s|sec)\s*(\d+[A-Za-z]*)\b', query_lower)
            for section in section_matches:
                if section in citation_lower:
                    score += 10
            
            if score > 0:
                result = provision.copy()
                result['relevance_score'] = score / 10  # Normalize score
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:top_k]
    
    def find_specific_provision(self, act_name: str, section: str, jurisdiction: str = None) -> Optional[Dict]:
        """Find specific provision"""
        act_lower = act_name.lower()
        section_lower = section.lower()
        
        for provision in self.fallback_data:
            citation_lower = provision['citation'].lower()
            
            # Check for act name match
            act_words = act_lower.split()
            act_match = all(word in citation_lower for word in act_words if len(word) > 2)
            
            # Check for section match
            section_match = f"s {section_lower}" in citation_lower or f"section {section_lower}" in citation_lower
            
            if act_match and section_match:
                return self._format_provision_result(provision)
        
        return None
    
    def _format_provision_result(self, provision: Dict) -> Dict:
        """Format provision for API response"""
        return {
            'id': provision['id'],
            'provision_text': provision['text'],
            'metadata': {
                'title': provision['citation'],
                'lastAmended': provision.get('date', ''),
                'effectiveDate': provision.get('date', ''),
                'jurisdiction': provision.get('jurisdiction', ''),
                'type': provision.get('type', '')
            },
            'source': 'Legal Corpus Lite',
            'full_act_url': provision.get('url', ''),
            'notes': [
                f"Retrieved from Legal Corpus Lite (fallback mode)",
                f"Document type: {provision.get('type', 'Unknown')}",
                f"Jurisdiction: {provision.get('jurisdiction', 'Unknown')}"
            ],
            'related_provisions': [],
            'case_references': []
        }

# Global instance
legal_corpus_lite = LegalCorpusLite()

# Initialize on import
legal_corpus_lite.initialize()

# Export functions
def search_legal_provisions(query: str, top_k: int = 10) -> List[Dict]:
    """Search for legal provisions"""
    return legal_corpus_lite.search_provisions(query, top_k)

def find_specific_legal_provision(act_name: str, section: str, jurisdiction: str = None) -> Optional[Dict]:
    """Find specific legal provision"""
    return legal_corpus_lite.find_specific_provision(act_name, section, jurisdiction)

def get_corpus_stats() -> Dict:
    """Get corpus statistics"""
    return {
        'status': 'lite_mode',
        'document_count': len(legal_corpus_lite.fallback_data),
        'cache_available': False,
        'mode': 'fallback'
    }

def initialize_corpus():
    """Initialize corpus (no-op for lite version)"""
    pass