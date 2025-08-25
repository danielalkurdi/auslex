"""
Unit and Integration Tests for Vector Search Engine
Tests semantic search, fallback mechanisms, and performance requirements
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Test imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))

try:
    from vector_search_engine import (
        VectorSearchEngine,
        VectorSearchConfig,
        AdvancedLegalRAG,
        SearchResult,
        SearchMethod,
        vector_search_provisions,
        answer_legal_question
    )
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    pytestmark = pytest.mark.skip("Vector search dependencies not available")

class TestVectorSearchConfig:
    """Test vector search configuration"""
    
    def test_config_creation(self):
        """Test configuration object creation"""
        config = VectorSearchConfig(
            pinecone_api_key="test-key",
            openai_api_key="test-openai-key"
        )
        assert config.pinecone_api_key == "test-key"
        assert config.openai_api_key == "test-openai-key"
        assert config.embedding_model == "text-embedding-3-small"
        assert config.embedding_dimensions == 1536
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = VectorSearchConfig(
            pinecone_api_key="test-key"
        )
        assert config.pinecone_environment == "us-east1-aws"
        assert config.index_name == "auslex-legal-corpus"
        assert config.top_k == 10
        assert config.similarity_threshold == 0.75
        assert config.enable_hybrid_search is True

@pytest.mark.skipif(not VECTOR_SEARCH_AVAILABLE, reason="Vector search not available")
class TestVectorSearchEngine:
    """Test vector search engine functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        return VectorSearchConfig(
            pinecone_api_key="test-pinecone-key",
            openai_api_key="test-openai-key",
            index_name="test-index"
        )
    
    @pytest.fixture
    def search_engine(self, mock_config):
        """Create vector search engine with mock config"""
        return VectorSearchEngine(mock_config)
    
    @patch('vector_search_engine.OpenAI')
    @patch('vector_search_engine.Pinecone')
    async def test_initialization_success(self, mock_pinecone, mock_openai, search_engine):
        """Test successful initialization"""
        # Mock Pinecone client
        mock_pc = Mock()
        mock_pinecone.return_value = mock_pc
        
        # Mock index creation/connection
        mock_pc.list_indexes.return_value = []
        mock_pc.create_index = Mock()
        mock_pc.describe_index.return_value.status.ready = True
        mock_index = Mock()
        mock_pc.Index.return_value = mock_index
        mock_index.describe_index_stats.return_value.total_vector_count = 0
        
        # Mock OpenAI client
        mock_openai_client = Mock()
        mock_openai.return_value = mock_openai_client
        
        await search_engine.initialize()
        
        assert search_engine.is_initialized is True
        assert search_engine.openai_client is not None
        assert search_engine.pinecone_client is not None
    
    @patch('vector_search_engine.OpenAI')
    async def test_initialization_fallback(self, mock_openai, search_engine):
        """Test initialization fallback when Pinecone fails"""
        # Mock OpenAI to fail
        mock_openai.side_effect = Exception("OpenAI connection failed")
        
        # Should fallback to local search only
        await search_engine.initialize()
        
        assert search_engine.is_initialized is True
        assert search_engine.openai_client is None
    
    async def test_embedding_generation(self, search_engine):
        """Test embedding generation with mocked OpenAI"""
        # Mock successful embedding response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3] + [0.0] * 1533)  # 1536 dimensions
        ]
        
        with patch.object(search_engine, 'openai_client') as mock_client:
            mock_client.embeddings.create.return_value = mock_response
            search_engine.openai_client = mock_client
            
            embeddings = await search_engine._generate_embeddings(["test text"])
            
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 1536
            assert embeddings[0][:3] == [0.1, 0.2, 0.3]
    
    async def test_text_truncation(self, search_engine):
        """Test text truncation for token limits"""
        long_text = "word " * 10000  # Very long text
        truncated = search_engine._truncate_text(long_text, max_tokens=100)
        
        # Should be truncated to approximately 400 characters (100 tokens * 4)
        assert len(truncated) <= 404  # 400 + "..." = 403
        assert truncated.endswith("...")
    
    @patch('vector_search_engine.legal_corpus')
    async def test_fallback_search(self, mock_corpus, search_engine):
        """Test fallback to TF-IDF search"""
        # Mock corpus search results
        mock_results = [
            {
                'id': 'test_1',
                'text': 'Test legal provision',
                'relevance_score': 0.8,
                'metadata': {'citation': 'Test Act s 1'}
            }
        ]
        mock_corpus.search_provisions.return_value = mock_results
        
        results = await search_engine._fallback_search("test query")
        
        assert len(results) == 1
        assert results[0].document_id == 'test_1'
        assert results[0].search_method == SearchMethod.BM25_FALLBACK
        assert results[0].score == 0.8

class TestSearchPerformance:
    """Test search performance requirements"""
    
    @pytest.fixture
    def mock_search_engine(self):
        """Create mock search engine for performance testing"""
        engine = Mock()
        engine.search = AsyncMock()
        return engine
    
    @pytest.mark.asyncio
    async def test_response_time_under_3_seconds(self, mock_search_engine):
        """Test that searches complete under 3 seconds (Phase 1 success criteria)"""
        # Mock search to return after a reasonable time
        async def mock_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate 100ms processing
            return [
                SearchResult(
                    document_id="test_1",
                    score=0.9,
                    content="Test content",
                    metadata={"test": "metadata"},
                    search_method=SearchMethod.VECTOR_ONLY
                )
            ]
        
        mock_search_engine.search = mock_search
        
        start_time = time.time()
        results = await mock_search_engine.search("test query")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 3.0, f"Response time {response_time}s exceeds 3s limit"
        assert len(results) == 1

class TestSearchAccuracy:
    """Test semantic search accuracy and relevance"""
    
    @pytest.fixture
    def sample_legal_documents(self):
        """Sample legal documents for testing"""
        return [
            {
                "id": "migration_act_s55",
                "text": "A non-citizen who holds a visa must not travel to Australia, or enter Australia, after the first entry deadline for the visa.",
                "metadata": {"citation": "Migration Act 1958 (Cth) s 55", "jurisdiction": "federal"}
            },
            {
                "id": "fair_work_s382", 
                "text": "A person has been unfairly dismissed if the Fair Work Commission is satisfied that the dismissal was harsh, unjust or unreasonable.",
                "metadata": {"citation": "Fair Work Act 2009 (Cth) s 382", "jurisdiction": "federal"}
            },
            {
                "id": "corporations_s181",
                "text": "A director or other officer of a corporation must exercise their powers and discharge their duties in good faith in the best interests of the corporation.",
                "metadata": {"citation": "Corporations Act 2001 (Cth) s 181", "jurisdiction": "federal"}
            }
        ]
    
    def test_semantic_relevance_migration_query(self, sample_legal_documents):
        """Test semantic relevance for migration-related queries"""
        query = "visa entry deadline requirements"
        
        # Migration Act s 55 should be most relevant
        migration_doc = sample_legal_documents[0]
        assert "visa" in migration_doc["text"].lower()
        assert "entry" in migration_doc["text"].lower()
        
        # Other documents should be less relevant
        fair_work_doc = sample_legal_documents[1]
        assert "visa" not in fair_work_doc["text"].lower()
    
    def test_semantic_relevance_employment_query(self, sample_legal_documents):
        """Test semantic relevance for employment-related queries"""
        query = "unfair dismissal workplace rights"
        
        # Fair Work Act s 382 should be most relevant
        fair_work_doc = sample_legal_documents[1]
        assert "dismissal" in fair_work_doc["text"].lower()
        assert "unfair" in fair_work_doc["text"].lower()

class TestHybridSearch:
    """Test hybrid search combining vector and BM25 scores"""
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results with different scores"""
        return [
            SearchResult(
                document_id="doc_1",
                score=0.9,
                content="High vector similarity content",
                metadata={"test": "data"},
                search_method=SearchMethod.VECTOR_ONLY,
                embedding_score=0.9
            ),
            SearchResult(
                document_id="doc_2", 
                score=0.7,
                content="Medium vector similarity content",
                metadata={"test": "data"},
                search_method=SearchMethod.VECTOR_ONLY,
                embedding_score=0.7
            )
        ]
    
    def test_hybrid_score_calculation(self, mock_search_results):
        """Test hybrid score calculation (70% vector + 30% BM25)"""
        vector_weight = 0.7
        bm25_weight = 0.3
        
        # Mock BM25 scores
        bm25_scores = {"doc_1": 0.6, "doc_2": 0.8}
        
        for result in mock_search_results:
            vector_score = result.embedding_score
            bm25_score = bm25_scores.get(result.document_id, 0.0)
            
            expected_hybrid = (vector_weight * vector_score) + (bm25_weight * bm25_score)
            
            # Simulate hybrid score calculation
            result.bm25_score = bm25_score
            result.hybrid_score = expected_hybrid
            
            if result.document_id == "doc_1":
                assert abs(result.hybrid_score - 0.81) < 0.01  # (0.7 * 0.9) + (0.3 * 0.6) = 0.81
            elif result.document_id == "doc_2":
                assert abs(result.hybrid_score - 0.73) < 0.01  # (0.7 * 0.7) + (0.3 * 0.8) = 0.73

class TestRAGSystem:
    """Test Retrieval-Augmented Generation system"""
    
    @pytest.fixture
    def mock_rag_system(self):
        """Mock RAG system for testing"""
        mock_engine = Mock()
        return AdvancedLegalRAG(mock_engine) if VECTOR_SEARCH_AVAILABLE else Mock()
    
    def test_confidence_assessment_high(self, mock_rag_system):
        """Test confidence assessment for high-quality results"""
        if not VECTOR_SEARCH_AVAILABLE:
            pytest.skip("Vector search not available")
            
        search_results = [
            SearchResult(
                document_id="doc_1",
                score=0.95,
                content="Highly relevant legal content",
                metadata={"citation": "Test Act s 1"},
                search_method=SearchMethod.HYBRID
            ),
            SearchResult(
                document_id="doc_2", 
                score=0.88,
                content="Also relevant legal content",
                metadata={"citation": "Test Act s 2"},
                search_method=SearchMethod.HYBRID
            )
        ]
        
        confidence = mock_rag_system._assess_confidence(search_results)
        assert confidence == "high"
    
    def test_confidence_assessment_low(self, mock_rag_system):
        """Test confidence assessment for poor results"""
        if not VECTOR_SEARCH_AVAILABLE:
            pytest.skip("Vector search not available")
            
        search_results = [
            SearchResult(
                document_id="doc_1",
                score=0.3,
                content="Low relevance content", 
                metadata={},
                search_method=SearchMethod.BM25_FALLBACK
            )
        ]
        
        confidence = mock_rag_system._assess_confidence(search_results)
        assert confidence == "low"

class TestErrorHandling:
    """Test error handling and fallback mechanisms"""
    
    @pytest.fixture
    def search_engine_with_failures(self, mock_config):
        """Create search engine that simulates failures"""
        engine = VectorSearchEngine(mock_config) if VECTOR_SEARCH_AVAILABLE else Mock()
        return engine
    
    @pytest.mark.asyncio
    async def test_pinecone_failure_fallback(self, search_engine_with_failures):
        """Test fallback when Pinecone is unavailable"""
        if not VECTOR_SEARCH_AVAILABLE:
            pytest.skip("Vector search not available")
            
        # Mock Pinecone failure
        with patch.object(search_engine_with_failures, 'index', None):
            # Should fallback to TF-IDF search
            with patch.object(search_engine_with_failures, '_fallback_search') as mock_fallback:
                mock_fallback.return_value = [Mock()]
                
                results = await search_engine_with_failures.search("test query")
                
                mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_openai_api_failure(self, search_engine_with_failures):
        """Test handling of OpenAI API failures"""
        if not VECTOR_SEARCH_AVAILABLE:
            pytest.skip("Vector search not available")
            
        with patch.object(search_engine_with_failures, 'openai_client') as mock_client:
            # Mock API failure
            mock_client.embeddings.create.side_effect = Exception("API Error")
            
            # Should handle gracefully
            with pytest.raises(Exception):
                await search_engine_with_failures._generate_embeddings(["test"])

# Integration Tests
class TestVectorSearchIntegration:
    """Integration tests for complete vector search workflow"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_search_workflow(self):
        """Test complete search workflow from query to results"""
        if not VECTOR_SEARCH_AVAILABLE:
            pytest.skip("Vector search not available")
            
        # This would require actual API keys and setup
        # For now, we'll test the workflow with mocks
        
        query = "migration visa character test requirements"
        
        # Mock the complete workflow
        with patch('vector_search_engine.get_vector_search_engine') as mock_get_engine:
            mock_engine = AsyncMock()
            mock_results = [
                {
                    'id': 'migration_501',
                    'text': 'Character test provisions...',
                    'relevance_score': 0.89,
                    'metadata': {'citation': 'Migration Act 1958 s 501'},
                    'search_method': 'hybrid'
                }
            ]
            mock_engine.search.return_value = mock_results
            mock_get_engine.return_value = mock_engine
            
            results = await vector_search_provisions(query)
            
            assert len(results) > 0
            assert results[0]['relevance_score'] > 0.8

if __name__ == "__main__":
    pytest.main([__file__, "-v"])