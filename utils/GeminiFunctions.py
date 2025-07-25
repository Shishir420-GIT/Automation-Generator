import streamlit as st
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_fixed
import logging
import time
from typing import Optional, Dict, Any
import re
from .mermaid_renderer import FlowchartGenerator

class GenerativeFunction:
    def __init__(self):
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize API configuration
        self._initialize_api()
        
        # Generation configuration
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
        }
        
        # Initialize Mermaid flowchart generator
        self.flowchart_generator = FlowchartGenerator()
    
    def _initialize_api(self):
        """Initialize Gemini API with proper error handling"""
        try:
            api_key = st.secrets.get("API_KEY")
            if not api_key:
                st.error("❌ **API Configuration Error**")
                st.error("Gemini API key not found in secrets. Please configure your API key.")
                st.info("**To fix this:**\n1. Add your API key to `.streamlit/secrets.toml`\n2. Restart the application")
                st.stop()
            
            genai.configure(api_key=api_key)
            self.logger.info("Gemini API initialized successfully")
            
        except Exception as e:
            st.error(f"❌ **API Initialization Failed**\n{str(e)}")
            st.info("**Troubleshooting Steps:**\n1. Check your API key\n2. Verify internet connection\n3. Ensure proper secrets configuration")
            st.stop()
    
    def _validate_inputs(self, text: str, domain: str, operation: str = "generation") -> bool:
        """Validate inputs before processing"""
        errors = []
        
        # Text validation
        if not text or not text.strip():
            errors.append("❌ Text content is empty")
        elif len(text.strip()) < 50:
            errors.append("❌ Text content is too short (minimum 50 characters)")
        elif len(text.strip()) > 50000:
            errors.append("⚠️ Text content is very long and may be truncated")
        
        # Domain validation
        if not domain or not domain.strip():
            errors.append("❌ Domain information is required")
        elif len(domain.strip()) < 2:
            errors.append("❌ Domain must be at least 2 characters")
        
        # Check for potentially problematic content
        suspicious_patterns = ['<script>', '<?php', 'javascript:', 'data:']
        if any(pattern in text.lower() for pattern in suspicious_patterns):
            errors.append("⚠️ Text contains potentially problematic content")
        
        if errors:
            st.error(f"**Input Validation Failed for {operation}:**")
            for error in errors:
                st.write(error)
            return False
        
        return True
    
    def _handle_api_error(self, error: Exception, operation: str) -> Optional[str]:
        """Handle API errors gracefully with specific guidance"""
        error_msg = str(error).lower()
        
        # Quota and rate limiting errors
        if any(keyword in error_msg for keyword in ['quota', 'limit', 'rate']):
            st.error(f"❌ **API Quota Exceeded**")
            st.warning(f"You've reached the API limit for {operation}")
            st.info("""
            **What you can do:**
            • Wait a few minutes and try again
            • Check your Google Cloud billing status
            • Consider upgrading your API quota
            • Try with shorter content
            """)
            return None
        
        # Safety filter errors
        elif any(keyword in error_msg for keyword in ['safety', 'blocked', 'filter']):
            st.warning(f"⚠️ **Content Safety Filter Triggered**")
            st.info(f"The AI safety system blocked content during {operation}")
            st.info("""
            **How to resolve:**
            • Try rephrasing your request
            • Remove any potentially sensitive content
            • Use more neutral language
            • Focus on technical aspects only
            """)
            return None
        
        # Network and connectivity errors
        elif any(keyword in error_msg for keyword in ['network', 'connection', 'timeout', 'unreachable']):
            st.error(f"❌ **Network Connection Error**")
            st.info(f"Unable to connect to AI service during {operation}")
            st.info("""
            **Troubleshooting steps:**
            • Check your internet connection
            • Try again in a few moments
            • Verify firewall settings
            • Check if the service is available
            """)
            return None
        
        # Authentication errors
        elif any(keyword in error_msg for keyword in ['auth', 'key', 'credential', 'permission']):
            st.error(f"❌ **Authentication Error**")
            st.error(f"API authentication failed during {operation}")
            st.info("""
            **How to fix:**
            • Verify your API key is correct
            • Check if your API key has expired
            • Ensure proper permissions are set
            • Try regenerating your API key
            """)
            return None
        
        # Generic errors
        else:
            st.error(f"❌ **Error during {operation}**")
            st.error(f"Details: {str(error)}")
            st.info("""
            **General troubleshooting:**
            • Try again with different input
            • Check your input for special characters
            • Ensure your content is appropriate
            • Contact support if issue persists
            """)
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _generate_with_retry(self, model, prompt: str, operation: str) -> Optional[str]:
        """Generate content with retry logic and better error handling"""
        try:
            response = model.generate_content([prompt], safety_settings=self.safety_settings)
            
            # Check if response was blocked
            if not response.candidates:
                st.warning(f"⚠️ **Response Blocked During {operation}**")
                
                # Show safety ratings if available
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.safety_ratings:
                    st.info("**Safety Ratings:**")
                    for rating in response.prompt_feedback.safety_ratings:
                        st.write(f"• {rating.category.name}: {rating.probability.name}")
                
                st.info("""
                **Suggestions:**
                • Try rephrasing your content
                • Remove technical jargon that might be misinterpreted
                • Use more general terms
                • Focus on business processes rather than technical implementation
                """)
                return None
            
            # Check if response is empty or too short
            response_text = response.text.strip()
            if not response_text:
                st.warning(f"⚠️ Empty response received for {operation}")
                return None
            
            if len(response_text) < 20:
                st.warning(f"⚠️ Very short response received for {operation}")
                st.info("This might indicate an issue with the input or API service.")
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"Error in {operation}: {str(e)}")
            raise e
    
    def gemini_generate_content(self, prompt: str, model_name: str = "gemini-1.5-flash", operation: str = "content generation") -> Optional[str]:
        """Enhanced content generation with comprehensive error handling"""
        try:
            # Validate prompt
            if not prompt or len(prompt.strip()) < 10:
                st.error("❌ Prompt is too short or empty")
                return None
            
            if len(prompt) > 100000:  # 100k character limit
                st.warning("⚠️ Prompt is very long, truncating to 100,000 characters")
                prompt = prompt[:100000]
            
            # Initialize model
            model = genai.GenerativeModel(model_name=model_name, generation_config=self.generation_config)
            
            # Generate with retry
            return self._generate_with_retry(model, prompt, operation)
            
        except Exception as e:
            return self._handle_api_error(e, operation)
    
    def gemini_summarize(self, text: str, domain: str, extra_info: str = "") -> Optional[str]:
        """Enhanced summarize with validation and error handling"""
        operation = "document summarization"
        
        # Validate inputs
        if not self._validate_inputs(text, domain, operation):
            return None
        
        try:
            prompt = f"""
            Analyze the following text from a PDF document related to the {domain} domain. 
            Additional context: {extra_info}

            Generate a comprehensive summary of the document, breaking it down into the following sections:
            1. Overview: Provide a brief overview of the document's main topic and purpose.
            2. Key Points: List the main ideas or arguments presented in the document.
            3. Detailed Summary: Expand on the key points, providing more context and explanation.
            4. Conclusion: Summarize the main takeaways or conclusions from the document.
            5. Potential Automation Steps: Based on the content, suggest potential steps for automating processes described in the document.

            Text to analyze:
            {text[:10000]}

            Please format the summary in a clear, structured manner with proper headings.
            """
            
            result = self.gemini_generate_content(prompt, operation=operation)
            
            if result:
                self.logger.info(f"Successfully generated summary for {domain} domain")
            
            return result
            
        except Exception as e:
            return self._handle_api_error(e, operation)
    
    def gemini_generate_block_diagram(self, summary: str, domain: str, extra_info: str = "") -> Optional[str]:
        """Enhanced block diagram generation with validation"""
        operation = "block diagram generation"
        
        # Validate inputs
        if not summary or len(summary.strip()) < 50:
            st.error("❌ Summary is too short for diagram generation")
            return None
        
        try:
            prompt = f"""
            Based on the following summary of a document in the {domain} domain,
            create a detailed block diagram of the automation script flow.
            Make it clearly labeled and easy to understand.
            Additional context: {extra_info}

            Summary:
            {summary}

            Please provide a textual representation of the block diagram using ASCII characters 
            or structured text format. Include:
            - Start and end points
            - Decision points (Yes/No branches)
            - Process steps
            - Error handling paths
            - Clear flow direction arrows

            Format the diagram to be readable and professional.
            """
            
            result = self.gemini_generate_content(prompt, operation=operation)
            
            if result:
                self.logger.info(f"Successfully generated block diagram for {domain} domain")
            
            return result
            
        except Exception as e:
            return self._handle_api_error(e, operation)
    
    def gemini_generate_script(self, summary: str, domain: str, extra_info: str = "") -> Optional[str]:
        """Enhanced script generation with validation and safety checks"""
        operation = "automation script generation"
        
        # Validate inputs
        if not self._validate_inputs(summary, domain, operation):
            return None
        
        try:
            prompt = f"""
            Based on the following summary of a document in the {domain} domain,
            create a completely safe and secure automation script.
            
            IMPORTANT SAFETY REQUIREMENTS:
            - Use only safe, standard libraries
            - Include comprehensive error handling
            - Add input validation
            - Include logging and monitoring
            - Follow security best practices
            - Make the script production-ready
            
            Additional context: {extra_info}

            Summary:
            {summary}

            Please provide a detailed Python script with:
            1. Clear documentation and comments
            2. Proper error handling with try-catch blocks
            3. Input validation
            4. Logging configuration
            5. Main function structure
            6. Safe file operations
            7. No hardcoded credentials or sensitive data

            The script should be ready to run in a production environment.
            """
            
            result = self.gemini_generate_content(prompt, operation=operation)
            
            if result:
                # Basic safety check on generated script
                if self._validate_generated_script(result):
                    self.logger.info(f"Successfully generated safe script for {domain} domain")
                    return result
                else:
                    st.warning("⚠️ Generated script failed safety validation. Please review carefully.")
                    return result  # Still return but with warning
            
            return result
            
        except Exception as e:
            return self._handle_api_error(e, operation)
    
    def _validate_generated_script(self, script: str) -> bool:
        """Basic safety validation for generated scripts"""
        dangerous_patterns = [
            'rm -rf', 'del /f', 'format c:', 'DROP TABLE', 'DELETE FROM',
            'exec(', 'eval(', '__import__', 'subprocess.call',
            'os.system', 'shell=True'
        ]
        
        script_lower = script.lower()
        found_issues = []
        
        for pattern in dangerous_patterns:
            if pattern.lower() in script_lower:
                found_issues.append(pattern)
        
        if found_issues:
            st.warning(f"⚠️ **Potentially dangerous patterns detected:** {', '.join(found_issues)}")
            st.info("Please review the generated script carefully before execution.")
            return False
        
        return True
    
    def gemini_generate_unit_tests(self, summary: str, script: str, domain: str, extra_info: str = "") -> Optional[str]:
        """Enhanced unit test generation"""
        operation = "unit test generation"
        
        # Validate inputs
        if not script or len(script.strip()) < 50:
            st.error("❌ Script is too short for meaningful test generation")
            return None
        
        try:
            prompt = f"""
            Based on the following summary and Python script for the {domain} domain,
            create comprehensive unit tests using Python's unittest framework.
            
            Summary:
            {summary[:2000]}

            Script:
            {script[:5000]}

            Additional context: {extra_info}
            
            Generate unit tests that include:
            1. Test for main functionality
            2. Edge case testing
            3. Error handling validation
            4. Input validation tests
            5. Mock external dependencies
            6. Proper test setup and teardown
            7. Clear test documentation

            Follow unittest best practices and ensure tests are comprehensive but focused.
            """
            
            result = self.gemini_generate_content(prompt, operation=operation)
            
            if result:
                self.logger.info(f"Successfully generated unit tests for {domain} domain")
            
            return result
            
        except Exception as e:
            return self._handle_api_error(e, operation)
    
    def gemini_generate_prerequisites(self, summary: str, domain: str, extra_info: str = "") -> Optional[str]:
        """Enhanced prerequisites generation"""
        operation = "prerequisites generation"
        
        # Validate inputs
        if not self._validate_inputs(summary, domain, operation):
            return None
        
        try:
            prompt = f"""
            Based on the following summary of a document in the {domain} domain,
            create a comprehensive list of prerequisites needed for the automation to run successfully.
            
            Additional context: {extra_info}

            Summary:
            {summary}

            Please organize the prerequisites into the following sections:
            
            ## 1. Hardware Requirements
            - List the minimum server or machine specifications required
            - Include CPU, RAM, storage, and network requirements
            
            ## 2. Software Requirements
            - Operating system compatibility
            - Required programming language versions
            - Essential libraries and packages
            - Database requirements (if applicable)
            
            ## 3. Access Requirements
            - Required permissions and access rights
            - API keys or credentials needed
            - Network access requirements
            - Service dependencies
            
            ## 4. Environment Setup
            - Step-by-step installation instructions
            - Configuration requirements
            - Environment variables needed
            - Security considerations
            
            ## 5. Testing Requirements
            - Test data requirements
            - Testing environment setup
            - Validation procedures
            
            Make the instructions clear and actionable for technical and non-technical users.
            """
            
            result = self.gemini_generate_content(prompt, operation=operation)
            
            if result:
                self.logger.info(f"Successfully generated prerequisites for {domain} domain")
            
            return result
            
        except Exception as e:
            return self._handle_api_error(e, operation)
    
    def gemini_generate_mermaid_diagram(self, summary: str, domain: str, extra_info: str = "", complexity: str = "moderate") -> Optional[str]:
        """Generate Mermaid flowchart diagram using AI enhancement and fallback generation"""
        operation = "Mermaid diagram generation"
        
        # Validate inputs
        if not self._validate_inputs(summary, domain, operation):
            return None
        
        try:
            # First try AI-enhanced generation
            ai_generated = self._generate_ai_mermaid_diagram(summary, domain, extra_info, complexity)
            
            if ai_generated and self._validate_mermaid_syntax(ai_generated):
                self.logger.info(f"Successfully generated AI-enhanced Mermaid diagram for {domain} domain")
                return ai_generated
            
            # Fallback to template-based generation
            self.logger.info("AI generation failed or invalid, using template-based fallback")
            fallback_diagram = self.flowchart_generator.generate_automation_flowchart(summary, domain, complexity)
            
            if fallback_diagram:
                self.logger.info(f"Successfully generated template-based Mermaid diagram for {domain} domain")
                return fallback_diagram
            
            # Final fallback
            return self.flowchart_generator._create_default_diagram()
            
        except Exception as e:
            self.logger.error(f"Mermaid diagram generation failed: {str(e)}")
            return self.flowchart_generator._create_error_diagram(str(e))
    
    def _generate_ai_mermaid_diagram(self, summary: str, domain: str, extra_info: str, complexity: str) -> Optional[str]:
        """Generate Mermaid diagram using AI with specific prompts"""
        try:
            prompt = f"""
            Create a COMPLEX programming flowchart for {domain} automation using PROPER FLOWCHART SYMBOLS.
            
            Domain: {domain}
            Summary: {summary[:1500]}
            Complexity: {complexity}
            
            REQUIREMENTS FOR COMPLEX FLOW:
            1. Multiple decision points with Yes/No branches
            2. Error handling with retry loops
            3. Parallel processing paths where applicable
            4. Proper error states and recovery mechanisms
            5. Realistic automation workflow structure
            
            MANDATORY FLOWCHART SYNTAX RULES:
            1. Start with: flowchart TD
            2. PROPER FLOWCHART SYMBOLS:
               - START/END (Oval): A(("Start"))
               - PROCESS/TASK (Rectangle): B["Process Step"]  
               - DECISION (Diamond): C{{"Input Valid?"}}
               - INPUT/OUTPUT (Parallelogram): D[/"Read File"/]
               - CONNECTOR (Circle): E((A))
            3. Connections: A --> B
            4. Conditional edges: C -->|"Yes"| D and C -->|"No"| E
            5. ALL labels in double quotes
            6. Use meaningful node IDs (A-Z, numbers)
            
            EXAMPLE PROPER FLOWCHART STRUCTURE:
            ```
            flowchart TD
                A(("Start")) --> B[/"Read Input File"/]
                B --> C["Initialize System"]
                C --> D{{"Config Valid?"}}
                D -->|"No"| E["Display Error Message"]
                D -->|"Yes"| F["Connect to Service"]
                F --> G{{"Connection Success?"}}
                G -->|"No"| H["Increment Retry Counter"]
                H --> I{{"Max Retries?"}}
                I -->|"No"| F
                I -->|"Yes"| J["Log Connection Error"]
                G -->|"Yes"| K[/"Input Credentials"/]
                K --> L["Authenticate User"]
                L --> M{{"Auth Success?"}}
                M -->|"No"| N["Handle Auth Error"]
                M -->|"Yes"| O["Process Main Task"]
                O --> P{{"Processing Success?"}}
                P -->|"Yes"| Q[/"Output Results"/]
                P -->|"No"| R["Log Processing Error"]
                Q --> S(("End: Success"))
                E --> T(("End: Config Error"))
                J --> U(("End: Connection Failed"))
                N --> V(("End: Auth Failed"))
                R --> W(("End: Processing Failed"))
            ```
            
            Create a similar complex flow for the {domain} domain with:
            - At least 3-5 decision points
            - 2-3 error handling paths
            - 1-2 retry mechanisms
            - Multiple end states
            
            Return ONLY the flowchart code. NO explanations.
            """
            
            result = self.gemini_generate_content(prompt, operation="AI Mermaid generation")
            
            if result:
                # Clean the result to ensure it's pure Mermaid syntax
                cleaned_result = self._clean_ai_mermaid_output(result)
                return cleaned_result
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI Mermaid generation failed: {str(e)}")
            return None
    
    def _clean_ai_mermaid_output(self, ai_output: str) -> str:
        """Clean AI output to extract pure Mermaid syntax"""
        lines = ai_output.split('\n')
        mermaid_lines = []
        in_code_block = False
        found_flowchart = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check for code block markers
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Skip explanatory text before flowchart
            if not found_flowchart and not stripped.startswith('flowchart'):
                continue
            
            # Found flowchart directive
            if stripped.startswith('flowchart'):
                found_flowchart = True
                mermaid_lines.append(stripped)
                continue
            
            # If we're in flowchart and line looks like Mermaid syntax
            if found_flowchart:
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Stop if we hit explanatory text
                if any(word in stripped.lower() for word in ['explanation', 'this diagram', 'the flowchart', 'note:', 'this shows']):
                    break
                
                # Clean the line for proper syntax
                cleaned_line = self._clean_mermaid_line(stripped)
                if cleaned_line:
                    mermaid_lines.append(cleaned_line)
        
        result = '\n'.join(mermaid_lines)
        
        # Ensure we have a valid start
        if not result.strip().startswith('flowchart'):
            result = f"flowchart TD\n{result}"
        
        return result
    
    def _clean_mermaid_line(self, line: str) -> str:
        """Clean individual Mermaid line for syntax correctness"""
        import re
        
        # Skip style and empty lines
        if line.startswith('style ') or not line.strip():
            return line
        
        # Fix common syntax issues
        # Ensure node labels are properly quoted
        line = re.sub(r'\[([^"]*)\]', r'["\1"]', line)
        line = re.sub(r'\(\[([^"]*)\]\)', r'(["\1"])', line)
        line = re.sub(r'\{\{([^"]*)\}\}', r'{{"\1"}}', line)
        
        # Convert single braces to double braces for decision nodes (Mermaid requirement)
        line = re.sub(r'([A-Z0-9]+)\{([^}]*)\}', r'\1{{"\2"}}', line)
        
        # Fix edge labels
        line = re.sub(r'\|\s*([^"]+?)\s*\|', r'|"\1"|', line)
        
        # Only remove backslashes which can break Mermaid syntax
        # Keep < > { } as they are essential for Mermaid arrows and decision nodes
        line = re.sub(r'\\', '', line)
        
        return line
    
    def _validate_mermaid_syntax(self, mermaid_code: str) -> bool:
        """Enhanced validation of Mermaid syntax"""
        if not mermaid_code or not mermaid_code.strip():
            return False
        
        lines = [line.strip() for line in mermaid_code.split('\n') if line.strip()]
        
        # Must start with flowchart directive
        if not any(line.startswith('flowchart') for line in lines[:3]):
            return False
        
        # Check for common syntax errors
        for line in lines[1:]:  # Skip the flowchart directive
            if not line or line.startswith('style '):
                continue
                
            # Check for unquoted labels in nodes
            if '[' in line and ']' in line:
                # Extract content between brackets
                bracket_matches = re.findall(r'\[([^\]]*)\]', line)
                for match in bracket_matches:
                    if match and not (match.startswith('"') and match.endswith('"')):
                        return False
            
            # Check for unquoted labels in decision nodes
            if '{{' in line and '}}' in line:
                decision_matches = re.findall(r'\{\{([^}]*)\}\}', line)
                for match in decision_matches:
                    if match and not (match.startswith('"') and match.endswith('"')):
                        return False
            
            # Check for unquoted edge labels
            if '|' in line and '-->' in line:
                edge_matches = re.findall(r'\|([^|]*)\|', line)
                for match in edge_matches:
                    if match and not (match.strip().startswith('"') and match.strip().endswith('"')):
                        return False
        
        # Should have some node definitions and connections
        has_nodes = any('-->' in line or '[' in line or '(' in line or '{' in line for line in lines)
        
        return has_nodes
    
    def convert_text_diagram_to_mermaid(self, text_diagram: str, automation_type: str = "process") -> str:
        """Convert existing text-based diagrams to Mermaid format"""
        try:
            return self.flowchart_generator.text_to_mermaid(text_diagram, automation_type)
        except Exception as e:
            self.logger.error(f"Text to Mermaid conversion failed: {str(e)}")
            return self.flowchart_generator._create_error_diagram(str(e))