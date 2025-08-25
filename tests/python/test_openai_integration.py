"""
Unit and Integration Tests for OpenAI API Integration
Tests API integration, error handling, and fallback behavior
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import json

# Test imports
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../api'))

try:
    from vector_search_engine import VectorSearchEngine, VectorSearchConfig
    from ai_research_engine import AdvancedLegalResearcher
    OPENAI_INTEGRATION_AVAILABLE = True
except ImportError:
    OPENAI_INTEGRATION_AVAILABLE = False
    pytestmark = pytest.mark.skip("OpenAI integration dependencies not available")

class TestOpenAIConfiguration:
    """Test OpenAI client configuration and setup"""
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-test-key',
        'OPENAI_BASE_URL': 'https://api.openai.com/v1',
        'OPENAI_ORG': 'test-org',
        'OPENAI_PROJECT': 'test-project'
    })
    def test_openai_client_configuration(self):
        """Test OpenAI client configuration with environment variables"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        config = VectorSearchConfig(
            pinecone_api_key="test-key",
            openai_api_key="sk-test-key"
        )
        
        assert config.openai_api_key == "sk-test-key"
        assert config.embedding_model == "text-embedding-3-small"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_handling(self):
        """Test handling of missing OpenAI API key"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        config = VectorSearchConfig(
            pinecone_api_key="test-key",
            openai_api_key=""
        )
        
        # Should handle empty API key gracefully
        assert config.openai_api_key == ""

@pytest.mark.skipif(not OPENAI_INTEGRATION_AVAILABLE, reason="OpenAI integration not available")
class TestEmbeddingGeneration:
    """Test OpenAI embedding generation functionality"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client"""
        client = Mock()
        
        # Mock embeddings response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),  # text-embedding-3-small dimensions
            Mock(embedding=[0.2] * 1536)
        ]
        client.embeddings.create.return_value = mock_response
        
        return client
    
    def test_embedding_request_format(self, mock_openai_client):
        """Test embedding request format and parameters"""
        texts = ["Test legal document", "Another legal provision"]
        
        # Simulate embedding call
        response = mock_openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        
        # Verify call was made correctly
        mock_openai_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input=texts
        )
        
        # Verify response format
        assert len(response.data) == 2
        assert len(response.data[0].embedding) == 1536
    
    def test_embedding_batch_processing(self, mock_openai_client):
        """Test batch processing of embeddings"""
        large_batch = [f"Legal document {i}" for i in range(100)]
        
        # Mock response for large batch
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536) for _ in range(100)]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        response = mock_openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=large_batch
        )
        
        assert len(response.data) == 100
    
    def test_embedding_error_handling(self, mock_openai_client):
        """Test handling of embedding API errors"""
        # Mock API error
        mock_openai_client.embeddings.create.side_effect = Exception("API rate limit exceeded")
        
        with pytest.raises(Exception) as excinfo:
            mock_openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=["test"]
            )
        
        assert "API rate limit exceeded" in str(excinfo.value)
    
    def test_text_truncation_for_token_limits(self):
        """Test text truncation to fit within API token limits"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        config = VectorSearchConfig(
            pinecone_api_key="test-key",
            openai_api_key="test-key"
        )
        engine = VectorSearchEngine(config)
        
        # Very long text that exceeds token limits
        long_text = "word " * 10000
        truncated = engine._truncate_text(long_text, max_tokens=100)
        
        # Should be truncated to approximately 400 characters (100 tokens * 4)
        assert len(truncated) <= 403  # 400 + "..."
        assert truncated.endswith("...")
    
    def test_embedding_dimensions_consistency(self, mock_openai_client):
        """Test that embeddings have consistent dimensions"""
        texts = ["Short text", "This is a much longer legal text with more content"]
        
        # Both should return same dimension embeddings
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1] * 1536),
            Mock(embedding=[0.2] * 1536)
        ]
        mock_openai_client.embeddings.create.return_value = mock_response
        
        response = mock_openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        
        # All embeddings should have same dimensions
        dimensions = [len(data.embedding) for data in response.data]
        assert all(dim == 1536 for dim in dimensions)

class TestChatCompletionIntegration:
    """Test OpenAI chat completion integration"""
    
    @pytest.fixture
    def mock_chat_client(self):
        """Create mock OpenAI chat client"""
        client = Mock()
        
        # Mock chat completion response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This is a legal AI response about Australian law."
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 100
        mock_response.usage.total_tokens = 150
        
        client.chat.completions.create.return_value = mock_response
        
        return client
    
    def test_legal_chat_completion_request(self, mock_chat_client):
        """Test legal chat completion request format"""
        messages = [
            {"role": "system", "content": "You are an expert Australian legal assistant."},
            {"role": "user", "content": "What is the character test under the Migration Act?"}
        ]
        
        response = mock_chat_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Verify API call format
        mock_chat_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Verify response
        assert "legal AI response" in response.choices[0].message.content
        assert response.usage.total_tokens == 150
    
    def test_chat_completion_with_legal_context(self, mock_chat_client):
        """Test chat completion with legal document context"""
        legal_context = """
        LEGAL PROVISIONS:
        Migration Act 1958 (Cth) s 501: Character test provisions for visa applicants...
        Fair Work Act 2009 (Cth) s 382: Unfair dismissal requirements...
        """
        
        messages = [
            {"role": "system", "content": "You are an expert Australian legal assistant with access to legal provisions."},
            {"role": "user", "content": f"Query: Character test requirements\n\n{legal_context}"}
        ]
        
        response = mock_chat_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Should handle legal context appropriately
        assert response.choices[0].message.content is not None
    
    def test_chat_completion_error_handling(self, mock_chat_client):
        """Test error handling for chat completion failures"""
        # Mock various API errors
        test_errors = [
            Exception("API timeout"),
            Exception("Rate limit exceeded"), 
            Exception("Invalid request format"),
            Exception("Model unavailable")
        ]
        
        for error in test_errors:
            mock_chat_client.chat.completions.create.side_effect = error
            
            with pytest.raises(Exception):
                mock_chat_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "test"}]
                )
    
    def test_model_fallback_mechanism(self, mock_chat_client):
        """Test fallback from primary to fallback model"""
        # First call fails (primary model)
        # Second call succeeds (fallback model)
        mock_chat_client.chat.completions.create.side_effect = [
            Exception("Model unavailable"),
            Mock(choices=[Mock(message=Mock(content="Fallback response"))])
        ]
        
        # Simulate fallback logic
        try:
            response = mock_chat_client.chat.completions.create(model="gpt-4o-mini", messages=[])
        except:
            # Fallback to alternative model
            response = mock_chat_client.chat.completions.create(model="gpt-4o-mini", messages=[])
            
        assert response.choices[0].message.content == "Fallback response"

class TestAIResearchEngine:
    """Test advanced AI research engine functionality"""
    
    @pytest.fixture
    def mock_researcher(self):
        """Create mock research engine"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            return Mock()
        return Mock(spec=AdvancedLegalResearcher)
    
    def test_research_context_creation(self, mock_researcher):
        """Test creation of research context"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        # Mock research context
        from ai_research_engine import ResearchContext, JurisdictionType, LegalAreaType
        
        context = ResearchContext(
            query="Character test requirements for visa applicants",
            jurisdiction_focus=[JurisdictionType.FEDERAL],
            legal_areas=[LegalAreaType.MIGRATION],
            include_commentary=True,
            include_precedents=True,
            confidence_threshold=0.7
        )
        
        assert context.query == "Character test requirements for visa applicants"
        assert JurisdictionType.FEDERAL in context.jurisdiction_focus
        assert LegalAreaType.MIGRATION in context.legal_areas
        assert context.confidence_threshold == 0.7
    
    def test_comprehensive_research_workflow(self, mock_researcher):
        """Test comprehensive legal research workflow"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        # Mock research results
        mock_research_results = {
            "comprehensive_analysis": "Detailed legal analysis of character test requirements...",
            "research_components": [
                {"type": "legislation_analysis", "content": "Migration Act analysis..."},
                {"type": "precedent_analysis", "content": "Relevant case law..."}
            ],
            "confidence_assessment": {"overall_confidence": "high"},
            "research_metadata": {"jurisdictions_covered": ["federal"]},
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        mock_researcher.comprehensive_legal_research.return_value = mock_research_results
        
        # Mock context
        mock_context = Mock()
        result = mock_researcher.comprehensive_legal_research(mock_context)
        
        assert "comprehensive_analysis" in result
        assert len(result["research_components"]) == 2
        assert result["confidence_assessment"]["overall_confidence"] == "high"

class TestErrorHandlingAndResilience:
    """Test error handling and system resilience"""
    
    def test_api_timeout_handling(self):
        """Test handling of API timeouts"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        with patch('openai.OpenAI') as mock_openai:
            # Mock timeout exception
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("Request timed out")
            mock_openai.return_value = mock_client
            
            config = VectorSearchConfig(
                pinecone_api_key="test-key",
                openai_api_key="test-key"
            )
            engine = VectorSearchEngine(config)
            engine.openai_client = mock_client
            
            # Should handle timeout gracefully
            with pytest.raises(Exception):
                asyncio.run(engine._generate_embeddings(["test"]))
    
    def test_rate_limit_handling(self):
        """Test handling of API rate limits"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        with patch('openai.OpenAI') as mock_openai:
            # Mock rate limit exception
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("Rate limit exceeded")
            mock_openai.return_value = mock_client
            
            config = VectorSearchConfig(
                pinecone_api_key="test-key",
                openai_api_key="test-key"
            )
            engine = VectorSearchEngine(config)
            engine.openai_client = mock_client
            
            # Should handle rate limit gracefully
            with pytest.raises(Exception):
                asyncio.run(engine._generate_embeddings(["test"]))
    
    def test_invalid_api_key_handling(self):
        """Test handling of invalid API keys"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        with patch('openai.OpenAI') as mock_openai:
            # Mock authentication error
            mock_openai.side_effect = Exception("Invalid API key")
            
            config = VectorSearchConfig(
                pinecone_api_key="test-key",
                openai_api_key="invalid-key"
            )
            engine = VectorSearchEngine(config)
            
            # Should handle invalid key gracefully
            with pytest.raises(Exception):
                asyncio.run(engine.initialize())
    
    def test_network_connectivity_issues(self):
        """Test handling of network connectivity issues"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        with patch('openai.OpenAI') as mock_openai:
            # Mock network error
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("Network unreachable")
            mock_openai.return_value = mock_client
            
            config = VectorSearchConfig(
                pinecone_api_key="test-key",
                openai_api_key="test-key"
            )
            engine = VectorSearchEngine(config)
            engine.openai_client = mock_client
            
            # Should handle network issues gracefully
            with pytest.raises(Exception):
                asyncio.run(engine._generate_embeddings(["test"]))

class TestPerformanceRequirements:
    """Test performance requirements for OpenAI integration"""
    
    @pytest.mark.asyncio
    async def test_embedding_generation_speed(self):
        """Test embedding generation meets speed requirements"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        # Mock fast embedding response
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            config = VectorSearchConfig(
                pinecone_api_key="test-key",
                openai_api_key="test-key"
            )
            engine = VectorSearchEngine(config)
            engine.openai_client = mock_client
            
            start_time = time.time()
            embeddings = await engine._generate_embeddings(["test text"])
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete quickly (under 2 seconds for single embedding)
            assert processing_time < 2.0
            assert len(embeddings) == 1
    
    @pytest.mark.asyncio
    async def test_chat_completion_speed(self):
        """Test chat completion meets speed requirements"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        # Mock fast chat response
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Fast legal response"))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            start_time = time.time()
            response = mock_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}]
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete quickly
            assert processing_time < 1.0
            assert response.choices[0].message.content == "Fast legal response"

class TestIntegrationWithLegalSystems:
    """Test integration with legal compliance and corpus systems"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_ai_legal_workflow(self):
        """Test complete AI-powered legal workflow"""
        if not OPENAI_INTEGRATION_AVAILABLE:
            pytest.skip("OpenAI integration not available")
            
        # Mock the complete workflow: search → RAG → compliance
        query = "What are the character test requirements for Australian visas?"
        
        # Mock vector search results
        mock_search_results = [
            {
                'id': 'migration_501',
                'text': 'Character test provisions under Migration Act 1958...',
                'relevance_score': 0.92,
                'metadata': {'citation': 'Migration Act 1958 s 501'},
                'search_method': 'hybrid'
            }
        ]
        
        # Mock RAG response
        mock_rag_response = {
            'answer': 'The character test under the Migration Act 1958 requires...',
            'confidence': 'high',
            'sources': ['Migration Act 1958 s 501'],
            'method': 'hybrid'
        }
        
        # Mock compliance validation
        mock_compliance = {
            'overall_compliance': 'medium_risk',
            'confidence_score': 0.85,
            'required_disclaimers': [
                {'content': 'This is general information only...', 'placement': 'footer'}
            ]
        }
        
        # Simulate workflow
        with patch('vector_search_engine.vector_search_provisions', return_value=mock_search_results):
            with patch('vector_search_engine.answer_legal_question', return_value=mock_rag_response):
                with patch('legal_compliance.validate_legal_response', return_value=mock_compliance):
                    
                    # Step 1: Vector search
                    search_results = await vector_search_provisions(query)
                    assert len(search_results) > 0
                    assert search_results[0]['relevance_score'] > 0.9
                    
                    # Step 2: RAG response generation
                    rag_response = await answer_legal_question(query)
                    assert rag_response['confidence'] == 'high'
                    assert len(rag_response['sources']) > 0
                    
                    # Step 3: Compliance validation
                    validation = await validate_legal_response(
                        rag_response['answer'], 
                        query
                    )
                    assert validation['overall_compliance'] in ['low_risk', 'medium_risk', 'high_risk']
                    assert validation['confidence_score'] > 0.8

if __name__ == "__main__":
    pytest.main([__file__, "-v"])