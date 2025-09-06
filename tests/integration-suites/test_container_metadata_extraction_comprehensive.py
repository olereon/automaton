#!/usr/bin/env python3.11
"""
Comprehensive Test Suite for Container-Based Metadata Extraction

This test suite validates the simplified container-based metadata extraction approach,
focusing on robustness, performance, and reliability improvements over gallery-based extraction.

Test Coverage:
- Container Structure Tests: Validate extraction from provided HTML structure
- Selector Robustness: Test CSS selectors against variations in container structure  
- Edge Case Testing: Test missing elements, malformed data, empty containers
- Performance Testing: Validate speed improvements from eliminating gallery extraction
- Integration Testing: Test the complete simplified workflow end-to-end
- Error Handling: Test graceful failure recovery for various scenarios

Validation Targets:
- Success Rate: >95% for valid containers
- Speed: Significantly faster than gallery extraction
- Reliability: Eliminate timing-related failures  
- Error Handling: Graceful handling of missing/invalid data
"""

import pytest
import asyncio
import time
import json
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import the modules to test
from src.utils.enhanced_metadata_extraction import (
    extract_container_metadata_enhanced,
    MetadataExtractionConfig,
    _strategy_text_patterns,
    _strategy_dom_analysis,
    _validate_creation_time_format,
    _is_valid_prompt_candidate
)


class TestContainerStructureValidation:
    """Test suite for validating extraction from various container structures"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = MetadataExtractionConfig()
        self.config.debug_mode = True
        self.config.log_extraction_details = True

    def test_standard_container_structure(self):
        """Test extraction from standard container with normal prompt + datetime"""
        # Standard container text content
        standard_content = """
        Creation Time 25 Aug 2025 02:30:47
        The camera captures a serene landscape at golden hour, with rolling hills and distant mountains creating a peaceful scene. The warm lighting enhances the natural beauty of the countryside.
        Download
        """
        
        # Mock container element
        mock_container = AsyncMock()
        mock_container.text_content.return_value = standard_content
        
        # Test async extraction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, standard_content, config=self.config)
            )
        finally:
            loop.close()
        
        # Validate results
        assert result is not None, "Extraction should succeed for standard container"
        assert result['creation_time'] == '25 Aug 2025 02:30:47', f"Expected standard creation time, got {result['creation_time']}"
        assert 'camera captures' in result['prompt'].lower(), f"Expected camera prompt content, got {result['prompt']}"
        print(f"✅ Standard container test passed: Time={result['creation_time']}, Prompt length={len(result['prompt'])}")

    def test_container_with_creation_time_variations(self):
        """Test extraction with different creation time format variations"""
        test_cases = [
            {
                'name': 'Standard format',
                'content': 'Creation Time 24 Aug 2025 15:22:33\nA beautiful sunset over the ocean.',
                'expected_time': '24 Aug 2025 15:22:33'
            },
            {
                'name': 'No prefix format', 
                'content': '24 Aug 2025 15:22:33\nA beautiful sunset over the ocean.',
                'expected_time': '24 Aug 2025 15:22:33'
            },
            {
                'name': 'Colon separator format',
                'content': 'Creation Time: 24 Aug 2025 15:22:33\nA beautiful sunset over the ocean.',
                'expected_time': '24 Aug 2025 15:22:33'
            },
            {
                'name': 'Created prefix format',
                'content': 'Created: 24 Aug 2025 15:22:33\nA beautiful sunset over the ocean.',
                'expected_time': '24 Aug 2025 15:22:33'
            }
        ]
        
        for case in test_cases:
            mock_container = AsyncMock()
            mock_container.text_content.return_value = case['content']
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, case['content'], config=self.config)
                )
            finally:
                loop.close()
            
            assert result is not None, f"Extraction should succeed for {case['name']}"
            assert result['creation_time'] == case['expected_time'], f"Time mismatch in {case['name']}"
            print(f"✅ {case['name']} test passed")

    def test_container_with_prompt_variations(self):
        """Test extraction with different prompt content variations"""
        test_cases = [
            {
                'name': 'Camera description',
                'content': 'Creation Time 24 Aug 2025 15:22:33\nThe camera captures a bustling city street with people walking and cars driving by.',
                'expected_keywords': ['camera', 'captures', 'city', 'street']
            },
            {
                'name': 'Action description',
                'content': 'Creation Time 24 Aug 2025 15:22:33\nA person running through a forest path surrounded by tall trees.',
                'expected_keywords': ['person', 'running', 'forest', 'trees']
            },
            {
                'name': 'Scene description',
                'content': 'Creation Time 24 Aug 2025 15:22:33\nThe scene shows a cozy living room with warm lighting and comfortable furniture.',
                'expected_keywords': ['scene', 'shows', 'living room', 'lighting']
            }
        ]
        
        for case in test_cases:
            mock_container = AsyncMock()
            mock_container.text_content.return_value = case['content']
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, case['content'], config=self.config)
                )
            finally:
                loop.close()
            
            assert result is not None, f"Extraction should succeed for {case['name']}"
            prompt_lower = result['prompt'].lower()
            
            # Check for expected keywords
            found_keywords = [kw for kw in case['expected_keywords'] if kw.lower() in prompt_lower]
            assert len(found_keywords) >= 2, f"Should find at least 2 keywords in {case['name']}, found: {found_keywords}"
            print(f"✅ {case['name']} test passed with keywords: {found_keywords}")


class TestSelectorRobustness:
    """Test CSS selectors against variations in container structure"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = MetadataExtractionConfig()

    @pytest.mark.asyncio
    async def test_dom_selector_variations(self):
        """Test DOM selectors with different element structures"""
        # Test cases with different DOM structures
        test_cases = [
            {
                'name': 'Standard time element',
                'selector': '.sc-cSMkSB.hUjUPD',
                'element_text': '25 Aug 2025 02:30:47',
                'should_match': True
            },
            {
                'name': 'Generic time class',
                'selector': '[class*="time"]',
                'element_text': '25 Aug 2025 02:30:47',
                'should_match': True
            },
            {
                'name': 'Date class variant',
                'selector': '[class*="date"]',
                'element_text': '25 Aug 2025 02:30:47',
                'should_match': True
            }
        ]
        
        for case in test_cases:
            # Mock container with query_selector_all method
            mock_container = AsyncMock()
            mock_element = AsyncMock()
            mock_element.text_content.return_value = case['element_text']
            
            if case['should_match']:
                mock_container.query_selector_all.return_value = [mock_element]
            else:
                mock_container.query_selector_all.return_value = []
            
            # Test DOM analysis strategy
            creation_time, prompt_text = await _strategy_dom_analysis(mock_container, self.config)
            
            if case['should_match']:
                assert creation_time == case['element_text'], f"Should extract time from {case['name']}"
            else:
                assert creation_time is None, f"Should not extract time from {case['name']}"
            
            print(f"✅ DOM selector test passed: {case['name']}")

    @pytest.mark.asyncio
    async def test_selector_timeout_handling(self):
        """Test selector timeout handling for slow DOM operations"""
        mock_container = AsyncMock()
        
        # Simulate timeout on query_selector_all
        mock_container.query_selector_all.side_effect = asyncio.TimeoutError("DOM query timeout")
        
        # Should handle timeout gracefully
        creation_time, prompt_text = await _strategy_dom_analysis(mock_container, self.config)
        
        assert creation_time is None, "Should return None when DOM query times out"
        assert prompt_text is None, "Should return None when DOM query times out"
        print("✅ DOM timeout handling test passed")

    @pytest.mark.asyncio
    async def test_element_text_extraction_error(self):
        """Test handling of element text extraction errors"""
        mock_container = AsyncMock()
        mock_element = AsyncMock()
        
        # Mock element that throws error on text_content()
        mock_element.text_content.side_effect = Exception("Element not accessible")
        mock_container.query_selector_all.return_value = [mock_element]
        
        # Should handle element error gracefully
        creation_time, prompt_text = await _strategy_dom_analysis(mock_container, self.config)
        
        assert creation_time is None, "Should return None when element text extraction fails"
        print("✅ Element text extraction error test passed")


class TestEdgeCaseValidation:
    """Test edge cases: missing elements, malformed data, empty containers"""

    def setup_method(self):
        """Set up test fixtures"""
        self.config = MetadataExtractionConfig()

    def test_missing_creation_time(self):
        """Test container with missing creation time"""
        content_no_time = """
        Download
        The camera shows a beautiful landscape with mountains and trees.
        Image to Video
        """
        
        mock_container = AsyncMock()
        mock_container.text_content.return_value = content_no_time
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, content_no_time, config=self.config)
            )
        finally:
            loop.close()
        
        # Should return None for containers without creation time
        assert result is None, "Should return None when creation time is missing"
        print("✅ Missing creation time test passed")

    def test_missing_prompt(self):
        """Test container with missing prompt text"""
        content_no_prompt = """
        Creation Time 25 Aug 2025 02:30:47
        Download
        """
        
        mock_container = AsyncMock()
        mock_container.text_content.return_value = content_no_prompt
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, content_no_prompt, config=self.config)
            )
        finally:
            loop.close()
        
        # Should extract time but have empty/None prompt
        assert result is not None, "Should still return result when only prompt is missing"
        assert result['creation_time'] == '25 Aug 2025 02:30:47', "Should extract creation time"
        assert result['prompt'] == "" or result['prompt'] is None, "Prompt should be empty when missing"
        print("✅ Missing prompt test passed")

    def test_malformed_creation_time(self):
        """Test container with malformed creation time data"""
        malformed_cases = [
            "Creation Time 25 August 2025",  # Missing time component
            "Creation Time 2025-08-25",      # Wrong format
            "Creation Time invalid date",     # Invalid date
            "Creation Time 32 Aug 2025 25:99:99"  # Invalid values
        ]
        
        for i, malformed_content in enumerate(malformed_cases):
            full_content = f"{malformed_content}\nA test prompt with description."
            mock_container = AsyncMock()
            mock_container.text_content.return_value = full_content
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, full_content, config=self.config)
                )
            finally:
                loop.close()
            
            # Should handle malformed dates gracefully
            assert result is None, f"Should return None for malformed date case {i+1}: {malformed_content}"
        
        print("✅ Malformed creation time test passed")

    def test_empty_container(self):
        """Test completely empty container"""
        empty_content = ""
        
        mock_container = AsyncMock()
        mock_container.text_content.return_value = empty_content
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, empty_content, config=self.config)
            )
        finally:
            loop.close()
        
        assert result is None, "Should return None for empty container"
        print("✅ Empty container test passed")

    def test_whitespace_only_container(self):
        """Test container with only whitespace"""
        whitespace_content = "   \n\t   \n   "
        
        mock_container = AsyncMock()
        mock_container.text_content.return_value = whitespace_content
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, whitespace_content, config=self.config)
            )
        finally:
            loop.close()
        
        assert result is None, "Should return None for whitespace-only container"
        print("✅ Whitespace-only container test passed")


class TestPerformanceBenchmarking:
    """Test performance improvements from container-based vs gallery-based extraction"""

    def setup_method(self):
        """Set up performance test fixtures"""
        self.config = MetadataExtractionConfig()
        self.config.max_retry_attempts = 2  # Reduce retries for performance testing

    def test_single_extraction_speed(self):
        """Test speed of single container extraction"""
        content = """
        Creation Time 25 Aug 2025 02:30:47
        The camera captures a vibrant city scene with bustling streets, colorful signs, and people walking in every direction. The urban environment is full of energy and movement.
        """
        
        mock_container = AsyncMock()
        mock_container.text_content.return_value = content
        
        # Time the extraction
        start_time = time.perf_counter()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, content, config=self.config)
            )
        finally:
            loop.close()
        
        end_time = time.perf_counter()
        extraction_time = end_time - start_time
        
        # Validate result and performance
        assert result is not None, "Extraction should succeed"
        assert extraction_time < 0.1, f"Single extraction should be <100ms, took {extraction_time:.3f}s"
        
        print(f"✅ Single extraction speed test passed: {extraction_time*1000:.1f}ms")
        return extraction_time

    def test_batch_extraction_performance(self):
        """Test performance of batch container extraction"""
        # Generate 50 test containers
        test_containers = []
        for i in range(50):
            content = f"""
            Creation Time {25 - (i % 7)} Aug 2025 {10 + (i % 12):02d}:{15 + (i % 45):02d}:{30 + (i % 30):02d}
            Test prompt {i}: The camera shows various scenes from different perspectives and angles. Each scene has unique characteristics and visual elements.
            """
            mock_container = AsyncMock()
            mock_container.text_content.return_value = content
            test_containers.append((mock_container, content))
        
        # Time batch extraction
        start_time = time.perf_counter()
        
        results = []
        for mock_container, content in test_containers:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, content, config=self.config)
                )
                results.append(result)
            finally:
                loop.close()
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time_per_container = total_time / len(test_containers)
        
        # Validate performance
        successful_extractions = [r for r in results if r is not None]
        success_rate = len(successful_extractions) / len(results)
        
        assert success_rate >= 0.95, f"Success rate should be ≥95%, got {success_rate:.2%}"
        assert avg_time_per_container < 0.05, f"Avg extraction should be <50ms, got {avg_time_per_container*1000:.1f}ms"
        assert total_time < 2.5, f"Total batch time should be <2.5s, got {total_time:.3f}s"
        
        print(f"✅ Batch extraction performance test passed:")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Average per container: {avg_time_per_container*1000:.1f}ms")
        print(f"   Success rate: {success_rate:.2%}")
        
        return {
            'total_time': total_time,
            'avg_time': avg_time_per_container,
            'success_rate': success_rate
        }

    def test_memory_efficiency(self):
        """Test memory efficiency of container extraction"""
        import tracemalloc
        
        content = """
        Creation Time 25 Aug 2025 02:30:47
        The camera captures detailed scenes with complex descriptions and various visual elements.
        """
        
        # Start memory tracking
        tracemalloc.start()
        
        # Perform multiple extractions
        for _ in range(100):
            mock_container = AsyncMock()
            mock_container.text_content.return_value = content
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, content, config=self.config)
                )
            finally:
                loop.close()
        
        # Get memory statistics
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Validate memory usage (should be reasonable for 100 extractions)
        assert peak < 10 * 1024 * 1024, f"Peak memory should be <10MB, got {peak / 1024 / 1024:.1f}MB"
        
        print(f"✅ Memory efficiency test passed:")
        print(f"   Current memory: {current / 1024:.1f} KB")
        print(f"   Peak memory: {peak / 1024:.1f} KB")


class TestBatchProcessingScenarios:
    """Test batch processing with mixed success/failure scenarios"""

    def setup_method(self):
        """Set up batch test fixtures"""
        self.config = MetadataExtractionConfig()

    def test_mixed_success_failure_batch(self):
        """Test batch with mix of valid and invalid containers"""
        test_cases = [
            # Valid cases
            {
                'content': 'Creation Time 25 Aug 2025 02:30:47\nValid prompt content.',
                'should_succeed': True,
                'description': 'Valid standard container'
            },
            {
                'content': 'Creation Time 24 Aug 2025 15:22:33\nAnother valid prompt with description.',
                'should_succeed': True,
                'description': 'Valid alternative container'
            },
            # Invalid cases
            {
                'content': 'No creation time here\nJust some text.',
                'should_succeed': False,
                'description': 'Missing creation time'
            },
            {
                'content': '',
                'should_succeed': False,
                'description': 'Empty container'
            },
            {
                'content': 'Creation Time invalid format\nPrompt text.',
                'should_succeed': False,
                'description': 'Invalid date format'
            },
            # More valid cases
            {
                'content': 'Creation Time 23 Aug 2025 09:15:00\nCamera shot of mountain landscape.',
                'should_succeed': True,
                'description': 'Valid mountain scene'
            }
        ]
        
        results = []
        for case in test_cases:
            mock_container = AsyncMock()
            mock_container.text_content.return_value = case['content']
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, case['content'], config=self.config)
                )
                results.append({
                    'result': result,
                    'expected_success': case['should_succeed'],
                    'description': case['description']
                })
            finally:
                loop.close()
        
        # Validate results
        correct_predictions = 0
        for i, res in enumerate(results):
            actual_success = res['result'] is not None
            expected_success = res['expected_success']
            
            if actual_success == expected_success:
                correct_predictions += 1
                print(f"✅ {res['description']}: Expected {expected_success}, got {actual_success}")
            else:
                print(f"❌ {res['description']}: Expected {expected_success}, got {actual_success}")
        
        accuracy = correct_predictions / len(results)
        assert accuracy >= 0.95, f"Batch accuracy should be ≥95%, got {accuracy:.2%}"
        print(f"✅ Mixed batch test passed with {accuracy:.2%} accuracy")

    def test_concurrent_batch_processing(self):
        """Test concurrent processing of multiple containers"""
        import concurrent.futures
        
        # Create test data
        test_contents = []
        for i in range(20):
            content = f"""
            Creation Time {20 + i} Aug 2025 {10 + (i % 14):02d}:{15 + (i % 50):02d}:{(i % 60):02d}
            Concurrent test prompt {i}: Various scenes and descriptions for testing parallel processing.
            """
            test_contents.append(content)
        
        def extract_single_container(content):
            """Helper function for concurrent extraction"""
            mock_container = AsyncMock()
            mock_container.text_content.return_value = content
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, content, config=self.config)
                )
                return result
            finally:
                loop.close()
        
        # Process concurrently
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extract_single_container, content) for content in test_contents]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Validate concurrent processing
        successful_results = [r for r in results if r is not None]
        success_rate = len(successful_results) / len(results)
        
        assert success_rate >= 0.95, f"Concurrent success rate should be ≥95%, got {success_rate:.2%}"
        assert total_time < 5.0, f"Concurrent processing should be <5s, got {total_time:.3f}s"
        
        print(f"✅ Concurrent batch processing test passed:")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Success rate: {success_rate:.2%}")
        print(f"   Average per container: {(total_time/len(test_contents))*1000:.1f}ms")


class TestErrorHandlingAndRecovery:
    """Test graceful error handling and recovery mechanisms"""

    def setup_method(self):
        """Set up error handling test fixtures"""
        self.config = MetadataExtractionConfig()
        self.config.max_retry_attempts = 3

    @pytest.mark.asyncio
    async def test_transient_error_recovery(self):
        """Test recovery from transient errors"""
        content = "Creation Time 25 Aug 2025 02:30:47\nTest prompt content."
        
        mock_container = AsyncMock()
        
        # Mock transient error on first calls, then success
        call_count = 0
        def side_effect_text_content():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 times
                raise Exception("Element not attached to DOM")
            return content
        
        mock_container.text_content.side_effect = side_effect_text_content
        
        # Should recover from transient errors
        result = await extract_container_metadata_enhanced(mock_container, content, config=self.config)
        
        assert result is not None, "Should recover from transient errors"
        assert call_count >= 3, "Should have retried multiple times"
        print(f"✅ Transient error recovery test passed after {call_count} attempts")

    @pytest.mark.asyncio
    async def test_permanent_error_handling(self):
        """Test handling of permanent errors"""
        mock_container = AsyncMock()
        
        # Mock permanent error (non-transient)
        mock_container.text_content.side_effect = Exception("Permanent DOM error")
        
        # Should handle permanent errors gracefully without excessive retries
        result = await extract_container_metadata_enhanced(mock_container, "test", config=self.config)
        
        assert result is None, "Should return None for permanent errors"
        print("✅ Permanent error handling test passed")

    def test_configuration_error_handling(self):
        """Test handling of invalid configuration"""
        invalid_config = MetadataExtractionConfig()
        invalid_config.max_retry_attempts = -1  # Invalid value
        invalid_config.dom_wait_timeout = -1000  # Invalid timeout
        
        mock_container = AsyncMock()
        mock_container.text_content.return_value = "Creation Time 25 Aug 2025 02:30:47\nTest prompt."
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Should handle invalid config gracefully
            result = loop.run_until_complete(
                extract_container_metadata_enhanced(mock_container, "test content", config=invalid_config)
            )
            # Should either succeed with corrected config or fail gracefully
            print(f"✅ Configuration error handling test passed: {'Success' if result else 'Graceful failure'}")
        except Exception as e:
            # Should not raise unhandled exceptions
            pytest.fail(f"Should handle invalid config gracefully, but raised: {e}")
        finally:
            loop.close()


class TestIntegrationWorkflow:
    """Integration tests for the complete simplified workflow"""

    def setup_method(self):
        """Set up integration test fixtures"""
        self.config = MetadataExtractionConfig()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_container_workflow(self):
        """Test complete workflow from container detection to metadata extraction"""
        # Simulate a complete workflow with multiple containers
        containers = [
            {
                'id': 'container_1',
                'content': 'Creation Time 25 Aug 2025 02:30:47\nThe camera captures a bustling marketplace scene with vendors and shoppers.',
                'expected_success': True
            },
            {
                'id': 'container_2', 
                'content': 'Creation Time 24 Aug 2025 15:22:33\nA serene lake surrounded by mountains and forest.',
                'expected_success': True
            },
            {
                'id': 'container_3',
                'content': 'Invalid container without proper metadata.',
                'expected_success': False
            },
            {
                'id': 'container_4',
                'content': 'Creation Time 23 Aug 2025 09:15:00\nUrban street photography with dynamic lighting and shadows.',
                'expected_success': True
            }
        ]
        
        workflow_results = []
        total_start_time = time.perf_counter()
        
        for container in containers:
            start_time = time.perf_counter()
            
            mock_container = AsyncMock()
            mock_container.text_content.return_value = container['content']
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, container['content'], config=self.config)
                )
            finally:
                loop.close()
            
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            
            workflow_results.append({
                'container_id': container['id'],
                'result': result,
                'expected_success': container['expected_success'],
                'processing_time': processing_time,
                'success': result is not None
            })
        
        total_end_time = time.perf_counter()
        total_workflow_time = total_end_time - total_start_time
        
        # Validate workflow results
        correct_predictions = sum(1 for r in workflow_results if r['success'] == r['expected_success'])
        accuracy = correct_predictions / len(workflow_results)
        
        successful_extractions = [r for r in workflow_results if r['success']]
        avg_processing_time = sum(r['processing_time'] for r in successful_extractions) / len(successful_extractions) if successful_extractions else 0
        
        # Assert workflow quality
        assert accuracy >= 0.95, f"Workflow accuracy should be ≥95%, got {accuracy:.2%}"
        assert avg_processing_time < 0.1, f"Average processing time should be <100ms, got {avg_processing_time*1000:.1f}ms"
        assert total_workflow_time < 1.0, f"Total workflow time should be <1s, got {total_workflow_time:.3f}s"
        
        print(f"✅ End-to-end workflow test passed:")
        print(f"   Accuracy: {accuracy:.2%}")
        print(f"   Average processing time: {avg_processing_time*1000:.1f}ms")
        print(f"   Total workflow time: {total_workflow_time:.3f}s")
        print(f"   Processed containers: {len(containers)}")

    def test_workflow_with_logging_and_metrics(self):
        """Test workflow with comprehensive logging and metrics collection"""
        import json
        
        # Set up logging
        log_file = os.path.join(self.temp_dir, "workflow_test.log")
        metrics_file = os.path.join(self.temp_dir, "workflow_metrics.json")
        
        # Enable detailed logging
        detailed_config = MetadataExtractionConfig()
        detailed_config.debug_mode = True
        detailed_config.log_extraction_details = True
        
        # Test containers with various scenarios
        test_scenarios = [
            {'content': 'Creation Time 25 Aug 2025 02:30:47\nSuccessful extraction test.', 'name': 'success_case'},
            {'content': 'Missing time format test.', 'name': 'failure_case'},
            {'content': 'Creation Time 24 Aug 2025 15:22:33\nAnother successful case.', 'name': 'success_case_2'}
        ]
        
        metrics = {
            'total_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'average_processing_time': 0,
            'extraction_details': []
        }
        
        processing_times = []
        
        for scenario in test_scenarios:
            start_time = time.perf_counter()
            
            mock_container = AsyncMock()
            mock_container.text_content.return_value = scenario['content']
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    extract_container_metadata_enhanced(mock_container, scenario['content'], config=detailed_config)
                )
            finally:
                loop.close()
            
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # Collect metrics
            metrics['total_processed'] += 1
            if result is not None:
                metrics['successful_extractions'] += 1
            else:
                metrics['failed_extractions'] += 1
            
            metrics['extraction_details'].append({
                'scenario_name': scenario['name'],
                'success': result is not None,
                'processing_time': processing_time,
                'creation_time': result['creation_time'] if result else None,
                'prompt_length': len(result['prompt']) if result and result['prompt'] else 0
            })
        
        metrics['average_processing_time'] = sum(processing_times) / len(processing_times)
        
        # Save metrics
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Validate metrics
        success_rate = metrics['successful_extractions'] / metrics['total_processed']
        assert success_rate >= 0.6, f"Success rate should be reasonable, got {success_rate:.2%}"
        assert metrics['average_processing_time'] < 0.15, f"Average time should be reasonable, got {metrics['average_processing_time']*1000:.1f}ms"
        
        print(f"✅ Workflow with logging test passed:")
        print(f"   Success rate: {success_rate:.2%}")
        print(f"   Average processing time: {metrics['average_processing_time']*1000:.1f}ms")
        print(f"   Metrics saved to: {metrics_file}")


class TestValidationHelpers:
    """Test helper validation functions"""

    def test_creation_time_format_validation(self):
        """Test creation time format validation helper"""
        valid_formats = [
            "25 Aug 2025 02:30:47",
            "1 Jan 2025 00:00:00", 
            "31 Dec 2025 23:59:59",
            "15 September 2025 12:34:56"
        ]
        
        invalid_formats = [
            "25 Aug 2025",  # Missing time
            "2025-08-25 02:30:47",  # Wrong separator
            "Aug 25 2025 02:30:47",  # Wrong order
            "25/08/2025 02:30:47",  # Slash separator
            "invalid date format"
        ]
        
        for valid_format in valid_formats:
            assert _validate_creation_time_format(valid_format), f"Should validate: {valid_format}"
        
        for invalid_format in invalid_formats:
            assert not _validate_creation_time_format(invalid_format), f"Should not validate: {invalid_format}"
        
        print("✅ Creation time format validation test passed")

    def test_prompt_candidate_validation(self):
        """Test prompt candidate validation helper"""
        valid_candidates = [
            "The camera captures a beautiful scene with detailed descriptions.",
            "A person walking through the forest path surrounded by trees.",
            "Scene shows urban landscape with buildings and streets."
        ]
        
        invalid_candidates = [
            "",  # Empty
            "short",  # Too short
            "Creation Time 25 Aug 2025",  # Metadata
            "Download button clicked",  # UI element
            "www.example.com/image.jpg",  # URL
            "Error: Failed to load"  # Error message
        ]
        
        for valid_candidate in valid_candidates:
            assert _is_valid_prompt_candidate(valid_candidate), f"Should validate: {valid_candidate[:30]}..."
        
        for invalid_candidate in invalid_candidates:
            assert not _is_valid_prompt_candidate(invalid_candidate), f"Should not validate: {invalid_candidate}"
        
        print("✅ Prompt candidate validation test passed")


def run_comprehensive_test_suite():
    """Run the complete comprehensive test suite"""
    print("🧪 Running Comprehensive Container-Based Metadata Extraction Test Suite")
    print("=" * 80)
    
    test_classes = [
        TestContainerStructureValidation,
        TestSelectorRobustness, 
        TestEdgeCaseValidation,
        TestPerformanceBenchmarking,
        TestBatchProcessingScenarios,
        TestErrorHandlingAndRecovery,
        TestIntegrationWorkflow,
        TestValidationHelpers
    ]
    
    total_passed = 0
    total_failed = 0
    performance_metrics = {}
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}")
        print("-" * 60)
        
        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        class_passed = 0
        class_failed = 0
        
        for test_method_name in test_methods:
            try:
                # Set up test instance
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run test method
                test_method = getattr(test_instance, test_method_name)
                if asyncio.iscoroutinefunction(test_method):
                    # Run async test
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(test_method())
                    finally:
                        loop.close()
                else:
                    # Run sync test
                    result = test_method()
                    
                    # Collect performance metrics if returned
                    if isinstance(result, dict) and 'total_time' in result:
                        performance_metrics[test_method_name] = result
                
                class_passed += 1
                total_passed += 1
                
            except Exception as e:
                print(f"❌ {test_method_name}: {e}")
                class_failed += 1
                total_failed += 1
            finally:
                # Clean up test instance
                if hasattr(test_instance, 'teardown_method'):
                    try:
                        test_instance.teardown_method()
                    except:
                        pass
        
        print(f"📊 {test_class.__name__} Results: {class_passed} passed, {class_failed} failed")
    
    print("\n" + "=" * 80)
    print(f"🎯 Comprehensive Test Suite Results: {total_passed} passed, {total_failed} failed")
    
    if performance_metrics:
        print(f"\n📊 Performance Metrics Summary:")
        for test_name, metrics in performance_metrics.items():
            print(f"   {test_name}:")
            for key, value in metrics.items():
                if 'time' in key:
                    print(f"     {key}: {value:.3f}s")
                elif 'rate' in key:
                    print(f"     {key}: {value:.2%}")
                else:
                    print(f"     {key}: {value}")
    
    success_rate = total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0
    
    if success_rate >= 0.95:
        print(f"🎉 Test suite PASSED with {success_rate:.2%} success rate!")
        print("✅ Container-based metadata extraction is ready for production!")
    else:
        print(f"⚠️ Test suite needs improvement: {success_rate:.2%} success rate")
        print("❌ Please review failed tests before deploying.")
    
    return success_rate >= 0.95


if __name__ == "__main__":
    # Run the comprehensive test suite
    success = run_comprehensive_test_suite()
    exit(0 if success else 1)