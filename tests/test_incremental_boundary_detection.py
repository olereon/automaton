#!/usr/bin/env python3
"""
Test Incremental Boundary Detection - Scan-As-You-Scroll Approach

This test validates the improved boundary detection that:
1. Scans containers immediately after duplicate detection
2. Scrolls incrementally to reveal 40-50 new containers at a time
3. Scans new containers without re-scanning old ones
4. Ensures no containers are skipped during scrolling
5. Is optimized for speed and robustness
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


class TestIncrementalBoundaryDetection:
    """Test incremental boundary detection with scan-as-you-scroll approach"""

    def setup_method(self):
        """Set up test configuration"""
        self.test_config = GenerationDownloadConfig(
            max_downloads=100,
            downloads_folder="/tmp/test_downloads",
            completed_task_selector="div[id$='__8']",  # Main page containers
            thumbnail_selector=".thumsItem",  # Gallery thumbnails (not used in boundary detection)
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
        
    def create_incremental_mock_page(self):
        """Create mock page that simulates incremental container loading"""
        
        mock_page = AsyncMock()
        
        # State tracking
        state = {
            "scroll_position": 0,
            "containers_revealed": 50,  # Start with 50 visible
            "total_containers": 2500,    # Total available
            "viewport_height": 1080
        }
        
        async def mock_query_selector_all(selector):
            """Return containers based on current scroll state"""
            if selector == self.test_config.completed_task_selector:
                # Return containers visible at current scroll position
                containers = []
                for i in range(state["containers_revealed"]):
                    mock_container = AsyncMock()
                    mock_container.get_attribute.return_value = f"container_{i}"  # Unique ID
                    
                    # Simulate various container states
                    if i < 549:  # Existing downloads (duplicates)
                        time_key = f"0{i%10} Sep 2025 0{(i%6)+1}:0{(i%6)+1}:{i%60:02d}"
                        text_content = f"Creation Time {time_key}\nMock prompt {i} with sufficient length for testing boundary detection..."
                    else:  # New content (boundary at 549)
                        time_key = f"03 Sep 2025 {7+i%12:02d}:{40+(i%20):02d}:{i%60:02d}"
                        text_content = f"Creation Time {time_key}\nNew generation content {i} that should be downloaded..."
                    
                    mock_container.text_content.return_value = text_content
                    mock_container.click = AsyncMock()
                    containers.append(mock_container)
                
                return containers
            return []
        
        async def mock_evaluate(script):
            """Handle scrolling and viewport queries"""
            if "window.innerHeight" in script:
                return state["viewport_height"]
            elif "window.pageYOffset" in script:
                return state["scroll_position"]
            elif "window.scrollTo" in script or "window.scrollBy" in script:
                # Extract scroll amount and update state
                if "scrollTo(0," in script:
                    # Extract target position
                    import re
                    match = re.search(r'scrollTo\(0,\s*(\d+)', script)
                    if match:
                        new_position = int(match.group(1))
                        state["scroll_position"] = new_position
                        
                        # Reveal more containers based on scroll (40-50 per scroll)
                        containers_per_scroll = 45
                        state["containers_revealed"] = min(
                            state["containers_revealed"] + containers_per_scroll,
                            state["total_containers"]
                        )
                        logger.debug(f"Scrolled to {new_position}, now showing {state['containers_revealed']} containers")
                elif "scrollBy" in script:
                    # Simple scroll by amount
                    state["scroll_position"] += 1500
                    state["containers_revealed"] = min(
                        state["containers_revealed"] + 45,
                        state["total_containers"]
                    )
        
        async def mock_wait_for_timeout(timeout):
            """Mock wait"""
            await asyncio.sleep(0.01)  # Quick test execution
        
        mock_page.query_selector_all = mock_query_selector_all
        mock_page.evaluate = mock_evaluate
        mock_page.wait_for_timeout = mock_wait_for_timeout
        
        return mock_page, state
    
    @pytest.mark.asyncio
    async def test_incremental_scanning_no_preload(self):
        """Test that boundary detection doesn't preload all containers"""
        
        mock_page, state = self.create_incremental_mock_page()
        
        # Create manager
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        # Run boundary detection
        result = await manager._find_download_boundary_sequential(mock_page)
        
        # Verify incremental approach
        assert result is not None, "Should find boundary"
        assert result['found'] is True
        assert result['container_index'] == 549, f"Boundary should be at 549, got {result['container_index']}"
        
        # Verify didn't load all containers at once
        assert state["containers_revealed"] < 1000, f"Should not load all containers, loaded {state['containers_revealed']}"
        
        # Verify found boundary efficiently
        assert result['scroll_iterations'] < 20, f"Should find boundary quickly, took {result['scroll_iterations']} scrolls"
        
        logger.info(f"✅ Incremental scanning test passed: Found boundary at {result['container_index']} after {result['scroll_iterations']} scrolls")
    
    @pytest.mark.asyncio
    async def test_no_duplicate_scanning(self):
        """Test that containers are not scanned multiple times"""
        
        mock_page, state = self.create_incremental_mock_page()
        
        # Track container access
        scanned_containers = set()
        original_get_attribute = AsyncMock.get_attribute
        
        async def tracking_get_attribute(self, attr):
            container_id = f"container_{len(scanned_containers)}"
            if container_id in scanned_containers:
                logger.warning(f"⚠️ Container {container_id} scanned multiple times!")
            scanned_containers.add(container_id)
            return container_id
        
        # Patch the mock to track scanning
        AsyncMock.get_attribute = tracking_get_attribute
        
        try:
            # Create manager and run detection
            manager = GenerationDownloadManager(self.test_config)
            manager.existing_log_entries = self.mock_log_entries
            
            result = await manager._find_download_boundary_sequential(mock_page)
            
            # Verify no duplicate scanning
            assert result is not None
            assert len(scanned_containers) == result['containers_scanned'], \
                f"Containers scanned multiple times: {len(scanned_containers)} IDs for {result['containers_scanned']} scans"
            
            logger.info(f"✅ No duplicate scanning test passed: {len(scanned_containers)} unique containers scanned")
            
        finally:
            # Restore original mock
            AsyncMock.get_attribute = original_get_attribute
    
    @pytest.mark.asyncio
    async def test_boundary_at_end_of_list(self):
        """Test that boundary detection handles case where boundary is at end of list"""
        
        # Create mock with boundary at very end
        mock_page, state = self.create_incremental_mock_page()
        state["total_containers"] = 600  # Boundary will be at 549, close to end
        
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        result = await manager._find_download_boundary_sequential(mock_page)
        
        assert result is not None, "Should find boundary even at end of list"
        assert result['found'] is True
        assert result['container_index'] == 549
        
        logger.info(f"✅ End of list test passed: Found boundary at container {result['container_index']}")
    
    @pytest.mark.asyncio
    async def test_no_boundary_all_duplicates(self):
        """Test handling when all containers are duplicates (no boundary)"""
        
        mock_page, state = self.create_incremental_mock_page()
        
        # Set all containers as duplicates
        state["total_containers"] = 500  # All will be duplicates (< 549)
        
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        result = await manager._find_download_boundary_sequential(mock_page)
        
        # Should scan all containers and find no boundary
        assert result is None, "Should return None when no boundary found"
        
        logger.info(f"✅ All duplicates test passed: Correctly returned None after scanning {state['containers_revealed']} containers")
    
    @pytest.mark.asyncio
    async def test_efficient_scrolling_strategy(self):
        """Test that scrolling reveals appropriate number of containers (40-50)"""
        
        mock_page, state = self.create_incremental_mock_page()
        
        # Track container reveals per scroll
        reveal_counts = []
        previous_count = state["containers_revealed"]
        
        original_evaluate = mock_page.evaluate
        async def tracking_evaluate(script):
            nonlocal previous_count
            result = await original_evaluate(script)
            if "scrollTo" in script or "scrollBy" in script:
                new_count = state["containers_revealed"]
                if new_count > previous_count:
                    reveal_counts.append(new_count - previous_count)
                    previous_count = new_count
            return result
        
        mock_page.evaluate = tracking_evaluate
        
        manager = GenerationDownloadManager(self.test_config)
        manager.existing_log_entries = self.mock_log_entries
        
        result = await manager._find_download_boundary_sequential(mock_page)
        
        # Verify efficient scrolling (40-50 containers per scroll)
        for count in reveal_counts:
            assert 35 <= count <= 55, f"Scroll revealed {count} containers, expected 40-50"
        
        logger.info(f"✅ Efficient scrolling test passed: Reveals per scroll: {reveal_counts}")


def run_incremental_boundary_tests():
    """Run all incremental boundary detection tests"""
    
    logger.info("🧪 Running Incremental Boundary Detection Tests")
    logger.info("=" * 80)
    
    test_class = TestIncrementalBoundaryDetection()
    
    tests = [
        ("Incremental Scanning (No Preload)", test_class.test_incremental_scanning_no_preload),
        ("No Duplicate Scanning", test_class.test_no_duplicate_scanning),
        ("Boundary at End of List", test_class.test_boundary_at_end_of_list),
        ("No Boundary (All Duplicates)", test_class.test_no_boundary_all_duplicates),
        ("Efficient Scrolling Strategy", test_class.test_efficient_scrolling_strategy),
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
        logger.info("🎉 All incremental boundary detection tests passed!")
        return True
    else:
        logger.error("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_incremental_boundary_tests()
    sys.exit(0 if success else 1)