"""
Configuration management system for Automation Generator
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict

@dataclass
class LLMConfig:
    provider: str = "gemini"
    api_key: str = ""
    model: str = "gemini-1.5-flash"
    backup_providers: list = None

@dataclass
class DatabaseConfig:
    mongodb_uri: str = ""
    database_name: str = "automation_generator"
    collections: Dict[str, str] = None

@dataclass
class AppConfig:
    host: str = "localhost"
    port: int = 8501
    theme: str = "light"
    debug: bool = False
    log_level: str = "INFO"
    max_file_size_mb: int = 20
    session_timeout_hours: int = 24

@dataclass
class FeatureConfig:
    enable_community: bool = True
    enable_ratings: bool = True
    enable_analytics: bool = True
    enable_multi_language: bool = True
    enable_visualizations: bool = True
    enable_api: bool = False

@dataclass
class SecurityConfig:
    require_auth: bool = False
    allowed_domains: list = None
    rate_limiting: bool = True
    max_requests_per_hour: int = 100

@dataclass
class AdvancedConfig:
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    background_tasks: bool = True
    telemetry_enabled: bool = True


class ConfigManager:
    """Manages configuration for Automation Generator package"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        
        # Set default config directory
        if config_dir is None:
            self.config_dir = Path.home() / ".automation-generator"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_file = self.config_dir / "config.yaml"
        self.log_dir = self.config_dir / "logs"
        
        # Default configuration
        self._default_config = {
            "version": "1.0",
            "llm": asdict(LLMConfig()),
            "database": asdict(DatabaseConfig(collections={
                "solutions": "solutions",
                "ratings": "ratings", 
                "users": "users",
                "analytics": "analytics"
            })),
            "app": asdict(AppConfig()),
            "features": asdict(FeatureConfig()),
            "security": asdict(SecurityConfig(allowed_domains=[])),
            "advanced": asdict(AdvancedConfig())
        }
        
        self._config = None
        
    def ensure_config_dir(self) -> bool:
        """Create configuration directory if it doesn't exist"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create config directory: {e}")
            return False
            
    def create_config_template(self) -> bool:
        """Create configuration template file"""
        try:
            if not self.ensure_config_dir():
                return False
                
            template_content = """# Automation Generator Configuration
version: "1.0"

# Required: LLM Configuration
llm:
  provider: "gemini"  # gemini, openai, claude
  api_key: "${GEMINI_API_KEY}"  # Environment variable or direct key
  model: "gemini-1.5-flash"
  backup_providers: []  # Optional fallback providers

# Required: Database Configuration  
database:
  mongodb_uri: "${MONGODB_URI}"
  database_name: "automation_generator"
  collections:
    solutions: "solutions"
    ratings: "ratings"
    users: "users"
    analytics: "analytics"

# Optional: Application Settings
app:
  host: "localhost"
  port: 8501
  theme: "light"  # light, dark, auto
  debug: false
  log_level: "INFO"
  max_file_size_mb: 20
  session_timeout_hours: 24

# Optional: Feature Flags
features:
  enable_community: true
  enable_ratings: true
  enable_analytics: true
  enable_multi_language: true
  enable_visualizations: true
  enable_api: false  # Future: REST API

# Optional: Security Settings
security:
  require_auth: false  # Future: Authentication
  allowed_domains: []  # Future: Domain restrictions
  rate_limiting: true
  max_requests_per_hour: 100

# Optional: Advanced Settings
advanced:
  cache_enabled: true
  cache_ttl_hours: 24
  background_tasks: true
  telemetry_enabled: true  # Anonymous usage statistics
"""
            
            with open(self.config_file, 'w') as f:
                f.write(template_content)
                
            self.logger.info(f"Configuration template created: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create config template: {e}")
            return False
            
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with environment variable expansion"""
        if self._config is not None:
            return self._config
            
        try:
            if not self.config_file.exists():
                self.logger.warning(f"Config file not found: {self.config_file}")
                return self._default_config.copy()
            
            with open(self.config_file, 'r') as f:
                config_content = f.read()
                
            # Expand environment variables
            config_content = os.path.expandvars(config_content)
            
            config = yaml.safe_load(config_content)
            
            # Merge with defaults
            merged_config = self._deep_merge(self._default_config.copy(), config)
            
            self._config = merged_config
            return self._config
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._default_config.copy()
            
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            if not self.ensure_config_dir():
                return False
                
            with open(self.config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
                
            self._config = None  # Force reload
            self.logger.info(f"Configuration saved: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        config = self.load_config()
        keys = key.split('.')
        
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by key (supports dot notation)"""
        config = self.load_config()
        keys = key.split('.')
        
        # Navigate to parent
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
            
        # Set value
        current[keys[-1]] = value
        
        return self.save_config(config)
        
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration and return validation status and errors"""
        config = self.load_config()
        errors = []
        
        # Check required fields
        required_fields = [
            "llm.api_key",
            "database.mongodb_uri"
        ]
        
        for field in required_fields:
            value = self.get(field)
            if not value or value.startswith("${"):
                errors.append(f"Required field missing or not set: {field}")
                
        # Validate API key format
        api_key = self.get("llm.api_key", "")
        if api_key and not api_key.startswith("${") and len(api_key) < 10:
            errors.append("API key appears to be invalid (too short)")
            
        # Validate MongoDB URI format
        mongo_uri = self.get("database.mongodb_uri", "")
        if mongo_uri and not mongo_uri.startswith("${") and not mongo_uri.startswith("mongodb"):
            errors.append("MongoDB URI must start with 'mongodb://' or 'mongodb+srv://'")
            
        # Validate port
        port = self.get("app.port", 8501)
        if not isinstance(port, int) or port < 1024 or port > 65535:
            errors.append("Port must be an integer between 1024 and 65535")
            
        return len(errors) == 0, errors
        
    def get_streamlit_config(self) -> Dict[str, Any]:
        """Convert configuration to Streamlit secrets format"""
        config = self.load_config()
        
        streamlit_config = {
            "API_KEY": self.get("llm.api_key", ""),
            "mongoDB_URI": self.get("database.mongodb_uri", ""),
            "ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD", "")
        }
        
        return streamlit_config
        
    @staticmethod
    def _deep_merge(base_dict: Dict, override_dict: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base_dict.copy()
        
        for key, value in override_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result