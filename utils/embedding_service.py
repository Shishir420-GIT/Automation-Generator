import streamlit as st
import google.generativeai as genai
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

class GeminiEmbeddingService:
    """
    Service for generating embeddings using Google's Gemini API
    Handles text embeddings for semantic search functionality
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini API
        try:
            if not api_key:
                api_key = st.secrets.get("API_KEY")
            
            if not api_key:
                raise ValueError("Gemini API key not found in secrets")
            
            genai.configure(api_key=api_key)
            self.logger.info("Gemini Embedding Service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini Embedding Service: {e}")
            raise e
    
    def generate_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Generate embedding for a single text using Gemini
        
        Args:
            text: Text to generate embedding for
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of float values representing the embedding vector
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for embedding generation")
            return []
        
        try:
            # Clean and prepare text
            clean_text = self._prepare_text(text)
            
            # Generate embedding with retry logic
            for attempt in range(max_retries):
                try:
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=clean_text,
                        task_type="retrieval_document"
                    )
                    
                    if result and 'embedding' in result:
                        embedding = result['embedding']
                        self.logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                        return embedding
                    else:
                        self.logger.warning(f"No embedding in result: {result}")
                        
                except Exception as retry_error:
                    self.logger.warning(f"Embedding generation attempt {attempt + 1} failed: {retry_error}")
                    if attempt < max_retries - 1:
                        time.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        raise retry_error
            
            return []
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed after {max_retries} attempts: {e}")
            return []
    
    def generate_query_embedding(self, query: str, max_retries: int = 3) -> List[float]:
        """
        Generate embedding specifically optimized for search queries
        
        Args:
            query: Search query text
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of float values representing the query embedding vector
        """
        if not query or not query.strip():
            self.logger.warning("Empty query provided for embedding generation")
            return []
        
        try:
            # Clean query
            clean_query = query.strip()[:1000]  # Limit query length
            
            # Generate query embedding with retry logic
            for attempt in range(max_retries):
                try:
                    result = genai.embed_content(
                        model="models/embedding-001",
                        content=clean_query,
                        task_type="retrieval_query"
                    )
                    
                    if result and 'embedding' in result:
                        embedding = result['embedding']
                        self.logger.debug(f"Generated query embedding with {len(embedding)} dimensions")
                        return embedding
                    else:
                        self.logger.warning(f"No embedding in query result: {result}")
                        
                except Exception as retry_error:
                    self.logger.warning(f"Query embedding attempt {attempt + 1} failed: {retry_error}")
                    if attempt < max_retries - 1:
                        time.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        raise retry_error
            
            return []
            
        except Exception as e:
            self.logger.error(f"Query embedding generation failed after {max_retries} attempts: {e}")
            return []
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 5) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with rate limiting
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        total_texts = len(texts)
        
        self.logger.info(f"Starting batch embedding generation for {total_texts} texts")
        
        # Process in batches to avoid rate limits
        for i in range(0, total_texts, batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for j, text in enumerate(batch):
                embedding = self.generate_embedding(text)
                batch_embeddings.append(embedding)
                
                # Progress logging
                current = i + j + 1
                if current % 10 == 0 or current == total_texts:
                    self.logger.info(f"Processed {current}/{total_texts} embeddings")
                
                # Rate limiting - small delay between requests
                if j < len(batch) - 1:
                    time.sleep(0.1)
            
            all_embeddings.extend(batch_embeddings)
            
            # Delay between batches
            if i + batch_size < total_texts:
                time.sleep(1)
        
        self.logger.info(f"Completed batch embedding generation: {len(all_embeddings)} embeddings")
        return all_embeddings
    
    def _prepare_text(self, text: str) -> str:
        """
        Prepare text for embedding generation
        
        Args:
            text: Raw text input
            
        Returns:
            Cleaned and prepared text
        """
        if not text:
            return ""
        
        # Clean text
        clean_text = text.strip()
        
        # Remove excessive whitespace
        import re
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Truncate to model limits (Gemini embedding model handles ~2048 tokens)
        # Approximate: 1 token ≈ 4 characters, so ~8000 characters max
        max_chars = 7000
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "..."
            self.logger.debug(f"Text truncated to {max_chars} characters")
        
        return clean_text
    
    def create_combined_text_for_embedding(self, solution_data: Dict[str, Any]) -> str:
        """
        Create optimized combined text from solution data for better embeddings
        
        Args:
            solution_data: Dictionary containing solution fields
            
        Returns:
            Combined text optimized for embedding generation
        """
        components = []
        
        # Add domain with emphasis
        domain = solution_data.get('domain', '').strip()
        if domain:
            components.append(f"Domain: {domain}")
        
        # Add summary (most important for search)
        summary = solution_data.get('summary', '').strip()
        if summary:
            components.append(f"Summary: {summary}")
        
        # Add prerequisites (important for matching requirements)
        prerequisites = solution_data.get('prerequisites', '').strip()
        if prerequisites:
            components.append(f"Prerequisites: {prerequisites}")
        
        # Add extra info
        extra_info = solution_data.get('extra_info', '').strip()
        if extra_info:
            components.append(f"Additional Information: {extra_info}")
        
        # Add script context (brief overview only)
        script = solution_data.get('script', '').strip()
        if script:
            # Extract just the first few lines or comments for context
            script_lines = script.split('\n')[:5]  # First 5 lines
            script_preview = '\n'.join(script_lines)
            components.append(f"Script Context: {script_preview}")
        
        combined = '\n\n'.join(components)
        return self._prepare_text(combined)
    
    def test_embedding_service(self) -> Dict[str, Any]:
        """
        Test the embedding service functionality
        
        Returns:
            Dictionary with test results
        """
        test_results = {
            "service_initialized": False,
            "document_embedding": False,
            "query_embedding": False,
            "embedding_dimensions": 0,
            "test_timestamp": datetime.now(),
            "errors": []
        }
        
        try:
            # Test service initialization
            test_results["service_initialized"] = True
            
            # Test document embedding
            test_text = "This is a test automation for web scraping using Python and Selenium"
            doc_embedding = self.generate_embedding(test_text)
            
            if doc_embedding:
                test_results["document_embedding"] = True
                test_results["embedding_dimensions"] = len(doc_embedding)
            else:
                test_results["errors"].append("Failed to generate document embedding")
            
            # Test query embedding
            test_query = "python web scraping automation"
            query_embedding = self.generate_query_embedding(test_query)
            
            if query_embedding:
                test_results["query_embedding"] = True
            else:
                test_results["errors"].append("Failed to generate query embedding")
            
            self.logger.info("Embedding service test completed successfully")
            
        except Exception as e:
            error_msg = f"Embedding service test failed: {e}"
            test_results["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return test_results