import streamlit as st
import logging
from .MongoDBFunctions import MongoDB
from datetime import datetime
from typing import Dict, Any

class VectorSearchAdmin:
    """
    Admin utilities for managing vector search functionality
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def render_vector_search_dashboard(self):
        """Render the vector search management dashboard"""
        
        st.markdown("## 🔍 Vector Search Management")
        st.markdown("---")
        
        # Initialize MongoDB connection
        try:
            db = MongoDB()
            
            # Display vector search status
            self._render_status_section(db)
            
            # Display statistics
            self._render_stats_section(db)
            
            # Management actions
            self._render_management_actions(db)
            
        except Exception as e:
            st.error(f"❌ Failed to initialize database connection: {e}")
            st.info("Please check your MongoDB configuration and try again.")
    
    def _render_status_section(self, db: MongoDB):
        """Render the status section"""
        
        st.markdown("### 📊 Vector Search Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if db.vector_search_enabled:
                st.success("🟢 **Vector Search: Enabled**")
            else:
                st.error("🔴 **Vector Search: Disabled**")
        
        with col2:
            if db.embedding_service is not None:
                st.success("🟢 **Embedding Service: Available**")
            else:
                st.error("🔴 **Embedding Service: Unavailable**")
        
        with col3:
            if db.test_connection():
                st.success("🟢 **Database: Connected**")
            else:
                st.error("🔴 **Database: Disconnected**")
    
    def _render_stats_section(self, db: MongoDB):
        """Render the statistics section"""
        
        st.markdown("### 📈 Vector Search Statistics")
        
        try:
            stats = db.get_vector_search_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Documents", 
                    stats['total_documents'],
                    help="Total number of automation solutions in the database"
                )
            
            with col2:
                st.metric(
                    "With Embeddings", 
                    stats['with_embeddings'],
                    help="Documents that have vector embeddings for semantic search"
                )
            
            with col3:
                st.metric(
                    "Without Embeddings", 
                    stats['without_embeddings'],
                    help="Documents that need migration to support vector search"
                )
            
            with col4:
                st.metric(
                    "Vector Ready", 
                    f"{stats['percentage_ready']}%",
                    help="Percentage of documents ready for vector search"
                )
            
            # Progress bar
            if stats['total_documents'] > 0:
                progress = stats['with_embeddings'] / stats['total_documents']
                st.progress(progress)
                st.caption(f"Vector search readiness: {stats['with_embeddings']}/{stats['total_documents']} documents")
            
        except Exception as e:
            st.error(f"❌ Failed to load statistics: {e}")
    
    def _render_management_actions(self, db: MongoDB):
        """Render management action buttons"""
        
        st.markdown("### ⚙️ Management Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Index Management")
            
            if st.button("🔧 Create Vector Search Index", help="Create the vector search index in MongoDB Atlas"):
                with st.spinner("Creating vector search index..."):
                    try:
                        db.create_vector_search_index()
                    except Exception as e:
                        st.error(f"Failed to create index: {e}")
            
            if st.button("🔧 Create Text Search Index", help="Create the text search index in MongoDB Atlas"):
                with st.spinner("Creating text search index..."):
                    try:
                        db.create_search_index()
                    except Exception as e:
                        st.error(f"Failed to create index: {e}")
        
        with col2:
            st.markdown("#### Data Migration")
            
            # Migration controls
            max_docs = st.number_input(
                "Max documents to migrate", 
                min_value=1, 
                max_value=1000, 
                value=50,
                help="Limit the number of documents to migrate in one batch"
            )
            
            if st.button("🚀 Migrate Documents to Vector Search", help="Add vector embeddings to existing documents"):
                if not db.vector_search_enabled:
                    st.error("❌ Vector search is not enabled. Check your API configuration.")
                else:
                    with st.spinner("Migrating documents..."):
                        try:
                            db.migrate_existing_data_to_vectors(
                                batch_size=5,
                                max_documents=max_docs
                            )
                        except Exception as e:
                            st.error(f"Migration failed: {e}")
    
    def render_search_test_interface(self):
        """Render interface for testing search functionality"""
        
        st.markdown("### 🧪 Search Testing")
        st.markdown("Test different search methods to compare results")
        
        # Search input
        test_query = st.text_input(
            "Enter test search query:",
            placeholder="e.g., python web scraping automation, finance data processing",
            help="Enter a search query to test different search methods"
        )
        
        if test_query:
            try:
                db = MongoDB()
                
                # Create tabs for different search methods
                tab1, tab2, tab3, tab4 = st.tabs([
                    "🔍 Current Search", 
                    "⚡ Vector Search", 
                    "📝 Text Search", 
                    "🔄 Hybrid Search"
                ])
                
                with tab1:
                    st.markdown("**Current Search Method (Auto-fallback)**")
                    with st.spinner("Searching..."):
                        results = db.search_mongodb(test_query, limit=5)
                        self._display_search_results(results, "current")
                
                with tab2:
                    st.markdown("**Vector Search Only**")
                    if db.vector_search_enabled:
                        with st.spinner("Searching with vectors..."):
                            results = db.vector_search_mongodb(test_query, limit=5)
                            self._display_search_results(results, "vector")
                    else:
                        st.warning("Vector search not available")
                
                with tab3:
                    st.markdown("**Text Search Only**")
                    with st.spinner("Searching with text..."):
                        results = db._atlas_search(test_query, limit=5)
                        self._display_search_results(results, "text")
                
                with tab4:
                    st.markdown("**Hybrid Search (Vector + Text)**")
                    if db.vector_search_enabled:
                        with st.spinner("Searching with hybrid method..."):
                            results = db.hybrid_search_mongodb(test_query, limit=5)
                            self._display_search_results(results, "hybrid")
                    else:
                        st.warning("Hybrid search not available (requires vector search)")
                        
            except Exception as e:
                st.error(f"❌ Search test failed: {e}")
    
    def _display_search_results(self, results, search_type):
        """Display search results in a formatted way"""
        
        if not results:
            st.info(f"No results found using {search_type} search")
            return
        
        st.success(f"Found {len(results)} results using {search_type} search")
        
        for i, result in enumerate(results, 1):
            with st.expander(f"Result {i}: {result.get('domain', 'Unknown')}", expanded=False):
                
                # Display scores
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Domain:** {result.get('domain', 'N/A')}")
                    st.write(f"**Search Type:** {result.get('search_type', search_type)}")
                
                with col2:
                    # Display relevant scores
                    if 'vector_score' in result:
                        st.metric("Vector Score", f"{result['vector_score']:.3f}")
                    elif 'score' in result:
                        st.metric("Text Score", f"{result['score']:.1f}")
                    elif 'combined_score' in result:
                        st.metric("Combined Score", f"{result['combined_score']:.1f}")
                
                # Display summary
                st.markdown("**Summary:**")
                st.write(result.get('summary', 'No summary available')[:200] + "...")
                
                # Show search sources for hybrid results
                if 'search_sources' in result:
                    sources = ", ".join(result['search_sources'])
                    st.caption(f"Found via: {sources}")
    
    def render_embedding_test_interface(self):
        """Render interface for testing embedding generation"""
        
        st.markdown("### 🧬 Embedding Testing")
        st.markdown("Test the embedding generation service")
        
        # Test text input
        test_text = st.text_area(
            "Enter text to generate embedding:",
            placeholder="Enter some text to test embedding generation...",
            help="This will test if the Gemini embedding service is working properly"
        )
        
        if st.button("🧪 Generate Test Embedding"):
            if not test_text.strip():
                st.warning("Please enter some test text")
                return
            
            try:
                db = MongoDB()
                
                if not db.embedding_service:
                    st.error("❌ Embedding service not available")
                    return
                
                with st.spinner("Generating embedding..."):
                    # Test document embedding
                    doc_embedding = db.embedding_service.generate_embedding(test_text)
                    
                    # Test query embedding  
                    query_embedding = db.embedding_service.generate_query_embedding(test_text)
                
                if doc_embedding and query_embedding:
                    st.success("✅ Embedding generation successful!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Document Embedding Dimensions", len(doc_embedding))
                        st.write("First 5 values:", doc_embedding[:5])
                    
                    with col2:
                        st.metric("Query Embedding Dimensions", len(query_embedding))
                        st.write("First 5 values:", query_embedding[:5])
                    
                    # Calculate similarity
                    import numpy as np
                    similarity = np.dot(doc_embedding, query_embedding) / (
                        np.linalg.norm(doc_embedding) * np.linalg.norm(query_embedding)
                    )
                    st.metric("Cosine Similarity", f"{similarity:.4f}")
                    
                else:
                    st.error("❌ Failed to generate embeddings")
                    
            except Exception as e:
                st.error(f"❌ Embedding test failed: {e}")

def render_vector_admin_page():
    """Main function to render the vector search admin page"""
    
    st.set_page_config(
        page_title="Vector Search Admin",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Vector Search Administration")
    st.markdown("Manage and monitor semantic search capabilities")
    
    admin = VectorSearchAdmin()
    
    # Main dashboard
    admin.render_vector_search_dashboard()
    
    st.markdown("---")
    
    # Testing interfaces
    col1, col2 = st.columns(2)
    
    with col1:
        admin.render_search_test_interface()
    
    with col2:
        admin.render_embedding_test_interface()

if __name__ == "__main__":
    render_vector_admin_page()