"""
Australian Legal Corpus Integration
Integrates the Open Australian Legal Corpus from Hugging Face for comprehensive legal data
"""

import os
import json
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import pickle
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AustralianLegalCorpus:
    """
    Manages the Australian Legal Corpus for legal document search and retrieval
    """
    
    def __init__(self, cache_dir: str = "./legal_corpus_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.corpus_df = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.is_initialized = False
        
        # Cache file paths
        self.corpus_cache_file = self.cache_dir / "corpus_data.pkl"
        self.vectorizer_cache_file = self.cache_dir / "vectorizer.pkl"
        self.tfidf_cache_file = self.cache_dir / "tfidf_matrix.pkl"
        
    def initialize(self, force_reload: bool = False):
        """
        Initialize the legal corpus, loading from cache if available
        """
        try:
            if not force_reload and self._load_from_cache():
                logger.info("Loaded legal corpus from cache")
                self.is_initialized = True
                return
                
            logger.info("Loading Australian Legal Corpus from Hugging Face...")
            
            # Load the dataset
            dataset = load_dataset("isaacus/open-australian-legal-corpus", split="train")
            
            # Convert to pandas DataFrame for easier handling
            self.corpus_df = dataset.to_pandas()
            
            logger.info(f"Loaded {len(self.corpus_df)} legal documents")
            
            # Filter and prepare for search
            self._prepare_search_index()
            
            # Cache the processed data
            self._save_to_cache()
            
            self.is_initialized = True
            logger.info("Legal corpus initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize legal corpus: {e}")
            # Fall back to mock data if corpus loading fails
            self._initialize_fallback()
    
    def _prepare_search_index(self):
        """
        Prepare TF-IDF search index for the corpus
        """
        logger.info("Preparing search index...")
        
        # Clean and prepare text for indexing
        search_texts = []
        for _, row in self.corpus_df.iterrows():
            text = str(row.get('text', ''))
            citation = str(row.get('citation', ''))
            
            # Combine citation and text for better search
            search_text = f"{citation} {text}"
            search_texts.append(search_text)
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 3),
            max_df=0.95,
            min_df=2
        )
        
        # Fit and transform the corpus
        self.tfidf_matrix = self.vectorizer.fit_transform(search_texts)
        
        logger.info("Search index prepared")
    
    def search_provisions(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search for legal provisions matching the query
        """
        if not self.is_initialized:
            logger.warning("Corpus not initialized, using fallback search")
            return self._fallback_search(query, top_k)
        
        try:
            # Transform query using the same vectorizer
            query_vector = self.vectorizer.transform([query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.01:  # Minimum relevance threshold
                    row = self.corpus_df.iloc[idx]
                    
                    result = {
                        'id': f"corpus_{idx}",
                        'citation': str(row.get('citation', 'Unknown')),
                        'text': str(row.get('text', ''))[:2000],  # Limit text length
                        'jurisdiction': str(row.get('jurisdiction', '')),
                        'type': str(row.get('type', '')),
                        'date': str(row.get('date', '')),
                        'url': str(row.get('url', '')),
                        'relevance_score': float(similarities[idx]),
                        'metadata': {
                            'source': str(row.get('source', '')),
                            'version_id': str(row.get('version_id', '')),
                            'when_scraped': str(row.get('when_scraped', ''))
                        }
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._fallback_search(query, top_k)
    
    def find_specific_provision(self, act_name: str, section: str, jurisdiction: str = None) -> Optional[Dict]:
        """
        Find a specific legal provision by act name and section
        """
        if not self.is_initialized:
            return None
        
        try:
            # Create search patterns
            section_patterns = [
                f"section {section}",
                f"s {section}",
                f"sec {section}",
                f"{section}."
            ]
            
            act_patterns = [
                act_name.lower(),
                act_name.replace(' act', '').lower(),
                act_name.replace(' ', '').lower()
            ]
            
            # Search through the corpus
            for _, row in self.corpus_df.iterrows():
                text = str(row.get('text', '')).lower()
                citation = str(row.get('citation', '')).lower()
                
                # Check if this row matches our criteria
                act_match = any(pattern in text or pattern in citation for pattern in act_patterns)
                section_match = any(pattern in text or pattern in citation for pattern in section_patterns)
                
                if jurisdiction:
                    jurisdiction_match = jurisdiction.lower() in str(row.get('jurisdiction', '')).lower()
                    if act_match and section_match and jurisdiction_match:
                        return self._format_provision_result(row, f"corpus_specific_{row.name}")
                elif act_match and section_match:
                    return self._format_provision_result(row, f"corpus_specific_{row.name}")
            
            return None
            
        except Exception as e:
            logger.error(f"Specific provision search failed: {e}")
            return None
    
    def _format_provision_result(self, row, provision_id: str) -> Dict:
        """
        Format a corpus row into a provision result
        """
        return {
            'id': provision_id,
            'provision_text': str(row.get('text', ''))[:3000],
            'metadata': {
                'title': str(row.get('citation', 'Unknown')),
                'lastAmended': str(row.get('date', '')),
                'effectiveDate': str(row.get('date', '')),
                'jurisdiction': str(row.get('jurisdiction', '')),
                'type': str(row.get('type', ''))
            },
            'source': str(row.get('source', 'Australian Legal Corpus')),
            'full_act_url': str(row.get('url', '')),
            'notes': [
                f"Retrieved from {row.get('source', 'Australian Legal Corpus')}",
                f"Document type: {row.get('type', 'Unknown')}",
                f"Jurisdiction: {row.get('jurisdiction', 'Unknown')}"
            ],
            'related_provisions': [],
            'case_references': []
        }
    
    def _save_to_cache(self):
        """
        Save processed data to cache files
        """
        try:
            # Save corpus data
            with open(self.corpus_cache_file, 'wb') as f:
                pickle.dump(self.corpus_df, f)
            
            # Save vectorizer
            with open(self.vectorizer_cache_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            # Save TF-IDF matrix
            with open(self.tfidf_cache_file, 'wb') as f:
                pickle.dump(self.tfidf_matrix, f)
                
            logger.info("Saved corpus data to cache")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_from_cache(self) -> bool:
        """
        Load processed data from cache files
        """
        try:
            if not all([
                self.corpus_cache_file.exists(),
                self.vectorizer_cache_file.exists(),
                self.tfidf_cache_file.exists()
            ]):
                return False
            
            # Load corpus data
            with open(self.corpus_cache_file, 'rb') as f:
                self.corpus_df = pickle.load(f)
            
            # Load vectorizer
            with open(self.vectorizer_cache_file, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            # Load TF-IDF matrix
            with open(self.tfidf_cache_file, 'rb') as f:
                self.tfidf_matrix = pickle.load(f)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")
            return False
    
    def _initialize_fallback(self):
        """
        Initialize with fallback mock data if corpus loading fails
        """
        logger.info("Initializing with fallback mock data")
        
        # Create minimal fallback data
        fallback_data = [
            {
                'citation': 'Migration Act 1958 (Cth) s 359A',
                'text': 'Information and invitation given in writing by Tribunal...',
                'jurisdiction': 'Commonwealth',
                'type': 'primary_legislation'
            }
        ]
        
        self.corpus_df = pd.DataFrame(fallback_data)
        self.is_initialized = True
    
    def _fallback_search(self, query: str, top_k: int) -> List[Dict]:
        """
        Fallback search when main corpus is not available
        """
        return [{
            'id': 'fallback_1',
            'citation': 'Migration Act 1958 (Cth) s 359A',
            'text': 'Information and invitation given in writing by Tribunal...',
            'jurisdiction': 'Commonwealth',
            'type': 'primary_legislation',
            'relevance_score': 0.5,
            'metadata': {'source': 'Fallback'}
        }]

# Global corpus instance
legal_corpus = AustralianLegalCorpus()

# Initialize on import (in background)
def initialize_corpus():
    """
    Initialize the legal corpus
    """
    try:
        legal_corpus.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize corpus: {e}")

# Export main functions
def search_legal_provisions(query: str, top_k: int = 10) -> List[Dict]:
    """
    Search for legal provisions in the corpus
    """
    return legal_corpus.search_provisions(query, top_k)

def find_specific_legal_provision(act_name: str, section: str, jurisdiction: str = None) -> Optional[Dict]:
    """
    Find a specific legal provision
    """
    return legal_corpus.find_specific_provision(act_name, section, jurisdiction)

def get_corpus_stats() -> Dict:
    """
    Get statistics about the loaded corpus
    """
    if not legal_corpus.is_initialized:
        return {'status': 'not_initialized', 'document_count': 0}
    
    return {
        'status': 'initialized',
        'document_count': len(legal_corpus.corpus_df) if legal_corpus.corpus_df is not None else 0,
        'cache_available': legal_corpus.corpus_cache_file.exists()
    }