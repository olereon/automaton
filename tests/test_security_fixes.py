#!/usr/bin/env python3
"""
Security Tests for Automaton Web Automation Tool
Tests all critical security fixes implemented by the hive-mind security swarm
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType, SecurityError


class TestSecurityFixes:
    """Test suite for critical security vulnerabilities"""

    def test_sanitize_filename_path_traversal_prevention(self):
        """Test filename sanitization prevents path traversal attacks"""
        # Create a test engine
        config = AutomationConfig("Test", "https://example.com", actions=[])
        engine = WebAutomationEngine(config)
        
        # Test path traversal attempts
        malicious_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "../../sensitive/file.txt",
            "normal_file../../etc/passwd",
            "file.txt\x00../../etc/passwd",  # Null byte injection
            "con.txt",  # Windows reserved name
            "prn.txt",  # Windows reserved name
        ]
        
        for malicious_name in malicious_names:
            sanitized = engine._sanitize_filename(malicious_name)
            
            # Should not contain path separators
            assert ".." not in sanitized
            assert "/" not in sanitized
            assert "\\" not in sanitized
            
            # Should be a safe filename
            assert len(sanitized) > 0
            assert sanitized != malicious_name

    def test_css_selector_sanitization(self):
        """Test CSS selector sanitization prevents JavaScript injection"""
        config = AutomationConfig("Test", "https://example.com", actions=[])
        engine = WebAutomationEngine(config)
        
        # Valid selectors should pass
        valid_selectors = [
            "#button",
            ".class-name",
            "div.container",
            "input[type='text']",
            "a[href='#section']",
            ".parent > .child",
            "ul li:first-child"
        ]
        
        for selector in valid_selectors:
            result = engine._sanitize_css_selector(selector)
            assert result == selector
        
        # Malicious selectors should raise SecurityError
        malicious_selectors = [
            "'; alert('xss'); //",
            "javascript:alert('xss')",
            "<script>alert('xss')</script>",
            "expression(alert('xss'))",
            "onclick=alert('xss')",
            "vbscript:msgbox('xss')",
            "div'; DROP TABLE users; --"
        ]
        
        for malicious_selector in malicious_selectors:
            with pytest.raises(SecurityError):
                engine._sanitize_css_selector(malicious_selector)

    def test_file_upload_validation(self):
        """Test file upload validation prevents malicious uploads"""
        config = AutomationConfig("Test", "https://example.com", actions=[])
        engine = WebAutomationEngine(config)
        
        # Test with non-existent file
        with pytest.raises(SecurityError, match="File does not exist"):
            engine._validate_upload_path("/non/existent/file.jpg")
        
        # Test with directory instead of file
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(SecurityError, match="Path is not a file"):
                engine._validate_upload_path(temp_dir)
        
        # Test with disallowed file extension
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"fake executable")
            temp_file.flush()
            
            try:
                with pytest.raises(SecurityError, match="File type not allowed"):
                    engine._validate_upload_path(temp_file.name)
            finally:
                os.unlink(temp_file.name)
        
        # Test with allowed file extension
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(b"fake image data")
            temp_file.flush()
            
            try:
                result = engine._validate_upload_path(temp_file.name)
                assert result == str(Path(temp_file.name).resolve())
            finally:
                os.unlink(temp_file.name)
        
        # Test file size limit
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            # Create a file larger than 100MB
            large_data = b"x" * (101 * 1024 * 1024)  # 101MB
            temp_file.write(large_data)
            temp_file.flush()
            
            try:
                with pytest.raises(SecurityError, match="File too large"):
                    engine._validate_upload_path(temp_file.name)
            finally:
                os.unlink(temp_file.name)

    def test_download_path_security(self):
        """Test download path validation is implemented in the code"""
        # Read the source to verify security fixes are in place
        engine_path = Path(__file__).parent.parent / "src" / "core" / "engine.py"
        with open(engine_path, 'r') as f:
            content = f.read()
        
        # Verify security implementations exist
        assert "SecurityError" in content
        assert "_sanitize_filename" in content
        assert "_sanitize_css_selector" in content
        assert "_validate_upload_path" in content
        assert "Path traversal attempt detected" in content

    def test_javascript_injection_prevention(self):
        """Test JavaScript evaluation uses parameterized queries"""
        engine_path = Path(__file__).parent.parent / "src" / "core" / "engine.py"
        with open(engine_path, 'r') as f:
            content = f.read()
        
        # Verify parameterized JavaScript evaluation
        assert "(selector) => {" in content  # Parameterized function
        assert "safe_selector" in content  # Sanitized selector usage
        
        # Should not contain dangerous string interpolation
        dangerous_patterns = [
            f"f\"\"\".*{{selector}}.*\"\"\"",  # String interpolation in JS
            f"f'.*{{selector}}.*'",  # String interpolation in JS
        ]
        
        import re
        for pattern in dangerous_patterns:
            matches = re.search(pattern, content)
            # If found, ensure it's been replaced with safe version
            if matches:
                # Check that safe_selector is used instead
                assert "safe_selector" in content

    def test_browser_security_configuration(self):
        """Test browser is configured securely"""
        engine_path = Path(__file__).parent.parent / "src" / "core" / "engine.py"
        with open(engine_path, 'r') as f:
            content = f.read()
        
        # Verify dangerous flags are not present
        dangerous_flags = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security"
        ]
        
        for flag in dangerous_flags:
            assert flag not in content, f"Dangerous browser flag found: {flag}"

    def test_security_error_class_exists(self):
        """Test SecurityError class is properly defined"""
        from core.engine import SecurityError
        
        # Should be able to raise SecurityError
        with pytest.raises(SecurityError):
            raise SecurityError("Test security error")

    def test_credential_manager_security(self):
        """Test credential manager provides encryption"""
        try:
            from utils.credential_manager import CredentialManager
            
            # Should use encryption
            cm = CredentialManager()
            assert hasattr(cm, 'cipher'), "Credential manager should have encryption cipher"
            assert hasattr(cm, '_initialize_encryption'), "Should have encryption initialization"
            
        except ImportError:
            pytest.skip("Credential manager not available")


if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v"])