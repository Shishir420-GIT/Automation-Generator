"""
Embedding service for Automation Generator
Adapted from original embedding_service.py to work with package configuration
"""

import os
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

import google.generativeai as genai

from ..core.config_manager import ConfigManager


class GeminiEmbeddingService:
    """
    Service for generating embeddings using Google's Gemini API
    Handles text embeddings for semantic search functionality
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Configuration manager
        self.config_manager = config_manager or ConfigManager()
        
        # Initialize Gemini API
        try:
            if not api_key:
                api_key = self.config_manager.get("llm.api_key")
            
            if not api_key:
                raise ValueError("Gemini API key not found in configuration")
            
            # Handle environment variables
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                api_key = os.environ.get(env_var)
                if not api_key:
                    raise ValueError(f"Environment variable {env_var} not set")
            
            genai.configure(api_key=api_key)
            
            # Test the API key
            self._test_api_connection()
            
            self.logger.info("Gemini Embedding Service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini Embedding Service: {e}")
            raise e
    
    def _test_api_connection(self) -> None:
        """Test API connection with a simple embedding request"""
        try:
            # Use the embedding model to test connection
            test_text = "test connection"
            model = "models/embedding-001"
            
            result = genai.embed_content(
                model=model,
                content=test_text,
                task_type="SEMANTIC_SIMILARITY"
            )
            
            if not result or not result.get('embedding'):
                raise ValueError("API test failed - no embedding returned")
            
            self.logger.info("API connection test successful")
            
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            raise
    
    def generate_embeddings(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> Optional[List[float]]:
        """
        Generate embeddings for given text using Gemini API
        
        Args:
            text: Text to generate embeddings for
            task_type: Type of task ('SEMANTIC_SIMILARITY', 'CLASSIFICATION', 'CLUSTERING')
            
        Returns:
            List of float values representing the embedding vector
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for embedding generation")
            return None
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text_for_embedding(text)
            
            if len(cleaned_text) > 20000:  # Gemini embedding limit
                self.logger.warning(f"Text too long ({len(cleaned_text)} chars), truncating")
                cleaned_text = cleaned_text[:19900] + "..."
            
            # Generate embedding using Gemini
            model = "models/embedding-001"
            
            result = genai.embed_content(
                model=model,
                content=cleaned_text,
                task_type=task_type
            )
            
            if not result or not result.get('embedding'):
                raise ValueError("No embedding returned from API")
            
            embeddings = result['embedding']
            
            self.logger.debug(f"Generated embedding vector of length {len(embeddings)}")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {str(e)}")
            return None
    
    def generate_batch_embeddings(self, texts: List[str], 
                                task_type: str = "SEMANTIC_SIMILARITY",
                                batch_size: int = 10) -> Dict[int, Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to generate embeddings for
            task_type: Type of task for embedding generation
            batch_size: Number of texts to process in each batch
            
        Returns:
            Dictionary mapping text index to embedding vector
        """
        embeddings_dict = {}
        
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_start_time = time.time()
                
                self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                
                for j, text in enumerate(batch):
                    text_index = i + j
                    embeddings = self.generate_embeddings(text, task_type)
                    embeddings_dict[text_index] = embeddings
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                
                batch_time = time.time() - batch_start_time
                self.logger.info(f"Batch processed in {batch_time:.2f} seconds")
                
                # Longer delay between batches to avoid rate limiting
                if i + batch_size < len(texts):
                    time.sleep(1)
            
            success_count = sum(1 for emb in embeddings_dict.values() if emb is not None)
            self.logger.info(f"Successfully generated embeddings for {success_count}/{len(texts)} texts")
            
            return embeddings_dict
            
        except Exception as e:
            self.logger.error(f"Batch embedding generation failed: {str(e)}")
            return embeddings_dict
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embedding vectors
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        try:
            # Ensure same dimensions
            if len(embedding1) != len(embedding2):
                self.logger.error("Embedding vectors have different dimensions")
                return 0.0
            
            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
            magnitude1 = sum(a * a for a in embedding1) ** 0.5
            magnitude2 = sum(b * b for b in embedding2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            similarity = dot_product / (magnitude1 * magnitude2)
            return similarity
            
        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: Dict[Any, List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """
        Find most similar embeddings to a query embedding
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: Dictionary of candidate embeddings with identifiers
            top_k: Number of top similar results to return
            
        Returns:
            List of tuples (identifier, similarity_score) sorted by similarity
        """
        try:
            similarities = []
            
            for identifier, candidate_embedding in candidate_embeddings.items():
                if candidate_embedding is not None:
                    similarity = self.calculate_similarity(query_embedding, candidate_embedding)
                    similarities.append((identifier, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            self.logger.error(f"Similar embedding search failed: {str(e)}")
            return []
    
    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean and prepare text for embedding generation"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = ' '.join(text.split())
        
        # Remove or replace problematic characters
        cleaned = cleaned.replace('\x00', ' ')  # Remove null characters
        cleaned = cleaned.replace('\ufeff', '')  # Remove BOM
        
        # Ensure text is not too short
        if len(cleaned.strip()) < 10:
            cleaned = f"Document content: {cleaned}"
        
        return cleaned.strip()
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding service"""
        try:
            # Test embedding to get vector dimensions
            test_embedding = self.generate_embeddings("test text")
            
            stats = {
                "service_name": "Gemini Embedding Service",
                "model": "models/embedding-001",
                "api_available": test_embedding is not None,
                "vector_dimensions": len(test_embedding) if test_embedding else None,
                "max_text_length": 20000,
                "supported_task_types": ["SEMANTIC_SIMILARITY", "CLASSIFICATION", "CLUSTERING"]
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get embedding stats: {str(e)}")
            return {
                "service_name": "Gemini Embedding Service",
                "api_available": False,
                "error": str(e)
            }