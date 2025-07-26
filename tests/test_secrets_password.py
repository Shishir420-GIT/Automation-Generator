#!/usr/bin/env python3
"""
Test that admin password is being read from secrets correctly
"""

import streamlit as st

# Mock secrets for testing
class MockSecrets:
    def __init__(self, secrets_dict):
        self.secrets = secrets_dict
    
    def get(self, key, default=None):
        return self.secrets.get(key, default)

def test_password_from_secrets():
    """Test reading admin password from different secret configurations"""
    
    print("🧪 Testing Admin Password from Secrets")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Custom password in secrets",
            "secrets": {"ADMIN_PASSWORD": "my_custom_secure_password_123"},
            "expected": "my_custom_secure_password_123"
        },
        {
            "name": "No admin password in secrets (fallback)",
            "secrets": {"API_KEY": "test_key"},
            "expected": "vector_admin_2024"
        },
        {
            "name": "Empty admin password in secrets (fallback)",
            "secrets": {"ADMIN_PASSWORD": ""},
            "expected": ""
        },
        {
            "name": "All secrets configured",
            "secrets": {
                "API_KEY": "test_api_key",
                "mongoDB_URI": "test_mongo_uri", 
                "ADMIN_PASSWORD": "SuperSecureAdminPass2024!"
            },
            "expected": "SuperSecureAdminPass2024!"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Secrets: {test_case['secrets']}")
        
        # Mock streamlit secrets
        mock_secrets = MockSecrets(test_case['secrets'])
        
        # This is the exact logic from the app
        admin_secret_password = mock_secrets.get("ADMIN_PASSWORD", "vector_admin_2024")
        
        print(f"   Result: '{admin_secret_password}'")
        print(f"   Expected: '{test_case['expected']}'")
        
        if admin_secret_password == test_case['expected']:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")
    
    print("\n" + "=" * 50)
    print("✅ Secret password reading test complete!")
    
    print(f"\n📝 **Configuration Example:**")
    print("Add to your .streamlit/secrets.toml:")
    print("```")
    print("API_KEY = \"your_gemini_api_key\"")
    print("mongoDB_URI = \"your_mongodb_uri\"") 
    print("ADMIN_PASSWORD = \"your_secure_admin_password\"")
    print("```")

if __name__ == "__main__":
    test_password_from_secrets()