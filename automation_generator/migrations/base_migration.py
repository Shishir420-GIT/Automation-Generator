"""
Base migration system for Automation Generator
Handles database schema migrations and version tracking
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.errors import DuplicateKeyError

from ..core.config_manager import ConfigManager
from ..core.mongo_functions import MongoDB


class BaseMigration(ABC):
    """Base class for database migrations"""
    
    version: str = ""
    description: str = ""
    
    def __init__(self, db: MongoDB):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def up(self) -> bool:
        """Apply migration"""
        pass
    
    @abstractmethod
    def down(self) -> bool:
        """Rollback migration"""
        pass
    
    def validate(self) -> bool:
        """Validate migration was applied correctly"""
        return True


class MigrationManager:
    """Manages database migrations and version tracking"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager or ConfigManager()
        
        # Initialize database connection
        self.db = MongoDB(self.config_manager)
        
        # Migration tracking collection
        self.migrations_collection = self.db.db["migration_history"]
        
        # Ensure migration tracking is set up
        self._initialize_migration_tracking()
    
    def _initialize_migration_tracking(self):
        """Initialize migration tracking collection"""
        try:
            # Create index for version uniqueness
            self.migrations_collection.create_index("version", unique=True)
            
            # Create migration tracking document if it doesn't exist
            tracking_doc = {
                "_id": "migration_tracking",
                "current_version": None,
                "applied_migrations": [],
                "last_migration_date": None,
                "schema_version": "2.0"
            }
            
            try:
                self.migrations_collection.insert_one(tracking_doc)
                self.logger.info("Migration tracking initialized")
            except DuplicateKeyError:
                # Document already exists
                pass
                
        except Exception as e:
            self.logger.error(f"Failed to initialize migration tracking: {e}")
            raise
    
    def get_current_version(self) -> Optional[str]:
        """Get current database version"""
        try:
            tracking = self.migrations_collection.find_one({"_id": "migration_tracking"})
            return tracking.get("current_version") if tracking else None
        except Exception as e:
            self.logger.error(f"Failed to get current version: {e}")
            return None
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migrations"""
        try:
            tracking = self.migrations_collection.find_one({"_id": "migration_tracking"})
            return tracking.get("applied_migrations", []) if tracking else []
        except Exception as e:
            self.logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_available_migrations(self) -> Dict[str, BaseMigration]:
        """Get all available migration classes"""
        # Import migration modules
        migrations = {}
        
        try:
            from .migration_scripts.migration_001_initial_schema import Migration001
            from .migration_scripts.migration_002_add_ratings import Migration002
            from .migration_scripts.migration_003_add_vector_search import Migration003
            from .migration_scripts.migration_004_add_analytics import Migration004
            
            migration_classes = [Migration001, Migration002, Migration003, Migration004]
            
            for migration_class in migration_classes:
                migration_instance = migration_class(self.db)
                migrations[migration_instance.version] = migration_instance
            
        except ImportError as e:
            self.logger.warning(f"Some migration modules not available: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load migrations: {e}")
        
        return migrations
    
    def get_pending_migrations(self, target_version: Optional[str] = None) -> List[str]:
        """Get list of pending migrations"""
        available_migrations = self.get_available_migrations()
        applied_migrations = self.get_applied_migrations()
        
        # Sort versions
        all_versions = sorted(available_migrations.keys())
        
        if target_version:
            # Only include migrations up to target version
            all_versions = [v for v in all_versions if v <= target_version]
        
        # Filter out already applied migrations
        pending = [v for v in all_versions if v not in applied_migrations]
        
        return pending
    
    def get_rollback_migrations(self, from_version: str, to_version: str) -> List[str]:
        """Get list of migrations to rollback"""
        available_migrations = self.get_available_migrations()
        applied_migrations = self.get_applied_migrations()
        
        # Get migrations between versions (in reverse order for rollback)
        rollback_migrations = []
        
        for version in sorted(available_migrations.keys(), reverse=True):
            if to_version < version <= from_version and version in applied_migrations:
                rollback_migrations.append(version)
        
        return rollback_migrations
    
    def apply_migration(self, version: str) -> bool:
        """Apply a specific migration"""
        available_migrations = self.get_available_migrations()
        
        if version not in available_migrations:
            self.logger.error(f"Migration {version} not found")
            return False
        
        migration = available_migrations[version]
        
        try:
            self.logger.info(f"Applying migration {version}: {migration.description}")
            
            # Execute migration
            if not migration.up():
                self.logger.error(f"Migration {version} up() method failed")
                return False
            
            # Validate migration
            if not migration.validate():
                self.logger.error(f"Migration {version} validation failed")
                return False
            
            # Record migration as applied
            self._record_migration(version, "applied")
            
            self.logger.info(f"Successfully applied migration {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply migration {version}: {e}")
            return False
    
    def rollback_migration(self, version: str) -> bool:
        """Rollback a specific migration"""
        available_migrations = self.get_available_migrations()
        
        if version not in available_migrations:
            self.logger.error(f"Migration {version} not found")
            return False
        
        migration = available_migrations[version]
        
        try:
            self.logger.info(f"Rolling back migration {version}: {migration.description}")
            
            # Execute rollback
            if not migration.down():
                self.logger.error(f"Migration {version} down() method failed")
                return False
            
            # Record migration as rolled back
            self._record_migration(version, "rolled_back")
            
            self.logger.info(f"Successfully rolled back migration {version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rollback migration {version}: {e}")
            return False
    
    def _record_migration(self, version: str, action: str):
        """Record migration application or rollback"""
        try:
            current_time = datetime.utcnow()
            
            # Insert migration record
            migration_record = {
                "version": version,
                "action": action,  # "applied" or "rolled_back"
                "timestamp": current_time,
                "description": self.get_available_migrations().get(version, {}).description or ""
            }
            
            self.migrations_collection.insert_one(migration_record)
            
            # Update tracking document
            if action == "applied":
                self.migrations_collection.update_one(
                    {"_id": "migration_tracking"},
                    {
                        "$set": {
                            "current_version": version,
                            "last_migration_date": current_time
                        },
                        "$addToSet": {
                            "applied_migrations": version
                        }
                    }
                )
            elif action == "rolled_back":
                self.migrations_collection.update_one(
                    {"_id": "migration_tracking"},
                    {
                        "$pull": {
                            "applied_migrations": version
                        },
                        "$set": {
                            "last_migration_date": current_time
                        }
                    }
                )
                
                # Update current version to the highest remaining applied migration
                applied_migrations = self.get_applied_migrations()
                if applied_migrations:
                    new_current = max(applied_migrations)
                    self.migrations_collection.update_one(
                        {"_id": "migration_tracking"},
                        {"$set": {"current_version": new_current}}
                    )
                else:
                    self.migrations_collection.update_one(
                        {"_id": "migration_tracking"},
                        {"$set": {"current_version": None}}
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to record migration {version}: {e}")
            raise
    
    def get_previous_version(self, current_version: Optional[str]) -> Optional[str]:
        """Get the previous version before current"""
        if not current_version:
            return None
        
        available_migrations = self.get_available_migrations()
        applied_migrations = self.get_applied_migrations()
        
        # Get applied versions sorted
        applied_versions = [v for v in sorted(available_migrations.keys()) if v in applied_migrations]
        
        try:
            current_index = applied_versions.index(current_version)
            if current_index > 0:
                return applied_versions[current_index - 1]
            else:
                return None  # This is the first version
        except ValueError:
            return None  # Current version not found in applied migrations
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get complete migration history"""
        try:
            # Get all migration records (excluding tracking document)
            cursor = self.migrations_collection.find(
                {"_id": {"$ne": "migration_tracking"}},
                sort=[("timestamp", -1)]  # Most recent first
            )
            
            history = []
            for record in cursor:
                record.pop('_id', None)  # Remove MongoDB ObjectId
                history.append(record)
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get migration history: {e}")
            return []