"""
Pytest configuration and fixtures for Automation Generator tests
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

@pytest.fixture(scope="session")
def test_data_dir():
    """Get the test data directory"""
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_sop_text():
    """Sample SOP text for testing"""
    return """
    Standard Operating Procedure for Server Deployment
    
    1. Prepare the server environment
       - Update system packages
       - Install required dependencies
       - Configure firewall rules
    
    2. Deploy the application
       - Clone the repository
       - Install application dependencies  
       - Configure environment variables
       - Start the application services
    
    3. Verify deployment
       - Check service status
       - Run health checks
       - Monitor logs for errors
       - Perform smoke tests
    
    4. Post-deployment tasks
       - Update documentation
       - Notify stakeholders
       - Schedule monitoring alerts
    """

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "version": "1.0",
        "llm": {
            "provider": "gemini",
            "api_key": "test-api-key-123456789",
            "model": "gemini-1.5-flash"
        },
        "database": {
            "mongodb_uri": "mongodb://localhost:27017/test_automation",
            "database_name": "test_automation"
        },
        "app": {
            "host": "localhost",
            "port": 8501,
            "debug": True
        }
    }

@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return Mock(text="#!/bin/bash\necho 'Generated automation script'")

@pytest.fixture
def mock_mongodb_client():
    """Mock MongoDB client for testing"""
    client = Mock()
    db = Mock()
    collection = Mock()
    
    client.__getitem__.return_value = db
    db.__getitem__.return_value = collection
    
    return client

@pytest.fixture
def env_vars():
    """Provide clean environment variables for testing"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "GEMINI_API_KEY": "test-gemini-key-123",
        "MONGODB_URI": "mongodb://localhost:27017/test",
        "AUTOMATION_GENERATOR_CONFIG_DIR": "/tmp/test-config"
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

# Skip integration tests by default
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may require external services)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle markers"""
    if config.getoption("--integration"):
        # If --integration flag is used, don't skip integration tests
        return
    
    skip_integration = pytest.mark.skip(reason="Integration tests skipped (use --integration to run)")
    
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external services"
    )