"""
Integration Tests for Corpus Ingestion Pipeline
Tests end-to-end corpus processing and vector database population
"""

import pytest
import asyncio
import tempfile
import os
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any
from datetime import datetime

# Test imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))

try:
    from corpus_processor import (
        CorpusProcessor,
        ProcessingStatus,
        DocumentType,
        ProcessingMetrics,
        DocumentMetadata,
        get_corpus_processor,
        process_legal_corpus
    )
    from vector_search_engine import VectorSearchConfig
    CORPUS_PROCESSING_AVAILABLE = True
except ImportError:
    CORPUS_PROCESSING_AVAILABLE = False
    pytestmark = pytest.mark.skip("Corpus processing dependencies not available")

@pytest.mark.skipif(not CORPUS_PROCESSING_AVAILABLE, reason="Corpus processing not available")
class TestCorpusProcessor:
    """Test corpus processor functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock vector search configuration"""
        return VectorSearchConfig(
            pinecone_api_key="test-pinecone-key",
            openai_api_key="test-openai-key",
            index_name="test-index"
        )
    
    @pytest.fixture
    def processor(self, mock_config):
        """Create corpus processor with mock config"""
        return CorpusProcessor(mock_config)
    
    @pytest.fixture
    def sample_legal_documents(self):
        """Sample legal documents for testing"""
        return [
            {
                'text': 'A non-citizen who holds a visa must not travel to Australia, or enter Australia, after the first entry deadline for the visa.',
                'citation': 'Migration Act 1958 (Cth) s 55',
                'jurisdiction': 'federal',
                'type': 'legislation',
                'date': '1958-01-01',
                'url': 'https://www.legislation.gov.au/Details/C2023C00094',
                'source': 'Federal Register of Legislation',
                'version_id': 'C2023C00094',
                'when_scraped': '2023-01-01T00:00:00Z'
            },
            {
                'text': 'A person has been unfairly dismissed if the Fair Work Commission is satisfied that the dismissal was harsh, unjust or unreasonable.',
                'citation': 'Fair Work Act 2009 (Cth) s 382',
                'jurisdiction': 'federal',
                'type': 'legislation',
                'date': '2009-01-01',
                'url': 'https://www.legislation.gov.au/Details/C2022C00174',
                'source': 'Federal Register of Legislation',
                'version_id': 'C2022C00174',
                'when_scraped': '2023-01-01T00:00:00Z'
            },
            {
                'text': 'In Smith v Commissioner of Taxation, the Federal Court held that...',
                'citation': 'Smith v Commissioner of Taxation [2023] FCA 100',
                'jurisdiction': 'federal',
                'type': 'case',
                'date': '2023-03-15',
                'url': 'https://www.austlii.edu.au/cgi-bin/viewdoc/au/cases/cth/FCA/2023/100.html',
                'source': 'AustLII',
                'version_id': 'FCA_2023_100',
                'when_scraped': '2023-03-16T00:00:00Z'
            }
        ]
    
    def test_processor_initialization(self, processor):
        """Test processor initialization"""
        assert processor.config is not None
        assert processor.vector_engine is None  # Not initialized yet
        assert processor.dataset is None
        assert processor.metrics.total_documents == 0
    
    def test_document_type_classification(self, processor):
        """Test document type classification logic"""
        # Test legislation classification
        leg_type = processor._classify_document_type(
            "This act provides for...",
            "Migration Act 1958 (Cth)",
            "https://legislation.gov.au"
        )
        assert leg_type == DocumentType.LEGISLATION
        
        # Test case law classification
        case_type = processor._classify_document_type(
            "The court held that...",
            "Smith v Jones [2023] HCA 1",
            "https://austlii.edu.au"
        )
        assert case_type == DocumentType.CASE_LAW
        
        # Test regulation classification
        reg_type = processor._classify_document_type(
            "This regulation establishes...",
            "Migration Regulations 1994 (Cth) reg 2.07",
            "https://legislation.gov.au"
        )
        assert reg_type == DocumentType.REGULATION
    
    def test_jurisdiction_extraction(self, processor):
        """Test jurisdiction extraction from citations"""
        # Federal jurisdiction
        federal_jurisdiction = processor._extract_jurisdiction(
            "Migration Act 1958 (Cth) s 55",
            "https://legislation.gov.au"
        )
        assert federal_jurisdiction == 'federal'
        
        # State jurisdiction
        nsw_jurisdiction = processor._extract_jurisdiction(
            "Crimes Act 1900 (NSW) s 61",
            "https://legislation.nsw.gov.au"
        )
        assert nsw_jurisdiction == 'nsw'
        
        # Unknown jurisdiction
        unknown_jurisdiction = processor._extract_jurisdiction(
            "Some Unknown Act 2023",
            "https://unknown.gov.au"
        )
        assert unknown_jurisdiction == 'unknown'
    
    def test_token_count_estimation(self, processor):
        """Test token count estimation"""
        short_text = "This is a short text"
        long_text = "word " * 1000
        
        short_tokens = processor._calculate_token_estimate(short_text)
        long_tokens = processor._calculate_token_estimate(long_text)
        
        assert short_tokens > 0
        assert long_tokens > short_tokens
        assert long_tokens == len(long_text) // 4  # Rough approximation
    
    def test_text_cleaning_validation(self, processor):
        """Test text cleaning and validation"""
        # Valid text
        valid_text = "This is a valid legal document with sufficient content for processing and analysis."
        is_valid, cleaned = processor._clean_and_validate_text(valid_text)
        assert is_valid is True
        assert cleaned == valid_text
        
        # Too short text
        short_text = "Too short"
        is_valid, error = processor._clean_and_validate_text(short_text)
        assert is_valid is False
        assert "too short" in error.lower()
        
        # Text with excessive whitespace
        messy_text = "This  has   too    much     whitespace."
        is_valid, cleaned = processor._clean_and_validate_text(messy_text)
        assert is_valid is True
        assert "  " not in cleaned  # Should remove excessive whitespace
    
    def test_document_metadata_processing(self, processor, sample_legal_documents):
        """Test document metadata processing"""
        doc = sample_legal_documents[0]
        metadata = processor._process_document_metadata(doc, 0)
        
        assert isinstance(metadata, DocumentMetadata)
        assert metadata.document_id.startswith("doc_0_")
        assert metadata.citation == doc['citation']
        assert metadata.jurisdiction == 'federal'
        assert metadata.document_type == DocumentType.LEGISLATION
        assert metadata.processing_status == ProcessingStatus.PENDING
        assert metadata.text_length > 0
        assert metadata.token_count > 0
        assert metadata.embedding_hash is not None
    
    @patch('corpus_processor.load_dataset')
    async def test_load_legal_corpus_success(self, mock_load_dataset, processor):
        """Test successful legal corpus loading"""
        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.__len__ = Mock(return_value=1000)
        mock_load_dataset.return_value = mock_dataset
        
        success = await processor.load_legal_corpus()
        
        assert success is True
        assert processor.dataset is not None
        assert processor.metrics.total_documents == 1000
        mock_load_dataset.assert_called_once()
    
    @patch('corpus_processor.load_dataset')
    async def test_load_legal_corpus_failure(self, mock_load_dataset, processor):
        """Test legal corpus loading failure"""
        mock_load_dataset.side_effect = Exception("Dataset loading failed")
        
        success = await processor.load_legal_corpus()
        
        assert success is False
        assert processor.dataset is None
    
    @pytest.mark.asyncio
    async def test_single_batch_processing_success(self, processor, sample_legal_documents):
        """Test successful single batch processing"""
        # Mock vector engine
        mock_vector_engine = Mock()
        mock_vector_engine.is_initialized = True
        mock_vector_engine._generate_embeddings = AsyncMock(
            return_value=[[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
        )
        mock_vector_engine.index = Mock()
        mock_vector_engine.index.upsert = Mock()
        
        processor.vector_engine = mock_vector_engine
        
        # Mock dataset
        processor.dataset = sample_legal_documents
        
        success = await processor._process_single_batch(0, 3, skip_existing=False)
        
        assert success is True
        mock_vector_engine._generate_embeddings.assert_called_once()
        mock_vector_engine.index.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_single_batch_processing_embedding_failure(self, processor, sample_legal_documents):
        """Test single batch processing with embedding failure"""
        # Mock vector engine with embedding failure
        mock_vector_engine = Mock()
        mock_vector_engine.is_initialized = True
        mock_vector_engine._generate_embeddings = AsyncMock(
            side_effect=Exception("Embedding generation failed")
        )
        
        processor.vector_engine = mock_vector_engine
        processor.dataset = sample_legal_documents
        
        success = await processor._process_single_batch(0, 3, skip_existing=False)
        
        assert success is False
        processor.metrics.failed_documents == 3
    
    @pytest.mark.asyncio
    async def test_checkpointing(self, processor):
        """Test checkpoint saving and loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            checkpoint_file = os.path.join(temp_dir, 'test_checkpoint.json')
            
            # Save checkpoint
            await processor.save_checkpoint(checkpoint_file, 100)
            
            assert os.path.exists(checkpoint_file)
            
            # Verify checkpoint contents
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            assert checkpoint_data['last_processed_index'] == 100
            assert 'timestamp' in checkpoint_data
            assert 'metrics' in checkpoint_data
    
    def test_processing_statistics(self, processor):
        """Test processing statistics generation"""
        # Set some sample metrics
        processor.metrics.total_documents = 1000
        processor.metrics.processed_documents = 950
        processor.metrics.failed_documents = 30
        processor.metrics.skipped_documents = 20
        processor.metrics.processing_time = 300.0
        
        stats = processor.get_processing_statistics()
        
        assert 'processing_metrics' in stats
        assert 'performance' in stats
        assert 'system_info' in stats
        
        performance = stats['performance']
        assert performance['success_rate'] == 0.95
        assert performance['processing_speed'] > 0

class TestQueryProcessor:
    """Test query processing functionality"""
    
    @pytest.fixture
    def query_processor(self):
        """Create query processor"""
        if not CORPUS_PROCESSING_AVAILABLE:
            return Mock()
        from corpus_processor import QueryProcessor
        return QueryProcessor()
    
    def test_migration_query_intent_extraction(self, query_processor):
        """Test legal intent extraction for migration queries"""
        if not CORPUS_PROCESSING_AVAILABLE:
            pytest.skip("Corpus processing not available")
            
        query = "What is the character test for Australian visas under section 501?"
        intent = query_processor.extract_legal_intent(query)
        
        assert 'migration' in intent['legal_domains']
        assert 'federal' in intent['jurisdictions']
        assert len([c for c in intent['citations'] if '501' in c]) > 0
        assert intent['complexity_score'] > 0
        assert intent['needs_specific_citation'] is True
    
    def test_employment_query_intent_extraction(self, query_processor):
        """Test legal intent extraction for employment queries"""
        if not CORPUS_PROCESSING_AVAILABLE:
            pytest.skip("Corpus processing not available")
            
        query = "How does the Fair Work Act define unfair dismissal?"
        intent = query_processor.extract_legal_intent(query)
        
        assert 'employment' in intent['legal_domains']
        assert 'definition' in intent['query_types']
        assert intent['complexity_score'] > 0
    
    def test_multi_jurisdictional_query(self, query_processor):
        """Test multi-jurisdictional query detection"""
        if not CORPUS_PROCESSING_AVAILABLE:
            pytest.skip("Corpus processing not available")
            
        query = "How do NSW and Victoria differ in their property law regarding landlord rights?"
        intent = query_processor.extract_legal_intent(query)
        
        assert 'nsw' in intent['jurisdictions']
        assert 'vic' in intent['jurisdictions']
        assert intent['multi_jurisdictional'] is True

@pytest.mark.integration
class TestCorpusIngestionIntegration:
    """Integration tests for complete corpus ingestion workflow"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_end_to_end_corpus_processing(self):
        """Test complete corpus processing workflow"""
        if not CORPUS_PROCESSING_AVAILABLE:
            pytest.skip("Corpus processing not available")
        
        # This would require actual API keys and setup
        # For now, we'll test the workflow with mocks
        
        with patch('corpus_processor.get_vector_search_engine') as mock_get_engine:
            with patch('corpus_processor.load_dataset') as mock_load_dataset:
                
                # Mock vector engine
                mock_engine = AsyncMock()
                mock_engine.is_initialized = True
                mock_engine._generate_embeddings = AsyncMock(
                    return_value=[[0.1] * 1536, [0.2] * 1536]
                )
                mock_engine.index = Mock()
                mock_engine.index.upsert = Mock()
                mock_get_engine.return_value = mock_engine
                
                # Mock dataset
                sample_docs = [
                    {
                        'text': 'Sample legal document 1 with sufficient content for processing.',
                        'citation': 'Test Act 2023 s 1',
                        'jurisdiction': 'federal',
                        'url': 'https://test.gov.au',
                        'source': 'Test Source',
                        'version_id': 'test_1',
                        'when_scraped': '2023-01-01T00:00:00Z',
                        'date': '2023-01-01'
                    },
                    {
                        'text': 'Sample legal document 2 with different content for processing.',
                        'citation': 'Test Regulation 2023 reg 1',
                        'jurisdiction': 'federal', 
                        'url': 'https://test.gov.au',
                        'source': 'Test Source',
                        'version_id': 'test_2',
                        'when_scraped': '2023-01-01T00:00:00Z',
                        'date': '2023-01-01'
                    }
                ]
                
                mock_dataset = Mock()
                mock_dataset.__len__ = Mock(return_value=2)
                mock_dataset.__getitem__ = Mock(side_effect=lambda i: sample_docs[i])
                mock_load_dataset.return_value = mock_dataset
                
                # Process corpus
                metrics = await process_legal_corpus(
                    batch_size=2,
                    start_index=0,
                    max_documents=2
                )
                
                # Verify results
                assert metrics.total_documents == 2
                assert metrics.processed_documents > 0
                assert metrics.processing_time > 0
                assert metrics.success_rate > 0
                
                # Verify vector engine interactions
                mock_engine._generate_embeddings.assert_called()
                mock_engine.index.upsert.assert_called()
    
    @pytest.mark.asyncio
    async def test_corpus_processing_with_failures(self):
        """Test corpus processing handles failures gracefully"""
        if not CORPUS_PROCESSING_AVAILABLE:
            pytest.skip("Corpus processing not available")
        
        with patch('corpus_processor.get_vector_search_engine') as mock_get_engine:
            with patch('corpus_processor.load_dataset') as mock_load_dataset:
                
                # Mock vector engine with failures
                mock_engine = AsyncMock()
                mock_engine.is_initialized = True
                mock_engine._generate_embeddings = AsyncMock(
                    side_effect=Exception("API failure")
                )
                mock_get_engine.return_value = mock_engine
                
                # Mock dataset
                sample_docs = [
                    {
                        'text': 'Sample document for failure testing with sufficient content.',
                        'citation': 'Test Act s 1',
                        'jurisdiction': 'federal',
                        'url': 'https://test.gov.au',
                        'source': 'Test',
                        'version_id': 'test_1', 
                        'when_scraped': '2023-01-01T00:00:00Z',
                        'date': '2023-01-01'
                    }
                ]
                
                mock_dataset = Mock()
                mock_dataset.__len__ = Mock(return_value=1)
                mock_dataset.__getitem__ = Mock(return_value=sample_docs[0])
                mock_load_dataset.return_value = mock_dataset
                
                # Process corpus (should handle failures)
                metrics = await process_legal_corpus(
                    batch_size=1,
                    start_index=0,
                    max_documents=1
                )
                
                # Should complete without crashing
                assert metrics.total_documents == 1
                assert metrics.failed_documents > 0
                assert metrics.success_rate < 1.0

class TestPerformanceRequirements:
    """Test performance requirements for corpus processing"""
    
    @pytest.mark.asyncio
    async def test_batch_processing_speed(self):
        """Test that batch processing meets speed requirements"""
        if not CORPUS_PROCESSING_AVAILABLE:
            pytest.skip("Corpus processing not available")
        
        # Mock fast processing
        with patch('corpus_processor.get_vector_search_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_engine.is_initialized = True
            mock_engine._generate_embeddings = AsyncMock(
                return_value=[[0.1] * 1536] * 10  # 10 embeddings
            )
            mock_engine.index = Mock()
            mock_engine.index.upsert = Mock()
            mock_get_engine.return_value = mock_engine
            
            config = VectorSearchConfig(
                pinecone_api_key="test-key",
                openai_api_key="test-key"
            )
            
            processor = CorpusProcessor(config)
            processor.vector_engine = mock_engine
            
            # Mock 10 documents
            sample_docs = []
            for i in range(10):
                sample_docs.append({
                    'text': f'Sample legal document {i} with sufficient content for processing and embedding generation.',
                    'citation': f'Test Act s {i}',
                    'jurisdiction': 'federal',
                    'url': 'https://test.gov.au',
                    'source': 'Test',
                    'version_id': f'test_{i}',
                    'when_scraped': '2023-01-01T00:00:00Z',
                    'date': '2023-01-01'
                })
            
            processor.dataset = sample_docs
            
            import time
            start_time = time.time()
            
            success = await processor._process_single_batch(0, 10, skip_existing=False)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            assert success is True
            # Should process 10 documents in under 5 seconds (mocked)
            assert processing_time < 5.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])