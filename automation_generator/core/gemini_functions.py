"""
Gemini AI integration for Automation Generator
Adapted from original GeminiFunctions.py to work with package configuration
"""

import os
import logging
import time
import re
from typing import Optional, Dict, Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import retry, stop_after_attempt, wait_fixed

from ..utils.mermaid_renderer import FlowchartGenerator
from .config_manager import ConfigManager


class GenerativeFunction:
    """AI-powered automation generation using Gemini API"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Configuration manager
        self.config_manager = config_manager or ConfigManager()
        
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
            api_key = self.config_manager.get("llm.api_key")
            if not api_key:
                raise ValueError("Gemini API key not found in configuration")
            
            # Handle environment variables
            if api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                api_key = os.environ.get(env_var)
                if not api_key:
                    raise ValueError(f"Environment variable {env_var} not set")
            
            genai.configure(api_key=api_key)
            self.logger.info("Gemini API initialized successfully")
            
        except Exception as e:
            self.logger.error(f"API initialization failed: {str(e)}")
            raise
    
    def _validate_inputs(self, text: str, domain: str, operation: str = "generation") -> tuple[bool, list[str]]:
        """Validate inputs before processing"""
        errors = []
        
        # Text validation
        if not text or not text.strip():
            errors.append("Text content is empty")
        elif len(text.strip()) < 50:
            errors.append("Text content is too short (minimum 50 characters)")
        elif len(text.strip()) > 50000:
            errors.append("Text content is very long and may be truncated")
        
        # Domain validation
        if not domain or not domain.strip():
            errors.append("Domain information is required")
        elif len(domain.strip()) < 2:
            errors.append("Domain must be at least 2 characters")
        
        # Check for potentially problematic content
        suspicious_patterns = ['<script>', '<?php', 'javascript:', 'data:']
        if any(pattern in text.lower() for pattern in suspicious_patterns):
            errors.append("Text contains potentially problematic content")
        
        return len(errors) == 0, errors
    
    def _handle_api_error(self, error: Exception, operation: str) -> Optional[str]:
        """Handle API errors gracefully with specific guidance"""
        error_msg = str(error).lower()
        
        # Quota and rate limiting errors
        if any(keyword in error_msg for keyword in ['quota', 'limit', 'rate']):
            self.logger.error(f"API quota exceeded for {operation}")
            return "API quota exceeded. Please try again later."
        
        # Authentication errors
        if any(keyword in error_msg for keyword in ['api', 'key', 'auth']):
            self.logger.error(f"API authentication failed for {operation}")
            return "API authentication failed. Please check your API key."
        
        # Network errors
        if any(keyword in error_msg for keyword in ['network', 'connection', 'timeout']):
            self.logger.error(f"Network error for {operation}: {error_msg}")
            return "Network connection error. Please check your internet connection."
        
        # Generic error handling
        self.logger.error(f"Unexpected error in {operation}: {error_msg}")
        return f"An error occurred during {operation}. Please try again."
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _make_api_call(self, prompt: str, operation: str) -> str:
        """Make API call with retry logic"""
        try:
            model = genai.GenerativeModel(
                model_name=self.config_manager.get("llm.model", "gemini-1.5-flash"),
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            response = model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from API")
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"API call failed for {operation}: {str(e)}")
            raise
    
    def generate_automation_script(self, sop_text: str, domain: str, script_type: str = "bash") -> Optional[str]:
        """Generate automation script from SOP text"""
        
        # Validate inputs
        is_valid, errors = self._validate_inputs(sop_text, domain, "script generation")
        if not is_valid:
            self.logger.error(f"Input validation failed: {errors}")
            return None
        
        try:
            prompt = f"""
You are an expert automation engineer. Convert the following Standard Operating Procedure (SOP) 
into a {script_type} automation script for the {domain} domain.

SOP Text:
{sop_text}

Requirements:
1. Create a complete, executable {script_type} script
2. Include proper error handling and logging
3. Add comments explaining each step
4. Make it production-ready with appropriate checks
5. Include input validation where necessary
6. Follow {script_type} best practices
7. Make the script idempotent where possible

Domain Context: {domain}

Generate only the script code with comprehensive comments.
"""
            
            script = self._make_api_call(prompt, "script generation")
            
            # Clean up the response
            script = self._clean_script_output(script)
            
            self.logger.info(f"Successfully generated {script_type} script for {domain}")
            return script
            
        except Exception as e:
            error_msg = self._handle_api_error(e, "script generation")
            self.logger.error(f"Script generation failed: {error_msg}")
            return None
    
    def generate_flowchart(self, sop_text: str, domain: str) -> Optional[str]:
        """Generate Mermaid flowchart from SOP text"""
        
        # Validate inputs
        is_valid, errors = self._validate_inputs(sop_text, domain, "flowchart generation")
        if not is_valid:
            self.logger.error(f"Input validation failed: {errors}")
            return None
        
        try:
            prompt = f"""
You are a process visualization expert. Convert the following Standard Operating Procedure (SOP) 
into a Mermaid flowchart for the {domain} domain.

SOP Text:
{sop_text}

Requirements:
1. Create a clear, logical flowchart using Mermaid syntax
2. Use appropriate decision points and process steps
3. Include error handling paths where applicable
4. Use meaningful node names and descriptions
5. Make it visually clear and easy to follow
6. Use proper Mermaid flowchart syntax (graph TD or graph LR)

Domain Context: {domain}

Generate only the Mermaid flowchart code.
"""
            
            flowchart = self._make_api_call(prompt, "flowchart generation")
            
            # Clean up the response and validate Mermaid syntax
            flowchart = self._clean_mermaid_output(flowchart)
            
            self.logger.info(f"Successfully generated flowchart for {domain}")
            return flowchart
            
        except Exception as e:
            error_msg = self._handle_api_error(e, "flowchart generation")
            self.logger.error(f"Flowchart generation failed: {error_msg}")
            return None
    
    def analyze_sop_complexity(self, sop_text: str, domain: str) -> Optional[Dict[str, Any]]:
        """Analyze SOP complexity and provide automation recommendations"""
        
        # Validate inputs
        is_valid, errors = self._validate_inputs(sop_text, domain, "complexity analysis")
        if not is_valid:
            self.logger.error(f"Input validation failed: {errors}")
            return None
        
        try:
            prompt = f"""
You are an automation consultant. Analyze the following Standard Operating Procedure (SOP) 
and provide a comprehensive complexity assessment for automation in the {domain} domain.

SOP Text:
{sop_text}

Analyze and provide:
1. Complexity Score (1-10, where 10 is most complex)
2. Automation Feasibility (High/Medium/Low)
3. Key Automation Challenges
4. Recommended Automation Approach
5. Estimated Development Time
6. Required Skills/Technologies
7. Risk Assessment
8. Success Probability

Format your response as a structured analysis with clear sections.
Domain Context: {domain}
"""
            
            analysis = self._make_api_call(prompt, "complexity analysis")
            
            # Parse the analysis into structured format
            parsed_analysis = self._parse_complexity_analysis(analysis)
            
            self.logger.info(f"Successfully analyzed SOP complexity for {domain}")
            return parsed_analysis
            
        except Exception as e:
            error_msg = self._handle_api_error(e, "complexity analysis")
            self.logger.error(f"Complexity analysis failed: {error_msg}")
            return None
    
    def _clean_script_output(self, script: str) -> str:
        """Clean up script output from AI response"""
        # Remove markdown code blocks
        script = re.sub(r'^```\w*\n', '', script, flags=re.MULTILINE)
        script = re.sub(r'\n```$', '', script, flags=re.MULTILINE)
        
        # Remove extra whitespace
        script = script.strip()
        
        return script
    
    def _clean_mermaid_output(self, mermaid: str) -> str:
        """Clean up Mermaid output from AI response"""
        # Remove markdown code blocks
        mermaid = re.sub(r'^```mermaid\n', '', mermaid, flags=re.MULTILINE)
        mermaid = re.sub(r'^```\n', '', mermaid, flags=re.MULTILINE) 
        mermaid = re.sub(r'\n```$', '', mermaid, flags=re.MULTILINE)
        
        # Remove extra whitespace
        mermaid = mermaid.strip()
        
        # Ensure it starts with graph directive
        if not mermaid.startswith(('graph', 'flowchart')):
            mermaid = 'graph TD\n' + mermaid
        
        return mermaid
    
    def _parse_complexity_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse complexity analysis into structured format"""
        # This is a simplified parser - could be enhanced with more sophisticated parsing
        result = {
            "raw_analysis": analysis,
            "complexity_score": None,
            "automation_feasibility": None,
            "challenges": [],
            "recommendations": [],
            "estimated_time": None,
            "required_skills": [],
            "risk_level": None
        }
        
        # Extract complexity score
        score_match = re.search(r'complexity.*?(\d+)', analysis.lower())
        if score_match:
            result["complexity_score"] = int(score_match.group(1))
        
        # Extract feasibility
        feasibility_match = re.search(r'feasibility.*?(high|medium|low)', analysis.lower())
        if feasibility_match:
            result["automation_feasibility"] = feasibility_match.group(1).title()
        
        return result