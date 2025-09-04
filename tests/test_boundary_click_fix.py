#!/usr/bin/env python3
"""
Test Boundary Click Fix - Verify Gallery Opening
===============================================

This test validates the enhanced boundary click mechanism that:
1. Attempts multiple click strategies on boundary container
2. Verifies that gallery actually opens after click
3. Returns failure if click doesn't result in gallery opening

The fix addresses the cycling issue where boundary was found but 
click didn't properly open gallery, causing automation to loop.
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


class TestBoundaryClickFix:
    """Test the enhanced boundary click verification"""

    def setup_method(self):
        """Set up test configuration"""
        self.test_config = GenerationDownloadConfig(
            max_downloads=100,
            downloads_folder="/tmp/test_downloads",
            completed_task_selector="div[id$='__8']",
            creation_time_text="Creation Time"
        )

    @pytest.mark.asyncio
    async def test_boundary_click_with_gallery_verification_success(self):
        """Test successful boundary click that opens gallery"""
        
        # Create mock container and page
        mock_container = AsyncMock()
        mock_page = AsyncMock()
        mock_container.page = mock_page
        
        # Mock successful interactive element click
        mock_interactive_element = AsyncMock()
        mock_container.query_selector.return_value = mock_interactive_element
        
        # Mock gallery verification success
        mock_gallery_indicator = AsyncMock()
        mock_gallery_indicator.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_indicator
        mock_page.url.return_value = "https://wan.video/generate/gallery/12345"
        
        manager = GenerationDownloadManager(self.test_config)
        
        # Test boundary click
        result = await manager._click_boundary_container(mock_container, 42)
        
        # Verify success
        assert result is True
        mock_interactive_element.click.assert_called_once()
        mock_page.wait_for_timeout.assert_called()
        
        logger.info("✅ Boundary click with gallery verification SUCCESS test passed")

    @pytest.mark.asyncio
    async def test_boundary_click_gallery_verification_failure(self):
        """Test boundary click that fails to open gallery"""
        
        # Create mock container and page
        mock_container = AsyncMock()
        mock_page = AsyncMock()
        mock_container.page = mock_page
        
        # Mock interactive element click
        mock_interactive_element = AsyncMock()
        mock_container.query_selector.return_value = mock_interactive_element
        
        # Mock gallery verification failure (no gallery indicators found)
        mock_page.wait_for_selector.side_effect = asyncio.TimeoutError("Gallery indicator not found")
        mock_page.url.return_value = "https://wan.video/generate"  # Still on main page
        
        # Mock direct container click also failing to open gallery
        mock_container.click = AsyncMock()
        
        manager = GenerationDownloadManager(self.test_config)
        
        # Test boundary click
        result = await manager._click_boundary_container(mock_container, 42)
        
        # Verify failure
        assert result is False
        mock_interactive_element.click.assert_called()
        mock_container.click.assert_called_with(force=True)  # Should try direct click too
        
        logger.info("✅ Boundary click gallery verification FAILURE test passed")

    @pytest.mark.asyncio
    async def test_gallery_verification_method(self):
        """Test the _verify_gallery_opened method independently"""
        
        mock_page = AsyncMock()
        manager = GenerationDownloadManager(self.test_config)
        
        # Test successful gallery verification
        mock_gallery_element = AsyncMock()
        mock_gallery_element.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_element
        mock_page.url.return_value = "https://wan.video/generate/gallery"
        
        result = await manager._verify_gallery_opened(mock_page)
        assert result is True
        
        # Test failed gallery verification
        mock_page.wait_for_selector.side_effect = asyncio.TimeoutError("No gallery indicators")
        mock_page.url.return_value = "https://wan.video/generate"
        
        result = await manager._verify_gallery_opened(mock_page)
        assert result is False
        
        logger.info("✅ Gallery verification method test passed")

    @pytest.mark.asyncio
    async def test_multiple_selector_strategies(self):
        """Test that multiple selectors are tried when first one fails"""
        
        mock_container = AsyncMock()
        mock_page = AsyncMock()
        mock_container.page = mock_page
        
        # First selector fails, second succeeds
        mock_container.query_selector.side_effect = [
            None,  # First selector (.sc-abVJb.eNepQa) returns None
            AsyncMock(),  # Second selector (.sc-eGFoZs.eRfPry) succeeds
        ]
        
        # Mock successful gallery verification
        mock_gallery_indicator = AsyncMock()
        mock_gallery_indicator.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_indicator
        
        manager = GenerationDownloadManager(self.test_config)
        
        result = await manager._click_boundary_container(mock_container, 42)
        
        # Verify success and that multiple selectors were tried
        assert result is True
        assert mock_container.query_selector.call_count == 2
        
        logger.info("✅ Multiple selector strategies test passed")

    @pytest.mark.asyncio
    async def test_direct_click_fallback(self):
        """Test that direct container click is used as fallback"""
        
        mock_container = AsyncMock()
        mock_page = AsyncMock()
        mock_container.page = mock_page
        
        # All selectors return None (no interactive elements found)
        mock_container.query_selector.return_value = None
        
        # Mock successful gallery verification after direct click
        mock_gallery_indicator = AsyncMock()
        mock_gallery_indicator.is_visible.return_value = True
        mock_page.wait_for_selector.return_value = mock_gallery_indicator
        
        manager = GenerationDownloadManager(self.test_config)
        
        result = await manager._click_boundary_container(mock_container, 42)
        
        # Verify direct click was attempted
        assert result is True
        mock_container.click.assert_called_with(force=True)
        
        logger.info("✅ Direct click fallback test passed")


def run_boundary_click_tests():
    """Run all boundary click fix tests"""
    
    logger.info("🧪 Running Boundary Click Fix Tests")
    logger.info("=" * 80)
    
    test_class = TestBoundaryClickFix()
    
    tests = [
        ("Boundary Click Success", test_class.test_boundary_click_with_gallery_verification_success),
        ("Boundary Click Failure", test_class.test_boundary_click_gallery_verification_failure),
        ("Gallery Verification Method", test_class.test_gallery_verification_method),
        ("Multiple Selector Strategies", test_class.test_multiple_selector_strategies),
        ("Direct Click Fallback", test_class.test_direct_click_fallback),
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
        logger.info("🎉 All boundary click fix tests passed!")
        logger.info("\n💡 The enhanced boundary click verification should fix the cycling issue:")
        logger.info("   ✅ Clicks boundary container using multiple strategies")
        logger.info("   ✅ Verifies gallery actually opens after click")
        logger.info("   ✅ Returns failure if gallery doesn't open")
        logger.info("   ✅ Prevents false success that caused cycling")
        return True
    else:
        logger.error("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_boundary_click_tests()
    sys.exit(0 if success else 1)