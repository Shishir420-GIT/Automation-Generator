"""
MongoDB integration for Automation Generator
Adapted from original MongoDBFunctions.py to work with package configuration
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

from ..utils.embedding_service import GeminiEmbeddingService
from .config_manager import ConfigManager


class MongoDB:
    """MongoDB database operations for Automation Generator"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Configuration manager
        self.config_manager = config_manager or ConfigManager()
        
        # Initialize database connection with error handling
        self._initialize_connection()
        
        # Initialize embedding service
        self._initialize_embedding_service()
    
    def _initialize_connection(self):
        """Initialize MongoDB connection with proper error handling"""
        try:
            mongo_uri = self.config_manager.get("database.mongodb_uri")
            if not mongo_uri:
                raise ValueError("MongoDB URI not found in configuration")
            
            # Handle environment variables
            if mongo_uri.startswith("${") and mongo_uri.endswith("}"):
                env_var = mongo_uri[2:-1]
                mongo_uri = os.environ.get(env_var)
                if not mongo_uri:
                    raise ValueError(f"Environment variable {env_var} not set")
            
            # Initialize client with timeout settings
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database and collections
            db_name = self.config_manager.get("database.database_name", "automation_generator")
            self.db = self.client[db_name]
            
            collections = self.config_manager.get("database.collections", {})
            self.collection = self.db[collections.get("solutions", "solutions")]
            self.ratings_collection = self.db[collections.get("ratings", "ratings")]
            self.users_collection = self.db[collections.get("users", "users")]
            self.analytics_collection = self.db[collections.get("analytics", "analytics")]
            
            self.logger.info("MongoDB connection initialized successfully")
            
        except ServerSelectionTimeoutError as e:
            self.logger.error(f"MongoDB connection timeout: {str(e)}")
            raise ConnectionError("Unable to connect to MongoDB. Please check your connection and URI.")
            
        except ConnectionFailure as e:
            self.logger.error(f"MongoDB connection failed: {str(e)}")
            raise ConnectionError(f"MongoDB connection failed: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error initializing MongoDB: {str(e)}")
            raise
    
    def _initialize_embedding_service(self):
        """Initialize Gemini embedding service for vector search"""
        try:
            self.embedding_service = GeminiEmbeddingService(self.config_manager)
            self.vector_search_enabled = True
            self.logger.info("Vector search enabled with Gemini embeddings")
            
        except Exception as e:
            self.logger.warning(f"Vector search disabled - embedding service failed: {e}")
            self.embedding_service = None
            self.vector_search_enabled = False
    
    def _handle_db_error(self, error: Exception, operation: str) -> None:
        """Handle database errors gracefully"""
        error_msg = str(error).lower()
        
        # Log the error
        self.logger.error(f"Database error during {operation}: {error_msg}")
        
        # Re-raise with more context
        if any(keyword in error_msg for keyword in ['connection', 'timeout', 'network']):
            raise ConnectionError(f"Database connection error during {operation}")
        elif any(keyword in error_msg for keyword in ['auth', 'credential', 'permission']):
            raise PermissionError(f"Database authentication error during {operation}")
        else:
            raise RuntimeError(f"Database error during {operation}: {str(error)}")
    
    def save_solution(self, solution_data: Dict[str, Any]) -> Optional[str]:
        """Save automation solution to database"""
        try:
            # Add metadata
            solution_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "version": "2.0"
            })
            
            # Generate embeddings if vector search is enabled
            if self.vector_search_enabled and 'sop_text' in solution_data:
                try:
                    embeddings = self.embedding_service.generate_embeddings(solution_data['sop_text'])
                    solution_data['embeddings'] = embeddings
                    self.logger.info("Generated embeddings for solution")
                except Exception as e:
                    self.logger.warning(f"Failed to generate embeddings: {e}")
            
            # Insert solution
            result = self.collection.insert_one(solution_data)
            solution_id = str(result.inserted_id)
            
            self.logger.info(f"Solution saved successfully with ID: {solution_id}")
            return solution_id
            
        except Exception as e:
            self._handle_db_error(e, "saving solution")
            return None
    
    def get_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific solution by ID"""
        try:
            from bson import ObjectId
            
            solution = self.collection.find_one({"_id": ObjectId(solution_id)})
            
            if solution:
                # Convert ObjectId to string for JSON serialization
                solution['_id'] = str(solution['_id'])
                self.logger.info(f"Retrieved solution: {solution_id}")
                return solution
            else:
                self.logger.warning(f"Solution not found: {solution_id}")
                return None
                
        except Exception as e:
            self._handle_db_error(e, "retrieving solution")
            return None
    
    def search_solutions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search solutions using text search or vector search"""
        try:
            solutions = []
            
            # Try vector search first if available
            if self.vector_search_enabled and query.strip():
                try:
                    solutions = self._vector_search(query, limit)
                    if solutions:
                        self.logger.info(f"Vector search returned {len(solutions)} results")
                        return solutions
                except Exception as e:
                    self.logger.warning(f"Vector search failed, falling back to text search: {e}")
            
            # Fallback to text search
            solutions = self._text_search(query, limit)
            self.logger.info(f"Text search returned {len(solutions)} results")
            return solutions
            
        except Exception as e:
            self._handle_db_error(e, "searching solutions")
            return []
    
    def _vector_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform vector-based similarity search"""
        if not self.embedding_service:
            return []
        
        try:
            # Generate query embeddings
            query_embeddings = self.embedding_service.generate_embeddings(query)
            
            # MongoDB Atlas Vector Search pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embeddings", 
                        "queryVector": query_embeddings,
                        "numCandidates": limit * 10,
                        "limit": limit
                    }
                },
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "domain": 1,
                        "sop_text": 1,
                        "script_content": 1,
                        "script_type": 1,
                        "created_at": 1,
                        "rating": {"$ifNull": ["$rating", 0]},
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            return []
    
    def _text_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform text-based search"""
        try:
            # Create text search query
            search_filter = {
                "$or": [
                    {"domain": {"$regex": query, "$options": "i"}},
                    {"sop_text": {"$regex": query, "$options": "i"}},
                    {"script_content": {"$regex": query, "$options": "i"}}
                ]
            }
            
            # Execute search
            cursor = self.collection.find(search_filter).limit(limit).sort("created_at", -1)
            
            results = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                results.append(doc)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Text search error: {e}")
            return []
    
    def get_recent_solutions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently created solutions"""
        try:
            cursor = self.collection.find().limit(limit).sort("created_at", -1)
            
            solutions = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                solutions.append(doc)
            
            self.logger.info(f"Retrieved {len(solutions)} recent solutions")
            return solutions
            
        except Exception as e:
            self._handle_db_error(e, "retrieving recent solutions")
            return []
    
    def save_rating(self, solution_id: str, rating: int, feedback: str = "") -> bool:
        """Save user rating for a solution"""
        try:
            rating_data = {
                "solution_id": solution_id,
                "rating": rating,
                "feedback": feedback,
                "created_at": datetime.utcnow()
            }
            
            # Save rating
            self.ratings_collection.insert_one(rating_data)
            
            # Update solution with average rating
            self._update_solution_rating(solution_id)
            
            self.logger.info(f"Rating saved for solution {solution_id}: {rating}")
            return True
            
        except Exception as e:
            self._handle_db_error(e, "saving rating")
            return False
    
    def _update_solution_rating(self, solution_id: str) -> None:
        """Update solution with calculated average rating"""
        try:
            # Calculate average rating
            pipeline = [
                {"$match": {"solution_id": solution_id}},
                {"$group": {
                    "_id": "$solution_id",
                    "avg_rating": {"$avg": "$rating"},
                    "rating_count": {"$sum": 1}
                }}
            ]
            
            result = list(self.ratings_collection.aggregate(pipeline))
            
            if result:
                avg_rating = result[0]['avg_rating']
                rating_count = result[0]['rating_count']
                
                from bson import ObjectId
                self.collection.update_one(
                    {"_id": ObjectId(solution_id)},
                    {"$set": {
                        "avg_rating": round(avg_rating, 1),
                        "rating_count": rating_count,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                self.logger.info(f"Updated average rating for solution {solution_id}: {avg_rating}")
                
        except Exception as e:
            self.logger.error(f"Error updating solution rating: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "total_solutions": self.collection.count_documents({}),
                "total_ratings": self.ratings_collection.count_documents({}),
                "database_name": self.db.name,
                "vector_search_enabled": self.vector_search_enabled,
                "collections": {
                    "solutions": self.collection.name,
                    "ratings": self.ratings_collection.name
                }
            }
            
            # Get recent activity
            recent_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            stats["solutions_today"] = self.collection.count_documents({
                "created_at": {"$gte": recent_date}
            })
            
            self.logger.info("Database statistics retrieved successfully")
            return stats
            
        except Exception as e:
            self._handle_db_error(e, "retrieving database stats")
            return {}
    
    def close_connection(self):
        """Close database connection"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
                self.logger.info("MongoDB connection closed")
        except Exception as e:
            self.logger.error(f"Error closing MongoDB connection: {e}")