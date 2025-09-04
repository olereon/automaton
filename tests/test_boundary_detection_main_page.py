#!/usr/bin/env python3
"""
Test Enhanced Boundary Detection - Main Generation Page Scrolling

This test validates the improved boundary detection that:
1. Scrolls extensively on the main generation page (not gallery)
2. Uses completed_task_selector for main page containers
3. Loads thousands of containers instead of just 42
4. Properly finds boundaries between download sessions
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


class TestBoundaryDetectionMainPage:
    """Test boundary detection improvements for main generation page scanning"""

    def setup_method(self):
        """Set up test configuration"""
        self.test_config = GenerationDownloadConfig(
            max_downloads=100,
            downloads_folder="/tmp/test_downloads",
            completed_task_selector="div[id$='__8']",  # Main page containers
            thumbnail_selector=".thumsItem, .thumbnail-item, .thumsCou",  # Gallery thumbnails
            creation_time_text="Creation Time"
        )
        
        # Create mock log entries (simulate 549 existing downloads)
        self.mock_log_entries = {}
        for i in range(549):
            time_key = f"0{i%10} Sep 2025 0{(i%6)+1}:0{(i%6)+1}:{i%60:02d}"
            self.mock_log_entries[time_key] = {
                'id': f"#{i+1:09d}",
                'prompt': f"Mock prompt {i} with sufficient length for testing boundary detection..."
            }
        
    def create_mock_page(self, containers_per_scroll=50, max_containers=2500):
        """Create mock page that simulates extensive scrolling on main generation page"""
        
        mock_page = AsyncMock()
        
        # Track scroll state
        scroll_state = {"scroll_count": 0, "containers_loaded": 0}
        
        async def mock_query_selector_all(selector):
            """Mock container loading based on scroll state"""
            if selector == self.test_config.completed_task_selector:
                # Main page containers - increase with scrolling
                containers_loaded = min(
                    scroll_state["containers_loaded"] + containers_per_scroll * scroll_state["scroll_count"],
                    max_containers
                )
                
                # Create mock containers
                mock_containers = []
                for i in range(containers_loaded):
                    mock_container = AsyncMock()
                    
                    # Simulate various container states
                    if i < 549:  # Existing downloads
                        time_key = f"0{i%10} Sep 2025 0{(i%6)+1}:0{(i%6)+1}:{i%60:02d}"
                        text_content = f"Creation Time {time_key}\nMock prompt {i} with sufficient length for testing boundary detection..."
                    elif i >= 549 and i < 559:  # New content (boundary)
                        time_key = f"03 Sep 2025 {7+i%12:02d}:{40+(i%20):02d}:{i%60:02d}"
                        text_content = f"Creation Time {time_key}\nNew generation content {i} that should be downloaded..."
                    else:  # More new content
                        time_key = f"03 Sep 2025 {8+(i%12):02d}:{i%60:02d}:{(i*17)%60:02d}"
                        text_content = f"Creation Time {time_key}\nAdditional new content {i} for comprehensive testing..."
                    
                    mock_container.text_content.return_value = text_content
                    mock_container.click = AsyncMock()
                    mock_container.query_selector.return_value = AsyncMock()
                    mock_containers.append(mock_container)
                
                return mock_containers
            
            elif selector == self.test_config.thumbnail_selector:
                # Gallery thumbnails - should not be used in boundary detection
                return []
            
            return []
        
        async def mock_evaluate(script):
            """Mock page scrolling"""
            if "scrollTo" in script:
                scroll_state["scroll_count"] += 1
                logger.debug(f"Mock scroll #{scroll_state['scroll_count']}")
        
        async def mock_wait_for_timeout(timeout):
            """Mock wait"""
            await asyncio.sleep(0.01)  # Quick test execution
        
        mock_page.query_selector_all = mock_query_selector_all
        mock_page.evaluate = mock_evaluate
        mock_page.wait_for_timeout = mock_wait_for_timeout
        
        return mock_page, scroll_state
    
    @pytest.mark.asyncio
    async def test_extensive_main_page_scrolling(self):
        """Test that boundary detection scrolls extensively on main generation page"""
        
        # Create mock page with 2500 containers total
        mock_page, scroll_state = self.create_mock_page(
            containers_per_scroll=50,
            max_containers=2500
        )
        
        # Create manager
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        # Test the new scrolling method
        containers_loaded = await manager._scroll_entire_generation_page_for_boundary_detection(mock_page)
        
        # Verify extensive scrolling occurred
        assert scroll_state["scroll_count"] > 10, f"Expected >10 scrolls, got {scroll_state['scroll_count']}"
        assert containers_loaded > 1000, f"Expected >1000 containers, got {containers_loaded}"
        
        logger.info(f"✅ Extensive scrolling test passed: {scroll_state['scroll_count']} scrolls, {containers_loaded} containers")
    
    @pytest.mark.asyncio 
    async def test_boundary_detection_with_thousands_of_containers(self):
        """Test boundary detection can handle thousands of containers"""
        
        # Create mock page with many containers
        mock_page, scroll_state = self.create_mock_page(
            containers_per_scroll=100,
            max_containers=5000
        )
        
        # Create manager
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        # Test full boundary detection
        result = await manager._find_download_boundary_sequential(mock_page)
        
        # Verify boundary was found
        assert result is not None, "Boundary detection should succeed with thousands of containers"
        assert result.get('found') is True, "Boundary should be found"
        assert result.get('container_index', 0) > 549, "Boundary should be after existing downloads"
        assert result.get('total_containers', 0) > 2000, "Should scan thousands of containers"
        
        logger.info(f"✅ Large scale boundary detection passed: container #{result.get('container_index')} of {result.get('total_containers')}")
    
    @pytest.mark.asyncio
    async def test_correct_selector_usage(self):
        """Test that boundary detection uses completed_task_selector, not thumbnail_selector"""
        
        mock_page = AsyncMock()
        
        # Track which selectors are called
        selector_calls = {"completed_task": 0, "thumbnail": 0}
        
        async def mock_query_selector_all(selector):
            if selector == self.test_config.completed_task_selector:
                selector_calls["completed_task"] += 1
                return [AsyncMock() for _ in range(100)]  # Mock containers
            elif selector == self.test_config.thumbnail_selector:
                selector_calls["thumbnail"] += 1
                return []
            return []
        
        mock_page.query_selector_all = mock_query_selector_all
        mock_page.evaluate = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        
        # Create manager
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        # Test scrolling method
        await manager._scroll_entire_generation_page_for_boundary_detection(mock_page)
        
        # Verify correct selector usage
        assert selector_calls["completed_task"] > 0, "Should use completed_task_selector for main page"
        assert selector_calls["thumbnail"] == 0, "Should NOT use thumbnail_selector for boundary detection"
        
        logger.info(f"✅ Selector usage test passed: completed_task calls={selector_calls['completed_task']}, thumbnail calls={selector_calls['thumbnail']}")

    @pytest.mark.asyncio
    async def test_boundary_detection_performance(self):
        """Test that boundary detection handles large datasets efficiently"""
        
        # Create mock page with very large dataset
        mock_page, scroll_state = self.create_mock_page(
            containers_per_scroll=200,
            max_containers=10000
        )
        
        # Create manager
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        # Time the boundary detection
        import time
        start_time = time.time()
        
        result = await manager._find_download_boundary_sequential(mock_page)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify performance and results
        assert result is not None, "Large dataset boundary detection should succeed"
        assert duration < 10.0, f"Boundary detection took too long: {duration:.2f}s"
        assert result.get('total_containers', 0) > 5000, "Should handle very large datasets"
        
        logger.info(f"✅ Performance test passed: {duration:.2f}s for {result.get('total_containers')} containers")


def run_boundary_detection_tests():
    """Run all boundary detection tests"""
    
    logger.info("🧪 Running Enhanced Boundary Detection Tests")
    logger.info("=" * 80)
    
    test_class = TestBoundaryDetectionMainPage()
    
    tests = [
        ("Extensive Main Page Scrolling", test_class.test_extensive_main_page_scrolling),
        ("Boundary Detection with Thousands of Containers", test_class.test_boundary_detection_with_thousands_of_containers),
        ("Correct Selector Usage", test_class.test_correct_selector_usage),
        ("Boundary Detection Performance", test_class.test_boundary_detection_performance),
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
            failed += 1
    
    logger.info("\n" + "=" * 80)
    logger.info(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All boundary detection tests passed!")
        return True
    else:
        logger.error("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_boundary_detection_tests()
    sys.exit(0 if success else 1)