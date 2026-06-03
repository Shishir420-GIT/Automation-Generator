import streamlit as st
import PyPDF2
import os
from datetime import datetime
from pymongo import MongoClient
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_fixed


# Configure the Gemini API (you'll need to set up your API key)
try:
    genai.configure(api_key=os.environ["API_KEY"])
    #genai.configure(api_key=st.secrets["API_KEY"])
except:
    st.error("API_KEY is not set in the environment variables. Please set it and restart the application.")
    st.stop()

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Establish MongoDB connection (assuming credentials are in environment variables)
client = MongoClient(os.environ["mongoDB_URI"])
db = client["Automation"]
collection = db["solutions"]

# Function to perform MongoDB vector search
# Function to perform full-text search on the summary field using MongoDB Atlas Search
def search_mongodb(query):
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
    results = list(collection.aggregate(pipeline))
    return results

# Function to create a search index on the summary field
def create_search_index():
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
    collection.create_search_index(index)
    print("Search index on summary created.")

# Function to display the search results in Streamlit
def search_bar():
    query = st.text_input("Search Solutions (Summary)")
    if query:
        results = search_mongodb(query)
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
            
# Function to add solution to MongoDB
def add_solution_to_mongodb(summary, prerequisites, script, unit_tests, domain, extra_info):
    solution = {
        "domain": domain,
        "summary": summary,
        "prerequisites": prerequisites,
        "script": script,
        "unit_tests": unit_tests,
        "extra_info": extra_info,
        "timestamp": datetime.now()
    }
    collection.insert_one(solution)
    st.success("Solution added to MongoDB!")

# Button to add generated content to MongoDB
def save_to_mongodb_button(summary, script, block_diagram, prerequisites, domain, extra_info):
    if st.button("Save Solution to MongoDB"):
        add_solution_to_mongodb(summary, script, block_diagram, prerequisites, domain, extra_info)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Retry Function
@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def generate_with_retry(model, prompt):
    return model.generate_content([prompt], safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    })

# Function to generate content using Gemini
def gemini_generate_content(prompt, model_name="gemini-1.5-flash"):
    model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
    try:
        response = generate_with_retry(model, prompt)
        
        if not response.candidates:
            st.warning("Response was blocked. Check safety ratings.")
            for rating in response.prompt_feedback.safety_ratings:
                st.write(f"{rating.category}: {rating.probability}")
            return None
        
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {str(e)}")
        return None

# Function to generate summary
def gemini_summarize(text, domain, extra_info):
    prompt = f"""
    Analyze the following text from a PDF document related to the {domain} domain. 
    Additional context: {extra_info}

    Generate a summary of the document, breaking it down into the following sections:
    1. Overview: Provide a brief overview of the document's main topic and purpose.
    2. Key Points: List the main ideas or arguments presented in the document.
    3. Detailed Summary: Expand on the key points, providing more context and explanation.
    4. Conclusion: Summarize the main takeaways or conclusions from the document.
    5. Potential Automation Steps: Based on the content, suggest potential steps for automating processes described in the document.

    Text to analyze:
    {text}

    Please format the summary in a clear, structured manner.
    """
    return gemini_generate_content(prompt)

# Function to generate block diagram
def gemini_generate_block_diagram(summary, domain, extra_info):
    prompt = f"""
    Based on the following summary of a document in the {domain} domain,
    Create a block diagram of the automation script flow.
    Make it labelled and understandable.
    Additional context: {extra_info}

    Summary:
    {summary}

    Please provide a textual representation of the block diagram,
    using ASCII characters or markdown formatting to illustrate the flow.
    """
    return gemini_generate_content(prompt)

# Function to generate script
def gemini_generate_script(summary, domain, extra_info):
    prompt = f"""
    Based on the following summary of a document in the {domain} domain,
    create a completely safe to run script to automate the described process.
    Select the appropriate language based on the requirement.
    Make sure there is no dangerous content in your response.
    Additional context: {extra_info}

    Summary:
    {summary}

    Please provide a detailed Python script with comments explaining each step of the automation process.
    """
    return gemini_generate_content(prompt)

# Function to generate unit tests for the script
def gemini_generate_unit_tests(summary, script, domain, extra_info):
    prompt = f"""
    Based on the following summary of a document in the {domain} domain and the generated Python script,
    create unit tests to validate the correctness of the script. Include tests for key functionality 
    and edge cases. Make sure the tests follow best practices using Python's unittest framework.

    Summary:
    {summary}

    Script:
    {script}

    Additional context: {extra_info}
    
    Please provide a detailed unit test code.
    """
    return gemini_generate_content(prompt)

# Function to generate prerequisites
def gemini_generate_prerequisites(summary, domain, extra_info):
    prompt = f"""
    Based on the following summary of a document in the {domain} domain,
    List the prerequisites needed for the automation to run, breaking it down into the following sections:
    1. Hardware Requirement: List which kind of server or machines would be required.
    2. Software requirement: List which packages or libraries or software would be required.
    3. Access Requirement: List out different kinds of access a person would require.
    4. Additional information: Based on the above steps, conclude and list any additional requirements left.
    Additional context: {extra_info}

    Summary:
    {summary}

    Please provide a comprehensive list of prerequisites, including software, libraries, and any specific configurations needed.
    """
    return gemini_generate_content(prompt)

# Main Function
def main():
    st.title("Automation Generator")

    search_bar()

    domain = st.text_input("Select Domain")
    extra_info = st.text_area("Additional Information")
    pdf_file = st.file_uploader("Upload PDF", type="pdf")

    if pdf_file:
        pdf_text = extract_text_from_pdf(pdf_file)
        summary = gemini_summarize(pdf_text, domain, extra_info)

        if summary:
            st.subheader("Summary")
            st.write(summary)

            block_diagram = gemini_generate_block_diagram(summary, domain, extra_info)
            st.subheader("Block Diagram")
            st.markdown(f"```\n{block_diagram}\n```")

            script = gemini_generate_script(summary, domain, extra_info)
            st.subheader("Automation Script")
            st.code(script, language='python')

            unit_tests = gemini_generate_unit_tests(summary, script, domain, extra_info)
            st.subheader("Unit Test Script")
            st.code(unit_tests, language='python')

            prerequisites = gemini_generate_prerequisites(summary, domain, extra_info)
            st.subheader("Prerequisites")
            st.write(prerequisites)

            if st.button("Save to MongoDB"):
                add_solution_to_mongodb(summary, script, block_diagram, prerequisites, domain, extra_info)

if __name__ == '__main__':
    #create_search_index()
    main()