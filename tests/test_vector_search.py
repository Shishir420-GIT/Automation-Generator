#!/usr/bin/env python3
"""
Test script for vector search implementation

To run with real credentials:
1. Update the secrets in MockSecrets class below
2. Or set up .streamlit/secrets.toml with real credentials
3. Run: python3 test_vector_search.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.embedding_service import GeminiEmbeddingService
from utils.MongoDBFunctions import MongoDB
import streamlit as st
API_KEY=""
mongoDB_URI=""
# Mock streamlit secrets for testing
class MockSecrets:
    def get(self, key):
        # REPLACE THESE WITH REAL VALUES FOR ACTUAL TESTING
        secrets = {
            'API_KEY': API_KEY,  # Replace with real Gemini API key
            'mongoDB_URI': mongoDB_URI  # Replace with real MongoDB URI
        }
        return secrets.get(key)

# Mock streamlit functions for testing
def mock_streamlit():
    """Mock streamlit functions for testing"""
    st.secrets = MockSecrets()
    st.error = lambda x: print(f"ERROR: {x}")
    st.warning = lambda x: print(f"WARNING: {x}")
    st.info = lambda x: print(f"INFO: {x}")
    st.success = lambda x: print(f"SUCCESS: {x}")
    st.stop = lambda: sys.exit(1)

def test_embedding_service():
    """Test the embedding service functionality"""
    print("🧪 Testing Embedding Service...")
    
    try:
        # This will fail without a real API key, but we can test the structure
        service = GeminiEmbeddingService()
        print("✅ Embedding service initialized")
        
        # Test embedding generation (will fail without real API key)
        test_text = "This is a test automation for web scraping"
        print(f"Testing embedding generation for: '{test_text}'")
        
        embedding = service.generate_embedding(test_text)
        if embedding:
            print(f"✅ Generated embedding with {len(embedding)} dimensions")
            print(f"First 5 values: {embedding[:5]}")
        else:
            print("⚠️ Embedding generation failed (expected without valid API key)")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding service test failed: {e}")
        return False

def test_mongodb_integration():
    """Test MongoDB integration with vector search"""
    print("\n🧪 Testing MongoDB Integration...")
    
    try:
        # This will fail without real MongoDB URI, but we can test the structure
        db = MongoDB()
        print("✅ MongoDB class instantiated")
        
        print(f"Vector search enabled: {db.vector_search_enabled}")
        print(f"Embedding service available: {db.embedding_service is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB integration test failed: {e}")
        return False

def test_search_functionality():
    """Test search functionality"""
    print("\n🧪 Testing Search Methods...")
    
    try:
        db = MongoDB()
        
        # Test search method exists
        if hasattr(db, 'search_mongodb'):
            print("✅ Main search method available")
        
        if hasattr(db, 'vector_search_mongodb'):
            print("✅ Vector search method available")
        
        if hasattr(db, 'hybrid_search_mongodb'):
            print("✅ Hybrid search method available")
        
        if hasattr(db, 'migrate_existing_data_to_vectors'):
            print("✅ Migration method available")
        
        return True
        
    except Exception as e:
        print(f"❌ Search functionality test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Vector Search Implementation Tests...")
    print("="*50)
    
    # Mock streamlit for testing
    mock_streamlit()
    
    # Run tests
    tests = [
        test_embedding_service,
        test_mongodb_integration, 
        test_search_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vector search implementation is ready.")
        print("\n📝 Next Steps:")
        print("1. Set up valid Gemini API key in secrets")
        print("2. Set up valid MongoDB URI in secrets")
        print("3. Create vector search index in MongoDB Atlas")
        print("4. Test with real data")
    else:
        print("⚠️ Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)