import streamlit as st
import PyPDF2
from utils.GeminiFunctions import GenerativeFunction
from utils.MongoDBFunctions import MongoDB
from utils.validators import InputValidator
from utils.mermaid_renderer import MermaidRenderer
import time

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Automation Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for theme and search
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

if 'show_search_results' not in st.session_state:
    st.session_state.show_search_results = False

if 'search_results' not in st.session_state:
    st.session_state.search_results = []

if 'create_mode' not in st.session_state:
    st.session_state.create_mode = True

# Theme configurations
def get_theme_config():
    """Get theme-specific configurations"""
    if st.session_state.theme == 'dark':
        return {
            'bg_color': '#0E1117',
            'secondary_bg': '#262730',
            'text_color': '#FAFAFA',
            'accent_color': '#FF6B6B',
            'success_bg': '#1B4332',
            'success_text': '#4AFF4A',
            'info_bg': '#1E3A8A',
            'info_text': '#60A5FA',
            'warning_bg': '#92400E',
            'warning_text': '#FCD34D',
            'error_bg': '#7F1D1D',
            'error_text': '#FCA5A5',
            'border_color': '#374151'
        }
    else:
        return {
            'bg_color': '#FFFFFF',
            'secondary_bg': '#F0F2F6',
            'text_color': '#262730',
            'accent_color': '#FF6B6B',
            'success_bg': '#D4EDDA',
            'success_text': '#155724',
            'info_bg': '#E3F2FD',
            'info_text': '#1976D2',
            'warning_bg': '#FFF3CD',
            'warning_text': '#856404',
            'error_bg': '#F8D7DA',
            'error_text': '#721C24',
            'border_color': '#DEE2E6'
        }

def apply_theme_css():
    """Apply theme-specific CSS"""
    theme = get_theme_config()
    
    st.markdown(f"""
    <style>
    /* Main theme variables */
    :root {{
        --bg-color: {theme['bg_color']};
        --secondary-bg: {theme['secondary_bg']};
        --text-color: {theme['text_color']};
        --accent-color: {theme['accent_color']};
        --border-color: {theme['border_color']};
    }}
    
    /* Main content styling */
    .main-header {{
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }}
    
    /* Theme-aware boxes */
    .info-box {{
        background: {theme['info_bg']};
        color: {theme['info_text']};
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid {theme['accent_color']};
        margin: 1rem 0;
    }}
    
    .success-box {{
        background: {theme['success_bg']};
        color: {theme['success_text']};
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }}
    
    .warning-box {{
        background: {theme['warning_bg']};
        color: {theme['warning_text']};
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9800;
        margin: 1rem 0;
    }}
    
    .error-box {{
        background: {theme['error_bg']};
        color: {theme['error_text']};
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #F44336;
        margin: 1rem 0;
    }}
    
    /* Upload area */
    .upload-area {{
        background: {theme['secondary_bg']};
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed {theme['border_color']};
        text-align: center;
        margin: 1rem 0;
        color: {theme['text_color']};
    }}
    
    /* Search results styling */
    .search-result-card {{
        background: {theme['secondary_bg']};
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid {theme['border_color']};
        margin: 0.5rem 0;
        color: {theme['text_color']};
    }}
    
    /* Sidebar styling */
    .sidebar-search {{
        background: {theme['secondary_bg']};
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }}
    
    /* Custom metrics */
    .metric-card {{
        background: {theme['secondary_bg']};
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid {theme['border_color']};
        text-align: center;
        margin: 0.5rem 0;
    }}
    </style>
    """, unsafe_allow_html=True)

# Initialize components with caching
@st.cache_resource
def init_components():
    """Initialize and cache expensive components"""
    try:
        gemini = GenerativeFunction()
        mongo_db = MongoDB()
        mermaid_renderer = MermaidRenderer()
        return gemini, mongo_db, mermaid_renderer
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

def comprehensive_validation(domain, uploaded_file, pdf_text):
    """Perform comprehensive validation with detailed feedback"""
    validator = InputValidator()
    validation_results = []
    
    # Domain validation
    domain_valid, domain_error = validator.validate_domain(domain)
    validation_results.append(("Domain validation", domain_valid, domain_error))
    
    # PDF file validation
    if uploaded_file:
        pdf_valid, pdf_error, pdf_info = validator.validate_pdf_file(uploaded_file)
        validation_results.append(("PDF file validation", pdf_valid, pdf_error))
        
        if pdf_valid:
            st.info(f"📄 **PDF Info:** {pdf_info['page_count']} pages, {pdf_info['pages_with_text']} with readable text")
    else:
        validation_results.append(("PDF file validation", False, "No file uploaded"))
    
    # Text content validation
    if pdf_text:
        text_valid, text_error, text_info = validator.validate_text_content(pdf_text)
        validation_results.append(("Text content validation", text_valid, text_error))
        
        if text_valid:
            st.info(f"📝 **Content Info:** {text_info['words']} words, {text_info['lines']} lines, {text_info['alpha_ratio']:.0%} readable text")
    else:
        validation_results.append(("Text content validation", False, "No text extracted"))
    
    # Show validation summary
    validator.show_validation_summary(validation_results)
    
    # Return overall result
    return all(result[1] for result in validation_results)

def create_sidebar_search(mongo_db):
    """Create the right sidebar search functionality"""
    
    with st.sidebar:
        st.markdown("### 🔍 Search Automation Solutions")
        
        # Search input
        search_query = st.text_input(
            "Search for solutions...",
            placeholder="e.g., invoice processing, data backup",
            key="sidebar_search_query"
        )
        
        # Search filters
        with st.expander("🎛️ Search Filters"):
            # Get popular domains for filter
            try:
                popular_domains = mongo_db.get_popular_domains(10)
                domain_options = [d['domain'] for d in popular_domains if d['domain']]
            except:
                domain_options = ["Finance", "Healthcare", "IT", "Manufacturing", "Retail", "Other"]
            
            domain_filter = st.multiselect(
                "Domain",
                domain_options,
                key="domain_filter"
            )
            
            sort_by = st.selectbox(
                "Sort by",
                ["Relevance", "Recent", "Most Popular", "Alphabetical"],
                key="sort_filter"
            )
        
        # Search button
        search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        
        if search_clicked and search_query:
            with st.spinner("Searching..."):
                try:
                    results = mongo_db.search_mongodb(search_query.strip())
                    # Ensure results is always a list
                    if results is None:
                        results = []
                    st.session_state.search_results = results
                    st.session_state.show_search_results = True
                    st.session_state.last_search_query = search_query
                    st.session_state.create_mode = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
                    st.session_state.search_results = []
        
        # Clear search button
        if st.session_state.show_search_results:
            if st.button("❌ Clear Search", use_container_width=True):
                st.session_state.search_results = []
                st.session_state.show_search_results = False
                st.session_state.create_mode = True
                st.rerun()
        
        # Show database stats
        with st.expander("📊 Database Stats"):
            try:
                stats = mongo_db.get_database_stats()
                st.metric("Total Solutions", stats.get('total_solutions', 0))
                st.metric("Active Solutions", stats.get('active_solutions', 0))
                st.metric("Domains", stats.get('total_domains', 0))
            except:
                st.info("Stats unavailable")
        
        # Navigation to create automation
        st.markdown("---")
        st.markdown("### 📝 Create New Automation")
        if st.button("➕ Create Automation", type="secondary", use_container_width=True):
            # Clear search results and navigate to create mode
            st.session_state.search_results = []
            st.session_state.show_search_results = False
            st.session_state.create_mode = True
            st.rerun()

def display_search_results():
    """Display search results in the main area"""
    if not st.session_state.show_search_results:
        return
    
    st.subheader(f"🔍 Search Results for '{st.session_state.get('last_search_query', '')}'")
    
    results = st.session_state.search_results
    
    # Handle empty results
    if not results:
        st.markdown(f"""
        <div class="warning-box">
            <h4>🔍 No Solutions Found</h4>
            <p>No automation solutions found for '<strong>{st.session_state.get('last_search_query', '')}</strong>'</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 💡 Search Tips:
        - Try different or more general keywords
        - Use domain-specific terms (e.g., "finance", "healthcare", "IT")
        - Search for process types (e.g., "automation", "reporting", "backup")
        - Check spelling and try synonyms
        - Try shorter search terms
        """)
        
        # Call to action for empty results
        st.markdown("### 🚀 Be the First!")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("Create the first automation solution for this search term and help others with similar needs!")
        
        with col2:
            if st.button("➕ Create New Automation", type="primary", use_container_width=True, key="create_from_empty"):
                # Clear search and navigate to create mode
                st.session_state.search_results = []
                st.session_state.show_search_results = False
                st.session_state.create_mode = True
                st.rerun()
        return
    
    st.success(f"✅ Found {len(results)} matching solutions")
    
    for i, result in enumerate(results):
        with st.container():
            # Create a card-like display
            st.markdown(f"""
            <div class="search-result-card">
                <h4>🔧 {result.get('domain', 'Unknown')} Automation</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Summary preview
                summary = result.get('summary', 'No summary available')
                preview = summary[:200] + "..." if len(summary) > 200 else summary
                st.markdown(f"**Summary:** {preview}")
                
                # Show timestamp and search info
                timestamp = result.get('timestamp', 'Unknown')
                if timestamp != 'Unknown':
                    try:
                        st.caption(f"📅 Added: {timestamp.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        st.caption(f"📅 Added: {str(timestamp)[:10]}")
                else:
                    st.caption("📅 Added: Unknown")
                
                # Show search type and score
                search_type = result.get('search_type', 'unknown')
                score = result.get('score', 0)
                if score > 0:
                    st.caption(f"🎯 Relevance: {score:.1f} ({search_type} search)")
            
            with col2:
                # Mock rating for now
                avg_rating = 4.2
                rating_count = 12
                st.markdown(f"""
                <div class="metric-card">
                    <h3>⭐ {avg_rating}</h3>
                    <p>({rating_count} reviews)</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Action buttons
                if st.button(f"👀 View Details", key=f"view_{i}", use_container_width=True):
                    st.session_state[f'show_details_{i}'] = not st.session_state.get(f'show_details_{i}', False)
                    st.rerun()
                
                if st.button(f"📋 Use Template", key=f"use_{i}", type="primary", use_container_width=True):
                    st.session_state.template_result = result
                    st.session_state.create_mode = True
                    st.session_state.show_search_results = False
                    st.success("✅ Template loaded! Switched to create mode.")
                    time.sleep(1)
                    st.rerun()
            
            # Show details if requested
            if st.session_state.get(f'show_details_{i}', False):
                with st.expander(f"📋 Details - {result.get('domain', 'Unknown')} Automation", expanded=True):
                    
                    # Tabs for organized display
                    tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "💻 Script", "🧪 Tests", "📋 Prerequisites"])
                    
                    with tab1:
                        st.markdown("**Complete Summary:**")
                        st.write(result.get('summary', 'No summary available'))
                        
                        if result.get('extra_info'):
                            st.markdown("**Additional Information:**")
                            st.write(result.get('extra_info', ''))
                    
                    with tab2:
                        if result.get('script'):
                            st.markdown("**Automation Script:**")
                            st.code(result['script'], language='python')
                            
                            # Download button
                            st.download_button(
                                "📥 Download Script",
                                result['script'],
                                file_name=f"automation_{result.get('domain', 'solution').lower().replace(' ', '_')}.py",
                                mime="text/plain",
                                key=f"dl_script_{i}"
                            )
                        else:
                            st.info("No script available")
                    
                    with tab3:
                        if result.get('unit_tests'):
                            st.markdown("**Unit Tests:**")
                            st.code(result['unit_tests'], language='python')
                            
                            # Download button
                            st.download_button(
                                "📥 Download Tests",
                                result['unit_tests'],
                                file_name=f"test_{result.get('domain', 'solution').lower().replace(' ', '_')}.py",
                                mime="text/plain",
                                key=f"dl_tests_{i}"
                            )
                        else:
                            st.info("No unit tests available")
                    
                    with tab4:
                        if result.get('prerequisites'):
                            st.markdown("**Prerequisites & Setup Requirements:**")
                            st.markdown(result['prerequisites'])
                        else:
                            st.info("No prerequisites available")
            
            st.markdown("---")
    
    # Call to action at bottom
    st.markdown("### 🚀 Didn't find what you're looking for?")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("Create your own automation solution and help others with similar needs!")
    
    with col2:
        if st.button("➕ Create New Automation", type="primary", use_container_width=True):
            # Clear search and navigate to create mode
            st.session_state.search_results = []
            st.session_state.show_search_results = False
            st.session_state.create_mode = True
            st.rerun()

def show_create_automation_interface(gemini, mongo_db):
    """Display the create automation interface"""
    
    st.header("📝 Create New Automation")
    
    # Check if template is loaded
    if 'template_result' in st.session_state:
        template = st.session_state.template_result
        st.markdown(f"""
        <div class="info-box">
            <h4>📋 Template Loaded</h4>
            <p><strong>Domain:</strong> {template.get('domain', 'Unknown')}</p>
            <p><strong>Summary:</strong> {template.get('summary', 'No summary')[:100]}...</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("❌ Clear Template", use_container_width=True):
                del st.session_state.template_result
                st.rerun()
    
    # Input section with better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Pre-fill domain if template is loaded
        default_domain = ""
        if 'template_result' in st.session_state:
            default_domain = st.session_state.template_result.get('domain', '')
        
        domain = st.text_input(
            "🏢 Domain/Industry *",
            value=default_domain,
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
        # Tips and information - theme aware
        st.markdown(f"""
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
                st.markdown(f"""
                <div class="success-box">
                    <p style="margin: 0;"><strong>✅ File Ready</strong><br>Your PDF is ready for processing</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    <p style="margin: 0;"><strong>❌ File Too Large</strong><br>Please upload a file smaller than 20MB</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Process the document
    if uploaded_file and domain:
        # Extract text from PDF
        with st.spinner("📖 Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
        
        # Comprehensive validation
        if not comprehensive_validation(domain, uploaded_file, pdf_text):
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
                        help="Show advanced generation options including Mermaid diagrams"
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
                                help="Choose the complexity level for generated automation",
                                key="complexity_level"
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
                            # Step 1: Generate diagrams (both text and Mermaid)
                            status_text.text("📊 Creating process flow diagrams...")
                            progress_bar.progress(0.15)
                            time.sleep(0.5)
                            
                            block_diagram = gemini.gemini_generate_block_diagram(summary, domain, extra_info)
                            
                            status_text.text("🎨 Creating interactive Mermaid diagram...")
                            progress_bar.progress(0.25)
                            time.sleep(0.5)
                            
                            # Get complexity level from advanced options if available
                            complexity_level = st.session_state.get('complexity_level', 'moderate')
                            mermaid_diagram = gemini.gemini_generate_mermaid_diagram(summary, domain, extra_info, complexity_level)
                            
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
                            
                            # Display results in tabs
                            display_automation_results(block_diagram, mermaid_diagram, script, unit_tests, prerequisites, domain, summary, mongo_db, extra_info)
                        
                        except Exception as e:
                            progress_bar.empty()
                            status_text.empty()
                            st.markdown(f"""
                            <div class="error-box">
                                <p><strong>❌ Generation Failed</strong><br>{str(e)}</p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    <p><strong>❌ Summary Generation Failed</strong><br>Please try again with a different document or check your API configuration.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="error-box">
                <p><strong>❌ Text Extraction Failed</strong><br>Could not extract sufficient text from PDF. Please ensure your PDF contains readable text (not scanned images).</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif uploaded_file and not domain:
        st.markdown(f"""
        <div class="warning-box">
            <p><strong>⚠️ Missing Domain</strong><br>Please specify a domain/industry before processing the PDF</p>
        </div>
        """, unsafe_allow_html=True)
    
    elif domain and not uploaded_file:
        st.markdown(f"""
        <div class="info-box">
            <p><strong>📄 Upload Required</strong><br>Please upload a PDF document to continue</p>
        </div>
        """, unsafe_allow_html=True)

def display_automation_results(block_diagram, mermaid_diagram, script, unit_tests, prerequisites, domain, summary, mongo_db, extra_info):
    """Display generated automation results with enhanced visual diagrams"""
    
    st.markdown("---")
    st.subheader("🎉 Generated Automation Components")
    
    # Tabs for organized display
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎨 Interactive Diagram", "📊 Text Diagram", "💻 Script & Tests", "📋 Prerequisites", "💾 Downloads"])
    
    with tab1:
        st.markdown("**🎨 Interactive Mermaid Flowchart:**")
        
        if mermaid_diagram:
            # Get current theme for Mermaid rendering
            mermaid_theme = 'dark' if st.session_state.theme == 'dark' else 'default'
            
            # Initialize mermaid renderer
            mermaid_renderer = MermaidRenderer()
            
            # Validate diagram before rendering
            if mermaid_diagram.strip().startswith('flowchart'):
                # Render the diagram
                try:
                    mermaid_renderer.render_mermaid(mermaid_diagram, theme=mermaid_theme, height=500)
                except Exception as e:
                    st.error(f"❌ **Diagram Rendering Failed**: {str(e)}")
                    st.info("💡 **Fallback**: Check the Text Diagram tab for the process flow.")
                    st.code(mermaid_diagram, language="text")
            else:
                st.warning("⚠️ **Invalid Diagram Format**: Generated diagram may have syntax issues.")
                st.code(mermaid_diagram, language="text")
            
            # Show diagram controls
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown("**💡 Tip:** This interactive diagram shows the automation process flow with clickable elements and visual styling.")
            
            with col2:
                # Theme toggle for diagram
                if st.button("🎨 Switch Diagram Theme", help="Toggle between light and dark diagram themes"):
                    # Re-render with opposite theme
                    opposite_theme = 'default' if mermaid_theme == 'dark' else 'dark'
                    mermaid_renderer.render_mermaid(mermaid_diagram, theme=opposite_theme, height=500)
            
            with col3:
                # Download diagram
                download_link = mermaid_renderer.create_download_link(mermaid_diagram, f"{domain.lower().replace(' ', '_')}_diagram.mmd")
                if download_link:
                    st.markdown(download_link, unsafe_allow_html=True)
            
            # Show raw Mermaid code in expander
            with st.expander("🔧 View Mermaid Source Code"):
                st.code(mermaid_diagram, language="text")
                st.info("💡 You can copy this code and use it in other Mermaid-compatible tools or modify it as needed.")
        else:
            st.warning("⚠️ Interactive diagram generation failed. Please see the text diagram in the next tab.")
            st.info("This might happen due to API limitations or content complexity. The text diagram provides the same information in a different format.")
    
    with tab2:
        st.markdown("**📊 Text-Based Process Diagram:**")
        st.code(block_diagram, language="text")
        
        with st.expander("ℹ️ How to read this diagram"):
            st.info("""
            This text-based diagram shows the flow of your automation process:
            - Boxes represent process steps
            - Arrows show the sequence of operations
            - Decision points show where the process branches
            """)
    
    with tab3:
        # Two columns for script and tests
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🐍 Automation Script:**")
            st.code(script, language='python')
        
        with col2:
            st.markdown("**🧪 Unit Tests:**")
            st.code(unit_tests, language='python')
    
    with tab4:
        st.markdown("**📋 Prerequisites & Setup Requirements:**")
        st.markdown(prerequisites)
    
    with tab5:
        st.markdown("**💾 Download Generated Files:**")
        
        # Download buttons
        col1, col2, col3, col4 = st.columns(4)
        
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
            if mermaid_diagram:
                st.download_button(
                    "📥 Download Diagram",
                    mermaid_diagram,
                    file_name=f"diagram_{domain.lower().replace(' ', '_')}.mmd",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.button("📥 Diagram N/A", disabled=True, use_container_width=True)
        
        with col4:
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

## TEXT FLOW DIAGRAM
{block_diagram}

## MERMAID DIAGRAM
{mermaid_diagram if mermaid_diagram else 'Not generated'}
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
        st.markdown(f"""
        <div class="info-box">
            <p><strong>Help Others:</strong> Save this automation to help others with similar requirements.
            Your contribution will be searchable by the community and help build our knowledge base.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("💾 Save to Database", type="secondary", use_container_width=True):
            try:
                with st.spinner("Saving to database..."):
                    success = mongo_db.add_solution_to_mongodb(
                        summary, script, block_diagram, prerequisites, domain, extra_info
                    )
                    if success:
                        st.balloons()
            except Exception as e:
                st.error(f"❌ Failed to save: {str(e)}")

def main():
    # Apply theme CSS
    apply_theme_css()
    
    # Theme toggle in header
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Theme toggle
        theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
        theme_label = "Dark Mode" if st.session_state.theme == 'light' else "Light Mode"
        
        if st.button(f"{theme_icon} {theme_label}", key="theme_toggle"):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            st.rerun()
    
    with col2:
        # Main header
        st.markdown('<h1 class="main-header">🤖 Automation Generator</h1>', unsafe_allow_html=True)
    
    with col3:
        # Mode indicator
        mode_text = "🔍 Search Mode" if st.session_state.show_search_results else "📝 Create Mode"
        st.markdown(f"**{mode_text}**")
    
    # Subtitle
    st.markdown(f"""
    <div class="info-box">
        <p style="margin: 0; text-align: center;">
            Transform your Standard Operating Procedures into automated workflows with AI assistance
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    gemini, mongo_db, mermaid_renderer = init_components()
    
    # Create sidebar search
    create_sidebar_search(mongo_db)
    
    # Main content area
    if st.session_state.show_search_results and not st.session_state.create_mode:
        # Show search results
        display_search_results()
    else:
        # Show create automation interface
        show_create_automation_interface(gemini, mongo_db)
    
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
            - Enables community sharing
            """)
        
        with col2:
            st.markdown("""
            **💡 Best Practices:**
            - Use clear, structured documents
            - Provide specific domain context
            - Include detailed requirements
            - Review generated code before use
            - Test in safe environment first
            - Share solutions to help others
            """)

if __name__ == '__main__':
    main()