#!/usr/bin/env python3
"""
Migration Helper Script
Helps diagnose and perform vector search migration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.MongoDBFunctions import MongoDB
import streamlit as st

# Mock streamlit for testing
class MockSecrets:
    def get(self, key):
        # Read from the same credentials as your test file
        API_KEY = ""  # Your API key here
        mongoDB_URI = ""  # Your MongoDB URI here
        
        secrets = {
            'API_KEY': API_KEY,
            'mongoDB_URI': mongoDB_URI
        }
        return secrets.get(key)

def mock_streamlit():
    """Mock streamlit functions"""
    st.secrets = MockSecrets()
    st.error = lambda x: print(f"ERROR: {x}")
    st.warning = lambda x: print(f"WARNING: {x}")
    st.info = lambda x: print(f"INFO: {x}")
    st.success = lambda x: print(f"SUCCESS: {x}")
    st.stop = lambda: sys.exit(1)
    st.progress = lambda x: print(f"PROGRESS: {x*100:.1f}%")
    st.spinner = lambda x: print(f"SPINNER: {x}")
    st.empty = lambda: None
    st.rerun = lambda: None

def check_migration_status():
    """Check current migration status"""
    print("🔍 Checking Migration Status...")
    print("=" * 50)
    
    try:
        mock_streamlit()
        db = MongoDB()
        
        # Get vector search statistics
        stats = db.get_vector_search_stats()
        
        print(f"📊 Migration Status Report:")
        print(f"   Total Documents: {stats['total_documents']}")
        print(f"   With Embeddings: {stats['with_embeddings']}")
        print(f"   Without Embeddings: {stats['without_embeddings']}")
        print(f"   Vector Ready: {stats['percentage_ready']}%")
        print(f"   Vector Search Enabled: {stats['vector_search_enabled']}")
        print(f"   Embedding Service Available: {stats['embedding_service_available']}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if stats['without_embeddings'] == 0:
            print("   ✅ All documents have embeddings! Migration complete.")
        elif stats['without_embeddings'] <= 10:
            print("   🟢 Small batch remaining. Use Quick Migration.")
        elif stats['without_embeddings'] <= 50:
            print("   🟡 Medium batch remaining. Use Admin interface with 10-20 doc batches.")
        else:
            print("   🟠 Large batch remaining. Migrate gradually in 20-50 doc batches.")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

def test_embedding_generation():
    """Test if embedding generation is working"""
    print("\n🧪 Testing Embedding Generation...")
    print("=" * 50)
    
    try:
        mock_streamlit()
        db = MongoDB()
        
        if not db.embedding_service:
            print("❌ Embedding service not available")
            return False
        
        # Test embedding generation
        test_text = "This is a test automation for data processing"
        embedding = db.embedding_service.generate_embedding(test_text)
        
        if embedding:
            print(f"✅ Embedding generation successful!")
            print(f"   Dimensions: {len(embedding)}")
            print(f"   Sample values: {embedding[:3]}")
            return True
        else:
            print("❌ Embedding generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False

def perform_small_migration(max_docs=5):
    """Perform a small test migration"""
    print(f"\n🚀 Performing Small Migration ({max_docs} documents)...")
    print("=" * 50)
    
    try:
        mock_streamlit()
        db = MongoDB()
        
        if not db.vector_search_enabled:
            print("❌ Vector search not enabled")
            return False
        
        # Perform migration
        print("Starting migration...")
        db.migrate_existing_data_to_vectors(batch_size=2, max_documents=max_docs)
        
        # Check results
        stats_after = db.get_vector_search_stats()
        print(f"\n📊 Migration Results:")
        print(f"   Documents with embeddings: {stats_after['with_embeddings']}")
        print(f"   Vector ready: {stats_after['percentage_ready']}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def main():
    """Main migration helper"""
    print("🚀 Vector Search Migration Helper")
    print("=" * 50)
    
    # Step 1: Check status
    stats = check_migration_status()
    if not stats:
        print("❌ Cannot proceed - database connection failed")
        return
    
    # Step 2: Test embedding generation
    if not test_embedding_generation():
        print("❌ Cannot proceed - embedding generation failed")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your Gemini API key")
        print("   2. Verify API billing is enabled")
        print("   3. Check internet connectivity")
        return
    
    # Step 3: Ask if user wants to proceed with migration
    if stats['without_embeddings'] > 0:
        print(f"\n❓ Found {stats['without_embeddings']} documents without embeddings.")
        response = input("Do you want to migrate 5 documents as a test? (y/n): ").lower()
        
        if response == 'y':
            success = perform_small_migration(5)
            if success:
                print("\n✅ Small migration completed successfully!")
                print("\n📝 Next steps:")
                print("   1. Check your Streamlit app admin interface")
                print("   2. Use 'Quick Migration' for more documents")
                print("   3. Gradually increase batch sizes")
            else:
                print("\n❌ Migration failed. Check the errors above.")
        else:
            print("\n📝 Migration skipped. Use the Streamlit admin interface when ready.")
    else:
        print("\n✅ All documents already have embeddings!")
    
    print(f"\n🎯 Summary:")
    print(f"   Vector Search: {'✅ Ready' if stats['vector_search_enabled'] else '❌ Not Ready'}")
    print(f"   Embeddings: {'✅ Working' if stats['embedding_service_available'] else '❌ Not Working'}")
    print(f"   Migration: {stats['percentage_ready']}% complete")

if __name__ == "__main__":
    main()