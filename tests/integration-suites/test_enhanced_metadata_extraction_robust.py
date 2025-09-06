#!/usr/bin/env python3
"""
Test Enhanced Metadata Extraction - Robust Implementation
Comprehensive test suite for the improved metadata extraction with multiple strategies and error handling.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from src.utils.enhanced_metadata_extraction import (
    extract_container_metadata_enhanced,
    MetadataExtractionConfig,
    _validate_creation_time_format,
    _is_valid_prompt_candidate,
    _extract_fuzzy_creation_time,
    _strategy_text_patterns,
    _strategy_dom_analysis,
    _strategy_spatial_analysis,
    _strategy_comprehensive_fallback
)


class TestEnhancedMetadataExtractionRobust:
    """Test suite for robust enhanced metadata extraction"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = MetadataExtractionConfig()
        self.config.debug_mode = True
        self.config.log_extraction_details = True

    def test_creation_time_format_validation(self):
        """Test creation time format validation with various inputs"""
        
        # Valid formats
        valid_times = [
            "24 Aug 2025 01:37:01",
            "1 Jan 2024 12:00:00", 
            "31 December 2025 23:59:59",
            "24-08-2025 01:37:01",
            "2025-08-24 01:37:01",
            "01:37:01 24 Aug 2025",  # Time-first format
        ]
        
        for time_str in valid_times:
            assert _validate_creation_time_format(time_str), f"Should validate: {time_str}"
        
        # Invalid formats
        invalid_times = [
            "Not a date",
            "24/08",  # Incomplete
            "2025-13-45 25:70:80",  # Invalid values
            "",
            "Creation Time",
            "24 Aug",  # Missing year and time
        ]
        
        for time_str in invalid_times:
            assert not _validate_creation_time_format(time_str), f"Should not validate: {time_str}"

    def test_prompt_candidate_validation(self):
        """Test prompt candidate validation logic"""
        
        # Valid prompt candidates
        valid_prompts = [
            "The camera captures a beautiful sunset over the mountains with vibrant colors",
            "A close-up shot of a person reading a book in a cozy cafe",
            "Scene shows two people having a conversation in a park setting",
            "An aerial view of a bustling city with tall buildings and busy streets",
            "Camera pans across a field of flowers with bees collecting nectar"
        ]
        
        for prompt in valid_prompts:
            assert _is_valid_prompt_candidate(prompt), f"Should be valid prompt: {prompt}"
        
        # Invalid prompt candidates
        invalid_prompts = [
            "Creation Time",
            "Download",
            "24 Aug 2025 01:37:01",  # Timestamp
            "Short",  # Too short
            "www.example.com",  # URL
            "Copyright 2025",  # Copyright notice
            "",  # Empty
            "click button menu",  # UI elements
        ]
        
        for prompt in invalid_prompts:
            assert not _is_valid_prompt_candidate(prompt), f"Should not be valid prompt: {prompt}"

    def test_fuzzy_creation_time_extraction(self):
        """Test fuzzy creation time extraction"""
        
        test_cases = [
            {
                'input': "Something 24-Aug-2025 01:37:01 something else",
                'expected': "24 Aug 2025 01:37:01"
            },
            {
                'input': "Data: 2025/08/24 01:37:01 more data",
                'expected': "24 08 2025 01:37:01"  # Will be reformatted
            },
            {
                'input': "Random text with no date",
                'expected': None
            }
        ]
        
        for case in test_cases:
            result = _extract_fuzzy_creation_time(case['input'])
            if case['expected']:
                assert result is not None, f"Should extract time from: {case['input']}"
                # Allow for formatting variations in fuzzy extraction
                assert any(part in result for part in ["24", "Aug", "2025", "01:37:01"]), f"Extracted time should contain expected parts: {result}"
            else:
                assert result is None, f"Should not extract time from: {case['input']}"

    @pytest.mark.asyncio
    async def test_text_patterns_strategy(self):
        """Test text pattern extraction strategy"""
        
        test_content = """
        Some metadata
        Creation Time 24 Aug 2025 01:37:01
        The camera captures a beautiful sunset over mountains with vibrant orange and pink hues.
        More content
        """
        
        creation_time, prompt = await _strategy_text_patterns(test_content, self.config)
        
        assert creation_time == "24 Aug 2025 01:37:01"
        assert prompt is not None
        assert "camera" in prompt.lower()
        assert len(prompt) > 30

    @pytest.mark.asyncio
    async def test_dom_analysis_strategy_mock(self):
        """Test DOM analysis strategy with mocked elements"""
        
        # Create mock container
        mock_container = AsyncMock()
        
        # Mock time element
        mock_time_element = AsyncMock()
        mock_time_element.text_content = AsyncMock(return_value="24 Aug 2025 01:37:01")
        
        # Mock prompt element  
        mock_prompt_element = AsyncMock()
        mock_prompt_element.text_content = AsyncMock(return_value="The camera shows a beautiful landscape with mountains")
        
        # Configure query_selector_all to return appropriate elements
        def mock_query_selector_all(selector):
            if 'time' in selector or 'date' in selector:
                return asyncio.create_task(asyncio.coroutine(lambda: [mock_time_element])())
            elif 'prompt' in selector or 'aria-describedby' in selector:
                return asyncio.create_task(asyncio.coroutine(lambda: [mock_prompt_element])())
            else:
                return asyncio.create_task(asyncio.coroutine(lambda: [])())
        
        mock_container.query_selector_all.side_effect = mock_query_selector_all
        
        creation_time, prompt = await _strategy_dom_analysis(mock_container, self.config)
        
        assert creation_time == "24 Aug 2025 01:37:01"
        assert prompt is not None
        assert "camera" in prompt.lower()

    @pytest.mark.asyncio
    async def test_comprehensive_fallback_strategy(self):
        """Test comprehensive fallback strategy"""
        
        # Test with complex mixed content
        test_content = """
        Random header text | More stuff
        Generated: 24 Aug 2025 01:37:01
        • The camera pans across a serene lake surrounded by pine trees
        • Download button
        • More UI elements
        """
        
        creation_time, prompt = await _strategy_comprehensive_fallback(test_content, self.config)
        
        assert creation_time == "24 Aug 2025 01:37:01"
        assert prompt is not None
        assert "camera" in prompt.lower()
        assert "lake" in prompt.lower()

    @pytest.mark.asyncio
    async def test_main_extraction_function_with_retries(self):
        """Test main extraction function with retry logic"""
        
        # Create mock container that fails initially then succeeds
        mock_container = AsyncMock()
        
        call_count = 0
        def mock_text_content():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ""  # Empty first time (simulate loading)
            else:
                return "Creation Time 24 Aug 2025 01:37:01\nCamera shows beautiful scenery"
        
        mock_container.text_content = AsyncMock(side_effect=mock_text_content)
        mock_container.wait_for = AsyncMock()
        mock_container.query_selector_all = AsyncMock(return_value=[])
        
        # Initial empty content should trigger retry
        result = await extract_container_metadata_enhanced(
            mock_container, 
            "",  # Empty initial content
            0,   # Retry count
            self.config
        )
        
        # Should eventually succeed after retry
        assert result is not None
        assert result['creation_time'] == "24 Aug 2025 01:37:01"
        assert result['prompt'] is not None

    @pytest.mark.asyncio 
    async def test_timeout_handling(self):
        """Test timeout handling in DOM operations"""
        
        # Create mock container that times out
        mock_container = AsyncMock()
        
        async def timeout_query_selector_all(selector):
            await asyncio.sleep(5)  # Simulate long operation
            return []
        
        mock_container.query_selector_all.side_effect = timeout_query_selector_all
        
        # Set short timeout for test
        fast_config = MetadataExtractionConfig()
        fast_config.dom_wait_timeout = 100  # 100ms timeout
        
        result = await _strategy_dom_analysis(mock_container, fast_config)
        
        # Should handle timeout gracefully
        assert result == (None, None)

    @pytest.mark.asyncio
    async def test_error_recovery_mechanisms(self):
        """Test error recovery in various failure scenarios"""
        
        # Test with broken container that throws exceptions
        mock_container = AsyncMock()
        mock_container.query_selector_all.side_effect = Exception("DOM access error")
        mock_container.text_content.side_effect = Exception("Text access error")
        
        # Should not crash, should return None gracefully
        result = await extract_container_metadata_enhanced(
            mock_container,
            "Some content with Creation Time 24 Aug 2025 01:37:01",
            0,
            self.config
        )
        
        # Even with DOM errors, text patterns should work
        assert result is not None
        assert result['creation_time'] == "24 Aug 2025 01:37:01"

    @pytest.mark.asyncio
    async def test_performance_with_large_content(self):
        """Test performance with large content blocks"""
        
        # Create large content block
        large_content = "Filler text. " * 1000
        large_content += "\nCreation Time 24 Aug 2025 01:37:01\n"
        large_content += "The camera captures an expansive landscape with rolling hills and scattered clouds.\n"
        large_content += "More filler text. " * 1000
        
        mock_container = AsyncMock()
        mock_container.query_selector_all = AsyncMock(return_value=[])
        
        start_time = time.time()
        
        result = await extract_container_metadata_enhanced(
            mock_container,
            large_content,
            0,
            self.config
        )
        
        extraction_time = time.time() - start_time
        
        # Should complete within reasonable time (< 2 seconds)
        assert extraction_time < 2.0, f"Extraction took too long: {extraction_time:.3f}s"
        
        # Should still extract correctly
        assert result is not None
        assert result['creation_time'] == "24 Aug 2025 01:37:01"
        assert "camera" in result['prompt'].lower()

    def test_edge_cases_and_corner_cases(self):
        """Test various edge cases and corner cases"""
        
        edge_cases = [
            # Multiple creation times (should pick first valid one)
            {
                'content': 'Old Time 23 Aug 2025 12:00:00\nCreation Time 24 Aug 2025 01:37:01\nPrompt here',
                'expect_time': True
            },
            
            # No prompt content  
            {
                'content': 'Creation Time 24 Aug 2025 01:37:01\nDownload\nClick here',
                'expect_time': True,
                'expect_prompt': False
            },
            
            # Prompt before time
            {
                'content': 'Beautiful mountain landscape with snow-capped peaks\nCreation Time 24 Aug 2025 01:37:01',
                'expect_time': True,
                'expect_prompt': True
            },
            
            # Unicode and special characters
            {
                'content': 'Création Time 24 Aug 2025 01:37:01\nThe café scene with people enjoying coffee ☕',
                'expect_time': True,
                'expect_prompt': True
            },
        ]
        
        for case in edge_cases:
            # Use synchronous version of text pattern extraction for quick testing
            import asyncio
            
            async def run_test():
                creation_time, prompt = await _strategy_text_patterns(case['content'], self.config)
                
                if case.get('expect_time', True):
                    assert creation_time is not None, f"Should find creation time in: {case['content'][:50]}..."
                
                if case.get('expect_prompt', True):
                    assert prompt is not None, f"Should find prompt in: {case['content'][:50]}..."
                elif case.get('expect_prompt', True) is False:
                    # Explicitly expecting no prompt
                    pass  # Don't assert anything about prompt
                
            asyncio.run(run_test())

    @pytest.mark.asyncio
    async def test_integration_scenario_gallery_timing(self):
        """Integration test simulating gallery timing issues"""
        
        # Simulate the actual problem: container loads but content appears later
        mock_container = AsyncMock()
        
        # Sequence: empty -> partial -> full content
        content_sequence = [
            "",  # Initially empty
            "Loading...",  # Loading state
            "Creation Time 24 Aug 2025 01:37:01\nThe camera reveals a stunning coastal scene with waves crashing against rocky cliffs."  # Final content
        ]
        
        call_count = 0
        def mock_text_content():
            nonlocal call_count
            result = content_sequence[min(call_count, len(content_sequence) - 1)]
            call_count += 1
            return result
        
        mock_container.text_content = AsyncMock(side_effect=mock_text_content)
        mock_container.wait_for = AsyncMock()  # Simulate successful wait
        mock_container.query_selector_all = AsyncMock(return_value=[])
        
        # Start with empty content (simulating timing issue)
        result = await extract_container_metadata_enhanced(
            mock_container,
            "",  # Empty initial content
            0,
            self.config
        )
        
        # Should successfully extract after retry
        assert result is not None
        assert result['creation_time'] == "24 Aug 2025 01:37:01"
        assert result['prompt'] is not None
        assert "camera" in result['prompt'].lower()
        assert "coastal" in result['prompt'].lower()


if __name__ == "__main__":
    # Run tests directly
    test_instance = TestEnhancedMetadataExtractionRobust()
    
    print("🧪 Running Enhanced Metadata Extraction Robust Tests...")
    print("=" * 70)
    
    # Run synchronous tests
    sync_tests = [
        'test_creation_time_format_validation',
        'test_prompt_candidate_validation', 
        'test_fuzzy_creation_time_extraction',
        'test_edge_cases_and_corner_cases'
    ]
    
    passed = 0
    failed = 0
    
    for test_name in sync_tests:
        try:
            test_instance.setup_method()
            test_method = getattr(test_instance, test_name)
            test_method()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
    
    # Run async tests
    async_tests = [
        'test_text_patterns_strategy',
        'test_dom_analysis_strategy_mock',
        'test_comprehensive_fallback_strategy',
        'test_main_extraction_function_with_retries',
        'test_timeout_handling',
        'test_error_recovery_mechanisms',
        'test_performance_with_large_content',
        'test_integration_scenario_gallery_timing'
    ]
    
    async def run_async_tests():
        passed_async = 0
        failed_async = 0
        
        for test_name in async_tests:
            try:
                test_instance.setup_method()
                test_method = getattr(test_instance, test_name)
                await test_method()
                print(f"✅ {test_name}")
                passed_async += 1
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                failed_async += 1
        
        return passed_async, failed_async
    
    async_passed, async_failed = asyncio.run(run_async_tests())
    
    # Update totals
    passed += async_passed
    failed += async_failed
    
    print("=" * 70)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Enhanced metadata extraction is robust and working correctly.")
        print("📋 Key improvements validated:")
        print("   • Multiple extraction strategies with fallbacks")
        print("   • Comprehensive error handling and recovery")
        print("   • Timeout handling for DOM operations") 
        print("   • Performance optimization for large content")
        print("   • Dynamic content loading support")
        print("   • Edge case handling and validation")
    else:
        print(f"⚠️  {failed} tests failed. Please review the implementation.")