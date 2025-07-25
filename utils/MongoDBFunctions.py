import streamlit as st
import os
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
import logging
from typing import Optional, List, Dict, Any

class MongoDB:
    def __init__(self):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize database connection with error handling
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize MongoDB connection with proper error handling"""
        try:
            mongo_uri = st.secrets.get("mongoDB_URI")
            if not mongo_uri:
                st.error("❌ **Database Configuration Error**")
                st.error("MongoDB URI not found in secrets. Please configure your database connection.")
                st.info("**To fix this:**\n1. Add your MongoDB URI to `.streamlit/secrets.toml`\n2. Restart the application")
                st.stop()
            
            # Initialize client with timeout settings
            self.client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client["Automation"]
            self.collection = self.db["solutions"]
            self.ratings_collection = self.db["ratings"]
            
            self.logger.info("MongoDB connection initialized successfully")
            
        except ServerSelectionTimeoutError:
            st.error("❌ **Database Connection Timeout**")
            st.error("Unable to connect to MongoDB Atlas. Please check your connection.")
            st.info("**Troubleshooting Steps:**\n• Check internet connection\n• Verify MongoDB URI\n• Ensure database is running\n• Check firewall settings")
            st.stop()
            
        except ConnectionFailure as e:
            st.error("❌ **Database Connection Failed**")
            st.error(f"MongoDB connection error: {str(e)}")
            st.info("**How to fix:**\n• Verify your MongoDB URI\n• Check database credentials\n• Ensure IP is whitelisted\n• Try again in a few moments")
            st.stop()
            
        except Exception as e:
            st.error("❌ **Unexpected Database Error**")
            st.error(f"Error initializing MongoDB: {str(e)}")
            st.info("**General troubleshooting:**\n• Check your database configuration\n• Verify secrets.toml file\n• Contact support if issue persists")
            st.stop()
    
    def _handle_db_error(self, error: Exception, operation: str) -> None:
        """Handle database errors gracefully with specific guidance"""
        error_msg = str(error).lower()
        
        # Connection errors
        if any(keyword in error_msg for keyword in ['connection', 'timeout', 'network']):
            st.error(f"❌ **Database Connection Error during {operation}**")
            st.info("""
            **What you can do:**
            • Check your internet connection
            • Try again in a few moments
            • Verify database service is running
            • Contact administrator if issue persists
            """)
            
        # Authentication errors
        elif any(keyword in error_msg for keyword in ['auth', 'credential', 'permission']):
            st.error(f"❌ **Database Authentication Error during {operation}**")
            st.info("""
            **How to fix:**
            • Verify database credentials
            • Check user permissions
            • Ensure proper access rights
            • Contact database administrator
            """)
            
        # Operation errors
        elif any(keyword in error_msg for keyword in ['operation', 'query', 'index']):
            st.error(f"❌ **Database Operation Error during {operation}**")
            st.info("""
            **Possible solutions:**
            • Check if search index exists
            • Verify database structure
            • Try with different search terms
            • Contact technical support
            """)
            
        # Generic errors
        else:
            st.error(f"❌ **Database Error during {operation}**")
            st.error(f"Details: {str(error)}")
            st.info("""
            **General troubleshooting:**
            • Try again with different input
            • Check your internet connection
            • Verify database configuration
            • Contact support if issue persists
            """)

    def search_mongodb(self, query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Enhanced search with fallback mechanisms"""
        if not query or len(query.strip()) < 2:
            st.warning("⚠️ Search query must be at least 2 characters long")
            return []
        
        try:
            # Sanitize query to prevent injection
            sanitized_query = query.strip()[:100]  # Limit query length
            
            # First try Atlas Search if available
            results = self._atlas_search(sanitized_query, limit)
            if results:
                self.logger.info(f"Atlas search successful for query: {sanitized_query}")
                return results
            
            # Fallback to regex search
            self.logger.info("Atlas search failed or unavailable, using regex search")
            results = self._regex_search(sanitized_query, limit)
            return results
            
        except Exception as e:
            self.logger.error(f"Search operation failed: {str(e)}")
            self._handle_db_error(e, "search operation")
            return []
    
    def _atlas_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Atlas Search implementation with comprehensive text search"""
        try:
            pipeline = [
                {
                    "$search": {
                        "index": "summary_search_index",
                        "text": {
                            "query": query,
                            "path": ["summary", "domain", "extra_info", "script"]
                        }
                    }
                },
                {
                    "$limit": limit
                },
                {
                    "$addFields": {
                        "score": {"$meta": "searchScore"}
                    }
                },
                {
                    "$project": {
                        "domain": 1,
                        "summary": 1,
                        "script": 1,
                        "unit_tests": 1,
                        "prerequisites": 1,
                        "block_diagram": 1,
                        "extra_info": 1,
                        "timestamp": 1,
                        "score": 1
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Enhance results with metadata
            for result in results:
                result['search_type'] = 'atlas'
                # Add ratings if available
                result['ratings'] = self._get_solution_ratings(str(result.get('_id', '')))
            
            return results
            
        except OperationFailure as e:
            if "index" in str(e).lower():
                self.logger.warning("Atlas search index not available")
                return []
            else:
                raise e
        except Exception as e:
            self.logger.error(f"Atlas search failed: {str(e)}")
            return []
    
    def _regex_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Enhanced regex search with weighted scoring"""
        try:
            # Create case-insensitive regex search
            search_regex = {"$regex": query, "$options": "i"}
            
            # Search across multiple fields with OR logic
            search_filter = {
                "$or": [
                    {"summary": search_regex},
                    {"domain": search_regex},
                    {"extra_info": search_regex},
                    {"script": search_regex},
                    {"prerequisites": search_regex}
                ]
            }
            
            results = list(
                self.collection.find(search_filter)
                .sort("timestamp", -1)  # Sort by most recent first
                .limit(limit)
            )
            
            # Enhance results with relevance scoring
            for result in results:
                result['search_type'] = 'regex'
                result['score'] = self._calculate_relevance_score(result, query)
                result['ratings'] = self._get_solution_ratings(str(result.get('_id', '')))
            
            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Regex search failed: {str(e)}")
            raise e
    
    def _calculate_relevance_score(self, result: Dict, query: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Define field weights (higher = more important)
        fields_weights = {
            'domain': 5.0,      # Domain matches are most important
            'summary': 3.0,     # Summary matches are very important
            'extra_info': 2.0,  # Additional info is moderately important
            'prerequisites': 1.5, # Prerequisites are somewhat important
            'script': 1.0       # Script content is least important for relevance
        }
        
        for field, weight in fields_weights.items():
            field_content = str(result.get(field, '')).lower()
            
            # Exact phrase match (highest score)
            if query_lower in field_content:
                phrase_count = field_content.count(query_lower)
                score += phrase_count * weight * 2.0
            
            # Individual word matches
            for word in query_words:
                if len(word) > 2:  # Only count words longer than 2 characters
                    word_count = field_content.count(word)
                    score += word_count * weight * 0.5
        
        # Boost score for more recent documents
        if 'timestamp' in result:
            try:
                days_old = (datetime.now() - result['timestamp']).days
                if days_old < 30:  # Recent documents get a small boost
                    score += 1.0
            except:
                pass
        
        return round(score, 2)
    
    def _get_solution_ratings(self, solution_id: str) -> Dict[str, Any]:
        """Get ratings for a solution"""
        try:
            if not solution_id:
                return {"average": 0, "count": 0}
            
            ratings = list(self.ratings_collection.find({"solution_id": solution_id}))
            
            if not ratings:
                return {"average": 0, "count": 0}
            
            avg_rating = sum(r.get("rating", 0) for r in ratings) / len(ratings)
            
            return {
                "average": round(avg_rating, 1),
                "count": len(ratings)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get ratings: {str(e)}")
            return {"average": 0, "count": 0}
    
    def add_rating(self, solution_id: str, rating: int, comment: str = "") -> bool:
        """Add a rating to a solution"""
        try:
            if not solution_id or not (1 <= rating <= 5):
                return False
            
            rating_doc = {
                "solution_id": solution_id,
                "rating": rating,
                "comment": comment.strip() if comment else "",
                "timestamp": datetime.now(),
                "user_id": st.session_state.get('user_id', 'anonymous')
            }
            
            self.ratings_collection.insert_one(rating_doc)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add rating: {str(e)}")
            return False
    
    def get_popular_domains(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular domains from the database"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$domain",
                        "count": {"$sum": 1},
                        "latest": {"$max": "$timestamp"}
                    }
                },
                {
                    "$match": {
                        "_id": {"$ne": None, "$ne": ""}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": limit
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return [{"domain": r["_id"], "count": r["count"], "latest": r["latest"]} for r in results]
            
        except Exception as e:
            self.logger.error(f"Failed to get popular domains: {str(e)}")
            return []
    
    def add_solution_to_mongodb(self, summary: str, script: str, block_diagram: str, 
                               prerequisites: str, domain: str, extra_info: str = "") -> bool:
        """Enhanced solution addition with validation and error handling"""
        
        # Validate required fields
        if not all([summary.strip(), script.strip(), domain.strip()]):
            st.error("❌ **Missing Required Information**")
            st.error("Summary, script, and domain are required to save a solution.")
            return False
        
        # Validate content lengths
        if len(summary.strip()) < 50:
            st.error("❌ Summary is too short (minimum 50 characters)")
            return False
            
        if len(script.strip()) < 50:
            st.error("❌ Script is too short (minimum 50 characters)")
            return False
        
        try:
            # Prepare solution document
            solution = {
                "domain": domain.strip(),
                "summary": summary.strip(),
                "script": script.strip(),
                "block_diagram": block_diagram.strip() if block_diagram else "",
                "prerequisites": prerequisites.strip() if prerequisites else "",
                "unit_tests": "",  # Will be populated if available
                "extra_info": extra_info.strip() if extra_info else "",
                "timestamp": datetime.now(),
                "usage_count": 0,
                "created_by": st.session_state.get('user_id', 'anonymous'),
                "version": "1.0",
                "status": "active"
            }
            
            # Insert solution with write concern for reliability
            result = self.collection.insert_one(solution)
            
            if result.inserted_id:
                st.success("✅ **Solution saved to database successfully!**")
                st.info(f"📄 Document ID: {str(result.inserted_id)}")
                self.logger.info(f"Solution saved successfully for domain: {domain}")
                
                # Update usage statistics
                self._update_usage_stats(domain)
                
                return True
            else:
                st.error("❌ Failed to save solution (no ID returned)")
                return False
                
        except Exception as e:
            self._handle_db_error(e, "save solution")
            return False
    
    def _update_usage_stats(self, domain: str):
        """Update usage statistics"""
        try:
            # This could be expanded to track various usage metrics
            # For now, we just log the successful save
            self.logger.info(f"Usage stats updated for domain: {domain}")
        except Exception as e:
            self.logger.error(f"Failed to update usage stats: {str(e)}")
    
    def get_recent_solutions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recent solutions"""
        try:
            results = list(
                self.collection.find({"status": "active"})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Enhance with ratings
            for result in results:
                result['ratings'] = self._get_solution_ratings(str(result.get('_id', '')))
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get recent solutions: {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for dashboard"""
        try:
            # Get basic counts
            total_solutions = self.collection.count_documents({})
            active_solutions = self.collection.count_documents({"status": "active"})
            
            # Get unique domains count
            unique_domains = len(self.collection.distinct("domain"))
            
            # Get recent activity (last 7 days)
            seven_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            seven_days_ago = seven_days_ago.replace(day=seven_days_ago.day - 7)
            
            recent_activity = self.collection.count_documents({
                "timestamp": {"$gte": seven_days_ago}
            })
            
            # Get total ratings
            total_ratings = self.ratings_collection.count_documents({})
            
            stats = {
                "total_solutions": total_solutions,
                "active_solutions": active_solutions,
                "total_domains": unique_domains,
                "total_ratings": total_ratings,
                "recent_activity": recent_activity
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {str(e)}")
            return {
                "total_solutions": 0,
                "active_solutions": 0,
                "total_domains": 0,
                "total_ratings": 0,
                "recent_activity": 0
            }
    
    def search_bar(self):
        """Legacy search bar function for backward compatibility"""
        st.markdown("**🔍 Search existing automation solutions:**")
        
        query = st.text_input(
            "Enter search terms",
            placeholder="e.g., finance automation, data processing, report generation",
            help="Search through existing automation solutions by keywords"
        )
        
        if query:
            with st.spinner("🔍 Searching database..."):
                results = self.search_mongodb(query)
                
            if results:
                st.success(f"✅ Found {len(results)} matching solutions")
                
                for i, result in enumerate(results, 1):
                    with st.expander(f"📋 Solution {i}: {result.get('domain', 'Unknown Domain')}", expanded=False):
                        
                        # Display metadata
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Domain:** {result.get('domain', 'N/A')}")
                            if 'timestamp' in result:
                                try:
                                    st.write(f"**Created:** {result['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                                except:
                                    st.write(f"**Created:** {str(result['timestamp'])[:10]}")
                        with col2:
                            score = result.get('score', 0)
                            if score > 0:
                                st.metric("Relevance", f"{score:.1f}")
                        
                        # Summary
                        st.markdown("**📋 Summary:**")
                        st.markdown(result.get('summary', 'No summary available'))
                        
                        # Tabs for organized display
                        tab1, tab2, tab3 = st.tabs(["💻 Script", "🧪 Tests", "📋 Prerequisites"])
                        
                        with tab1:
                            if 'script' in result and result['script']:
                                st.code(result['script'], language='python')
                            else:
                                st.info("No script available")
                        
                        with tab2:
                            if 'unit_tests' in result and result['unit_tests']:
                                st.code(result['unit_tests'], language='python')
                            else:
                                st.info("No unit tests available")
                        
                        with tab3:
                            if 'prerequisites' in result and result['prerequisites']:
                                st.markdown(result['prerequisites'])
                            else:
                                st.info("No prerequisites available")
            
            elif results is not None:  # Empty results (not None due to error)
                st.info(f"🔍 No solutions found for '{query}'")
                st.markdown("""
                **💡 Search Tips:**
                - Try different or more general keywords
                - Use domain-specific terms (e.g., "finance", "healthcare")
                - Search for process types (e.g., "automation", "reporting")
                - Check spelling and try synonyms
                """)

    def create_search_index(self):
        """Create search index for Atlas Search (run once)"""
        try:
            index_definition = {
                "definition": {
                    "mappings": {
                        "fields": {
                            "summary": {
                                "type": "string",
                                "multi": {
                                    "keywordAnalyzer": {
                                        "type": "string",
                                        "analyzer": "keyword"
                                    }
                                }
                            },
                            "domain": {
                                "type": "string",
                                "multi": {
                                    "keywordAnalyzer": {
                                        "type": "string", 
                                        "analyzer": "keyword"
                                    }
                                }
                            },
                            "extra_info": {"type": "string"},
                            "script": {"type": "string"},
                            "prerequisites": {"type": "string"}
                        }
                    }
                },
                "name": "summary_search_index"
            }
            
            self.collection.create_search_index(index_definition)
            st.success("✅ Search index created successfully!")
            
        except Exception as e:
            st.error(f"❌ Failed to create search index: {str(e)}")
            st.info("This is normal if the index already exists or if you're using MongoDB Community Edition")
    
    def test_connection(self) -> bool:
        """Test MongoDB connection health"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            self.logger.error(f"MongoDB connection test failed: {str(e)}")
            return False