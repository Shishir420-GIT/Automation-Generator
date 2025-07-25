import streamlit as st
import streamlit.components.v1 as components
import base64
import json
from typing import Optional, Dict, Any, Tuple
import logging

class MermaidRenderer:
    """Enhanced Mermaid.js renderer for Streamlit with theme support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def render_mermaid(self, mermaid_code: str, theme: str = "default", 
                      height: int = 400, width: Optional[int] = None) -> None:
        """
        Render Mermaid diagram in Streamlit with theme support
        
        Args:
            mermaid_code: Mermaid diagram code
            theme: Theme for the diagram ('default', 'dark', 'forest', 'neutral')
            height: Height of the diagram container
            width: Width of the diagram container (None for auto)
        """
        try:
            # Validate mermaid code
            if not mermaid_code or not mermaid_code.strip():
                st.error("❌ Empty Mermaid diagram code")
                return
            
            # Basic syntax validation
            if not self._validate_basic_syntax(mermaid_code):
                st.error("❌ Invalid Mermaid syntax detected")
                st.info("💡 **Tip**: Check for proper quotes around labels and valid node formats")
                return
            
            # Clean and prepare the code
            cleaned_code = self._clean_mermaid_code(mermaid_code)
            
            # Generate unique ID for this diagram
            import hashlib
            diagram_id = hashlib.md5(cleaned_code.encode()).hexdigest()[:8]
            
            # Create HTML with Mermaid
            html_content = self._generate_mermaid_html(
                cleaned_code, theme, diagram_id, height, width
            )
            
            # Render in Streamlit
            components.html(html_content, height=height + 50, scrolling=False)
            
        except Exception as e:
            self.logger.error(f"Mermaid rendering failed: {str(e)}")
            st.error(f"❌ Failed to render diagram: {str(e)}")
            
            # Fallback: show code block
            st.markdown("**Diagram Code (fallback display):**")
            st.code(mermaid_code, language="text")
    
    def _validate_basic_syntax(self, code: str) -> bool:
        """Perform basic syntax validation"""
        lines = code.strip().split('\n')
        
        # Must start with a valid directive
        if not any(lines[0].strip().startswith(directive) for directive in [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 
            'stateDiagram', 'gantt', 'pie', 'gitgraph', 'mindmap'
        ]):
            return False
        
        # Check for common syntax errors
        for line in lines[1:]:
            stripped = line.strip()
            if not stripped or stripped.startswith('style '):
                continue
            
            # Check for unbalanced brackets/braces
            brackets = stripped.count('[') - stripped.count(']')
            braces = stripped.count('{') - stripped.count('}')
            parens = stripped.count('(') - stripped.count(')')
            
            if abs(brackets) > 2 or abs(braces) > 2 or abs(parens) > 2:
                return False
        
        return True
    
    def _clean_mermaid_code(self, code: str) -> str:
        """Clean and validate Mermaid code"""
        # Remove extra whitespace and normalize line endings
        code = code.strip().replace('\r\n', '\n').replace('\r', '\n')
        
        # Ensure code starts with a valid Mermaid directive
        if not any(code.startswith(directive) for directive in [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 
            'stateDiagram', 'gantt', 'pie', 'gitgraph', 'mindmap'
        ]):
            # If no directive found, assume it's a flowchart
            if not code.startswith('flowchart'):
                code = f"flowchart TD\n{code}"
        
        return code
    
    def _generate_mermaid_html(self, mermaid_code: str, theme: str, 
                              diagram_id: str, height: int, width: Optional[int]) -> str:
        """Generate HTML content for Mermaid diagram"""
        
        # Map theme names to Mermaid themes
        theme_mapping = {
            'light': 'default',
            'dark': 'dark',
            'default': 'default',
            'forest': 'forest',
            'neutral': 'neutral'
        }
        
        mermaid_theme = theme_mapping.get(theme, 'default')
        
        # Set width style
        width_style = f"width: {width}px;" if width else "width: 100%;"
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 10px;
                    font-family: 'Source Sans Pro', sans-serif;
                    background: transparent;
                }}
                .mermaid-container {{
                    {width_style}
                    height: {height}px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    overflow: auto;
                    background: transparent;
                }}
                .mermaid {{
                    max-width: 100%;
                    max-height: 100%;
                }}
                .error-message {{
                    color: #d32f2f;
                    background: #ffebee;
                    padding: 10px;
                    border-radius: 4px;
                    border-left: 4px solid #d32f2f;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid-container">
                <div class="mermaid" id="diagram-{diagram_id}">
                    {mermaid_code}
                </div>
            </div>
            
            <script>
                try {{
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: '{mermaid_theme}',
                        themeVariables: {{
                            fontFamily: 'Source Sans Pro, sans-serif',
                            fontSize: '14px'
                        }},
                        flowchart: {{
                            useMaxWidth: true,
                            htmlLabels: true,
                            curve: 'basis'
                        }},
                        sequence: {{
                            diagramMarginX: 50,
                            diagramMarginY: 10,
                            actorMargin: 50,
                            width: 150,
                            height: 65,
                            boxMargin: 10,
                            boxTextMargin: 5,
                            noteMargin: 10,
                            messageMargin: 35
                        }},
                        securityLevel: 'loose',
                        deterministicIds: false,
                        deterministicIDSeed: undefined
                    }});
                    
                    // Re-render if needed
                    mermaid.contentLoaded();
                    
                }} catch (error) {{
                    console.error('Mermaid rendering error:', error);
                    document.querySelector('.mermaid-container').innerHTML = 
                        '<div class="error-message">' + 
                        '<strong>Diagram Rendering Error:</strong><br>' + 
                        error.message + 
                        '</div>';
                }}
            </script>
        </body>
        </html>
        """
        
        return html_template
    
    def create_download_link(self, mermaid_code: str, filename: str = "diagram.mmd") -> str:
        """Create a download link for Mermaid diagram code"""
        try:
            # Create download content
            download_content = f"""# Mermaid Diagram
# Generated by Automation Generator
# To view: Copy the code below to https://mermaid.live

{mermaid_code}
"""
            
            # Encode for download
            b64 = base64.b64encode(download_content.encode()).decode()
            
            return f'<a href="data:text/plain;base64,{b64}" download="{filename}">📥 Download Diagram</a>'
            
        except Exception as e:
            self.logger.error(f"Failed to create download link: {str(e)}")
            return ""

class FlowchartGenerator:
    """Generate Mermaid flowcharts from automation descriptions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _sanitize_label(self, text: str) -> str:
        """Sanitize text for use in Mermaid labels"""
        if not text:
            return "Unknown"
        
        # Replace problematic characters
        sanitized = text.replace('"', "'").replace('\n', ' ').replace('\r', ' ')
        
        # Remove special characters that break Mermaid syntax
        import re
        sanitized = re.sub(r'[<>{}|\\]', '', sanitized)
        
        # Limit length to prevent layout issues
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + "..."
        
        return sanitized.strip() or "Unknown"
    
    def text_to_mermaid(self, text_diagram: str, automation_type: str = "process") -> str:
        """
        Convert text-based diagram to Mermaid format
        
        Args:
            text_diagram: Text-based process diagram
            automation_type: Type of automation (process, workflow, sequence)
            
        Returns:
            Mermaid diagram code
        """
        try:
            if not text_diagram or not text_diagram.strip():
                return self._create_default_diagram()
            
            # Parse the text diagram and convert to Mermaid
            if automation_type.lower() == "sequence":
                return self._convert_to_sequence_diagram(text_diagram)
            else:
                return self._convert_to_flowchart(text_diagram)
                
        except Exception as e:
            self.logger.error(f"Text to Mermaid conversion failed: {str(e)}")
            return self._create_error_diagram(str(e))
    
    def _convert_to_flowchart(self, text_diagram: str) -> str:
        """Convert text diagram to Mermaid flowchart"""
        lines = [line.strip() for line in text_diagram.split('\n') if line.strip()]
        
        mermaid_code = "flowchart TD\n"
        node_counter = 1
        node_mapping = {}
        created_nodes = []
        
        for line in lines:
            # Skip decorative lines
            if all(c in '|-+=*~' for c in line.replace(' ', '')):
                continue
            
            # Extract meaningful content
            clean_line = line.replace('|', '').replace('-', '').replace('+', '').strip()
            if not clean_line:
                continue
            
            # Sanitize the line for Mermaid
            clean_line = self._sanitize_label(clean_line)
            
            # Create node
            node_id = f"A{node_counter}"
            node_counter += 1
            created_nodes.append(node_id)
            
            # Determine node type and shape
            if any(keyword in clean_line.lower() for keyword in ['start', 'begin', 'initialize']):
                mermaid_code += f'    {node_id}(["{clean_line}"])\n'
                node_mapping['start'] = node_id
            elif any(keyword in clean_line.lower() for keyword in ['end', 'finish', 'complete', 'done']):
                mermaid_code += f'    {node_id}(["{clean_line}"])\n'
                node_mapping['end'] = node_id
            elif any(keyword in clean_line.lower() for keyword in ['if', 'check', 'verify', 'validate', '?']):
                mermaid_code += f'    {node_id}{{"{clean_line}"}}\n'
                node_mapping['decision'] = node_id
            elif any(keyword in clean_line.lower() for keyword in ['error', 'fail', 'exception']):
                mermaid_code += f'    {node_id}["{clean_line}"]\n'
                mermaid_code += f'    style {node_id} fill:#ffebee,stroke:#d32f2f\n'
            else:
                mermaid_code += f'    {node_id}["{clean_line}"]\n'
        
        # Add connections (simplified sequential flow)
        for i in range(len(created_nodes) - 1):
            mermaid_code += f'    {created_nodes[i]} --> {created_nodes[i + 1]}\n'
        
        return mermaid_code
    
    def _convert_to_sequence_diagram(self, text_diagram: str) -> str:
        """Convert text diagram to Mermaid sequence diagram"""
        lines = [line.strip() for line in text_diagram.split('\n') if line.strip()]
        
        mermaid_code = "sequenceDiagram\n"
        mermaid_code += "    participant U as User\n"
        mermaid_code += "    participant S as System\n"
        mermaid_code += "    participant D as Database\n"
        
        step_counter = 1
        for line in lines:
            clean_line = line.replace('|', '').replace('-', '').replace('+', '').strip()
            if not clean_line or all(c in '|-+=*~' for c in line.replace(' ', '')):
                continue
            
            # Simple mapping to sequence steps
            if any(keyword in clean_line.lower() for keyword in ['input', 'upload', 'enter']):
                mermaid_code += f'    U->>S: {clean_line}\n'
            elif any(keyword in clean_line.lower() for keyword in ['save', 'store', 'database']):
                mermaid_code += f'    S->>D: {clean_line}\n'
                mermaid_code += f'    D-->>S: Confirmation\n'
            elif any(keyword in clean_line.lower() for keyword in ['return', 'display', 'show']):
                mermaid_code += f'    S-->>U: {clean_line}\n'
            else:
                mermaid_code += f'    Note over S: {clean_line}\n'
            
            step_counter += 1
        
        return mermaid_code
    
    def _create_default_diagram(self) -> str:
        """Create a default automation flowchart"""
        return """flowchart TD
    A(["Start: Process Input"]) --> B["Validate Input Data"]
    B --> C{{"Input Valid?"}}
    C -->|"Yes"| D["Process Data"]
    C -->|"No"| E["Return Error"]
    D --> F["Generate Output"]
    F --> G["Save Results"]
    G --> H(["End: Process Complete"])
    E --> H
    
    style A fill:#e3f2fd,stroke:#1976d2
    style H fill:#e8f5e8,stroke:#4caf50
    style E fill:#ffebee,stroke:#d32f2f"""
    
    def _create_error_diagram(self, error_message: str) -> str:
        """Create an error diagram when conversion fails"""
        clean_error = self._sanitize_label(error_message[:50])
        return f"""flowchart TD
    A(["Diagram Generation"]) --> B["Parse Input"]
    B --> C{{"Error Occurred"}}
    C --> D["{clean_error}..."]
    D --> E(["Fallback Display"])
    
    style C fill:#ffebee,stroke:#d32f2f
    style D fill:#ffebee,stroke:#d32f2f"""
    
    def generate_automation_flowchart(self, summary: str, domain: str, 
                                    complexity: str = "moderate") -> str:
        """
        Generate a comprehensive automation flowchart based on summary and domain
        
        Args:
            summary: Automation summary/description
            domain: Domain/industry context
            complexity: Complexity level (simple, moderate, complex)
            
        Returns:
            Mermaid flowchart code
        """
        try:
            # Base structure varies by complexity
            if complexity.lower() == "simple":
                return self._generate_simple_flowchart(summary, domain)
            elif complexity.lower() == "complex":
                return self._generate_complex_flowchart(summary, domain)
            else:
                return self._generate_moderate_flowchart(summary, domain)
                
        except Exception as e:
            self.logger.error(f"Flowchart generation failed: {str(e)}")
            return self._create_error_diagram(str(e))
    
    def _generate_simple_flowchart(self, summary: str, domain: str) -> str:
        """Generate a simple 5-step flowchart"""
        clean_domain = self._sanitize_label(domain)
        return f"""flowchart TD
    A(["Start: {clean_domain} Process"]) --> B["Initialize System"]
    B --> C["Process Input Data"]
    C --> D["Execute Automation"]
    D --> E["Generate Results"]
    E --> F(["Complete"])
    
    style A fill:#e3f2fd,stroke:#1976d2
    style F fill:#e8f5e8,stroke:#4caf50"""
    
    def _generate_moderate_flowchart(self, summary: str, domain: str) -> str:
        """Generate a moderate complexity flowchart with branching and error handling"""
        clean_domain = self._sanitize_label(domain)
        return f"""flowchart TD
    A(["Start: {clean_domain} Automation"]) --> B["Initialize System"]
    B --> C["Load Configuration"]
    C --> D{{"Config Valid?"}}
    D -->|"No"| E["Handle Config Error"]
    D -->|"Yes"| F["Connect to Service"]
    F --> G{{"Connection Success?"}}
    G -->|"No"| H["Retry Connection"]
    G -->|"Yes"| I["Validate Input Data"]
    H --> J{{"Max Retries?"}}
    J -->|"No"| F
    J -->|"Yes"| K["Connection Failed"]
    I --> L{{"Data Valid?"}}
    L -->|"No"| M["Data Validation Error"]
    L -->|"Yes"| N["Process Data"]
    N --> O["Apply Business Rules"]
    O --> P{{"Processing Success?"}}
    P -->|"Yes"| Q["Generate Output"]
    P -->|"No"| R["Handle Processing Error"]
    Q --> S["Save Results"]
    S --> T{{"Save Successful?"}}
    T -->|"Yes"| U["Send Notifications"]
    T -->|"No"| V["Retry Save"]
    V --> W{{"Retry Limit Reached?"}}
    W -->|"No"| S
    W -->|"Yes"| X["Save Failed"]
    U --> Y(["Success: Process Complete"])
    E --> Z1(["End: Config Error"])
    K --> Z2(["End: Connection Failed"])
    M --> Z3(["End: Data Invalid"])
    R --> Z4(["End: Processing Failed"])
    X --> Z5(["End: Save Failed"])
    
    style A fill:#e3f2fd,stroke:#1976d2
    style Y fill:#e8f5e8,stroke:#4caf50
    style Z1 fill:#ffebee,stroke:#d32f2f
    style Z2 fill:#ffebee,stroke:#d32f2f
    style Z3 fill:#ffebee,stroke:#d32f2f
    style Z4 fill:#ffebee,stroke:#d32f2f
    style Z5 fill:#ffebee,stroke:#d32f2f
    style E fill:#fff3e0,stroke:#ff9800
    style M fill:#fff3e0,stroke:#ff9800
    style R fill:#fff3e0,stroke:#ff9800"""
    
    def _generate_complex_flowchart(self, summary: str, domain: str) -> str:
        """Generate a complex flowchart with multiple decision points"""
        clean_domain = self._sanitize_label(domain)
        return f"""flowchart TD
    A(["Start: {clean_domain} Workflow"]) --> B["Initialize Environment"]
    B --> C["Load Configuration"]
    C --> D["Validate Prerequisites"]
    D --> E{{"Prerequisites Met?"}}
    E -->|"No"| F["Setup Missing Components"]
    E -->|"Yes"| G["Load Input Data"]
    F --> G
    G --> H["Data Validation Layer"]
    H --> I{{"Data Quality Check"}}
    I -->|"Fail"| J["Data Cleaning Process"]
    I -->|"Pass"| K["Business Logic Processing"]
    J --> K
    K --> L["Apply Domain Rules"]
    L --> M{{"Rule Validation"}}
    M -->|"Fail"| N["Exception Handling"]
    M -->|"Pass"| O["Transform Data"]
    O --> P["Quality Assurance"]
    P --> Q{{"QA Pass?"}}
    Q -->|"No"| R["Issue Resolution"]
    Q -->|"Yes"| S["Generate Outputs"]
    R --> S
    S --> T["Backup Creation"]
    T --> U["Save to Database"]
    U --> V{{"Save Success?"}}
    V -->|"No"| W["Rollback & Retry"]
    V -->|"Yes"| X["Send Notifications"]
    W --> U
    X --> Y["Generate Reports"]
    Y --> Z["Cleanup Temporary Files"]
    Z --> AA(["Process Complete"])
    N --> BB["Log Error Details"]
    BB --> CC(["End with Error"])
    
    style A fill:#e3f2fd,stroke:#1976d2
    style AA fill:#e8f5e8,stroke:#4caf50
    style CC fill:#ffebee,stroke:#d32f2f
    style N fill:#fff3e0,stroke:#ff9800
    style J fill:#f3e5f5,stroke:#9c27b0
    style R fill:#f3e5f5,stroke:#9c27b0"""