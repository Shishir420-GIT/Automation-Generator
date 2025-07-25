# Automation Generator

This application allows users to upload an SOP-based PDF document and automatically create comprehensive automation solutions. The system generates professional flowcharts with proper symbols, executable scripts, and detailed prerequisites using Google's Gemini AI.

🌐 **Live Application**: [Automation Generator](https://automation-generator.streamlit.app/)

## Features
- **PDF Processing**: Upload and analyze SOP-based PDF documents
- **AI-Powered PDF Summarization**: Intelligent content extraction and summarization
- **Professional Flowchart Generation**: Creates Mermaid diagrams with proper flowchart symbols:
  - Ovals for Start/End points
  - Diamonds for Decision points
  - Rectangles for Process steps
  - Parallelograms for Input/Output operations
- **Script Generation**: AI-powered automation script creation
- **Prerequisites Analysis**: Comprehensive requirement identification
- **Interactive Workflow**: Review, regenerate, and refine automation outputs
- **Multiple Complexity Levels**: Simple, moderate, and complex flowchart generation
- **Theme Support**: Light and dark mode compatibility

## Dependencies

- Python 3.8+
- Streamlit (Web interface)
- PyPDF2 (PDF processing)
- google.generativeai (Gemini AI integration)
- base64 (File encoding)
- logging (Application logging)
- hashlib (Diagram identification)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shishir420-GIT/Automation-Generator.git
   cd Automation-Generator
   ```

2. Install the required packages:
   ```bash
   pip install streamlit PyPDF2 google.generativeai
   ```

3. Verify installation:
   ```bash
   python -c "import streamlit, PyPDF2, google.generativeai; print('All dependencies installed successfully')"
   ```

## Configuration

1. Set up gemini API key:
- Create a `.streamlit/secrets.toml` file in the project directory
- Add your API key:
  ```toml
  API_KEY = "your_api_key_id"
  mongoDB_URI = "your_mongoDB_connection_uri"
  ```
- Do not commit this file to version control

2. Ensure you have project created in Google Cloud with valid billing.

## Usage

1. **Start the Application**:
   ```bash
   streamlit run app.py
   ```

2. **Access the Web Interface**: Open the provided URL in your web browser (usually `http://localhost:8501`)

3. **Configure Your Automation**:
   - Enter the domain/industry context
   - Add any additional information for better AI understanding

4. **Upload PDF Document**: Upload your SOP-based PDF file for AI-powered analysis and summarization

5. **Generate Automation**: Click "Generate Automation" to create:
   - **Professional Flowchart**: Interactive Mermaid diagram with proper symbols
   - **Automation Script**: Executable code tailored to your requirements
   - **Prerequisites List**: Comprehensive setup and dependency requirements

6. **Review and Refine**: 
   - Examine the generated flowchart, script, and prerequisites
   - Use the regenerate option with additional context for improved precision
   - Download the flowchart for external use

7. **Interactive Features**:
   - Switch between different complexity levels
   - Apply different themes (light/dark)
   - Export diagrams and scripts


## Architecture

The application follows a modular structure:

```
Automation-Generator/
├── app.py                    # Main Streamlit application
├── utils/
│   ├── GeminiFunctions.py    # AI integration and content generation
│   ├── mermaid_renderer.py   # Flowchart generation and rendering  
│   ├── MongoDBFunctions.py   # Database operations
│   └── validators.py         # Input validation utilities
└── README.md
```

### Key Components:

- **MermaidRenderer**: Enhanced flowchart generation with proper symbols
- **FlowchartGenerator**: Converts text descriptions to professional flowcharts
- **GeminiFunctions**: AI-powered content generation using Gemini
- **Modular Design**: Organized utility functions for maintainability

## Deployment

### Streamlit Cloud (Recommended)
1. Fork this repository to your GitHub account
2. Connect your GitHub repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your Gemini API Key in Streamlit Cloud dashboard under "Secrets":
   ```toml
   API_KEY = "your_gemini_api_key"
   mongoDB_URI = "your_mongoDB_connection_uri"
   ```
4. Deploy automatically from your repository

### Local Development
- Ensure all dependencies are installed
- Set up `.streamlit/secrets.toml` with your API key
- Run `streamlit run app.py`

### Other Platforms
- Set the Gemini API Key as environment variable: `API_KEY`
- Create a free mongoDB cluster and get the connection uri: `mongoDB_URI`
- Ensure Python 3.8+ compatibility
- Install all dependencies from requirements if available

## Important Notes

⚠️ **Cost Considerations**: This application uses Google's Gemini AI API, which may incur costs based on usage. Review [Gemini pricing](https://cloud.google.com/vertex-ai/pricing) before extended use.

🔐 **Security**: 
- Never commit API keys to version control
- Use secure environment variables or secrets management
- Ensure your Google Cloud project has proper billing setup

📊 **Performance**: 
- PDF processing is optimized for standard SOP documents
- Flowchart rendering supports complex diagrams with multiple decision points
- AI generation may take 10-30 seconds depending on complexity

## Recent Updates

✅ **Enhanced Flowchart Symbols**: Updated to use proper flowchart conventions
- Ovals for Start/End points
- Diamonds for Decision points  
- Rectangles for Process steps
- Parallelograms for Input/Output operations

✅ **Improved Styling**: Professional appearance with better colors and stroke widths

✅ **Modular Architecture**: Organized code structure in `utils/` folder for better maintainability
