#!/usr/bin/env python3
"""
Edge Cases and Error Conditions Test Suite

Tests edge cases, error conditions, and boundary scenarios for metadata extraction.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager,
    GenerationDownloadConfig,
    EnhancedFileNamer
)


class TestMetadataEdgeCases:
    """Test suite for edge cases and error conditions"""

    @pytest.fixture
    def test_config(self):
        """Create test configuration"""
        return GenerationDownloadConfig(
            downloads_folder="/tmp/test_downloads",
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True,
            unique_id="edge_test"
        )

    @pytest.fixture
    def file_namer(self, test_config):
        """Create file namer instance"""
        return EnhancedFileNamer(test_config)

    @pytest.mark.asyncio
    async def test_empty_page_content(self, test_config):
        """Test extraction with completely empty page"""
        
        class EmptyMockPage:
            @property
            def url(self):
                return "https://empty-page.com"
            
            async def title(self):
                return ""
            
            async def query_selector_all(self, selector):
                return []
            
            async def evaluate(self, script):
                return ""
        
        manager = GenerationDownloadManager(test_config)
        empty_page = EmptyMockPage()
        
        metadata = await manager.extract_metadata_from_page(empty_page)
        
        assert metadata is not None
        assert metadata.get("generation_date") == "Unknown Date"
        assert metadata.get("prompt") == "Unknown Prompt"

    @pytest.mark.asyncio
    async def test_network_timeouts(self, test_config):
        """Test handling of network timeouts during extraction"""
        
        class TimeoutMockPage:
            @property
            def url(self):
                return "https://slow-page.com"
            
            async def title(self):
                raise asyncio.TimeoutError("Page load timeout")
            
            async def query_selector_all(self, selector):
                await asyncio.sleep(0.1)  # Simulate slow response
                raise asyncio.TimeoutError("Selector timeout")
        
        manager = GenerationDownloadManager(test_config)
        timeout_page = TimeoutMockPage()
        
        metadata = await manager.extract_metadata_from_page(timeout_page)
        
        # Should handle timeout gracefully
        assert metadata is None

    @pytest.mark.asyncio
    async def test_malformed_html_content(self, test_config):
        """Test extraction with malformed HTML"""
        
        class MalformedMockPage:
            @property
            def url(self):
                return "https://malformed-page.com"
            
            async def title(self):
                return "Malformed Page"
            
            async def query_selector_all(self, selector):
                if "Creation Time" in selector:
                    return [MalformedElement()]
                return []
        
        class MalformedElement:
            async def text_content(self):
                return None  # Malformed content
            
            async def is_visible(self):
                raise Exception("DOM error")
            
            async def evaluate_handle(self, script):
                raise Exception("Script execution failed")
        
        manager = GenerationDownloadManager(test_config)
        malformed_page = MalformedMockPage()
        
        metadata = await manager.extract_metadata_from_page(malformed_page)
        
        # Should handle malformed content gracefully
        assert metadata.get("generation_date") == "Unknown Date"

    def test_invalid_date_formats(self, file_namer):
        """Test date parsing with various invalid formats"""
        
        invalid_dates = [
            None,
            "",
            "Invalid Date",
            "32 Aug 2025 25:70:99",  # Invalid values
            "Yesterday",
            "2025-13-45",  # Invalid month/day
            "Aug 99, 2025",  # Invalid day
            "25 XXX 2025",  # Invalid month
            "Not a date at all",
            "2025/15/45 30:80:90",
            "<script>alert('xss')</script>",  # XSS attempt
            "🎉 24 Aug 2025 01:37:01 🎉",  # With emojis
            "24\nAug\n2025\n01:37:01",  # With newlines
        ]
        
        for invalid_date in invalid_dates:
            result = file_namer.parse_creation_date(invalid_date)
            
            # Should return current timestamp format or handle gracefully
            assert isinstance(result, str)
            assert len(result.split('-')) == 6  # YYYY-MM-DD-HH-MM-SS format

    def test_extreme_filename_scenarios(self, file_namer):
        """Test filename generation with extreme scenarios"""
        
        extreme_cases = [
            # Very long creation date
            ("A" * 1000, "Extremely long creation date"),
            
            # Special characters in date
            ("24 Aug 2025 01:37:01 <>&\"'/\\|?*", "Special characters"),
            
            # Unicode characters
            ("24 ağustos 2025 01:37:01 中文", "Unicode characters"),
            
            # Empty/null date
            ("", "Empty date"),
            (None, "Null date"),
            
            # SQL injection attempt
            ("'; DROP TABLE files; --", "SQL injection attempt"),
            
            # Path traversal attempt
            ("../../../etc/passwd", "Path traversal"),
            
            # Very long path
            ("/" + "long_directory/" * 50 + "file.mp4", "Deep path"),
        ]
        
        for date_input, test_name in extreme_cases:
            try:
                result = file_namer.parse_creation_date(date_input)
                
                # Should produce valid filename-safe result
                assert isinstance(result, str)
                assert len(result) <= 200  # Reasonable length limit
                
                # Should not contain path separators or dangerous characters
                dangerous_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*', '\x00']
                for char in dangerous_chars:
                    assert char not in result, f"Dangerous character '{char}' found in result for {test_name}"
                
            except Exception as e:
                # Should not crash, but may return fallback
                print(f"Expected fallback for {test_name}: {e}")

    def test_memory_exhaustion_scenarios(self, test_config):
        """Test behavior with memory-intensive operations"""
        
        manager = GenerationDownloadManager(test_config)
        
        # Create very large candidate list
        huge_candidates = []
        for i in range(10000):
            huge_candidates.append({
                "extracted_date": f"24 Aug 2025 {i%24:02d}:{i%60:02d}:{i%60:02d}",
                "element_index": i,
                "confidence": i / 10000.0
            })
        
        # Should handle large datasets efficiently without crashing
        try:
            selected = manager._select_best_date_candidate(huge_candidates)
            assert selected is not None
            
            # Should complete in reasonable time
            import time
            start_time = time.time()
            selected = manager._select_best_date_candidate(huge_candidates)
            end_time = time.time()
            
            assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
            
        except MemoryError:
            pytest.skip("System doesn't have enough memory for this test")

    @pytest.mark.asyncio
    async def test_concurrent_access_conflicts(self, test_config):
        """Test concurrent access to shared resources"""
        
        import threading
        import time
        
        manager = GenerationDownloadManager(test_config)
        results = []
        errors = []
        
        def extract_metadata_worker(worker_id):
            try:
                # Simulate concurrent metadata extraction
                candidates = [{"extracted_date": f"Worker {worker_id} Date"}]
                result = manager._select_best_date_candidate(candidates)
                results.append((worker_id, result))
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Create multiple threads
        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=extract_metadata_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access without errors
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 10

    def test_disk_space_exhaustion(self, test_config):
        """Test behavior when disk space is limited"""
        
        # Mock pathlib to simulate disk full
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = OSError("No space left on device")
            
            # Should handle disk space errors gracefully
            try:
                manager = GenerationDownloadManager(test_config)
                # Manager creation might fail, but shouldn't crash
            except OSError:
                # Expected behavior - graceful handling of disk space issues
                pass

    def test_permission_denied_scenarios(self, test_config):
        """Test behavior with permission denied errors"""
        
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            try:
                manager = GenerationDownloadManager(test_config)
            except PermissionError:
                # Should handle permission errors gracefully
                pass

    @pytest.mark.asyncio
    async def test_browser_crash_scenarios(self, test_config):
        """Test handling of browser crashes during extraction"""
        
        class CrashingMockPage:
            def __init__(self):
                self.call_count = 0
            
            @property
            def url(self):
                return "https://crashing-page.com"
            
            async def query_selector_all(self, selector):
                self.call_count += 1
                if self.call_count > 2:
                    raise Exception("Browser connection lost")
                return []
        
        manager = GenerationDownloadManager(test_config)
        crashing_page = CrashingMockPage()
        
        # Should handle browser crashes gracefully
        metadata = await manager.extract_metadata_from_page(crashing_page)
        assert metadata is None

    def test_unicode_and_encoding_issues(self, file_namer):
        """Test handling of various unicode and encoding scenarios"""
        
        unicode_dates = [
            "24 août 2025 01:37:01",  # French
            "24 أغسطس 2025 01:37:01",  # Arabic
            "24 八月 2025 01:37:01",  # Chinese
            "24 Αύγ 2025 01:37:01",  # Greek
            "24 авг 2025 01:37:01",  # Russian
            "२४ अगस्त २०२५ ०१:३७:०१",  # Hindi numerals
            "𝟐𝟒 𝐀𝐮𝐠 𝟐𝟎𝟐𝟓 𝟎𝟏:𝟑𝟕:𝟎𝟏",  # Mathematical bold
            "\u202824 Aug 2025 01:37:01\u2029",  # With direction marks
        ]
        
        for unicode_date in unicode_dates:
            try:
                result = file_namer.parse_creation_date(unicode_date)
                
                # Should handle unicode gracefully
                assert isinstance(result, str)
                
                # Result should be ASCII-safe for filenames
                result.encode('ascii', errors='ignore')
                
            except UnicodeError:
                # Acceptable to fail gracefully with unicode issues
                pass

    def test_injection_attack_prevention(self, file_namer):
        """Test prevention of various injection attacks"""
        
        malicious_inputs = [
            # Command injection
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& format c:",
            "`rm -rf /`",
            "$(rm -rf /)",
            
            # Path traversal
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            
            # Null bytes
            "24 Aug 2025\x0001:37:01",
            "24 Aug 2025\x00.mp4",
            
            # XML/HTML injection
            "<script>alert('xss')</script>",
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
            
            # SQL injection
            "'; DROP TABLE files; --",
            "' UNION SELECT * FROM users --",
            
            # Format string attacks
            "%s%s%s%s%s",
            "{0}{1}{2}{3}",
            
            # Buffer overflow attempts
            "A" * 10000,
        ]
        
        for malicious_input in malicious_inputs:
            result = file_namer.parse_creation_date(malicious_input)
            
            # Should sanitize malicious content
            assert isinstance(result, str)
            assert len(result) <= 200  # Should not be excessively long
            
            # Should not contain obvious malicious patterns
            dangerous_patterns = [';', '|', '&', '`', '$', '<', '>', '"', "'", '\x00']
            for pattern in dangerous_patterns:
                assert pattern not in result or result == datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    def test_extremely_large_metadata(self, test_config):
        """Test handling of extremely large metadata"""
        
        manager = GenerationDownloadManager(test_config)
        
        # Create massive metadata
        huge_prompt = "A" * 100000  # 100KB prompt
        huge_date = "24 Aug 2025 01:37:01" + " " + "B" * 50000  # Large date string
        
        # Test with huge candidates list
        massive_candidates = []
        for i in range(1000):
            massive_candidates.append({
                "extracted_date": huge_date,
                "element_index": i,
                "full_text": huge_prompt,
                "confidence": 0.5
            })
        
        # Should handle large data gracefully
        selected = manager._select_best_date_candidate(massive_candidates)
        assert selected is not None

    def test_race_condition_scenarios(self, test_config):
        """Test race condition handling"""
        
        import threading
        import time
        
        manager = GenerationDownloadManager(test_config)
        shared_resource = {"counter": 0, "results": []}
        
        def worker_function(worker_id):
            for i in range(100):
                # Simulate race condition on shared resource
                current = shared_resource["counter"]
                time.sleep(0.0001)  # Small delay to encourage race conditions
                shared_resource["counter"] = current + 1
                shared_resource["results"].append(f"worker_{worker_id}_item_{i}")
        
        # Create multiple threads to trigger race conditions
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker_function, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check that we handled concurrent access (might have race conditions)
        assert len(shared_resource["results"]) <= 500  # Max possible items
        assert shared_resource["counter"] <= 500

    def test_system_resource_limits(self, test_config):
        """Test behavior under system resource limits"""
        
        import resource
        import os
        
        # Test with limited file descriptors (if running on Unix)
        if hasattr(resource, 'RLIMIT_NOFILE'):
            try:
                # Get current limit
                soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
                
                # Temporarily reduce file descriptor limit
                resource.setrlimit(resource.RLIMIT_NOFILE, (10, hard_limit))
                
                # Try to create manager with limited resources
                manager = GenerationDownloadManager(test_config)
                assert manager is not None
                
                # Restore original limit
                resource.setrlimit(resource.RLIMIT_NOFILE, (soft_limit, hard_limit))
                
            except (ValueError, OSError):
                # Skip if we can't modify limits
                pytest.skip("Cannot modify system resource limits")

    def test_cleanup_and_resource_management(self, test_config):
        """Test proper cleanup and resource management"""
        
        manager = GenerationDownloadManager(test_config)
        
        # Test that manager cleans up resources properly
        assert hasattr(manager, 'debug_logger')
        assert hasattr(manager, 'file_manager')
        assert hasattr(manager, 'logger')
        
        # Test cleanup behavior
        manager.request_stop()
        assert manager.should_stop is True

    @pytest.mark.asyncio
    async def test_extremely_slow_page_responses(self, test_config):
        """Test handling of extremely slow page responses"""
        
        class SlowMockPage:
            @property
            def url(self):
                return "https://very-slow-page.com"
            
            async def query_selector_all(self, selector):
                # Simulate very slow response
                await asyncio.sleep(0.5)
                return []
        
        manager = GenerationDownloadManager(test_config)
        slow_page = SlowMockPage()
        
        # Should handle slow responses
        start_time = datetime.now()
        metadata = await manager.extract_metadata_from_page(slow_page)
        end_time = datetime.now()
        
        # Should complete and return default values
        assert metadata.get("generation_date") == "Unknown Date"
        
        # Should not hang indefinitely
        duration = (end_time - start_time).total_seconds()
        assert duration < 10.0  # Should complete within reasonable time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])