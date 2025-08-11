"""
Migration 004: Add analytics and user tracking
Creates analytics and users collections
"""

from pymongo.errors import OperationFailure
from ..base_migration import BaseMigration


class Migration004(BaseMigration):
    """Add analytics and user tracking capabilities"""
    
    version = "004"
    description = "Add analytics and users collections"
    
    def up(self) -> bool:
        """Create analytics and users collections"""
        try:
            self.logger.info("Adding analytics and user tracking...")
            
            # Create analytics collection with indexes
            analytics_collection = self.db.analytics_collection
            
            # Analytics indexes
            analytics_indexes = [
                ("event_type", 1),
                ("timestamp", -1),
                ("user_id", 1),
                ("solution_id", 1),
                [("event_type", 1), ("timestamp", -1)]  # Compound index
            ]
            
            for index_spec in analytics_indexes:
                try:
                    if isinstance(index_spec, list):
                        analytics_collection.create_index(index_spec)
                        self.logger.info(f"Created analytics compound index: {index_spec}")
                    else:
                        analytics_collection.create_index([(index_spec[0], index_spec[1])])
                        self.logger.info(f"Created analytics index on {index_spec[0]}")
                except OperationFailure as e:
                    if "already exists" not in str(e):
                        raise
            
            # Create users collection with indexes
            users_collection = self.db.users_collection
            
            # Users indexes
            users_indexes = [
                ("user_id", 1),
                ("created_at", -1),
                ("last_active", -1),
                ("session_id", 1)
            ]
            
            for field, direction in users_indexes:
                try:
                    users_collection.create_index([(field, direction)], sparse=True)
                    self.logger.info(f"Created users index on {field}")
                except OperationFailure as e:
                    if "already exists" not in str(e):
                        raise
            
            # Add analytics fields to solutions collection
            solutions_collection = self.db.collection
            
            result = solutions_collection.update_many(
                {"view_count": {"$exists": False}},
                {
                    "$set": {
                        "view_count": 0,
                        "download_count": 0,
                        "last_accessed": None,
                        "analytics_enabled": True
                    }
                }
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Added analytics fields to {result.modified_count} existing solutions")
            
            # Create initial analytics summary document
            analytics_summary = {
                "_id": "analytics_summary",
                "total_views": 0,
                "total_downloads": 0,
                "unique_users": 0,
                "popular_domains": [],
                "created_at": "2024-01-04T00:00:00Z",
                "last_updated": "2024-01-04T00:00:00Z"
            }
            
            try:
                analytics_collection.insert_one(analytics_summary)
                self.logger.info("Created analytics summary document")
            except OperationFailure:
                # Document might already exist
                analytics_collection.replace_one(
                    {"_id": "analytics_summary"},
                    analytics_summary,
                    upsert=True
                )
            
            # Update schema info
            solutions_collection.update_one(
                {"_id": "schema_info"},
                {
                    "$set": {
                        "version": "2.0",
                        "features": ["solutions", "ratings", "vector_search", "analytics", "users"],
                        "collections": {
                            "solutions": "solutions",
                            "ratings": "ratings", 
                            "analytics": "analytics",
                            "users": "users"
                        },
                        "last_updated": "2024-01-04T00:00:00Z"
                    }
                },
                upsert=True
            )
            
            self.logger.info("Analytics and user tracking setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add analytics: {e}")
            return False
    
    def down(self) -> bool:
        """Rollback analytics and user tracking"""
        try:
            self.logger.info("Rolling back analytics and user tracking...")
            
            # Drop analytics and users collections
            self.db.analytics_collection.drop()
            self.db.users_collection.drop()
            self.logger.info("Dropped analytics and users collections")
            
            # Remove analytics fields from solutions
            solutions_collection = self.db.collection
            solutions_collection.update_many(
                {},
                {
                    "$unset": {
                        "view_count": "",
                        "download_count": "",
                        "last_accessed": "",
                        "analytics_enabled": ""
                    }
                }
            )
            
            # Revert schema info
            solutions_collection.update_one(
                {"_id": "schema_info"},
                {
                    "$set": {
                        "version": "1.2",
                        "features": ["solutions", "ratings", "vector_search"]
                    },
                    "$unset": {
                        "collections": ""
                    }
                }
            )
            
            self.logger.info("Analytics rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback analytics: {e}")
            return False
    
    def validate(self) -> bool:
        """Validate analytics setup"""
        try:
            # Check that collections exist
            try:
                self.db.analytics_collection.count_documents({})
                self.db.users_collection.count_documents({})
            except Exception:
                self.logger.error("Analytics or users collections not accessible")
                return False
            
            # Check analytics collection indexes
            analytics_indexes = [index['name'] for index in self.db.analytics_collection.list_indexes()]
            expected_analytics_indexes = ['_id_', 'event_type_1', 'timestamp_-1', 'user_id_1', 'solution_id_1']
            
            missing_indexes = [idx for idx in expected_analytics_indexes if idx not in analytics_indexes]
            if missing_indexes:
                self.logger.warning(f"Missing analytics indexes: {missing_indexes}")
            
            # Check users collection indexes
            users_indexes = [index['name'] for index in self.db.users_collection.list_indexes()]
            expected_users_indexes = ['_id_', 'user_id_1', 'created_at_-1']
            
            missing_users_indexes = [idx for idx in expected_users_indexes if idx not in users_indexes]
            if missing_users_indexes:
                self.logger.warning(f"Missing users indexes: {missing_users_indexes}")
            
            # Check solutions have analytics fields
            solutions_collection = self.db.collection
            sample_solution = solutions_collection.find_one({"_id": {"$ne": "schema_info"}})
            
            if sample_solution:
                required_fields = ['view_count', 'download_count', 'analytics_enabled']
                missing_fields = [field for field in required_fields if field not in sample_solution]
                
                if missing_fields:
                    self.logger.error(f"Solutions missing analytics fields: {missing_fields}")
                    return False
            
            # Check analytics summary document
            analytics_summary = self.db.analytics_collection.find_one({"_id": "analytics_summary"})
            if not analytics_summary:
                self.logger.error("Analytics summary document not found")
                return False
            
            # Check schema info
            schema_info = solutions_collection.find_one({"_id": "schema_info"})
            if not schema_info:
                self.logger.error("Schema info document not found")
                return False
            
            features = schema_info.get("features", [])
            if "analytics" not in features or "users" not in features:
                self.logger.error("Analytics/users not listed in schema features")
                return False
            
            self.logger.info("Analytics validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Analytics validation failed: {e}")
            return False