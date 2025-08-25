"""
Vector Search Engine for Australian Legal Corpus
Integrates OpenAI embeddings with Pinecone vector database for semantic search
"""

import os
import json
import asyncio
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from enum import Enum

import openai
from openai import OpenAI
import pinecone
from pinecone import Pinecone, ServerlessSpec
import httpx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import existing corpus integration
from .legal_corpus import legal_corpus, get_corpus_stats

logger = logging.getLogger(__name__)

class SearchMethod(Enum):
    VECTOR_ONLY = "vector_only"
    HYBRID = "hybrid"
    BM25_FALLBACK = "bm25_fallback"

@dataclass
class VectorSearchConfig:
    pinecone_api_key: str
    pinecone_environment: str = "us-east1-aws"
    index_name: str = "auslex-legal-corpus"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    top_k: int = 10
    similarity_threshold: float = 0.75
    enable_hybrid_search: bool = True
    enable_metadata_filtering: bool = True

@dataclass 
class SearchResult:
    document_id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    search_method: SearchMethod
    embedding_score: Optional[float] = None
    bm25_score: Optional[float] = None
    hybrid_score: Optional[float] = None

class VectorSearchEngine:
    """
    Advanced vector search engine for Australian legal documents
    Combines OpenAI embeddings with Pinecone vector database
    """
    
    def __init__(self, config: VectorSearchConfig):
        self.config = config
        self.openai_client = None
        self.pinecone_client = None
        self.index = None
        self.is_initialized = False
        self.fallback_vectorizer = None
        self.fallback_matrix = None
        
    async def initialize(self, force_rebuild: bool = False):
        """Initialize vector search engine with OpenAI and Pinecone"""
        try:
            # Initialize OpenAI client
            self.openai_client = OpenAI(
                api_key=self.config.openai_api_key or os.getenv("OPENAI_API_KEY")
            )
            
            # Initialize Pinecone
            self.pinecone_client = Pinecone(
                api_key=self.config.pinecone_api_key or os.getenv("PINECONE_API_KEY")
            )
            
            # Create or connect to index
            await self._setup_pinecone_index(force_rebuild)
            
            # Initialize fallback search
            await self._setup_fallback_search()
            
            self.is_initialized = True
            logger.info("Vector search engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector search engine: {e}")
            # Fall back to existing TF-IDF search
            await self._initialize_fallback_only()
    
    async def _setup_pinecone_index(self, force_rebuild: bool = False):
        """Setup Pinecone index for legal documents"""
        index_name = self.config.index_name
        
        try:
            # Check if index exists
            existing_indexes = self.pinecone_client.list_indexes()
            index_exists = any(idx.name == index_name for idx in existing_indexes)
            
            if force_rebuild and index_exists:
                logger.info(f"Deleting existing index: {index_name}")
                self.pinecone_client.delete_index(index_name)
                index_exists = False
            
            if not index_exists:
                logger.info(f"Creating new Pinecone index: {index_name}")
                
                # Create index with serverless spec for cost efficiency
                self.pinecone_client.create_index(
                    name=index_name,
                    dimension=self.config.embedding_dimensions,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.config.pinecone_environment
                    )
                )
                
                # Wait for index to be ready
                import time
                while not self.pinecone_client.describe_index(index_name).status.ready:
                    time.sleep(1)
                
                logger.info(f"Index {index_name} created and ready")
            
            # Connect to index
            self.index = self.pinecone_client.Index(index_name)
            
            # Check if we need to populate the index
            stats = self.index.describe_index_stats()
            if stats.total_vector_count == 0 or force_rebuild:
                await self._populate_vector_index()
            
        except Exception as e:
            logger.error(f"Failed to setup Pinecone index: {e}")
            raise
    
    async def _populate_vector_index(self):
        """Populate Pinecone index with legal corpus embeddings"""
        logger.info("Starting vector index population...")
        
        # Initialize legal corpus if not already done
        if not legal_corpus.is_initialized:
            legal_corpus.initialize()
        
        if legal_corpus.corpus_df is None or len(legal_corpus.corpus_df) == 0:
            logger.warning("No corpus data available for vectorization")
            return
        
        # Process documents in batches
        batch_size = 100
        total_docs = len(legal_corpus.corpus_df)
        
        for batch_start in range(0, total_docs, batch_size):
            batch_end = min(batch_start + batch_size, total_docs)
            batch_df = legal_corpus.corpus_df.iloc[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start}-{batch_end} of {total_docs}")
            
            # Prepare texts for embedding
            texts = []
            metadatas = []
            ids = []
            
            for idx, row in batch_df.iterrows():
                # Combine citation and text for better search context
                text = f"{row.get('citation', '')} {row.get('text', '')}"
                texts.append(text)
                
                # Prepare metadata
                metadata = {
                    "citation": str(row.get('citation', '')),
                    "jurisdiction": str(row.get('jurisdiction', '')),
                    "type": str(row.get('type', '')),
                    "date": str(row.get('date', '')),
                    "url": str(row.get('url', '')),
                    "source": str(row.get('source', '')),
                    "version_id": str(row.get('version_id', '')),
                    "when_scraped": str(row.get('when_scraped', ''))
                }
                metadatas.append(metadata)
                ids.append(f"doc_{idx}")
            
            # Generate embeddings
            try:
                embeddings = await self._generate_embeddings(texts)
                
                # Prepare vectors for upsert
                vectors = [
                    {
                        "id": ids[i],
                        "values": embeddings[i],
                        "metadata": metadatas[i]
                    }
                    for i in range(len(texts))
                ]
                
                # Upsert to Pinecone
                self.index.upsert(vectors=vectors)
                
            except Exception as e:
                logger.error(f"Failed to process batch {batch_start}-{batch_end}: {e}")
                continue
        
        logger.info(f"Vector index population complete. Processed {total_docs} documents.")
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            # Split large texts to fit token limits
            processed_texts = [self._truncate_text(text, 8000) for text in texts]
            
            response = self.openai_client.embeddings.create(
                model=self.config.embedding_model,
                input=processed_texts
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """Truncate text to fit within token limits"""
        # Rough approximation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."
    
    async def _setup_fallback_search(self):
        """Setup fallback TF-IDF search using existing corpus"""
        try:
            if legal_corpus.vectorizer and legal_corpus.tfidf_matrix is not None:
                self.fallback_vectorizer = legal_corpus.vectorizer
                self.fallback_matrix = legal_corpus.tfidf_matrix
                logger.info("Fallback TF-IDF search initialized")
            else:
                logger.warning("No fallback search available")
        except Exception as e:
            logger.error(f"Failed to setup fallback search: {e}")
    
    async def _initialize_fallback_only(self):
        """Initialize with only fallback search (no vector capabilities)"""
        logger.info("Initializing with fallback search only")
        
        # Initialize legal corpus if not already done
        if not legal_corpus.is_initialized:
            legal_corpus.initialize()
        
        await self._setup_fallback_search()
        self.is_initialized = True
    
    async def search(
        self, 
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        search_method: SearchMethod = SearchMethod.HYBRID
    ) -> List[SearchResult]:
        """
        Perform semantic search with hybrid ranking
        """
        if not self.is_initialized:
            logger.warning("Search engine not initialized")
            return []
        
        try:
            # Try vector search first
            if self.index is not None and search_method != SearchMethod.BM25_FALLBACK:
                return await self._vector_search(query, filters, search_method)
            else:
                return await self._fallback_search(query)
                
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Fall back to TF-IDF search
            return await self._fallback_search(query)
    
    async def _vector_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        search_method: SearchMethod = SearchMethod.HYBRID
    ) -> List[SearchResult]:
        """Perform vector-based semantic search"""
        
        # Generate query embedding
        query_embeddings = await self._generate_embeddings([query])
        query_vector = query_embeddings[0]
        
        # Prepare filter conditions
        filter_dict = {}
        if filters and self.config.enable_metadata_filtering:
            for key, value in filters.items():
                if key in ["jurisdiction", "type", "source"]:
                    filter_dict[key] = {"$eq": value}
        
        # Query Pinecone
        search_params = {
            "vector": query_vector,
            "top_k": self.config.top_k,
            "include_metadata": True,
            "include_values": False
        }
        
        if filter_dict:
            search_params["filter"] = filter_dict
        
        query_response = self.index.query(**search_params)
        
        # Convert to SearchResult objects
        results = []
        for match in query_response.matches:
            if match.score >= self.config.similarity_threshold:
                # Get original document content
                doc_content = self._get_document_content(match.id)
                
                result = SearchResult(
                    document_id=match.id,
                    score=match.score,
                    content=doc_content,
                    metadata=match.metadata or {},
                    search_method=SearchMethod.VECTOR_ONLY,
                    embedding_score=match.score
                )
                results.append(result)
        
        # Apply hybrid scoring if requested
        if search_method == SearchMethod.HYBRID and self.fallback_vectorizer:
            results = await self._apply_hybrid_scoring(query, results)
        
        return results
    
    def _get_document_content(self, document_id: str) -> str:
        """Retrieve full document content by ID"""
        try:
            # Extract index from document ID
            doc_idx = int(document_id.replace("doc_", ""))
            
            if legal_corpus.corpus_df is not None and doc_idx < len(legal_corpus.corpus_df):
                row = legal_corpus.corpus_df.iloc[doc_idx]
                return str(row.get('text', ''))[:2000]  # Limit content length
            
            return "Content not available"
            
        except Exception as e:
            logger.error(f"Failed to retrieve content for {document_id}: {e}")
            return "Content not available"
    
    async def _apply_hybrid_scoring(
        self, 
        query: str, 
        vector_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Apply hybrid scoring combining vector and BM25 scores"""
        try:
            # Get BM25 scores using existing TF-IDF
            query_vector = self.fallback_vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.fallback_matrix).flatten()
            
            # Create mapping of document indices to BM25 scores
            bm25_scores = {}
            for idx, score in enumerate(similarities):
                bm25_scores[f"doc_{idx}"] = score
            
            # Update results with hybrid scoring
            for result in vector_results:
                bm25_score = bm25_scores.get(result.document_id, 0.0)
                
                # Combine scores (weighted average)
                vector_weight = 0.7
                bm25_weight = 0.3
                hybrid_score = (vector_weight * result.embedding_score) + (bm25_weight * bm25_score)
                
                result.bm25_score = bm25_score
                result.hybrid_score = hybrid_score
                result.score = hybrid_score  # Update primary score
                result.search_method = SearchMethod.HYBRID
            
            # Re-sort by hybrid score
            vector_results.sort(key=lambda x: x.hybrid_score or 0, reverse=True)
            
            return vector_results
            
        except Exception as e:
            logger.error(f"Failed to apply hybrid scoring: {e}")
            return vector_results
    
    async def _fallback_search(self, query: str) -> List[SearchResult]:
        """Fallback to TF-IDF search when vector search is unavailable"""
        
        if not self.fallback_vectorizer or self.fallback_matrix is None:
            logger.warning("No fallback search available")
            return []
        
        try:
            # Use existing corpus search
            corpus_results = legal_corpus.search_provisions(query, self.config.top_k)
            
            # Convert to SearchResult format
            results = []
            for idx, corpus_result in enumerate(corpus_results):
                result = SearchResult(
                    document_id=corpus_result.get('id', f'fallback_{idx}'),
                    score=corpus_result.get('relevance_score', 0.0),
                    content=corpus_result.get('text', ''),
                    metadata=corpus_result.get('metadata', {}),
                    search_method=SearchMethod.BM25_FALLBACK
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []

class AdvancedLegalRAG:
    """
    Retrieval-Augmented Generation system for legal queries
    Combines vector search with GPT-4 for accurate legal analysis
    """
    
    def __init__(self, search_engine: VectorSearchEngine):
        self.search_engine = search_engine
        self.openai_client = search_engine.openai_client
    
    async def answer_legal_query(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive legal answer using RAG"""
        
        # Retrieve relevant documents
        search_results = await self.search_engine.search(query, filters)
        
        if not search_results:
            return {
                "answer": "I couldn't find relevant legal information for your query. Please try rephrasing your question or contact a legal professional.",
                "confidence": "low",
                "sources": [],
                "method": "fallback"
            }
        
        # Prepare context for GPT-4
        context_documents = []
        citations = []
        
        for result in search_results[:5]:  # Use top 5 results
            context_documents.append({
                "content": result.content,
                "metadata": result.metadata,
                "relevance_score": result.score
            })
            
            if include_citations:
                citation = result.metadata.get('citation', 'Unknown citation')
                if citation not in citations:
                    citations.append(citation)
        
        # Generate response using GPT-4
        response = await self._generate_rag_response(query, context_documents)
        
        return {
            "answer": response,
            "confidence": self._assess_confidence(search_results),
            "sources": citations if include_citations else [],
            "method": search_results[0].search_method.value,
            "documents_used": len(context_documents)
        }
    
    async def _generate_rag_response(
        self, 
        query: str, 
        context_documents: List[Dict[str, Any]]
    ) -> str:
        """Generate response using retrieved context"""
        
        # Format context
        context_text = "\n\n".join([
            f"Document {i+1} (Relevance: {doc['relevance_score']:.2f}):\n{doc['content']}"
            for i, doc in enumerate(context_documents)
        ])
        
        system_prompt = """You are an expert Australian legal assistant. Use the provided legal documents to answer the user's question accurately and comprehensively.

IMPORTANT GUIDELINES:
1. Base your answer primarily on the provided documents
2. Cite specific legislation, cases, or provisions when relevant
3. Clearly distinguish between established law and commentary
4. Note any limitations or areas requiring professional legal advice
5. If the documents don't fully answer the question, acknowledge this
6. Use clear, accessible language while maintaining legal accuracy

Always include a disclaimer that this is general information only and not legal advice."""
        
        user_prompt = f"""
Query: {query}

Relevant Legal Documents:
{context_text}

Please provide a comprehensive answer based on the provided documents.
"""
        
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=2000
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            return "I apologize, but I encountered an error generating a response. Please try again or consult with a legal professional."
    
    def _assess_confidence(self, search_results: List[SearchResult]) -> str:
        """Assess confidence level based on search results"""
        if not search_results:
            return "low"
        
        # Consider top result score and number of results
        top_score = search_results[0].score
        result_count = len(search_results)
        
        if top_score >= 0.8 and result_count >= 3:
            return "high"
        elif top_score >= 0.6 and result_count >= 2:
            return "medium"
        else:
            return "low"

# Configuration and initialization
def create_vector_search_config() -> VectorSearchConfig:
    """Create vector search configuration from environment variables"""
    return VectorSearchConfig(
        pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
        pinecone_environment=os.getenv("PINECONE_ENVIRONMENT", "us-east1-aws"),
        index_name=os.getenv("PINECONE_INDEX_NAME", "auslex-legal-corpus"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
        top_k=int(os.getenv("SEARCH_TOP_K", "10")),
        similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.75")),
        enable_hybrid_search=os.getenv("ENABLE_HYBRID_SEARCH", "true").lower() == "true",
        enable_metadata_filtering=os.getenv("ENABLE_METADATA_FILTERING", "true").lower() == "true"
    )

# Global instances
_vector_config = None
_vector_engine = None
_legal_rag = None

async def get_vector_search_engine() -> VectorSearchEngine:
    """Get or create vector search engine singleton"""
    global _vector_config, _vector_engine
    
    if _vector_engine is None:
        _vector_config = create_vector_search_config()
        _vector_engine = VectorSearchEngine(_vector_config)
        await _vector_engine.initialize()
    
    return _vector_engine

async def get_legal_rag() -> AdvancedLegalRAG:
    """Get or create RAG system singleton"""
    global _legal_rag
    
    if _legal_rag is None:
        search_engine = await get_vector_search_engine()
        _legal_rag = AdvancedLegalRAG(search_engine)
    
    return _legal_rag

# Export main functions
async def vector_search_provisions(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    search_method: SearchMethod = SearchMethod.HYBRID
) -> List[Dict[str, Any]]:
    """Search legal provisions using vector similarity"""
    engine = await get_vector_search_engine()
    results = await engine.search(query, filters, search_method)
    
    # Convert to dict format for API compatibility
    return [
        {
            "id": result.document_id,
            "text": result.content,
            "relevance_score": result.score,
            "metadata": result.metadata,
            "search_method": result.search_method.value,
            "embedding_score": result.embedding_score,
            "bm25_score": result.bm25_score,
            "hybrid_score": result.hybrid_score
        }
        for result in results
    ]

async def answer_legal_question(
    query: str,
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Answer legal question using RAG system"""
    rag = await get_legal_rag()
    return await rag.answer_legal_query(query, filters)