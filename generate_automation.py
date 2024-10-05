import streamlit as st
import PyPDF2
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_fixed

# Configure the Gemini API (you'll need to set up your API key)
try:
    genai.configure(api_key=st.secrets["API_KEY"])
except:
    st.error("API_KEY is not set in the environment variables. Please set it and restart the application.")
    st.stop()

genai.configure(api_key=os.environ["API_KEY"])
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

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

# Main Streamlit UI
def main():
    st.title("Automation Generator")

    # Input components
    domain = st.text_input("Select Domain (Required)", key="domain")
    extra_info = st.text_area("Additional Relevant Information (Optional)", key="extra_info")
    pdf_file = st.file_uploader("Upload PDF File", type="pdf")

    if pdf_file is not None:
        pdf_text = extract_text_from_pdf(pdf_file)
        
        # Generate and display summary
        with st.spinner("Generating summary..."):
            summary = gemini_summarize(pdf_text, domain, extra_info)
        
        if summary:
            st.subheader("PDF Summary")
            st.markdown(summary)
        else:
            st.warning("Failed to generate summary. Please try again or adjust your input.")

        # Function to generate all components
        def generate_all_components():
            with st.spinner("Generating automation components..."):
                # Generate block diagram
                block_diagram = gemini_generate_block_diagram(summary, domain, extra_info)
                if block_diagram:
                    st.subheader("Block Diagram of Script Flow")
                    st.markdown(f"```\n{block_diagram}\n```")
                else:
                    st.warning("Failed to generate block diagram. Please try again or adjust your input.")

                # Generate script
                script = gemini_generate_script(summary, domain, extra_info)
                if script:
                    st.subheader("Automation Script")
                    st.code(script, language="python")
                    st.download_button("Download Script", script, file_name="automation_script.py")
                else:
                    st.warning("Failed to generate script. Please try again or adjust your input.")

                # Generate prerequisites
                prerequisites = gemini_generate_prerequisites(summary, domain, extra_info)
                if prerequisites:
                    st.subheader("Prerequisites")
                    st.markdown(prerequisites)
                else:
                    st.warning("Failed to generate prerequisites. Please try again or adjust your input.")

        # Button to generate automation
        if st.button("Generate Automation"):
            generate_all_components()

        # Button to regenerate all components
        if st.button("Regenerate All"):
            generate_all_components()

if __name__ == '__main__':
    main()