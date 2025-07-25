import streamlit as st
import PyPDF2
import re
from typing import Tuple, Optional, List, Dict, Any
import logging

class InputValidator:
    """Comprehensive input validation utilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def validate_pdf_file(uploaded_file) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Comprehensive PDF file validation with detailed feedback"""
        if not uploaded_file:
            return False, "No file uploaded", {}
        
        validation_info = {
            'file_size': uploaded_file.size,
            'file_name': uploaded_file.name,
            'file_type': uploaded_file.type
        }
        
        # Check file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            return False, "File must have a .pdf extension", validation_info
        
        # Check MIME type
        if uploaded_file.type != "application/pdf":
            return False, f"Invalid file type: {uploaded_file.type}. Expected: application/pdf", validation_info
        
        # Check file size (20MB limit)
        max_size = 20 * 1024 * 1024  # 20MB in bytes
        if uploaded_file.size > max_size:
            size_mb = uploaded_file.size / (1024 * 1024)
            return False, f"File size ({size_mb:.1f}MB) exceeds 20MB limit", validation_info
        
        # Check minimum file size (1KB)
        if uploaded_file.size < 1024:
            return False, "File is too small (minimum 1KB)", validation_info
        
        # Try to read PDF structure
        try:
            uploaded_file.seek(0)  # Reset file pointer
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            
            validation_info['page_count'] = len(pdf_reader.pages)
            
            if len(pdf_reader.pages) == 0:
                return False, "PDF appears to be empty (no pages found)", validation_info
            
            if len(pdf_reader.pages) > 100:
                return False, "PDF has too many pages (maximum 100 pages)", validation_info
            
            # Try to extract some text to verify readability
            sample_text = ""
            pages_with_text = 0
            
            for i, page in enumerate(pdf_reader.pages[:5]):  # Check first 5 pages
                try:
                    page_text = page.extract_text().strip()
                    if page_text:
                        sample_text += page_text[:200]  # Sample first 200 chars
                        pages_with_text += 1
                except:
                    continue
            
            validation_info['pages_with_text'] = pages_with_text
            validation_info['sample_text_length'] = len(sample_text)
            
            if pages_with_text == 0:
                return False, "PDF appears to contain no readable text (possibly scanned images)", validation_info
            
            if len(sample_text) < 50:
                return False, "PDF contains insufficient readable text", validation_info
            
            # Reset file pointer for future use
            uploaded_file.seek(0)
            
            return True, None, validation_info
            
        except Exception as e:
            return False, f"PDF validation failed: {str(e)}", validation_info
    
    @staticmethod
    def validate_domain(domain: str) -> Tuple[bool, Optional[str]]:
        """Validate domain/industry input"""
        if not domain:
            return False, "Domain is required"
        
        domain = domain.strip()
        
        if len(domain) < 2:
            return False, "Domain must be at least 2 characters long"
        
        if len(domain) > 100:
            return False, "Domain must be less than 100 characters long"
        
        # Check for invalid characters
        if re.search(r'[<>"\'\;\\]', domain):
            return False, "Domain contains invalid characters: < > \" ' ; \\"
        
        # Check for suspicious patterns
        suspicious_patterns = ['script', 'javascript', 'php', 'sql', 'exec']
        if any(pattern in domain.lower() for pattern in suspicious_patterns):
            return False, "Domain contains potentially problematic content"
        
        # Validate it looks like a reasonable domain name
        if not re.match(r'^[a-zA-Z0-9\s\-_.,&()]+$', domain):
            return False, "Domain contains invalid characters. Use letters, numbers, spaces, and basic punctuation only"
        
        return True, None
    
    @staticmethod
    def validate_extra_info(extra_info: str) -> Tuple[bool, Optional[str]]:
        """Validate additional information input"""
        if not extra_info:
            return True, None  # Optional field
        
        extra_info = extra_info.strip()
        
        if len(extra_info) > 2000:
            return False, "Additional information must be less than 2000 characters"
        
        # Check for suspicious patterns
        suspicious_patterns = ['<script', '<?php', 'javascript:', 'data:', 'vbscript:']
        if any(pattern in extra_info.lower() for pattern in suspicious_patterns):
            return False, "Additional information contains potentially dangerous content"
        
        return True, None
    
    @staticmethod
    def validate_text_content(text: str, min_length: int = 100) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate extracted text content"""
        content_info = {
            'length': len(text) if text else 0,
            'words': len(text.split()) if text else 0,
            'lines': len(text.splitlines()) if text else 0
        }
        
        if not text:
            return False, "No text content found", content_info
        
        text = text.strip()
        content_info['stripped_length'] = len(text)
        
        if len(text) < min_length:
            return False, f"Text content too short for meaningful analysis (minimum {min_length} characters, found {len(text)})", content_info
        
        # Check text quality
        words = text.split()
        if len(words) < 20:
            return False, f"Text appears to contain insufficient readable content ({len(words)} words found)", content_info
        
        # Calculate readability metrics
        avg_word_length = sum(len(word) for word in words) / len(words)
        content_info['avg_word_length'] = round(avg_word_length, 2)
        
        # Check for reasonable text characteristics
        if avg_word_length < 2:
            return False, "Text quality appears poor (very short words)", content_info
        
        if avg_word_length > 20:
            return False, "Text quality appears poor (very long words, possibly corrupted)", content_info
        
        # Check for reasonable character distribution
        alpha_chars = sum(1 for c in text if c.isalpha())
        alpha_ratio = alpha_chars / len(text) if text else 0
        content_info['alpha_ratio'] = round(alpha_ratio, 2)
        
        if alpha_ratio < 0.5:
            return False, f"Text appears to contain too many non-alphabetic characters ({alpha_ratio:.0%})", content_info
        
        return True, None, content_info
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        """Sanitize user input by removing potentially dangerous content"""
        if not text:
            return ""
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<\?php.*?\?>',
            r'javascript:',
            r'vbscript:',
            r'data:',
            r'<iframe[^>]*>.*?</iframe>',
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized
    
    @staticmethod
    def show_validation_summary(validation_results: List[Tuple[str, bool, Optional[str]]]):
        """Display validation results in a user-friendly format"""
        passed = sum(1 for _, success, _ in validation_results if success)
        total = len(validation_results)
        
        if passed == total:
            st.success(f"✅ **All validations passed** ({passed}/{total})")
        else:
            st.error(f"❌ **Validation failed** ({passed}/{total} checks passed)")
        
        # Show details in expander
        with st.expander("📋 Validation Details"):
            for check_name, success, message in validation_results:
                if success:
                    st.write(f"✅ {check_name}")
                else:
                    st.write(f"❌ {check_name}: {message}")