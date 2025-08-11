"""
Mermaid diagram rendering utilities for Automation Generator
Adapted from original mermaid_renderer.py to work without Streamlit dependencies
"""

import base64
import json
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple


class FlowchartGenerator:
    """Generate Mermaid flowchart syntax from text descriptions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def text_to_flowchart(self, text: str, style: str = "TD") -> str:
        """Convert text description to basic Mermaid flowchart"""
        # This is a simplified implementation
        # In practice, this would use AI or more sophisticated parsing
        
        lines = text.strip().split('\n')
        flowchart_lines = [f"graph {style}"]
        
        node_counter = 1
        for line in lines:
            line = line.strip()
            if line and len(line) > 5:  # Filter out very short lines
                node_id = f"A{node_counter}"
                # Clean line for Mermaid
                clean_line = line.replace('"', "'").replace('[', '').replace(']', '')
                if len(clean_line) > 50:
                    clean_line = clean_line[:47] + "..."
                
                flowchart_lines.append(f'    {node_id}["{clean_line}"]')
                
                if node_counter > 1:
                    prev_node = f"A{node_counter - 1}"
                    flowchart_lines.append(f"    {prev_node} --> {node_id}")
                
                node_counter += 1
        
        return '\n'.join(flowchart_lines)


class MermaidRenderer:
    """Enhanced Mermaid.js renderer with theme support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_mermaid_syntax(self, mermaid_code: str) -> Tuple[bool, Optional[str]]:
        """Validate basic Mermaid syntax"""
        if not mermaid_code or not mermaid_code.strip():
            return False, "Empty Mermaid diagram code"
        
        # Basic syntax validation
        if not self._validate_basic_syntax(mermaid_code):
            return False, "Invalid Mermaid syntax detected"
        
        return True, None
    
    def _validate_basic_syntax(self, code: str) -> bool:
        """Perform basic syntax validation"""
        try:
            lines = code.strip().split('\n')
            first_line = lines[0].strip().lower()
            
            # Check for valid diagram type
            valid_starts = ['graph', 'flowchart', 'sequencediagram', 'classDiagram', 'stateDiagram', 'journey', 'gitgraph']
            if not any(first_line.startswith(start.lower()) for start in valid_starts):
                return False
            
            # Check for balanced brackets and quotes
            brackets = {'[': ']', '(': ')', '{': '}', '<': '>'}
            quote_chars = ['"', "'", '`']
            
            for line in lines:
                # Check bracket balance
                stack = []
                in_quote = False
                quote_char = None
                
                for char in line:
                    if char in quote_chars and not in_quote:
                        in_quote = True
                        quote_char = char
                    elif char == quote_char and in_quote:
                        in_quote = False
                        quote_char = None
                    elif not in_quote:
                        if char in brackets:
                            stack.append(char)
                        elif char in brackets.values():
                            if not stack:
                                return False
                            if brackets.get(stack[-1]) != char:
                                return False
                            stack.pop()
                
                if stack:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Syntax validation error: {e}")
            return False
    
    def clean_mermaid_code(self, code: str) -> str:
        """Clean and prepare Mermaid code"""
        return self._clean_mermaid_code(code)
    
    def _clean_mermaid_code(self, code: str) -> str:
        """Clean Mermaid code for rendering"""
        # Remove extra whitespace
        lines = [line.rstrip() for line in code.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line.strip()]
        
        # Ensure proper indentation
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith(('graph', 'flowchart', 'sequenceDiagram')):
                cleaned_lines.append(line.strip())
            else:
                # Ensure proper indentation for content
                stripped = line.strip()
                if stripped and not stripped.startswith('    '):
                    cleaned_lines.append(f"    {stripped}")
                else:
                    cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def generate_mermaid_html(self, mermaid_code: str, theme: str = "default", 
                             height: int = 400, width: Optional[int] = None) -> str:
        """Generate HTML for Mermaid diagram"""
        return self._generate_mermaid_html(mermaid_code, theme, None, height, width)
    
    def _generate_mermaid_html(self, mermaid_code: str, theme: str, 
                              diagram_id: Optional[str], height: int, 
                              width: Optional[int]) -> str:
        """Generate HTML content for Mermaid diagram"""
        
        if not diagram_id:
            diagram_id = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
        
        width_style = f"width: {width}px;" if width else "width: 100%;"
        
        # Mermaid configuration
        mermaid_config = {
            "theme": theme,
            "themeVariables": {
                "fontSize": "16px"
            },
            "flowchart": {
                "htmlLabels": True,
                "useMaxWidth": True,
                "curve": "basis"
            },
            "sequence": {
                "diagramMarginX": 50,
                "diagramMarginY": 10,
                "actorMargin": 50,
                "width": 150,
                "height": 65,
                "boxMargin": 10,
                "boxTextMargin": 5,
                "noteMargin": 10,
                "messageMargin": 35
            }
        }
        
        config_json = json.dumps(mermaid_config)
        
        html_template = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.2.3/dist/mermaid.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    background-color: transparent;
                }}
                .mermaid-container {{
                    {width_style}
                    height: {height}px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: transparent;
                }}
                #mermaid-{diagram_id} {{
                    max-width: 100%;
                    max-height: 100%;
                }}
                .error-message {{
                    color: #ff4b4b;
                    background-color: #fff3f3;
                    border: 1px solid #ff4b4b;
                    border-radius: 4px;
                    padding: 12px;
                    text-align: center;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid-container">
                <div id="mermaid-{diagram_id}" class="mermaid">
                    {mermaid_code}
                </div>
            </div>
            
            <script>
                try {{
                    mermaid.initialize({config_json});
                    
                    // Error handling
                    mermaid.parseError = function(err, hash) {{
                        console.error('Mermaid parsing error:', err);
                        document.getElementById('mermaid-{diagram_id}').innerHTML = 
                            '<div class="error-message">⚠️ Diagram rendering failed: ' + err + '</div>';
                    }};
                    
                }} catch (error) {{
                    console.error('Mermaid initialization error:', error);
                    document.getElementById('mermaid-{diagram_id}').innerHTML = 
                        '<div class="error-message">❌ Failed to initialize diagram renderer</div>';
                }}
            </script>
        </body>
        </html>
        '''
        
        return html_template
    
    def export_diagram_data(self, mermaid_code: str, theme: str = "default") -> Dict[str, Any]:
        """Export diagram data for external use"""
        return {
            "mermaid_code": mermaid_code,
            "theme": theme,
            "html": self.generate_mermaid_html(mermaid_code, theme),
            "is_valid": self.validate_mermaid_syntax(mermaid_code)[0]
        }