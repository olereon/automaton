#!/usr/bin/env python3.11
"""
Test suite for simplified container-based metadata extraction
Tests the new approach that replaces complex gallery metadata extraction
"""

import asyncio
from unittest.mock import AsyncMock
import sys
import os

# Add the parent directory to sys.path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.generation_download_manager import GenerationDownloadManager


def test_container_metadata_extraction_success():
    """Test successful container metadata extraction with selectors"""
    
    async def run_test():
        # Create minimal manager instance
        manager = GenerationDownloadManager.__new__(GenerationDownloadManager)
        
        # Mock container with successful selectors
        mock_container = AsyncMock()
        
        # Mock time spans
        mock_time_span = AsyncMock()
        mock_time_span.text_content = AsyncMock(return_value="Creation Time")
        
        mock_time_value_span = AsyncMock()  
        mock_time_value_span.text_content = AsyncMock(return_value="01 Sep 2025 10:30:45")
        
        # Mock prompt elements
        mock_prompt_element = AsyncMock()
        mock_prompt_element.text_content = AsyncMock(return_value="A beautiful landscape with mountains and rivers...")
        
        # Setup selector calls
        def mock_query_selector_all(selector):
            if selector == 'span':
                return [mock_time_span, mock_time_value_span]
            elif '.sc-eKQYOU.bdGRCs' in selector:
                return [mock_prompt_element]
            return []
        
        mock_container.query_selector_all = AsyncMock(side_effect=mock_query_selector_all)
        
        # Test text content
        test_text = "Creation Time 01 Sep 2025 10:30:45\nA beautiful landscape with mountains and rivers..."
        
        # Execute extraction
        result = await manager._extract_container_metadata(mock_container, test_text)
        
        # Verify results
        assert result is not None
        assert result['creation_time'] == "01 Sep 2025 10:30:45"
        assert result['prompt'] == "A beautiful landscape with mountains and rivers"
        print("✅ Container extraction with selectors - SUCCESS")
        
    asyncio.run(run_test())


def test_container_metadata_fallback_to_text():
    """Test fallback to text-based extraction when selectors fail"""
    
    async def run_test():
        manager = GenerationDownloadManager.__new__(GenerationDownloadManager)
        
        # Mock container that fails selector calls
        mock_container = AsyncMock()
        mock_container.query_selector_all = AsyncMock(return_value=[])
        
        # Test text content with clear patterns
        test_text = """
        Some header text
        Creation Time 31 Aug 2025 13:32:04
        A detailed prompt about creating art with various elements and colors
        Some footer text
        """
        
        # Execute extraction  
        result = await manager._extract_container_metadata(mock_container, test_text)
        
        # Verify results
        assert result is not None
        assert result['creation_time'] == "31 Aug 2025 13:32:04"
        assert "detailed prompt about creating art" in result['prompt']
        print("✅ Container extraction with text fallback - SUCCESS")
        
    asyncio.run(run_test())


def test_container_metadata_extraction_failure():
    """Test complete extraction failure"""
    
    async def run_test():
        manager = GenerationDownloadManager.__new__(GenerationDownloadManager)
        
        # Mock container
        mock_container = AsyncMock()
        mock_container.query_selector_all = AsyncMock(return_value=[])
        
        # Test text with no recognizable patterns
        test_text = "Random text without any creation time or meaningful content"
        
        # Execute extraction
        result = await manager._extract_container_metadata(mock_container, test_text)
        
        # Verify failure
        assert result is None
        print("✅ Container extraction failure handling - SUCCESS")
        
    asyncio.run(run_test())


def run_all_tests():
    """Run all tests"""
    print("🧪 Running Simplified Container Extraction Tests...")
    
    try:
        test_container_metadata_extraction_success()
        test_container_metadata_fallback_to_text()  
        test_container_metadata_extraction_failure()
        print("\n🎉 All tests passed! Container-based metadata extraction is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()