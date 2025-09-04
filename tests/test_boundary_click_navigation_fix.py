#!/usr/bin/env python3
"""
Test Boundary Click Navigation Fix
=================================

This test validates the corrected boundary click implementation that uses
the same method as initial navigation (page.click with container ID selector).

The fix addresses the AttributeError where container.page was accessed incorrectly
and replaces complex child element clicking with direct page-level clicking.
"""

import pytest
import asyncio
import logging
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add parent directory for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestBoundaryClickNavigationFix:
    """Test the corrected boundary click implementation"""

    def setup_method(self):
        """Set up test configuration"""
        self.test_config = GenerationDownloadConfig(
            max_downloads=100,
            downloads_folder="/tmp/test_downloads",
            completed_task_selector="div[id$='__8']",
            creation_time_text="Creation Time"
        )

    @pytest.mark.asyncio
    async def test_boundary_click_uses_same_method_as_initial_navigation(self):
        """Test that boundary click now uses page.click() like initial navigation"""
        
        # Create mock container with proper page reference
        mock_container = AsyncMock()
        mock_frame = AsyncMock()
        mock_page = AsyncMock()
        
        # Mock the ElementHandle -> page reference chain (corrected approach)
        mock_container.owner_frame.return_value = mock_frame
        mock_frame.page.return_value = mock_page
        mock_page.url = "https://wan.video/generate"
        
        # Mock container ID (matches the example from the task)
        mock_container.get_attribute.return_value = "50cb0dc8c77c4a3e91c959c431aa3b53__13"
        
        # Mock successful gallery verification
        mock_gallery_indicator = AsyncMock()
        mock_gallery_indicator.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_indicator
        
        manager = GenerationDownloadManager(self.test_config)
        
        # Test boundary click with corrected implementation
        result = await manager._click_boundary_container(mock_container, 1)
        
        # Verify success
        assert result is True
        
        # Verify it used page.click() with container ID selector (same as initial navigation)
        expected_selector = "div[id='50cb0dc8c77c4a3e91c959c431aa3b53__13']"
        mock_page.click.assert_called_with(expected_selector, timeout=5000)
        
        # Verify page reference was obtained correctly
        mock_container.owner_frame.assert_called_once()
        mock_frame.page.assert_called_once()
        
        logger.info("✅ Boundary click now uses same method as initial navigation")

    @pytest.mark.asyncio 
    async def test_boundary_click_fallback_selector(self):
        """Test fallback selector when direct ID click fails"""
        
        mock_container = AsyncMock()
        mock_frame = AsyncMock()
        mock_page = AsyncMock()
        
        mock_container.owner_frame.return_value = mock_frame
        mock_frame.page.return_value = mock_page
        mock_page.url = "https://wan.video/generate"
        
        # Container ID with number suffix
        mock_container.get_attribute.return_value = "50cb0dc8c77c4a3e91c959c431aa3b53__13"
        
        # First click fails, second succeeds
        mock_page.click.side_effect = [
            Exception("Direct ID click failed"),  # First call fails
            None  # Second call succeeds
        ]
        
        # Mock successful gallery verification
        mock_gallery_indicator = AsyncMock()
        mock_gallery_indicator.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_indicator
        
        manager = GenerationDownloadManager(self.test_config)
        
        result = await manager._click_boundary_container(mock_container, 1)
        
        # Verify success with fallback
        assert result is True
        
        # Verify both selectors were tried
        assert mock_page.click.call_count == 2
        
        # Check fallback selector was used
        fallback_call = mock_page.click.call_args_list[1]
        expected_fallback = "div[id$='__13']"
        assert fallback_call[0][0] == expected_fallback
        
        logger.info("✅ Fallback selector works when direct ID click fails")

    @pytest.mark.asyncio
    async def test_boundary_click_no_container_id(self):
        """Test handling when container ID cannot be retrieved"""
        
        mock_container = AsyncMock()
        mock_frame = AsyncMock()
        mock_page = AsyncMock()
        
        mock_container.owner_frame.return_value = mock_frame
        mock_frame.page.return_value = mock_page
        
        # Mock missing container ID
        mock_container.get_attribute.return_value = None
        
        manager = GenerationDownloadManager(self.test_config)
        
        result = await manager._click_boundary_container(mock_container, 1)
        
        # Should fail gracefully
        assert result is False
        
        # Should not attempt any clicks
        mock_page.click.assert_not_called()
        
        logger.info("✅ Handles missing container ID gracefully")

    @pytest.mark.asyncio
    async def test_boundary_click_gallery_verification_fails(self):
        """Test when click succeeds but gallery doesn't open"""
        
        mock_container = AsyncMock()
        mock_frame = AsyncMock()
        mock_page = AsyncMock()
        
        mock_container.owner_frame.return_value = mock_frame
        mock_frame.page.return_value = mock_page
        mock_page.url = "https://wan.video/generate"
        
        mock_container.get_attribute.return_value = "50cb0dc8c77c4a3e91c959c431aa3b53__13"
        
        # Gallery verification fails
        mock_page.wait_for_selector.side_effect = asyncio.TimeoutError("Gallery not found")
        
        manager = GenerationDownloadManager(self.test_config)
        
        result = await manager._click_boundary_container(mock_container, 1)
        
        # Should fail due to gallery not opening
        assert result is False
        
        # Should have attempted click
        mock_page.click.assert_called_once()
        
        logger.info("✅ Correctly detects when gallery doesn't open after click")

    @pytest.mark.asyncio
    async def test_page_reference_extraction_methods(self):
        """Test different methods of getting page reference from ElementHandle"""
        
        mock_container = AsyncMock()
        mock_frame = AsyncMock()
        mock_page = AsyncMock()
        
        # Test the corrected approach: container.owner_frame().page()
        mock_container.owner_frame.return_value = mock_frame
        mock_frame.page.return_value = mock_page
        mock_page.url = "https://wan.video/generate"
        
        mock_container.get_attribute.return_value = "test__13"
        
        # Mock successful gallery verification
        mock_gallery_indicator = AsyncMock()
        mock_gallery_indicator.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_indicator
        
        manager = GenerationDownloadManager(self.test_config)
        
        result = await manager._click_boundary_container(mock_container, 1)
        
        assert result is True
        
        # Verify the correct method was used to get page reference
        mock_container.owner_frame.assert_called_once()
        mock_frame.page.assert_called_once()
        
        logger.info("✅ Page reference extracted correctly using owner_frame().page()")


def run_boundary_click_navigation_tests():
    """Run all boundary click navigation fix tests"""
    
    logger.info("🧪 Running Boundary Click Navigation Fix Tests")
    logger.info("=" * 80)
    
    test_class = TestBoundaryClickNavigationFix()
    
    tests = [
        ("Same Method as Initial Navigation", test_class.test_boundary_click_uses_same_method_as_initial_navigation),
        ("Fallback Selector", test_class.test_boundary_click_fallback_selector),
        ("No Container ID Handling", test_class.test_boundary_click_no_container_id),
        ("Gallery Verification Failure", test_class.test_boundary_click_gallery_verification_fails),
        ("Page Reference Extraction", test_class.test_page_reference_extraction_methods),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_class.setup_method()
            logger.info(f"\n🔬 Running: {test_name}")
            asyncio.run(test_func())
            logger.info(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ FAILED: {test_name} - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    logger.info("\n" + "=" * 80)
    logger.info(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All boundary click navigation fix tests passed!")
        logger.info("\n💡 Key improvements validated:")
        logger.info("   ✅ Uses page.click() instead of ElementHandle.click()")
        logger.info("   ✅ Correct page reference extraction with owner_frame().page()")
        logger.info("   ✅ Same approach as successful initial navigation")
        logger.info("   ✅ Proper fallback selector handling")
        logger.info("   ✅ Robust error handling for edge cases")
        return True
    else:
        logger.error("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_boundary_click_navigation_tests()
    sys.exit(0 if success else 1)