# Automation Generator Beta

This application allows users to upload an SOP based pdf, which lets them create an Automation around it, by providing a block daigram (text based), a script and list of pre-requisites to run the script, The AI being utilized here is Gemini-pro.

Project is Live at - [Automation Generator](https://automation-generator.streamlit.app/)

## Features
- Upload SOP based PDF
- Summarising the PDF.
- AI-powered script, flow and pre-requisite generation.
- Option to regenerate review code and regenerate it.

## Dependencies

- Python 3.7+
- Streamlit
- PyPDF2
- google.generativeai

## Installation

1. Clone this repository:
  ```git
  git clone https://github.com/yourusername/GenAI-Usecases.git
  cd Automation-Generator-Beta
  ```

2. Install the required packages:
  ```python
  pip install streamlit PyPDF2 google.generativeai
  ```

## Configuration

1. Set up gemini API key:
- Create a `.streamlit/secrets.toml` file in the project directory
- Add your API key:
  ```toml
  API_KEY = "your_api_key_id"
  ```
- Do not commit this file to version control

2. Ensure you have project created in Google Cloud with valid billing.

## Usage

1. Run the Streamlit app:
   ```cmd
    streamlit generate_automation.py
   ```

2. Open the provided URL in your web browser.

3. Add Domain and additional information needed.

4. Upload a PDF document, an AI powered PDF summary will be created.

5. Review the content generated and click "Generate Automation" to start automation creation.

6. Review the block daigram, Script and the Pre-requisites.

7. Regenerate, with more additional data if need more precise output.


## Deployment

- For Streamlit Cloud deployment, add your Gemini API Key in the Streamlit Cloud dashboard under the "Secrets" section.
- For other deployment options, ensure to set the  Gemini API Key as environment variables securely.

## Notes

- This application uses Gemini API Key Bedrock, which may incur costs. Please review Gemini pricing before extended use.
- Ensure your Google cloud project is created properly and is attached to a Billing.
