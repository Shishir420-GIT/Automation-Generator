"""
Migration 003: Add vector search capabilities
Adds vector search index and embedding fields
"""

from pymongo.errors import OperationFailure
from ..base_migration import BaseMigration


class Migration003(BaseMigration):
    """Add vector search capabilities"""
    
    version = "003"
    description = "Add vector search index and embedding fields"
    
    def up(self) -> bool:
        """Create vector search indexes and add embedding fields"""
        try:
            self.logger.info("Adding vector search capabilities...")
            
            solutions_collection = self.db.collection
            
            # Add embeddings field to existing solutions
            result = solutions_collection.update_many(
                {"embeddings": {"$exists": False}},
                {
                    "$set": {
                        "embeddings": None,
                        "embeddings_generated_at": None,
                        "vector_search_enabled": False
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Added embedding fields to {result.modified_count} existing solutions")
            
            # Note: Vector search index creation requires MongoDB Atlas
            # This will be handled by the vector admin tools in production
            
            try:
                # Try to create a vector search index
                # This will only work on MongoDB Atlas with vector search enabled
                vector_index_definition = {
                    "definition": {
                        "fields": [
                            {
                                "type": "vector",
                                "path": "embeddings",
                                "numDimensions": 768,  # Gemini embedding dimensions
                                "similarity": "cosine"
                            }
                        ]
                    }
                }
                
                # This is a placeholder - actual vector index creation requires Atlas admin API
                self.logger.info("Vector search index definition prepared (requires Atlas configuration)")
                
            except Exception as e:
                self.logger.warning(f"Vector search index creation skipped: {e}")
                # This is expected for non-Atlas deployments
            
            # Create regular index on embeddings field for housekeeping
            try:
                solutions_collection.create_index([("embeddings", 1)], sparse=True)
                solutions_collection.create_index([("vector_search_enabled", 1)])
                self.logger.info("Created supporting indexes for vector search")
            except OperationFailure as e:
                if "already exists" not in str(e):
                    raise
            
            # Update schema info
            solutions_collection.update_one(
                {"_id": "schema_info"},
                {
                    "$set": {
                        "version": "1.2",
                        "features": ["solutions", "ratings", "vector_search"],
                        "vector_search": {
                            "enabled": True,
                            "embedding_model": "gemini-embedding-001",
                            "dimensions": 768
                        },
                        "last_updated": "2024-01-03T00:00:00Z"
                    }
                },
                upsert=True
            )
            
            self.logger.info("Vector search setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add vector search: {e}")
            return False
    
    def down(self) -> bool:
        """Rollback vector search capabilities"""
        try:
            self.logger.info("Rolling back vector search capabilities...")
            
            solutions_collection = self.db.collection
            
            # Remove embedding fields from solutions
            solutions_collection.update_many(
                {},
                {
                    "$unset": {
                        "embeddings": "",
                        "embeddings_generated_at": "",
                        "vector_search_enabled": ""
                    }
                }
            )
            
            # Drop vector-related indexes
            try:
                solutions_collection.drop_index("embeddings_1")
                solutions_collection.drop_index("vector_search_enabled_1")
                self.logger.info("Dropped vector search indexes")
            except OperationFailure:
                pass  # Indexes might not exist
            
            # Revert schema info
            solutions_collection.update_one(
                {"_id": "schema_info"},
                {
                    "$set": {
                        "version": "1.1",
                        "features": ["solutions", "ratings"]
                    },
                    "$unset": {
                        "vector_search": ""
                    }
                }
            )
            
            self.logger.info("Vector search rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback vector search: {e}")
            return False
    
    def validate(self) -> bool:
        """Validate vector search was set up correctly"""
        try:
            solutions_collection = self.db.collection
            
            # Check that schema info has vector search feature
            schema_info = solutions_collection.find_one({"_id": "schema_info"})
            if not schema_info:
                self.logger.error("Schema info document not found")
                return False
            
            features = schema_info.get("features", [])
            if "vector_search" not in features:
                self.logger.error("Vector search not listed in schema features")
                return False
            
            # Check that solutions have embedding fields
            sample_solution = solutions_collection.find_one({
                "_id": {"$ne": "schema_info"},
                "embeddings": {"$exists": True}
            })
            
            if not sample_solution:
                # Check if there are any non-schema documents
                non_schema_count = solutions_collection.count_documents({"_id": {"$ne": "schema_info"}})
                if non_schema_count > 0:
                    self.logger.error("Solutions missing embedding fields")
                    return False
                else:
                    self.logger.info("No solutions to validate (empty collection)")
            
            # Check for supporting indexes
            index_names = [index['name'] for index in solutions_collection.list_indexes()]
            expected_indexes = ['embeddings_1', 'vector_search_enabled_1']
            
            for expected in expected_indexes:
                if expected not in index_names:
                    self.logger.warning(f"Missing expected index: {expected}")
            
            self.logger.info("Vector search validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Vector search validation failed: {e}")
            return False