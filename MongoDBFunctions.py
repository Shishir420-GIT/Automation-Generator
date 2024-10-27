import streamlit as st
import os
from datetime import datetime
from pymongo import MongoClient

class MongoDB:
    def __init__(self):
        self.client = MongoClient(os.environ["mongoDB_URI"])
        self.db = self.client["Automation"]
        self.collection = self.db["solutions"]

    def search_mongodb(self, query):
        """
        Function to perform full-text search on the summary field using MongoDB Atlas Search
        """
        pipeline = [
            {
                "$search": {
                    "index": "summary_search_index",  # Search against the 'summary' index
                    "text": {
                        "query": query,
                        "path": "summary"  # Search only in the 'summary' field
                    }
                }
            },
            {
                "$limit": 5  # Limit the number of results returned
            }
        ]
        results = list(self.collection.aggregate(pipeline))
        return results
    
    def create_search_index(self):
        """
        Function to create a search index on the summary field
        """
        index = {
            "definition": {
                "mappings": {
                    "fields": {
                        "summary": {
                            "type": "string"
                        }
                    }
                }
            },
            "name": "summary_search_index"  # This is the name of the index we'll use for searching summaries
        }
        self.collection.create_search_index(index)
        print("Search index on summary created.")

    def search_bar(self):
        """
        Function to display the search results in Streamlit
        """
        query = st.text_input("Search Solutions (Summary)")
        if query:
            results = self.search_mongodb(query)
            if results:
                st.subheader("Search Results")
                for result in results:
                    st.write(f"**Domain**: {result['domain']}")
                    st.write(f"**Summary**: {result['summary']}")
                    st.code(result['script'], language='python')
                    st.subheader("Unit Test")
                    st.code(result['unit_tests'], language='python')
                    st.write(f"**Prerequisites**: {result['prerequisites']}")
            else:
                st.warning("No results found.")
                
    # 
    def add_solution_to_mongodb(self, summary, prerequisites, script, unit_tests, domain, extra_info):
        """
        Function to add solution to MongoDB
        """
        solution = {
            "domain": domain,
            "summary": summary,
            "prerequisites": prerequisites,
            "script": script,
            "unit_tests": unit_tests,
            "extra_info": extra_info,
            "timestamp": datetime.now()
        }
        self.collection.insert_one(solution)
        st.success("Solution added to Database!")

    def save_to_mongodb_button(self, summary, script, block_diagram, prerequisites, domain, extra_info):
        """
        Button to add generated content to MongoDB
        """
        if st.button("Save Solution to Database"):
            self.add_solution_to_mongodb(summary, script, block_diagram, prerequisites, domain, extra_info)