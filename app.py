import streamlit as st
import PyPDF2
from GeminiFunctions import GenerativeFunction
from MongoDBFunctions import MongoDB
import time

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Automation Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components with caching
@st.cache_resource
def init_components():
    """Initialize and cache expensive components"""
    try:
        gemini = GenerativeFunction()
        mongo_db = MongoDB()
        return gemini, mongo_db
    except Exception as e:
        st.error(f"❌ Failed to initialize components: {str(e)}")
        st.stop()

def extract_text_from_pdf(pdf_file):
    """Enhanced PDF extraction with progress bar"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        total_pages = len(pdf_reader.pages)
        
        if total_pages == 0:
            st.error("❌ PDF appears to be empty")
            return None
        
        # Progress bar for PDF processing
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                text += page.extract_text()
                progress = (i + 1) / total_pages
                progress_bar.progress(progress)
                status_text.text(f"Processing page {i + 1} of {total_pages}")
            except Exception as e:
                st.warning(f"Could not extract text from page {i + 1}: {str(e)}")
                continue
        
        progress_bar.progress(1.0)
        status_text.text("✅ PDF processing complete!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return text
        
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        return None

def validate_inputs(domain, pdf_file, pdf_text):
    """Validate user inputs"""
    errors = []
    
    if not domain or len(domain.strip()) < 2:
        errors.append("Domain must be at least 2 characters long")
    
    if not pdf_file:
        errors.append("Please upload a PDF file")
    
    if pdf_file and pdf_file.size > 20 * 1024 * 1024:  # 20MB
        errors.append("PDF file must be smaller than 20MB")
    
    if pdf_text and len(pdf_text.strip()) < 100:
        errors.append("PDF content is too short for meaningful analysis (minimum 100 characters)")
    
    return errors

def main():
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .info-box {
        background: #E3F2FD;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #E8F5E8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    
    .upload-area {
        background: #F8F9FA;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #DEE2E6;
        text-align: center;
        margin: 1rem 0;
    }
    
    .metrics-container {
        background: #F0F2F6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Automation Generator</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <p style="margin: 0; text-align: center;">
            Transform your Standard Operating Procedures into automated workflows with AI assistance
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    gemini, mongo_db = init_components()
    
    # Search existing solutions section
    with st.expander("🔍 Search Existing Solutions", expanded=False):
        st.markdown("**Find automation solutions created by the community**")
        mongo_db.search_bar()
    
    st.markdown("---")
    
    # Main content area
    st.header("📝 Create New Automation")
    
    # Input section with better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Domain input
        domain = st.text_input(
            "🏢 Domain/Industry *",
            placeholder="e.g., Finance, Healthcare, IT Operations, Manufacturing",
            help="Specify the domain or industry for better AI understanding"
        )
        
        # Additional info
        extra_info = st.text_area(
            "📋 Additional Context (Optional)",
            placeholder="Provide specific requirements, constraints, or additional information that will help generate better automation...",
            height=100,
            help="The more context you provide, the better the generated automation will be"
        )
    
    with col2:
        # Tips and information
        st.markdown("""
        <div class="info-box">
            <h4>💡 Tips for Better Results</h4>
            <ul style="margin: 0.5rem 0;">
                <li>Use clear, well-structured SOPs</li>
                <li>Provide specific domain information</li>
                <li>Include relevant context</li>
                <li>Ensure PDFs have readable text</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # File upload section
    st.subheader("📄 Upload Your SOP Document")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload your Standard Operating Procedure document (Maximum 20MB)",
        accept_multiple_files=False
    )
    
    # File information display
    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**📁 File Information:**")
            file_info = {
                "📝 Filename": uploaded_file.name,
                "📊 Size": f"{uploaded_file.size / (1024*1024):.2f} MB",
                "🗂️ Type": uploaded_file.type
            }
            
            for key, value in file_info.items():
                st.write(f"{key}: {value}")
        
        with col2:
            # File validation feedback
            if uploaded_file.size <= 20 * 1024 * 1024:
                st.markdown("""
                <div class="success-box">
                    <p style="margin: 0;"><strong>✅ File Ready</strong><br>Your PDF is ready for processing</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("❌ File too large! Please upload a file smaller than 20MB.")
    
    # Process the document
    if uploaded_file and domain:
        # Extract text from PDF
        with st.spinner("📖 Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
        
        # Validate inputs
        validation_errors = validate_inputs(domain, uploaded_file, pdf_text)
        
        if validation_errors:
            st.error("❌ **Please fix the following errors:**")
            for error in validation_errors:
                st.write(f"• {error}")
            st.stop()
        
        if pdf_text:
            # Show extraction success
            st.markdown(f"""
            <div class="success-box">
                <p style="margin: 0;"><strong>✅ Text Extraction Successful</strong><br>
                Extracted {len(pdf_text):,} characters from {len(PyPDF2.PdfReader(uploaded_file).pages)} pages</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Generate summary
            with st.spinner("🧠 Analyzing document and generating summary..."):
                summary = gemini.gemini_summarize(pdf_text, domain, extra_info)
            
            if summary:
                # Display summary
                st.subheader("📋 Document Analysis Summary")
                st.markdown(summary)
                
                # Action buttons
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    generate_button = st.button(
                        "🚀 Generate Complete Automation",
                        type="primary",
                        use_container_width=True,
                        help="Generate script, tests, flow diagram, and prerequisites"
                    )
                
                with col2:
                    regenerate_summary = st.button(
                        "🔄 Regenerate Summary",
                        use_container_width=True,
                        help="Generate a new summary with the same content"
                    )
                
                with col3:
                    if st.button(
                        "⚙️ Advanced Options",
                        use_container_width=True,
                        help="Show advanced generation options"
                    ):
                        st.session_state.show_advanced = not st.session_state.get('show_advanced', False)
                
                # Advanced options
                if st.session_state.get('show_advanced', False):
                    with st.expander("⚙️ Advanced Generation Options", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            complexity_level = st.selectbox(
                                "Complexity Level",
                                ["Simple", "Moderate", "Complex", "Expert"],
                                index=1,
                                help="Choose the complexity level for generated automation"
                            )
                            
                            include_tests = st.checkbox(
                                "Generate Unit Tests",
                                value=True,
                                help="Include comprehensive unit tests"
                            )
                        
                        with col2:
                            script_language = st.selectbox(
                                "Preferred Language",
                                ["Auto-detect", "Python", "PowerShell", "Bash", "JavaScript"],
                                help="Choose programming language (Auto-detect recommended)"
                            )
                            
                            include_comments = st.checkbox(
                                "Detailed Comments",
                                value=True,
                                help="Include detailed code comments and documentation"
                            )
                
                # Regenerate summary
                if regenerate_summary:
                    st.rerun()
                
                # Generate automation
                if generate_button:
                    st.markdown("---")
                    st.subheader("🎯 Generating Your Automation")
                    
                    # Progress tracking
                    progress_container = st.container()
                    
                    with progress_container:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            # Step 1: Block Diagram
                            status_text.text("📊 Creating process flow diagram...")
                            progress_bar.progress(0.2)
                            time.sleep(0.5)  # Small delay for UX
                            
                            block_diagram = gemini.gemini_generate_block_diagram(summary, domain, extra_info)
                            
                            # Step 2: Script Generation  
                            status_text.text("💻 Generating automation script...")
                            progress_bar.progress(0.4)
                            time.sleep(0.5)
                            
                            script = gemini.gemini_generate_script(summary, domain, extra_info)
                            
                            # Step 3: Unit Tests
                            status_text.text("🧪 Creating unit tests...")
                            progress_bar.progress(0.7)
                            time.sleep(0.5)
                            
                            unit_tests = gemini.gemini_generate_unit_tests(summary, script, domain, extra_info)
                            
                            # Step 4: Prerequisites
                            status_text.text("📋 Identifying prerequisites...")
                            progress_bar.progress(0.9)
                            time.sleep(0.5)
                            
                            prerequisites = gemini.gemini_generate_prerequisites(summary, domain, extra_info)
                            
                            # Complete
                            progress_bar.progress(1.0)
                            status_text.text("✅ Generation complete!")
                            time.sleep(1)
                            
                            # Clear progress indicators
                            progress_bar.empty()
                            status_text.empty()
                            
                            # Display results
                            st.markdown("---")
                            st.subheader("🎉 Generated Automation Components")
                            
                            # Tabs for organized display
                            tab1, tab2, tab3, tab4 = st.tabs(["📊 Flow Diagram", "💻 Script & Tests", "📋 Prerequisites", "💾 Downloads"])
                            
                            with tab1:
                                st.markdown("**Process Flow Diagram:**")
                                st.code(block_diagram, language="text")
                                
                                with st.expander("ℹ️ How to read this diagram"):
                                    st.info("""
                                    This text-based diagram shows the flow of your automation process:
                                    - Boxes represent process steps
                                    - Arrows show the sequence of operations
                                    - Decision points show where the process branches
                                    """)
                            
                            with tab2:
                                # Two columns for script and tests
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("**🐍 Automation Script:**")
                                    st.code(script, language='python')
                                
                                with col2:
                                    st.markdown("**🧪 Unit Tests:**")
                                    st.code(unit_tests, language='python')
                            
                            with tab3:
                                st.markdown("**📋 Prerequisites & Setup Requirements:**")
                                st.markdown(prerequisites)
                            
                            with tab4:
                                st.markdown("**💾 Download Generated Files:**")
                                
                                # Download buttons
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.download_button(
                                        "📥 Download Script",
                                        script,
                                        file_name=f"automation_{domain.lower().replace(' ', '_')}.py",
                                        mime="text/plain",
                                        use_container_width=True
                                    )
                                
                                with col2:
                                    st.download_button(
                                        "📥 Download Tests", 
                                        unit_tests,
                                        file_name=f"test_automation_{domain.lower().replace(' ', '_')}.py",
                                        mime="text/plain",
                                        use_container_width=True
                                    )
                                
                                with col3:
                                    # Combined package
                                    combined_content = f"""# Automation Package for {domain}
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

## SUMMARY
{summary}

## PREREQUISITES
{prerequisites}

## AUTOMATION SCRIPT
{script}

## UNIT TESTS
{unit_tests}

## FLOW DIAGRAM
{block_diagram}
"""
                                    st.download_button(
                                        "📦 Download Package",
                                        combined_content,
                                        file_name=f"automation_package_{domain.lower().replace(' ', '_')}.txt",
                                        mime="text/plain",
                                        use_container_width=True
                                    )
                            
                            # Save to database section
                            st.markdown("---")
                            st.subheader("💾 Share with Community")
                            
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.info("""
                                **Help Others:** Save this automation to help others with similar requirements.
                                Your contribution will be searchable by the community and help build our knowledge base.
                                """)
                            
                            with col2:
                                if st.button("💾 Save to Database", type="secondary", use_container_width=True):
                                    try:
                                        with st.spinner("Saving to database..."):
                                            mongo_db.add_solution_to_mongodb(
                                                summary, script, block_diagram, prerequisites, domain, extra_info
                                            )
                                    except Exception as e:
                                        st.error(f"❌ Failed to save: {str(e)}")
                        
                        except Exception as e:
                            progress_bar.empty()
                            status_text.empty()
                            st.error(f"❌ Generation failed: {str(e)}")
                            st.info("💡 **Troubleshooting Tips:**")
                            st.markdown("""
                            - Check your internet connection
                            - Try with a simpler or more detailed description
                            - Ensure your domain information is specific
                            - Try again in a few moments
                            """)
            else:
                st.error("❌ Failed to generate summary. Please try again with a different document or check your API configuration.")
        
        else:
            st.error("❌ Could not extract text from PDF. Please ensure your PDF contains readable text (not scanned images).")
    
    elif uploaded_file and not domain:
        st.warning("⚠️ Please specify a domain/industry before processing the PDF")
    
    elif domain and not uploaded_file:
        st.info("📄 Please upload a PDF document to continue")
    
    # Footer with additional information
    st.markdown("---")
    with st.expander("ℹ️ About Automation Generator"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 What it does:**
            - Analyzes your SOP documents
            - Generates automation scripts
            - Creates unit tests
            - Provides setup requirements
            - Shows process flow diagrams
            """)
        
        with col2:
            st.markdown("""
            **💡 Best Practices:**
            - Use clear, structured documents
            - Provide specific domain context
            - Include detailed requirements
            - Review generated code before use
            - Test in safe environment first
            """)

if __name__ == '__main__':
    main()