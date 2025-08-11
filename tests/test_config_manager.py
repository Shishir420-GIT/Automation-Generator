"""
Unit tests for ConfigManager
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from automation_generator.core.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager instance with temporary directory"""
        return ConfigManager(temp_config_dir)
    
    def test_init_default_config_dir(self):
        """Test ConfigManager initialization with default config directory"""
        manager = ConfigManager()
        expected_dir = Path.home() / ".automation-generator"
        assert manager.config_dir == expected_dir
    
    def test_init_custom_config_dir(self, temp_config_dir):
        """Test ConfigManager initialization with custom config directory"""
        manager = ConfigManager(temp_config_dir)
        assert manager.config_dir == temp_config_dir
    
    def test_ensure_config_dir_creates_directory(self, config_manager):
        """Test that ensure_config_dir creates necessary directories"""
        # Remove directory if it exists
        if config_manager.config_dir.exists():
            config_manager.config_dir.rmdir()
        
        result = config_manager.ensure_config_dir()
        
        assert result is True
        assert config_manager.config_dir.exists()
        assert config_manager.log_dir.exists()
    
    def test_create_config_template_success(self, config_manager):
        """Test successful configuration template creation"""
        result = config_manager.create_config_template()
        
        assert result is True
        assert config_manager.config_file.exists()
        
        # Check content
        content = config_manager.config_file.read_text()
        assert "version:" in content
        assert "llm:" in content
        assert "database:" in content
    
    def test_load_config_nonexistent_file(self, config_manager):
        """Test loading config when file doesn't exist returns defaults"""
        config = config_manager.load_config()
        
        assert config is not None
        assert "version" in config
        assert "llm" in config
        assert "database" in config
    
    def test_load_config_with_env_variables(self, config_manager):
        """Test loading config with environment variable expansion"""
        # Create config with env variables
        config_content = """
version: "1.0"
llm:
  api_key: "${TEST_API_KEY}"
database:
  mongodb_uri: "${TEST_MONGO_URI}"
"""
        config_manager.config_file.parent.mkdir(parents=True, exist_ok=True)
        config_manager.config_file.write_text(config_content)
        
        # Set environment variables
        with patch.dict(os.environ, {
            'TEST_API_KEY': 'test-key-123',
            'TEST_MONGO_URI': 'mongodb://test:27017'
        }):
            config = config_manager.load_config()
            
            assert config['llm']['api_key'] == 'test-key-123'
            assert config['database']['mongodb_uri'] == 'mongodb://test:27017'
    
    def test_save_config_success(self, config_manager):
        """Test successful configuration saving"""
        test_config = {
            "version": "1.0",
            "llm": {"provider": "gemini", "api_key": "test-key"},
            "database": {"mongodb_uri": "mongodb://test:27017"}
        }
        
        result = config_manager.save_config(test_config)
        
        assert result is True
        assert config_manager.config_file.exists()
        
        # Verify saved content
        loaded_config = config_manager.load_config()
        assert loaded_config['llm']['provider'] == 'gemini'
        assert loaded_config['database']['mongodb_uri'] == 'mongodb://test:27017'
    
    def test_get_config_value(self, config_manager):
        """Test getting configuration values with dot notation"""
        test_config = {
            "llm": {"provider": "gemini", "api_key": "test-key"},
            "database": {"mongodb_uri": "mongodb://test:27017"}
        }
        config_manager.save_config(test_config)
        
        assert config_manager.get("llm.provider") == "gemini"
        assert config_manager.get("llm.api_key") == "test-key"
        assert config_manager.get("database.mongodb_uri") == "mongodb://test:27017"
        assert config_manager.get("nonexistent.key") is None
        assert config_manager.get("nonexistent.key", "default") == "default"
    
    def test_set_config_value(self, config_manager):
        """Test setting configuration values with dot notation"""
        # Create initial config
        config_manager.create_config_template()
        
        result = config_manager.set("llm.api_key", "new-api-key")
        assert result is True
        
        # Verify value was set
        assert config_manager.get("llm.api_key") == "new-api-key"
        
        # Test setting nested value
        result = config_manager.set("new.nested.value", "test")
        assert result is True
        assert config_manager.get("new.nested.value") == "test"
    
    def test_validate_config_success(self, config_manager):
        """Test configuration validation with valid config"""
        valid_config = {
            "version": "1.0",
            "llm": {"api_key": "valid-api-key-123456789"},
            "database": {"mongodb_uri": "mongodb://localhost:27017/test"},
            "app": {"port": 8501}
        }
        config_manager.save_config(valid_config)
        
        is_valid, errors = config_manager.validate_config()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_config_failures(self, config_manager):
        """Test configuration validation with invalid config"""
        invalid_config = {
            "version": "1.0",
            "llm": {"api_key": "${UNSET_API_KEY}"},  # Env var format
            "database": {"mongodb_uri": "invalid-uri"},  # Invalid URI
            "app": {"port": 99999}  # Invalid port
        }
        config_manager.save_config(invalid_config)
        
        is_valid, errors = config_manager.validate_config()
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("api_key" in error.lower() for error in errors)
        assert any("mongodb" in error.lower() for error in errors)
    
    def test_get_streamlit_config(self, config_manager):
        """Test getting Streamlit-compatible configuration"""
        test_config = {
            "llm": {"api_key": "test-api-key"},
            "database": {"mongodb_uri": "mongodb://test:27017"}
        }
        config_manager.save_config(test_config)
        
        streamlit_config = config_manager.get_streamlit_config()
        
        assert "API_KEY" in streamlit_config
        assert "mongoDB_URI" in streamlit_config
        assert streamlit_config["API_KEY"] == "test-api-key"
        assert streamlit_config["mongoDB_URI"] == "mongodb://test:27017"
    
    def test_deep_merge_functionality(self):
        """Test the deep merge utility function"""
        base = {
            "a": {"x": 1, "y": 2},
            "b": 3
        }
        override = {
            "a": {"y": 20, "z": 30},
            "c": 40
        }
        
        result = ConfigManager._deep_merge(base, override)
        
        expected = {
            "a": {"x": 1, "y": 20, "z": 30},
            "b": 3,
            "c": 40
        }
        
        assert result == expected