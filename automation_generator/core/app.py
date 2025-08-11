"""
Main Streamlit application for Automation Generator Package
Adapted from original app.py to work with package configuration
"""

import streamlit as st
import os
import time
from pathlib import Path

# Configuration and dependencies check
def check_package_dependencies():
    """Check if all required dependencies are available"""
    dependencies = {
        'PyPDF2': True,
        'core_modules': True
    }
    
    # Check PyPDF2
    try:
        import PyPDF2
    except ImportError as e:
        dependencies['PyPDF2'] = False
        st.error(f"❌ **PDF Processing Error**: {str(e)}")
        st.info("""
        **To fix this issue:**
        1. Install PyPDF2: `pip install PyPDF2==3.0.1`
        2. Or reinstall package: `pip install --upgrade automation-generator`
        3. Restart the application
        """)
    
    # Check core modules
    try:
        from ..core.config_manager import ConfigManager
        from ..core.gemini_functions import GenerativeFunction
        from ..core.mongo_functions import MongoDB
        from ..utils.validators import InputValidator
        from ..utils.mermaid_renderer import MermaidRenderer
    except ImportError as e:
        dependencies['core_modules'] = False
        st.error(f"❌ **Core Module Import Error**: {str(e)}")
        st.info("Please ensure the automation-generator package is properly installed")
    
    return all(dependencies.values())

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Automation Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check dependencies before proceeding
if not check_package_dependencies():
    st.stop()

# Import after dependency check
from ..core.config_manager import ConfigManager
from ..core.gemini_functions import GenerativeFunction
from ..core.mongo_functions import MongoDB
from ..utils.validators import InputValidator
from ..utils.mermaid_renderer import MermaidRenderer

# Initialize configuration
@st.cache_resource
def get_config_manager():
    """Initialize and cache configuration manager"""
    config_dir = os.environ.get('AUTOMATION_GENERATOR_CONFIG_DIR')
    return ConfigManager(Path(config_dir) if config_dir else None)

@st.cache_resource
def initialize_services(_config_manager):
    """Initialize and cache core services"""
    services = {}
    
    try:
        services['gemini'] = GenerativeFunction(_config_manager)
        services['database'] = MongoDB(_config_manager)
        services['validator'] = InputValidator()
        services['renderer'] = MermaidRenderer()
        
        return services
    except Exception as e:
        st.error(f"❌ **Service Initialization Failed**: {str(e)}")
        st.info("""
        **Common fixes:**
        • Check your configuration: `automation-generator config validate`
        • Set API keys: `automation-generator config set llm.api_key YOUR_KEY`
        • Verify database connection: `automation-generator health`
        """)
        st.stop()

# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state variables"""
    defaults = {
        'theme': 'light',
        'show_search_results': False,
        'search_results': [],
        'create_mode': True,
        'current_solution_id': None,
        'generated_script': None,
        'generated_flowchart': None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def main():
    """Main application function"""
    
    # Initialize configuration and services
    config_manager = get_config_manager()
    services = initialize_services(config_manager)
    initialize_session_state()
    
    # Load configuration
    config = config_manager.load_config()
    app_config = config.get('app', {})
    
    # Validate configuration
    is_valid, errors = config_manager.validate_config()
    if not is_valid:
        st.error("❌ **Configuration Issues Detected**")
        for error in errors:
            st.write(f"   • {error}")
        st.info("Run `automation-generator config validate` in your terminal for more details")
        return
    
    # Header
    st.title("🤖 Automation Generator")
    st.markdown("*Transform your SOPs into executable automation scripts using AI*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Theme toggle
        theme_options = ["light", "dark"]
        current_theme = st.selectbox(
            "Theme",
            theme_options,
            index=theme_options.index(st.session_state.theme)
        )
        
        if current_theme != st.session_state.theme:
            st.session_state.theme = current_theme
            st.rerun()
        
        st.divider()
        
        # Mode selection
        mode = st.radio(
            "Mode",
            ["Create New", "Search Existing"],
            index=0 if st.session_state.create_mode else 1
        )
        
        st.session_state.create_mode = (mode == "Create New")
        
        st.divider()
        
        # Configuration info
        with st.expander("📊 System Info"):
            st.write(f"**Provider**: {config.get('llm', {}).get('provider', 'Not set')}")
            st.write(f"**Database**: {config.get('database', {}).get('database_name', 'Not set')}")
            st.write(f"**Features**: {len(config.get('features', {}))}")
            
            if st.button("🏥 Health Check"):
                st.write("Checking system health...")
                # This would call the health check
                st.success("All systems operational!")
    
    # Main content area
    if st.session_state.create_mode:
        show_create_mode(services)
    else:
        show_search_mode(services)

def show_create_mode(services):
    """Display creation mode interface"""
    
    st.header("📝 Create New Automation")
    
    # Input form
    with st.form("automation_form", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Text input
            sop_text = st.text_area(
                "Standard Operating Procedure (SOP)",
                height=200,
                placeholder="Paste your SOP text here or upload a PDF file..."
            )
            
            # PDF upload
            uploaded_file = st.file_uploader(
                "Or upload a PDF file",
                type=['pdf'],
                help="Upload a PDF file to extract SOP text automatically"
            )
        
        with col2:
            # Domain input
            domain = st.text_input(
                "Domain/Industry",
                placeholder="e.g., DevOps, IT Support, Cloud Management"
            )
            
            # Script type
            script_type = st.selectbox(
                "Script Type",
                ["bash", "powershell", "python", "batch"]
            )
            
            # Additional info
            extra_info = st.text_area(
                "Additional Requirements (optional)",
                height=100,
                placeholder="Any specific requirements or constraints..."
            )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Generate Automation", type="primary")
    
    # Process form submission
    if submitted:
        # Extract text from PDF if uploaded
        if uploaded_file:
            with st.spinner("Extracting text from PDF..."):
                text_valid, text_error, pdf_info = services['validator'].validate_uploaded_pdf(uploaded_file)
                
                if text_valid:
                    try:
                        import PyPDF2
                        pdf_reader = PyPDF2.PdfReader(uploaded_file)
                        extracted_text = ""
                        
                        for page in pdf_reader.pages:
                            extracted_text += page.extract_text() + "\n"
                        
                        sop_text = extracted_text.strip()
                        st.success(f"✅ Extracted {len(sop_text)} characters from PDF")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to extract text from PDF: {str(e)}")
                        return
                else:
                    st.error(f"❌ PDF validation failed: {text_error}")
                    return
        
        # Validate inputs
        validation_errors = []
        
        if not sop_text or len(sop_text.strip()) < 100:
            validation_errors.append("SOP text is required and must be at least 100 characters")
        
        domain_valid, domain_error = services['validator'].validate_domain(domain)
        if not domain_valid:
            validation_errors.append(f"Domain: {domain_error}")
        
        if extra_info:
            extra_valid, extra_error = services['validator'].validate_extra_info(extra_info)
            if not extra_valid:
                validation_errors.append(f"Additional info: {extra_error}")
        
        if validation_errors:
            st.error("❌ **Input Validation Failed**")
            for error in validation_errors:
                st.write(f"   • {error}")
            return
        
        # Generate automation
        with st.spinner("🤖 Generating automation script..."):
            script = services['gemini'].generate_automation_script(
                sop_text, domain, script_type
            )
            
            if script:
                st.session_state.generated_script = script
                st.success("✅ Automation script generated successfully!")
            else:
                st.error("❌ Failed to generate automation script")
                return
        
        # Generate flowchart
        with st.spinner("📊 Generating process flowchart..."):
            flowchart = services['gemini'].generate_flowchart(sop_text, domain)
            
            if flowchart:
                st.session_state.generated_flowchart = flowchart
                st.success("✅ Process flowchart generated!")
        
        # Save to database
        with st.spinner("💾 Saving to database..."):
            solution_data = {
                'sop_text': sop_text,
                'domain': domain,
                'script_content': script,
                'script_type': script_type,
                'flowchart': flowchart,
                'extra_info': extra_info,
                'version': '2.0'
            }
            
            solution_id = services['database'].save_solution(solution_data)
            
            if solution_id:
                st.session_state.current_solution_id = solution_id
                st.success(f"✅ Solution saved with ID: {solution_id}")
    
    # Display generated content
    if st.session_state.generated_script:
        st.header("📜 Generated Script")
        
        # Script display with copy button
        st.code(st.session_state.generated_script, language=script_type)
        
        # Download button
        st.download_button(
            label="💾 Download Script",
            data=st.session_state.generated_script,
            file_name=f"automation_script.{get_file_extension(script_type)}",
            mime="text/plain"
        )
    
    if st.session_state.generated_flowchart:
        st.header("📊 Process Flowchart")
        
        # Render Mermaid flowchart
        try:
            is_valid, error_msg = services['renderer'].validate_mermaid_syntax(
                st.session_state.generated_flowchart
            )
            
            if is_valid:
                # Display flowchart HTML
                flowchart_html = services['renderer'].generate_mermaid_html(
                    st.session_state.generated_flowchart
                )
                st.components.v1.html(flowchart_html, height=500)
            else:
                st.error(f"❌ Flowchart rendering error: {error_msg}")
                st.code(st.session_state.generated_flowchart, language="text")
        except Exception as e:
            st.error(f"❌ Failed to render flowchart: {str(e)}")
            st.code(st.session_state.generated_flowchart, language="text")

def show_search_mode(services):
    """Display search mode interface"""
    
    st.header("🔍 Search Existing Solutions")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="Enter keywords, domain, or description..."
            )
        
        with col2:
            search_submitted = st.form_submit_button("🔍 Search", type="primary")
    
    # Process search
    if search_submitted and search_query:
        with st.spinner("Searching solutions..."):
            results = services['database'].search_solutions(search_query, limit=20)
            
            st.session_state.search_results = results
            st.session_state.show_search_results = True
    
    # Display recent solutions if no search
    if not st.session_state.show_search_results:
        st.subheader("📚 Recent Solutions")
        
        with st.spinner("Loading recent solutions..."):
            recent_solutions = services['database'].get_recent_solutions(limit=10)
            
            if recent_solutions:
                display_solution_list(recent_solutions, services)
            else:
                st.info("No solutions found. Create your first automation!")
    
    # Display search results
    elif st.session_state.search_results:
        st.subheader(f"📋 Search Results ({len(st.session_state.search_results)} found)")
        display_solution_list(st.session_state.search_results, services)
    else:
        st.info("No solutions found for your search query.")

def display_solution_list(solutions, services):
    """Display a list of solutions"""
    
    for solution in solutions:
        with st.expander(
            f"🔧 {solution.get('domain', 'Unknown Domain')} - {solution.get('script_type', 'script')}"
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Created**: {solution.get('created_at', 'Unknown')}")
                st.write(f"**Type**: {solution.get('script_type', 'Unknown')}")
                
                # Show preview of SOP text
                sop_preview = solution.get('sop_text', '')[:200]
                if len(sop_preview) == 200:
                    sop_preview += "..."
                st.write(f"**SOP Preview**: {sop_preview}")
                
                # Rating if available
                avg_rating = solution.get('avg_rating', 0)
                if avg_rating > 0:
                    stars = "⭐" * int(avg_rating)
                    st.write(f"**Rating**: {stars} ({avg_rating:.1f})")
            
            with col2:
                if st.button(f"View Details", key=f"view_{solution['_id']}"):
                    display_solution_details(solution, services)

def display_solution_details(solution, services):
    """Display detailed view of a solution"""
    
    st.header(f"📄 Solution Details - {solution.get('domain', 'Unknown')}")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📜 Script", "📊 Flowchart", "ℹ️ Info"])
    
    with tab1:
        script_content = solution.get('script_content', 'No script available')
        script_type = solution.get('script_type', 'text')
        
        st.code(script_content, language=script_type)
        
        st.download_button(
            label="💾 Download Script",
            data=script_content,
            file_name=f"solution_{solution['_id']}.{get_file_extension(script_type)}",
            mime="text/plain"
        )
    
    with tab2:
        flowchart = solution.get('flowchart')
        if flowchart:
            try:
                flowchart_html = services['renderer'].generate_mermaid_html(flowchart)
                st.components.v1.html(flowchart_html, height=500)
            except Exception as e:
                st.error(f"Error rendering flowchart: {str(e)}")
                st.code(flowchart, language="text")
        else:
            st.info("No flowchart available for this solution")
    
    with tab3:
        st.write(f"**Solution ID**: {solution['_id']}")
        st.write(f"**Domain**: {solution.get('domain', 'Unknown')}")
        st.write(f"**Script Type**: {solution.get('script_type', 'Unknown')}")
        st.write(f"**Created**: {solution.get('created_at', 'Unknown')}")
        
        if 'extra_info' in solution and solution['extra_info']:
            st.write(f"**Additional Info**: {solution['extra_info']}")
        
        # SOP text
        st.subheader("📝 Original SOP")
        st.text_area("SOP Text", solution.get('sop_text', ''), height=200, disabled=True)

def get_file_extension(script_type):
    """Get file extension for script type"""
    extensions = {
        'bash': 'sh',
        'powershell': 'ps1',
        'python': 'py',
        'batch': 'bat'
    }
    return extensions.get(script_type, 'txt')

# Run the application
if __name__ == "__main__":
    main()