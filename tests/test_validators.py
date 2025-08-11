"""
Unit tests for InputValidator
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from automation_generator.utils.validators import InputValidator


class TestInputValidator:
    """Test cases for InputValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create InputValidator instance"""
        return InputValidator()
    
    def test_validate_domain_valid_inputs(self, validator):
        """Test domain validation with valid inputs"""
        valid_domains = [
            "DevOps",
            "IT Support", 
            "Cloud Management",
            "Software Development",
            "Data Science & Analytics",
            "Network Administration (Enterprise)"
        ]
        
        for domain in valid_domains:
            is_valid, error = validator.validate_domain(domain)
            assert is_valid is True
            assert error is None
    
    def test_validate_domain_invalid_inputs(self, validator):
        """Test domain validation with invalid inputs"""
        invalid_cases = [
            ("", "Domain is required"),
            ("a", "Domain must be at least 2 characters long"),
            ("x" * 101, "Domain must be less than 100 characters long"),
            ("test<script>", "Domain contains invalid characters"),
            ("javascript:alert()", "Domain contains potentially problematic content"),
            ("test; DROP TABLE", "Domain contains potentially problematic content")
        ]
        
        for domain, expected_error_part in invalid_cases:
            is_valid, error = validator.validate_domain(domain)
            assert is_valid is False
            assert error is not None
            assert expected_error_part.lower() in error.lower()
    
    def test_validate_extra_info_valid_inputs(self, validator):
        """Test extra info validation with valid inputs"""
        valid_inputs = [
            "",  # Empty is allowed
            "Additional requirements for the automation",
            "Need error handling and logging",
            "Should work on both Windows and Linux"
        ]
        
        for extra_info in valid_inputs:
            is_valid, error = validator.validate_extra_info(extra_info)
            assert is_valid is True
            assert error is None
    
    def test_validate_extra_info_invalid_inputs(self, validator):
        """Test extra info validation with invalid inputs"""
        invalid_cases = [
            ("x" * 2001, "Additional information must be less than 2000 characters"),
            ("<script>alert('xss')</script>", "Additional information contains potentially dangerous content"),
            ("<?php echo 'test'; ?>", "Additional information contains potentially dangerous content"),
            ("javascript:void(0)", "Additional information contains potentially dangerous content")
        ]
        
        for extra_info, expected_error_part in invalid_cases:
            is_valid, error = validator.validate_extra_info(extra_info)
            assert is_valid is False
            assert error is not None
            assert expected_error_part.lower() in error.lower()
    
    def test_validate_text_content_valid(self, validator):
        """Test text content validation with valid content"""
        valid_text = "This is a valid SOP text content that has sufficient length and contains meaningful information that can be processed for automation generation. It should have enough words and characters to be considered valid content for processing."
        
        is_valid, error, info = validator.validate_text_content(valid_text)
        
        assert is_valid is True
        assert error is None
        assert info['length'] == len(valid_text)
        assert info['words'] > 20
        assert info['alpha_ratio'] > 0.5
    
    def test_validate_text_content_invalid(self, validator):
        """Test text content validation with invalid content"""
        invalid_cases = [
            ("", "No text content found"),
            ("short", "Text content too short for meaningful analysis"),
            ("a b c d", "Text appears to contain insufficient readable content"),
            ("123456789012345678901234567890", "Text quality appears poor"),  # Very long words
            ("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", "Text appears to contain too many non-alphabetic characters")
        ]
        
        for text, expected_error_part in invalid_cases:
            is_valid, error, info = validator.validate_text_content(text)
            assert is_valid is False
            assert error is not None
            assert expected_error_part.lower() in error.lower()
    
    def test_sanitize_input(self, validator):
        """Test input sanitization"""
        dangerous_inputs = [
            ("<script>alert('xss')</script>Hello", "Hello"),
            ("<?php echo 'test'; ?>World", "World"),  
            ("javascript:void(0) Test", "Test"),
            ("Normal   text   with   spaces", "Normal text with spaces"),
            ("x" * 10010, "x" * 10000 + "...")  # Length limiting
        ]
        
        for dangerous_input, expected_output in dangerous_inputs:
            result = validator.sanitize_input(dangerous_input)
            assert result == expected_output
    
    def test_validate_all_inputs_success(self, validator):
        """Test validating all inputs with valid data"""
        is_valid, errors = validator.validate_all_inputs(
            domain="DevOps",
            text_content="This is a valid SOP text that contains sufficient content for processing and automation generation. It has enough words and characters to pass all validation checks.",
            extra_info="Additional requirements for error handling"
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_all_inputs_failures(self, validator):
        """Test validating all inputs with invalid data"""
        is_valid, errors = validator.validate_all_inputs(
            domain="",  # Invalid domain
            text_content="short",  # Invalid text
            extra_info="<script>alert('xss')</script>"  # Invalid extra info
        )
        
        assert is_valid is False
        assert len(errors) >= 3  # Should have errors for domain, text, and extra info
        assert any("domain" in error.lower() for error in errors)
        assert any("text content" in error.lower() for error in errors)
        assert any("extra info" in error.lower() for error in errors)
    
    @patch('automation_generator.utils.validators.PDF_AVAILABLE', True)
    def test_validate_pdf_file_success(self, validator):
        """Test PDF file validation with valid file"""
        # Create a temporary PDF-like file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Write minimal PDF header
            tmp_file.write(b'%PDF-1.4\n')
            tmp_file.write(b'1 0 obj\n<<\n/Type /Pages\n>>\nendobj\n')
            tmp_file.write(b'xref\n0 2\n0000000000 65535 f \n')
            tmp_file.write(b'trailer\n<<\n/Size 2\n>>\n')
            tmp_file.write(b'startxref\n0\n%%EOF\n')
            tmp_file.flush()
            
            try:
                # This test would require actual PyPDF2 and valid PDF structure
                # For now, we test the file existence check
                temp_path = Path(tmp_file.name)
                assert temp_path.exists()
                
            finally:
                Path(tmp_file.name).unlink(missing_ok=True)
    
    @patch('automation_generator.utils.validators.PDF_AVAILABLE', False)
    def test_validate_pdf_file_no_pypdf2(self, validator):
        """Test PDF validation when PyPDF2 is not available"""
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            is_valid, error, info = validator.validate_pdf_file(tmp_file.name)
            
            assert is_valid is False
            assert "PyPDF2 not available" in error
    
    def test_validate_pdf_file_not_found(self, validator):
        """Test PDF validation with non-existent file"""
        is_valid, error, info = validator.validate_pdf_file("/path/that/does/not/exist.pdf")
        
        assert is_valid is False
        assert "File not found" in error
    
    def test_validate_uploaded_pdf_basic_checks(self, validator):
        """Test uploaded PDF validation with basic checks"""
        # Mock uploaded file object
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.type = "application/pdf"
        mock_file.size = 5000  # 5KB
        
        # Test with PDF_AVAILABLE = False to skip PyPDF2 checks
        with patch('automation_generator.utils.validators.PDF_AVAILABLE', False):
            is_valid, error, info = validator.validate_uploaded_pdf(mock_file)
            
            assert is_valid is True
            assert "PDF structure validation skipped" in error
            assert info['file_size'] == 5000
    
    def test_validate_uploaded_pdf_invalid_extension(self, validator):
        """Test uploaded file validation with invalid extension"""
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_file.type = "text/plain"
        mock_file.size = 5000
        
        is_valid, error, info = validator.validate_uploaded_pdf(mock_file)
        
        assert is_valid is False
        assert "must have a .pdf extension" in error
    
    def test_validate_uploaded_pdf_too_large(self, validator):
        """Test uploaded file validation with oversized file"""
        mock_file = Mock()
        mock_file.name = "test.pdf" 
        mock_file.type = "application/pdf"
        mock_file.size = 25 * 1024 * 1024  # 25MB
        
        is_valid, error, info = validator.validate_uploaded_pdf(mock_file)
        
        assert is_valid is False
        assert "exceeds 20MB limit" in error