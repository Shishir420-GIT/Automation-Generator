import streamlit as st
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_fixed

class GenerativeFunction:
    def __init__(self):
        # Configure the Gemini API (you'll need to set up your API key)
        try:
            genai.configure(api_key=os.environ["API_KEY"])
            #genai.configure(api_key=st.secrets["API_KEY"])
        except:
            st.error("API_KEY is not set in the environment variables. Please set it and restart the application.")
            st.stop()

        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

    # Retry Function
    #@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    def generate_with_retry(model, prompt):
        return model.generate_content([prompt], safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        })

    # Function to generate content using Gemini
    def gemini_generate_content(self, prompt, model_name="gemini-1.5-flash"):
        model = genai.GenerativeModel(model_name=model_name, generation_config=self.generation_config)
        try:
            #print(model)
            #print(prompt)
            #response = self.generate_with_retry(model, prompt)
            response = model.generate_content([prompt], safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            })
            
            if not response.candidates:
                st.warning("Response was blocked. Check safety ratings.")
                for rating in response.prompt_feedback.safety_ratings:
                    st.write(f"{rating.category}: {rating.probability}")
                return None
            
            return response.text
        except Exception as e:
            print(str(e))
            st.error(f"Error generating content here: {str(e)}")
            return None

    # Function to generate summary
    def gemini_summarize(self, text, domain, extra_info):
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
        return self.gemini_generate_content(prompt)

    # Function to generate block diagram
    def gemini_generate_block_diagram(self, summary, domain, extra_info):
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
        return self.gemini_generate_content(prompt)

    # Function to generate script
    def gemini_generate_script(self, summary, domain, extra_info):
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
        return self.gemini_generate_content(prompt)

    # Function to generate unit tests for the script
    def gemini_generate_unit_tests(self, summary, script, domain, extra_info):
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
        return self.gemini_generate_content(prompt)

    # Function to generate prerequisites
    def gemini_generate_prerequisites(self, summary, domain, extra_info):
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
        return self.gemini_generate_content(prompt)