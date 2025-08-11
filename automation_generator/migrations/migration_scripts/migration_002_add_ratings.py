"""
Migration 002: Add ratings collection and functionality
Creates ratings collection with proper indexes
"""

from pymongo.errors import OperationFailure
from ..base_migration import BaseMigration


class Migration002(BaseMigration):
    """Add ratings collection and functionality"""
    
    version = "002" 
    description = "Add ratings collection with indexes"
    
    def up(self) -> bool:
        """Create ratings collection and indexes"""
        try:
            self.logger.info("Adding ratings collection...")
            
            # Create ratings collection with indexes
            ratings_collection = self.db.ratings_collection
            
            # Create indexes for ratings
            indexes = [
                ("solution_id", 1),
                ("rating", 1),
                ("created_at", -1),
                [("solution_id", 1), ("created_at", -1)]  # Compound index
            ]
            
            for index_spec in indexes:
                try:
                    if isinstance(index_spec, list):
                        ratings_collection.create_index(index_spec)
                        self.logger.info(f"Created compound index: {index_spec}")
                    else:
                        ratings_collection.create_index([(index_spec[0], index_spec[1])])
                        self.logger.info(f"Created index on {index_spec[0]}")
                except OperationFailure as e:
                    if "already exists" not in str(e):
                        raise
            
            # Add rating fields to existing solutions (if any)
            solutions_collection = self.db.collection
            
            # Update solutions without rating fields
            result = solutions_collection.update_many(
                {"avg_rating": {"$exists": False}},
                {
                    "$set": {
                        "avg_rating": 0,
                        "rating_count": 0
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Added rating fields to {result.modified_count} existing solutions")
            
            # Update schema info
            solutions_collection.update_one(
                {"_id": "schema_info"},
                {
                    "$set": {
                        "version": "1.1",
                        "features": ["solutions", "ratings"],
                        "last_updated": "2024-01-02T00:00:00Z"
                    }
                },
                upsert=True
            )
            
            self.logger.info("Ratings collection setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add ratings collection: {e}")
            return False
    
    def down(self) -> bool:
        """Rollback ratings collection"""
        try:
            self.logger.info("Rolling back ratings collection...")
            
            # Drop ratings collection
            ratings_collection = self.db.ratings_collection
            ratings_collection.drop()
            self.logger.info("Dropped ratings collection")
            
            # Remove rating fields from solutions
            solutions_collection = self.db.collection
            solutions_collection.update_many(
                {},
                {
                    "$unset": {
                        "avg_rating": "",
                        "rating_count": ""
                    }
                }
            )
            
            # Revert schema info
            solutions_collection.update_one(
                {"_id": "schema_info"},
                {
                    "$set": {
                        "version": "1.0",
                        "features": ["solutions"]
                    },
                    "$unset": {
                        "last_updated": ""
                    }
                }
            )
            
            self.logger.info("Ratings collection rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback ratings collection: {e}")
            return False
    
    def validate(self) -> bool:
        """Validate ratings collection was created correctly"""
        try:
            ratings_collection = self.db.ratings_collection
            
            # Check that collection exists (by trying to get stats)
            try:
                ratings_collection.count_documents({})
            except Exception:
                self.logger.error("Ratings collection does not exist or is not accessible")
                return False
            
            # Check for proper indexes
            index_names = [index['name'] for index in ratings_collection.list_indexes()]
            expected_indexes = ['_id_', 'solution_id_1', 'rating_1', 'created_at_-1']
            
            missing_indexes = [idx for idx in expected_indexes if idx not in index_names]
            if missing_indexes:
                self.logger.warning(f"Missing expected indexes: {missing_indexes}")
            
            # Check that solutions have rating fields
            solutions_collection = self.db.collection
            sample_solution = solutions_collection.find_one({"_id": {"$ne": "schema_info"}})
            
            if sample_solution:
                if 'avg_rating' not in sample_solution or 'rating_count' not in sample_solution:
                    self.logger.error("Solutions missing rating fields")
                    return False
            
            self.logger.info("Ratings collection validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Ratings validation failed: {e}")
            return False