"""
Migration 001: Initial database schema setup
Creates basic collections and indexes for Automation Generator
"""

from pymongo.errors import OperationFailure
from ..base_migration import BaseMigration


class Migration001(BaseMigration):
    """Initial database schema setup"""
    
    version = "001"
    description = "Initial schema setup with solutions collection"
    
    def up(self) -> bool:
        """Create initial database schema"""
        try:
            self.logger.info("Creating initial database schema...")
            
            # Create solutions collection with indexes
            solutions_collection = self.db.collection
            
            # Create indexes for better performance
            indexes = [
                ("domain", 1),
                ("created_at", -1),
                ("script_type", 1),
                ("version", 1)
            ]
            
            for field, direction in indexes:
                try:
                    solutions_collection.create_index([(field, direction)])
                    self.logger.info(f"Created index on {field}")
                except OperationFailure as e:
                    if "already exists" not in str(e):
                        raise
            
            # Create compound index for text search
            try:
                solutions_collection.create_index([
                    ("domain", "text"),
                    ("sop_text", "text"),
                    ("script_content", "text")
                ])
                self.logger.info("Created text search index")
            except OperationFailure as e:
                if "already exists" not in str(e):
                    raise
            
            # Insert schema version document
            schema_info = {
                "_id": "schema_info",
                "version": "1.0",
                "created_at": "2024-01-01T00:00:00Z",
                "description": "Initial schema with solutions collection"
            }
            
            try:
                solutions_collection.insert_one(schema_info)
                self.logger.info("Inserted schema info document")
            except OperationFailure:
                # Document might already exist
                solutions_collection.replace_one(
                    {"_id": "schema_info"},
                    schema_info,
                    upsert=True
                )
            
            self.logger.info("Initial schema setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create initial schema: {e}")
            return False
    
    def down(self) -> bool:
        """Rollback initial schema (drops indexes but keeps data)"""
        try:
            self.logger.info("Rolling back initial schema...")
            
            solutions_collection = self.db.collection
            
            # Drop custom indexes (keep _id index)
            index_info = solutions_collection.list_indexes()
            
            for index in index_info:
                index_name = index['name']
                if index_name != '_id_':  # Don't drop the default _id index
                    try:
                        solutions_collection.drop_index(index_name)
                        self.logger.info(f"Dropped index {index_name}")
                    except OperationFailure:
                        pass  # Index might not exist
            
            # Remove schema info document
            solutions_collection.delete_one({"_id": "schema_info"})
            
            self.logger.info("Initial schema rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback initial schema: {e}")
            return False
    
    def validate(self) -> bool:
        """Validate that initial schema was created correctly"""
        try:
            solutions_collection = self.db.collection
            
            # Check that collection exists and has documents (at least schema info)
            doc_count = solutions_collection.count_documents({})
            if doc_count == 0:
                self.logger.warning("Solutions collection is empty")
            
            # Check for schema info document
            schema_info = solutions_collection.find_one({"_id": "schema_info"})
            if not schema_info:
                self.logger.error("Schema info document not found")
                return False
            
            # Check that some indexes exist
            index_names = [index['name'] for index in solutions_collection.list_indexes()]
            if len(index_names) < 2:  # At least _id and one other index
                self.logger.warning("Expected more indexes to be created")
                return False
            
            self.logger.info("Initial schema validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            return False