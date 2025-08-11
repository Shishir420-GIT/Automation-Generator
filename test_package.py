#!/usr/bin/env python3
"""
Test script for the Automation Generator package
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

def run_command(cmd, input_data=None, capture_output=True):
    """Run a command and return result"""
    print(f"🧪 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            input=input_data, 
            text=True, 
            capture_output=capture_output,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ Success: {' '.join(cmd)}")
            if result.stdout:
                print(f"📋 Output:\n{result.stdout}")
        else:
            print(f"❌ Failed: {' '.join(cmd)}")
            if result.stderr:
                print(f"🚨 Error:\n{result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout: {' '.join(cmd)}")
        return None
    except Exception as e:
        print(f"💥 Exception: {e}")
        return None

def test_cli_help():
    """Test CLI help commands"""
    print("\n🧪 Testing CLI Help Commands")
    print("=" * 50)
    
    commands = [
        ["automation-generator", "--help"],
        ["automation-generator", "config", "--help"],
        ["automation-generator", "init", "--help"],
        ["automation-generator", "health", "--help"],
        ["automation-generator", "migrate", "--help"]
    ]
    
    for cmd in commands:
        run_command(cmd)

def test_config_commands():
    """Test configuration commands"""
    print("\n🧪 Testing Configuration Commands")
    print("=" * 50)
    
    # Test config path
    run_command(["automation-generator", "config", "path"])
    
    # Test config show (should work even without config file)
    run_command(["automation-generator", "config", "show"])

def test_health_command():
    """Test health command"""
    print("\n🧪 Testing Health Command")
    print("=" * 50)
    
    # This will fail without proper config but should show what's wrong
    run_command(["automation-generator", "health"])

def test_package_imports():
    """Test package imports"""
    print("\n🧪 Testing Package Imports")
    print("=" * 50)
    
    try:
        from automation_generator import ConfigManager, InputValidator
        print("✅ Core imports successful")
        
        # Test ConfigManager
        config_manager = ConfigManager()
        print(f"✅ ConfigManager created: {config_manager.config_dir}")
        
        # Test InputValidator
        validator = InputValidator()
        valid, error = validator.validate_domain("DevOps")
        print(f"✅ InputValidator working: {valid}, {error}")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")

def test_with_temp_config():
    """Test with temporary configuration"""
    print("\n🧪 Testing with Temporary Configuration")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test init with custom config dir
        print(f"📁 Using temp config dir: {temp_path}")
        
        # Create a minimal config file
        config_file = temp_path / "config.yaml"
        config_content = """
version: "1.0"
llm:
  provider: "gemini"
  api_key: "test-key-123"
database:
  mongodb_uri: "mongodb://localhost:27017/test"
app:
  port: 8501
"""
        config_file.write_text(config_content)
        print("✅ Created test config file")
        
        # Test config commands with the temp config
        run_command([
            "automation-generator", 
            "--config-dir", str(temp_path),
            "config", "show"
        ])
        
        run_command([
            "automation-generator",
            "--config-dir", str(temp_path), 
            "config", "validate"
        ])

def main():
    """Main test function"""
    print("🚀 Automation Generator Package Testing")
    print("=" * 60)
    
    # Test 1: Package imports
    test_package_imports()
    
    # Test 2: CLI help commands
    test_cli_help()
    
    # Test 3: Configuration commands
    test_config_commands()
    
    # Test 4: Health command
    test_health_command()
    
    # Test 5: Temporary configuration
    test_with_temp_config()
    
    print("\n🎉 Testing Complete!")
    print("=" * 60)
    print("\n📋 Next Steps for Full Testing:")
    print("1. Set up API keys: export GEMINI_API_KEY='your-key'")
    print("2. Set up MongoDB: export MONGODB_URI='your-mongo-uri'") 
    print("3. Run: automation-generator init")
    print("4. Run: automation-generator migrate")
    print("5. Run: automation-generator run")

if __name__ == "__main__":
    main()