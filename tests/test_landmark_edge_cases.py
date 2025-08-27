#!/usr/bin/env python3
"""
Edge Case Validation Tests for Landmark-Based Extraction

This test suite validates edge cases, error handling, and robustness
of the landmark-based metadata extraction system.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
import sys
import os
from datetime import datetime
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.enhanced_metadata_extractor import EnhancedMetadataExtractor
from utils.landmark_extractor import DOMNavigator, ElementInfo
from utils.extraction_strategies import CreationTimeLandmarkStrategy
from utils.landmark_extractor import ImageToVideoLandmarkStrategy

logger = logging.getLogger(__name__)


class EdgeCaseTestConfig:
    """Configuration for edge case testing"""
    def __init__(self):
        self.image_to_video_text = "Image to video"
        self.creation_time_text = "Creation Time"
        self.prompt_ellipsis_pattern = "</span>..."
        self.download_no_watermark_text = "Download without Watermark"
        self.generation_date_selector = ".date-selector"
        self.prompt_selector = ".prompt-selector"
        self.use_landmark_extraction = True
        self.fallback_to_legacy = True
        self.quality_threshold = 0.6


class ErrorInducingPage:
    """Mock page that simulates various error conditions"""
    
    def __init__(self, error_type="none"):
        self.error_type = error_type
        self.query_count = 0
        
    async def query_selector_all(self, selector):
        self.query_count += 1
        
        if self.error_type == "timeout":
            raise asyncio.TimeoutError("Query timeout")
        elif self.error_type == "dom_exception":
            raise Exception("DOM Exception: Element not found")
        elif self.error_type == "memory_error":
            if self.query_count > 5:
                raise MemoryError("Insufficient memory")
        elif self.error_type == "empty_results":
            return []
        elif self.error_type == "none_results":
            return None
        elif self.error_type == "corrupted_elements":
            # Return elements that will cause errors when accessed
            corrupted_element = Mock()
            corrupted_element.text_content = AsyncMock(side_effect=Exception("Element corrupted"))
            corrupted_element.bounding_box = AsyncMock(side_effect=Exception("Bounding box error"))
            corrupted_element.is_visible = AsyncMock(side_effect=Exception("Visibility error"))
            return [corrupted_element]
        
        return []
    
    async def query_selector(self, selector):
        results = await self.query_selector_all(selector)
        return results[0] if results else None
    
    async def wait_for_selector(self, selector, timeout=30000):
        if self.error_type == "wait_timeout":
            raise asyncio.TimeoutError(f"Timeout waiting for {selector}")
        return await self.query_selector(selector)
    
    async def evaluate(self, script):
        if self.error_type == "js_error":
            raise Exception("JavaScript execution failed")
        return None


class TestMissingLandmarks:
    """Test cases for missing or inaccessible landmarks"""
    
    @pytest.mark.asyncio
    async def test_no_image_to_video_landmarks(self):
        """Test when no 'Image to video' landmarks are found"""
        config = EdgeCaseTestConfig()
        page = ErrorInducingPage("empty_results")
        debug_logger = Mock()
        
        extractor = EnhancedMetadataExtractor(config, debug_logger)
        result = await extractor.extract_metadata_from_page(page)
        
        # Should gracefully handle missing landmarks
        assert result is not None
        assert result.get('extraction_method') in ['legacy_fallback', 'failed_all_methods', 'critical_error']
        print("✓ No landmarks handled gracefully")
    
    @pytest.mark.asyncio
    async def test_no_creation_time_elements(self):
        """Test when Creation Time elements are missing"""
        config = EdgeCaseTestConfig()
        
        # Create page with Image to video but no Creation Time
        page = Mock()
        image_to_video_element = Mock()
        image_to_video_element.text_content = AsyncMock(return_value="Image to video")
        image_to_video_element.bounding_box = AsyncMock(return_value={'x': 0, 'y': 0, 'width': 100, 'height': 20})
        image_to_video_element.is_visible = AsyncMock(return_value=True)
        
        page.query_selector_all = AsyncMock(side_effect=lambda selector: (
            [image_to_video_element] if "Image to video" in selector else []
        ))
        page.query_selector = AsyncMock(return_value=None)
        page.wait_for_selector = AsyncMock(return_value=None)
        
        extractor = EnhancedMetadataExtractor(config, Mock())
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        print("✓ Missing Creation Time handled")
    
    @pytest.mark.asyncio
    async def test_corrupted_landmark_elements(self):
        """Test when landmark elements are corrupted or inaccessible"""
        config = EdgeCaseTestConfig()
        page = ErrorInducingPage("corrupted_elements")
        
        extractor = EnhancedMetadataExtractor(config, Mock())
        result = await extractor.extract_metadata_from_page(page)
        
        # Should handle corrupted elements gracefully
        assert result is not None
        assert result.get('generation_date') is not None  # Should have defaults
        assert result.get('prompt') is not None
        print("✓ Corrupted elements handled gracefully")


class TestMultiplePanelScenarios:
    """Test cases for complex multiple panel scenarios"""
    
    @pytest.mark.asyncio
    async def test_ten_identical_panels(self):
        """Test handling of many identical panels"""
        config = EdgeCaseTestConfig()
        
        # Create page with 10 identical panels
        page = Mock()
        elements = []
        
        for i in range(10):
            element = Mock()
            element.text_content = AsyncMock(return_value="Image to video")
            element.bounding_box = AsyncMock(return_value={
                'x': 100, 'y': 100 + i * 50, 'width': 120, 'height': 24
            })
            element.is_visible = AsyncMock(return_value=True)
            elements.append(element)
        
        page.query_selector_all = AsyncMock(return_value=elements)
        page.query_selector = AsyncMock(return_value=elements[0] if elements else None)
        page.wait_for_selector = AsyncMock(return_value=elements[0] if elements else None)
        
        navigator = DOMNavigator(page)
        landmarks = await navigator.find_elements_by_landmark("Image to video")
        
        assert len(landmarks) == 10
        print(f"✓ Handled {len(landmarks)} identical panels")
    
    @pytest.mark.asyncio
    async def test_mixed_panel_states(self):
        """Test panels in different states (processing, completed, failed)"""
        config = EdgeCaseTestConfig()
        page = Mock()
        
        # Create panels with different metadata quality
        panel_data = [
            {"text": "Image to video", "has_date": True, "has_prompt": True, "status": "completed"},
            {"text": "Image to video", "has_date": False, "has_prompt": True, "status": "processing"},
            {"text": "Image to video", "has_date": True, "has_prompt": False, "status": "failed"},
            {"text": "Processing...", "has_date": False, "has_prompt": False, "status": "processing"}
        ]
        
        elements = []
        for i, data in enumerate(panel_data):
            element = Mock()
            element.text_content = AsyncMock(return_value=data["text"])
            element.panel_data = data
            elements.append(element)
        
        page.query_selector_all = AsyncMock(return_value=elements)
        
        navigator = DOMNavigator(page)
        landmarks = await navigator.find_elements_by_landmark("Image to video")
        
        # Should find 3 proper landmarks (excluding "Processing...")
        valid_landmarks = [l for l in landmarks if l.text_content == "Image to video"]
        assert len(valid_landmarks) >= 3
        print(f"✓ Mixed panel states handled: {len(valid_landmarks)} valid panels")


class TestDataValidationEdgeCases:
    """Test cases for data validation and malformed content"""
    
    @pytest.mark.asyncio
    async def test_invalid_date_formats(self):
        """Test handling of various invalid date formats"""
        config = EdgeCaseTestConfig()
        
        invalid_dates = [
            "Invalid Date",
            "2024-13-45 25:70:90",  # Impossible date/time
            "NOT_A_DATE",
            "",
            None,
            "2024/08/26",  # Different format
            "Aug 26, 2024",  # Natural language
            "1234567890",  # Timestamp
            "∞",  # Special character
            "2024-08-26T14:30:15.123Z"  # ISO format with timezone
        ]
        
        for invalid_date in invalid_dates:
            page = Mock()
            
            # Mock creation time element
            creation_element = Mock()
            creation_element.text_content = AsyncMock(return_value="Creation Time")
            
            # Mock date element with invalid date
            date_element = Mock()
            date_element.text_content = AsyncMock(return_value=str(invalid_date) if invalid_date else "")
            
            # Mock parent container
            parent = Mock()
            parent.query_selector_all = AsyncMock(return_value=[creation_element, date_element])
            creation_element.evaluate_handle = AsyncMock(return_value=parent)
            
            page.query_selector_all = AsyncMock(side_effect=lambda selector: (
                [creation_element] if "Creation Time" in selector else []
            ))
            
            strategy = CreationTimeLandmarkStrategy(DOMNavigator(page), config)
            from utils.extraction_strategies import ExtractionContext
            
            context = ExtractionContext(
                page=page, thumbnail_index=0, landmark_elements=[], 
                content_area=None, metadata_panels=[]
            )
            
            result = await strategy.extract(context, "generation_date")
            
            # Should handle gracefully without crashing
            assert result is not None
            print(f"✓ Invalid date handled: '{invalid_date}' -> {result.extracted_value}")
    
    @pytest.mark.asyncio
    async def test_extremely_long_prompts(self):
        """Test handling of extremely long or malformed prompts"""
        config = EdgeCaseTestConfig()
        
        # Test various problematic prompts
        problematic_prompts = [
            "A" * 10000,  # Extremely long
            "",  # Empty
            None,  # Null
            "🚀🌟💫" * 1000,  # Many Unicode characters
            "Prompt with\nnewlines\rand\ttabs",  # Special whitespace
            "<script>alert('xss')</script>",  # HTML injection
            "Prompt with \"quotes\" and 'apostrophes'",  # Quotes
            "Multiple...ellipses...everywhere...",  # Multiple ellipses
        ]
        
        for prompt in problematic_prompts:
            page = Mock()
            
            # Mock prompt element
            prompt_element = Mock()
            prompt_element.text_content = AsyncMock(return_value=str(prompt) if prompt else "")
            prompt_element.evaluate = AsyncMock(return_value=f"{prompt}</span>..." if prompt else "")
            
            page.query_selector_all = AsyncMock(side_effect=lambda selector: (
                [prompt_element] if "aria-describedby" in selector else []
            ))
            
            extractor = EnhancedMetadataExtractor(config, Mock())
            result = await extractor.extract_metadata_from_page(page)
            
            assert result is not None
            extracted_prompt = result.get('prompt', 'Unknown Prompt')
            
            # Verify reasonable handling
            if extracted_prompt != 'Unknown Prompt':
                assert len(extracted_prompt) <= 5000  # Should be truncated if too long
            
            print(f"✓ Problematic prompt handled: {len(str(prompt)) if prompt else 0} chars -> {len(extracted_prompt)} chars")


class TestNetworkAndTimingIssues:
    """Test cases for network timeouts and timing issues"""
    
    @pytest.mark.asyncio
    async def test_query_timeout_handling(self):
        """Test handling of DOM query timeouts"""
        config = EdgeCaseTestConfig()
        page = ErrorInducingPage("timeout")
        
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        # Should handle timeout gracefully
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        assert result.get('extraction_method') in ['legacy_fallback', 'failed_all_methods', 'critical_error']
        print("✓ Query timeout handled gracefully")
    
    @pytest.mark.asyncio
    async def test_wait_for_selector_timeout(self):
        """Test handling of wait_for_selector timeouts"""
        config = EdgeCaseTestConfig()
        page = ErrorInducingPage("wait_timeout")
        
        extractor = EnhancedMetadataExtractor(config, Mock())
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        print("✓ Wait timeout handled gracefully")
    
    @pytest.mark.asyncio
    async def test_javascript_execution_errors(self):
        """Test handling of JavaScript execution errors"""
        config = EdgeCaseTestConfig()
        page = ErrorInducingPage("js_error")
        
        extractor = EnhancedMetadataExtractor(config, Mock())
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        print("✓ JavaScript errors handled gracefully")
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test handling under memory pressure"""
        config = EdgeCaseTestConfig()
        page = ErrorInducingPage("memory_error")
        
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        # Should handle memory errors gracefully
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        print("✓ Memory pressure handled gracefully")


class TestConcurrencyAndRaceConditions:
    """Test cases for concurrent access and race conditions"""
    
    @pytest.mark.asyncio
    async def test_concurrent_extraction_requests(self):
        """Test multiple concurrent extraction requests"""
        config = EdgeCaseTestConfig()
        
        # Create a page that simulates slow responses
        class SlowPage:
            def __init__(self):
                self.call_count = 0
            
            async def query_selector_all(self, selector):
                self.call_count += 1
                await asyncio.sleep(0.1)  # Simulate slow DOM query
                return []
            
            async def query_selector(self, selector):
                return None
            
            async def wait_for_selector(self, selector, timeout=30000):
                return None
        
        page = SlowPage()
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        # Launch multiple concurrent extractions
        tasks = []
        for i in range(5):
            task = asyncio.create_task(extractor.extract_metadata_from_page(page))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete without errors
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Task {i} failed with: {result}"
            assert result is not None
        
        print(f"✓ {len(results)} concurrent extractions completed successfully")
    
    @pytest.mark.asyncio
    async def test_extraction_state_isolation(self):
        """Test that multiple extractor instances don't interfere"""
        config = EdgeCaseTestConfig()
        page = Mock()
        page.query_selector_all = AsyncMock(return_value=[])
        page.query_selector = AsyncMock(return_value=None)
        page.wait_for_selector = AsyncMock(return_value=None)
        
        # Create multiple extractor instances
        extractors = [EnhancedMetadataExtractor(config, Mock()) for _ in range(3)]
        
        # Run extractions and modify stats independently
        for i, extractor in enumerate(extractors):
            await extractor.extract_metadata_from_page(page)
            extractor.extraction_stats['landmark_attempts'] = i + 10  # Modify stats
        
        # Verify stats are isolated
        for i, extractor in enumerate(extractors):
            stats = extractor.get_extraction_stats()
            assert stats['landmark_attempts'] == i + 10
        
        print("✓ Extractor state isolation verified")


class TestResourceExhaustionScenarios:
    """Test cases for resource exhaustion and cleanup"""
    
    @pytest.mark.asyncio
    async def test_large_dom_handling(self):
        """Test handling of very large DOM structures"""
        config = EdgeCaseTestConfig()
        
        # Simulate page with thousands of elements
        class LargeDOMPage:
            def __init__(self, element_count=1000):
                self.element_count = element_count
                self.elements = []
                
                # Create many mock elements
                for i in range(element_count):
                    element = Mock()
                    element.text_content = AsyncMock(return_value=f"Element {i}")
                    element.bounding_box = AsyncMock(return_value={'x': i, 'y': i, 'width': 100, 'height': 20})
                    element.is_visible = AsyncMock(return_value=i % 10 == 0)  # Only some visible
                    self.elements.append(element)
            
            async def query_selector_all(self, selector):
                # Return different subsets based on selector
                if "Image to video" in selector:
                    return self.elements[:5]  # First 5 are landmarks
                return self.elements[:100]  # Limit results to avoid memory issues
            
            async def query_selector(self, selector):
                results = await self.query_selector_all(selector)
                return results[0] if results else None
            
            async def wait_for_selector(self, selector, timeout=30000):
                return await self.query_selector(selector)
        
        page = LargeDOMPage(1000)
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        print(f"✓ Large DOM ({page.element_count} elements) handled successfully")
    
    @pytest.mark.asyncio
    async def test_extraction_cleanup_on_error(self):
        """Test that resources are cleaned up properly on errors"""
        config = EdgeCaseTestConfig()
        
        class ErrorAfterPartialWorkPage:
            def __init__(self):
                self.query_count = 0
            
            async def query_selector_all(self, selector):
                self.query_count += 1
                if self.query_count > 3:
                    raise Exception("Simulated error after partial work")
                return []
            
            async def query_selector(self, selector):
                return None
            
            async def wait_for_selector(self, selector, timeout=30000):
                return None
        
        page = ErrorAfterPartialWorkPage()
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        # Should handle error gracefully and still return result
        result = await extractor.extract_metadata_from_page(page)
        
        assert result is not None
        assert result.get('extraction_method') == 'critical_error'
        print("✓ Error cleanup handled properly")


# Performance and stress tests
class TestPerformanceEdgeCases:
    """Test cases for performance under edge conditions"""
    
    @pytest.mark.asyncio
    async def test_extraction_under_time_pressure(self):
        """Test extraction performance under time constraints"""
        config = EdgeCaseTestConfig()
        
        class TimeConstrainedPage:
            def __init__(self, delay=0.05):
                self.delay = delay
                self.call_count = 0
            
            async def query_selector_all(self, selector):
                self.call_count += 1
                await asyncio.sleep(self.delay)  # Simulate slow queries
                return []
            
            async def query_selector(self, selector):
                return None
            
            async def wait_for_selector(self, selector, timeout=30000):
                return None
        
        page = TimeConstrainedPage(0.05)  # 50ms per query
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        start_time = asyncio.get_event_loop().time()
        result = await extractor.extract_metadata_from_page(page)
        end_time = asyncio.get_event_loop().time()
        
        extraction_time = end_time - start_time
        
        assert result is not None
        print(f"✓ Time-constrained extraction completed in {extraction_time:.3f}s")
        print(f"  DOM queries made: {page.call_count}")
        
        # Should complete within reasonable time even under constraints
        assert extraction_time < 5.0  # Should not take more than 5 seconds


# Test runner with comprehensive edge case coverage
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])