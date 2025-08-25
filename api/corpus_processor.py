"""
Corpus Processing Pipeline for HuggingFace Australian Legal Corpus
Handles batch processing, embedding generation, and Pinecone ingestion
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
import time

# HuggingFace datasets for corpus loading
try:
    from datasets import load_dataset, Dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    load_dataset = lambda *args, **kwargs: None
    Dataset = None

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import vector search components
from .vector_search_engine import (
    VectorSearchEngine,
    VectorSearchConfig,
    get_vector_search_engine
)

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DocumentType(Enum):
    LEGISLATION = "legislation"
    CASE_LAW = "case_law"
    REGULATION = "regulation"
    COMMENTARY = "commentary"
    UNKNOWN = "unknown"

@dataclass
class ProcessingMetrics:
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    skipped_documents: int = 0
    total_tokens: int = 0
    processing_time: float = 0.0
    embeddings_generated: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_documents == 0:
            return 0.0
        return self.processed_documents / self.total_documents
    
    @property
    def processing_speed(self) -> float:
        if self.processing_time == 0:
            return 0.0
        return self.processed_documents / self.processing_time

@dataclass
class DocumentMetadata:
    document_id: str
    original_index: int
    citation: str
    jurisdiction: str
    document_type: DocumentType
    date: Optional[str]
    url: str
    source: str
    version_id: str
    when_scraped: str
    text_length: int
    token_count: int
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    embedding_hash: Optional[str] = None

class CorpusProcessor:
    """
    Processes HuggingFace Australian Legal Corpus for vector database ingestion
    """
    
    def __init__(self, config: VectorSearchConfig):
        self.config = config
        self.vector_engine = None
        self.dataset = None
        self.processing_lock = threading.Lock()
        self.metrics = ProcessingMetrics()
        
    async def initialize(self):
        """Initialize corpus processor with vector search engine"""
        try:
            # Initialize vector search engine
            self.vector_engine = await get_vector_search_engine()
            
            logger.info("Corpus processor initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize corpus processor: {e}")
            return False
    
    async def load_legal_corpus(self, 
                               dataset_name: str = "isaacus/open-australian-legal-corpus",
                               split: str = "train",
                               streaming: bool = False) -> bool:
        """Load HuggingFace legal corpus dataset"""
        
        if not DATASETS_AVAILABLE:
            logger.error("HuggingFace datasets library not available")
            return False
        
        try:
            logger.info(f"Loading legal corpus: {dataset_name}")
            
            # Load dataset with streaming for memory efficiency
            self.dataset = load_dataset(
                dataset_name,
                split=split,
                streaming=streaming,
                trust_remote_code=True
            )
            
            if streaming:
                # For streaming datasets, we can't get total count easily
                logger.info("Dataset loaded in streaming mode")
                self.metrics.total_documents = -1  # Unknown for streaming
            else:
                self.metrics.total_documents = len(self.dataset)
                logger.info(f"Dataset loaded successfully: {self.metrics.total_documents:,} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load legal corpus: {e}")
            return False
    
    def _classify_document_type(self, text: str, citation: str, url: str) -> DocumentType:
        """Classify document type based on content and metadata"""
        text_lower = text.lower()
        citation_lower = citation.lower()
        
        # Classification rules based on content patterns
        if any(word in citation_lower for word in ['act', 'statute', 'law']):
            return DocumentType.LEGISLATION
        elif any(word in citation_lower for word in ['regulation', 'rule', 'order']):
            return DocumentType.REGULATION
        elif ' v ' in citation_lower or 'case' in citation_lower:
            return DocumentType.CASE_LAW
        elif any(word in text_lower[:500] for word in ['commentary', 'analysis', 'review']):
            return DocumentType.COMMENTARY
        else:
            return DocumentType.UNKNOWN
    
    def _extract_jurisdiction(self, citation: str, url: str) -> str:
        """Extract jurisdiction from citation and URL"""
        citation_lower = citation.lower()
        
        # Federal indicators
        federal_indicators = ['cth', 'commonwealth', 'federal', 'hca', 'fca', 'fcca']
        if any(indicator in citation_lower for indicator in federal_indicators):
            return 'federal'
        
        # State/territory indicators
        state_mapping = {
            'nsw': ['nsw', 'new south wales', 'nswsc', 'nswca'],
            'vic': ['vic', 'victoria', 'vsc', 'vsca'],
            'qld': ['qld', 'queensland', 'qsc', 'qca'],
            'sa': ['sa', 'south australia', 'sasc', 'sascfc'],
            'wa': ['wa', 'western australia', 'wasc', 'wasca'],
            'tas': ['tas', 'tasmania', 'tassc', 'tascca'],
            'nt': ['nt', 'northern territory', 'ntsc', 'ntca'],
            'act': ['act', 'australian capital territory', 'actsc', 'actca']
        }
        
        for state, indicators in state_mapping.items():
            if any(indicator in citation_lower for indicator in indicators):
                return state
        
        return 'unknown'
    
    def _calculate_token_estimate(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def _create_embedding_hash(self, text: str) -> str:
        """Create hash of text for duplicate detection"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _clean_and_validate_text(self, text: str) -> Tuple[bool, str]:
        """Clean and validate document text"""
        if not text or len(text.strip()) < 50:
            return False, "Text too short"
        
        # Clean text
        cleaned = text.strip()
        
        # Remove excessive whitespace
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Check for reasonable text length (not too long for embeddings)
        if len(cleaned) > 500000:  # 500KB limit
            cleaned = cleaned[:500000] + "..."
            logger.warning(f"Text truncated to 500KB limit")
        
        return True, cleaned
    
    def _process_document_metadata(self, doc: Dict[str, Any], index: int) -> DocumentMetadata:
        """Process and extract metadata from a single document"""
        
        # Extract basic fields
        text = doc.get('text', '')
        citation = doc.get('citation', f'Document {index}')
        url = doc.get('url', '')
        source = doc.get('source', 'unknown')
        version_id = doc.get('version_id', '')
        when_scraped = doc.get('when_scraped', '')
        date = doc.get('date', None)
        
        # Validate and clean text
        is_valid, cleaned_text = self._clean_and_validate_text(text)
        
        # Extract derived metadata
        document_type = self._classify_document_type(cleaned_text, citation, url)
        jurisdiction = self._extract_jurisdiction(citation, url)
        token_count = self._calculate_token_estimate(cleaned_text)
        embedding_hash = self._create_embedding_hash(cleaned_text)
        
        # Create document ID
        document_id = f"doc_{index}_{embedding_hash[:8]}"
        
        return DocumentMetadata(
            document_id=document_id,
            original_index=index,
            citation=citation,
            jurisdiction=jurisdiction,
            document_type=document_type,
            date=date,
            url=url,
            source=source,
            version_id=version_id,
            when_scraped=when_scraped,
            text_length=len(cleaned_text),
            token_count=token_count,
            processing_status=ProcessingStatus.PENDING if is_valid else ProcessingStatus.SKIPPED,
            error_message=None if is_valid else cleaned_text,
            embedding_hash=embedding_hash
        )
    
    async def process_corpus_batch(self, 
                                 batch_size: int = 100,
                                 start_index: int = 0,
                                 max_documents: Optional[int] = None,
                                 skip_existing: bool = True) -> ProcessingMetrics:
        """Process legal corpus in batches for vector database ingestion"""
        
        if not self.dataset:
            raise ValueError("Dataset not loaded. Call load_legal_corpus() first.")
        
        if not self.vector_engine or not self.vector_engine.is_initialized:
            raise ValueError("Vector engine not initialized.")
        
        self.metrics = ProcessingMetrics(start_time=datetime.utcnow())
        
        try:
            # Determine processing range
            if hasattr(self.dataset, '__len__'):
                total_available = len(self.dataset)
            else:
                total_available = max_documents or 10000  # Default for streaming
            
            end_index = min(
                start_index + (max_documents or total_available),
                total_available
            )
            
            self.metrics.total_documents = end_index - start_index
            
            logger.info(f"Processing documents {start_index} to {end_index-1} in batches of {batch_size}")
            
            # Process in batches
            for batch_start in range(start_index, end_index, batch_size):
                batch_end = min(batch_start + batch_size, end_index)
                
                logger.info(f"Processing batch {batch_start}-{batch_end-1}")
                
                batch_success = await self._process_single_batch(
                    batch_start, 
                    batch_end,
                    skip_existing
                )
                
                if not batch_success:
                    logger.error(f"Batch {batch_start}-{batch_end-1} failed")
                    continue
                
                # Progress update
                progress = (batch_end - start_index) / self.metrics.total_documents * 100
                logger.info(f"Progress: {progress:.1f}% ({batch_end - start_index}/{self.metrics.total_documents})")
        
        except Exception as e:
            logger.error(f"Corpus processing failed: {e}")
            self.metrics.end_time = datetime.utcnow()
            if self.metrics.start_time:
                self.metrics.processing_time = (self.metrics.end_time - self.metrics.start_time).total_seconds()
            raise
        
        # Finalize metrics
        self.metrics.end_time = datetime.utcnow()
        if self.metrics.start_time:
            self.metrics.processing_time = (self.metrics.end_time - self.metrics.start_time).total_seconds()
        
        logger.info(f"Corpus processing completed:")
        logger.info(f"  - Total documents: {self.metrics.total_documents:,}")
        logger.info(f"  - Processed: {self.metrics.processed_documents:,}")
        logger.info(f"  - Failed: {self.metrics.failed_documents:,}")
        logger.info(f"  - Skipped: {self.metrics.skipped_documents:,}")
        logger.info(f"  - Success rate: {self.metrics.success_rate:.1%}")
        logger.info(f"  - Processing time: {self.metrics.processing_time:.1f}s")
        logger.info(f"  - Speed: {self.metrics.processing_speed:.1f} docs/second")
        
        return self.metrics
    
    async def _process_single_batch(self, 
                                   start_idx: int, 
                                   end_idx: int,
                                   skip_existing: bool) -> bool:
        """Process a single batch of documents"""
        
        try:
            # Extract batch from dataset
            if hasattr(self.dataset, '__getitem__'):
                # Standard dataset
                batch_docs = [self.dataset[i] for i in range(start_idx, end_idx)]
            else:
                # Streaming dataset
                batch_docs = []
                for i, doc in enumerate(self.dataset):
                    if i >= end_idx:
                        break
                    if i >= start_idx:
                        batch_docs.append(doc)
            
            # Process metadata for batch
            metadata_list = []
            texts_to_embed = []
            
            for i, doc in enumerate(batch_docs):
                doc_index = start_idx + i
                metadata = self._process_document_metadata(doc, doc_index)
                metadata_list.append(metadata)
                
                if metadata.processing_status == ProcessingStatus.PENDING:
                    is_valid, cleaned_text = self._clean_and_validate_text(doc.get('text', ''))
                    if is_valid:
                        texts_to_embed.append(cleaned_text)
                    else:
                        metadata.processing_status = ProcessingStatus.SKIPPED
                        metadata.error_message = "Text validation failed"
                        self.metrics.skipped_documents += 1
                else:
                    self.metrics.skipped_documents += 1
            
            if not texts_to_embed:
                logger.warning(f"No valid texts to embed in batch {start_idx}-{end_idx-1}")
                return True
            
            # Generate embeddings
            try:
                embeddings = await self.vector_engine._generate_embeddings(texts_to_embed)
                self.metrics.embeddings_generated += len(embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {start_idx}-{end_idx-1}: {e}")
                # Mark all as failed
                for metadata in metadata_list:
                    if metadata.processing_status == ProcessingStatus.PENDING:
                        metadata.processing_status = ProcessingStatus.FAILED
                        metadata.error_message = f"Embedding generation failed: {str(e)}"
                        self.metrics.failed_documents += 1
                return False
            
            # Prepare vectors for Pinecone
            vectors = []
            embedding_idx = 0
            
            for metadata in metadata_list:
                if metadata.processing_status == ProcessingStatus.PENDING:
                    vector_data = {
                        "id": metadata.document_id,
                        "values": embeddings[embedding_idx],
                        "metadata": {
                            "citation": metadata.citation,
                            "jurisdiction": metadata.jurisdiction,
                            "type": metadata.document_type.value,
                            "date": metadata.date or "",
                            "url": metadata.url,
                            "source": metadata.source,
                            "version_id": metadata.version_id,
                            "when_scraped": metadata.when_scraped,
                            "text_length": metadata.text_length,
                            "token_count": metadata.token_count,
                            "original_index": metadata.original_index
                        }
                    }
                    vectors.append(vector_data)
                    embedding_idx += 1
            
            # Upsert to Pinecone
            if vectors:
                try:
                    self.vector_engine.index.upsert(vectors=vectors)
                    
                    # Mark as successfully processed
                    for metadata in metadata_list:
                        if metadata.processing_status == ProcessingStatus.PENDING:
                            metadata.processing_status = ProcessingStatus.COMPLETED
                            self.metrics.processed_documents += 1
                            self.metrics.total_tokens += metadata.token_count
                
                except Exception as e:
                    logger.error(f"Failed to upsert vectors for batch {start_idx}-{end_idx-1}: {e}")
                    # Mark all pending as failed
                    for metadata in metadata_list:
                        if metadata.processing_status == ProcessingStatus.PENDING:
                            metadata.processing_status = ProcessingStatus.FAILED
                            metadata.error_message = f"Vector upsert failed: {str(e)}"
                            self.metrics.failed_documents += 1
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Batch processing failed for {start_idx}-{end_idx-1}: {e}")
            self.metrics.failed_documents += (end_idx - start_idx)
            return False
    
    async def resume_processing(self, checkpoint_file: str) -> ProcessingMetrics:
        """Resume processing from a checkpoint"""
        
        if not os.path.exists(checkpoint_file):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_file}")
        
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            last_processed = checkpoint_data.get('last_processed_index', 0)
            batch_size = checkpoint_data.get('batch_size', 100)
            total_documents = checkpoint_data.get('total_documents', 0)
            
            logger.info(f"Resuming processing from index {last_processed}")
            
            return await self.process_corpus_batch(
                batch_size=batch_size,
                start_index=last_processed + 1,
                max_documents=total_documents - last_processed - 1
            )
            
        except Exception as e:
            logger.error(f"Failed to resume processing: {e}")
            raise
    
    async def save_checkpoint(self, checkpoint_file: str, last_processed_index: int):
        """Save processing checkpoint"""
        
        checkpoint_data = {
            'last_processed_index': last_processed_index,
            'timestamp': datetime.utcnow().isoformat(),
            'total_documents': self.metrics.total_documents,
            'processed_documents': self.metrics.processed_documents,
            'failed_documents': self.metrics.failed_documents,
            'batch_size': 100,  # Default batch size
            'metrics': asdict(self.metrics)
        }
        
        try:
            os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            
            logger.info(f"Checkpoint saved: {checkpoint_file}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        
        return {
            "processing_metrics": asdict(self.metrics),
            "performance": {
                "success_rate": self.metrics.success_rate,
                "processing_speed": self.metrics.processing_speed,
                "embeddings_per_second": self.metrics.embeddings_generated / max(self.metrics.processing_time, 1),
                "avg_tokens_per_doc": self.metrics.total_tokens / max(self.metrics.processed_documents, 1)
            },
            "system_info": {
                "dataset_available": self.dataset is not None,
                "vector_engine_initialized": self.vector_engine is not None and self.vector_engine.is_initialized,
                "pinecone_connected": hasattr(self, 'vector_engine') and self.vector_engine and hasattr(self.vector_engine, 'index'),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

class QueryProcessor:
    """
    Enhanced query processing for legal intent extraction and optimization
    """
    
    def __init__(self):
        self.legal_domains = {
            'migration': ['visa', 'migration', 'citizenship', 'character test', 'deportation'],
            'employment': ['unfair dismissal', 'workplace', 'fair work', 'employment'],
            'criminal': ['criminal', 'charge', 'offence', 'conviction', 'sentence'],
            'family': ['divorce', 'custody', 'child support', 'family court'],
            'corporate': ['director', 'corporation', 'company', 'asic', 'corporate law'],
            'property': ['property', 'real estate', 'conveyancing', 'landlord', 'tenant'],
            'constitutional': ['constitutional', 'human rights', 'high court']
        }
        
        self.jurisdiction_keywords = {
            'federal': ['commonwealth', 'federal', 'cth', 'high court', 'federal court'],
            'nsw': ['nsw', 'new south wales', 'sydney'],
            'vic': ['victoria', 'vic', 'melbourne'],
            'qld': ['queensland', 'qld', 'brisbane'],
            'sa': ['south australia', 'sa', 'adelaide'],
            'wa': ['western australia', 'wa', 'perth'],
            'tas': ['tasmania', 'tas', 'hobart'],
            'nt': ['northern territory', 'nt', 'darwin'],
            'act': ['act', 'canberra', 'australian capital territory']
        }
    
    def extract_legal_intent(self, query: str) -> Dict[str, Any]:
        """Extract legal intent, domain, and jurisdiction from query"""
        
        query_lower = query.lower()
        
        # Extract legal domain
        detected_domains = []
        for domain, keywords in self.legal_domains.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_domains.append(domain)
        
        # Extract jurisdiction preferences
        detected_jurisdictions = []
        for jurisdiction, keywords in self.jurisdiction_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_jurisdictions.append(jurisdiction)
        
        # Extract citation references
        import re
        citations = []
        
        # Look for section references
        section_matches = re.findall(r'(?:section|s\.?)\s*(\d+[a-z]*)', query_lower)
        citations.extend([f"section {match}" for match in section_matches])
        
        # Look for act references
        act_matches = re.findall(r'([a-z\s]+act\s*\d{4})', query_lower)
        citations.extend(act_matches)
        
        # Determine query type
        query_types = []
        if any(word in query_lower for word in ['what is', 'define', 'explain']):
            query_types.append('definition')
        if any(word in query_lower for word in ['how to', 'procedure', 'process']):
            query_types.append('procedural')
        if any(word in query_lower for word in ['penalty', 'punishment', 'sentence']):
            query_types.append('consequences')
        if any(word in query_lower for word in ['example', 'case', 'instance']):
            query_types.append('examples')
        
        return {
            'original_query': query,
            'legal_domains': detected_domains,
            'jurisdictions': detected_jurisdictions,
            'citations': citations,
            'query_types': query_types,
            'complexity_score': len(detected_domains) + len(detected_jurisdictions) + len(citations),
            'needs_specific_citation': len(citations) > 0,
            'multi_jurisdictional': len(detected_jurisdictions) > 1,
            'processed_at': datetime.utcnow().isoformat()
        }

# Global instances and helper functions
_corpus_processor = None
_query_processor = None

async def get_corpus_processor(config: Optional[VectorSearchConfig] = None) -> CorpusProcessor:
    """Get or create corpus processor singleton"""
    global _corpus_processor
    
    if _corpus_processor is None:
        if config is None:
            from .vector_search_engine import create_vector_search_config
            config = create_vector_search_config()
        
        _corpus_processor = CorpusProcessor(config)
        await _corpus_processor.initialize()
    
    return _corpus_processor

def get_query_processor() -> QueryProcessor:
    """Get or create query processor singleton"""
    global _query_processor
    
    if _query_processor is None:
        _query_processor = QueryProcessor()
    
    return _query_processor

# Export main functions
async def process_legal_corpus(
    batch_size: int = 100,
    start_index: int = 0,
    max_documents: Optional[int] = None,
    dataset_name: str = "isaacus/open-australian-legal-corpus"
) -> ProcessingMetrics:
    """Process HuggingFace legal corpus for vector database"""
    
    processor = await get_corpus_processor()
    
    # Load dataset if not already loaded
    if not processor.dataset:
        success = await processor.load_legal_corpus(dataset_name)
        if not success:
            raise RuntimeError("Failed to load legal corpus")
    
    return await processor.process_corpus_batch(
        batch_size=batch_size,
        start_index=start_index,
        max_documents=max_documents
    )

async def analyze_query_intent(query: str) -> Dict[str, Any]:
    """Analyze query for legal intent and optimization"""
    processor = get_query_processor()
    return processor.extract_legal_intent(query)

async def get_corpus_processing_status() -> Dict[str, Any]:
    """Get current corpus processing status"""
    try:
        processor = await get_corpus_processor()
        return processor.get_processing_statistics()
    except Exception as e:
        return {
            "error": str(e),
            "processor_available": False,
            "timestamp": datetime.utcnow().isoformat()
        }