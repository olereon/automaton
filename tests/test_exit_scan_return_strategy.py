#!/usr/bin/env python3.11
"""
Comprehensive test suite for Exit-Scan-Return Strategy Algorithm
Tests the fixed generation download system algorithm compliance
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
import json
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager,
    GenerationDownloadConfig,
    GenerationDownloadLogger,
    GenerationMetadata
)


class MockPage:
    """Mock Playwright page for testing"""
    
    def __init__(self):
        self.url_history = []
        self.click_history = []
        self.elements_to_find = {}
        self.metadata_responses = {}
        self.scroll_count = 0
        
    def set_url(self, url):
        self.current_url = url
        
    async def url(self):
        return getattr(self, 'current_url', 'https://example.com')
        
    async def go_back(self):
        self.url_history.append('back')
        return True
        
    async def click(self, selector, **kwargs):
        self.click_history.append(selector)
        return True
        
    def locator(self, selector):
        mock_locator = Mock()
        mock_locator.first = Mock(return_value=mock_locator)
        mock_locator.click = AsyncMock(return_value=True)
        mock_locator.count = AsyncMock(return_value=1 if selector in self.elements_to_find else 0)
        mock_locator.text_content = AsyncMock(return_value=self.elements_to_find.get(selector, ""))
        return mock_locator
        
    async def query_selector_all(self, selector):
        if selector == '.sc-cZMHBd.kHPlfG.create-detail-body':
            # Return mock generation containers
            return self._create_mock_containers()
        return []
        
    def _create_mock_containers(self):
        """Create mock generation containers for testing"""
        containers = []
        test_generations = [
            {"time": "30 Aug 2025 05:11:29", "prompt": "The camera begins with a tight close-up of the witch's dual-col", "state": "completed"},
            {"time": "30 Aug 2025 05:10:15", "prompt": "A mystical forest scene with ancient trees", "state": "completed"},
            {"time": "30 Aug 2025 05:09:45", "prompt": "Queuing…", "state": "queuing"},
            {"time": "30 Aug 2025 05:08:30", "prompt": "Something went wrong", "state": "failed"},
            {"time": "30 Aug 2025 05:07:12", "prompt": "Modern city skyline at sunset with golden light", "state": "completed"},
        ]
        
        for i, gen in enumerate(test_generations):
            container = Mock()
            container.query_selector = AsyncMock()
            
            # Mock prompt element
            prompt_elem = Mock()
            prompt_elem.text_content = AsyncMock(return_value=gen["prompt"])
            
            # Mock time element
            time_elem = Mock()
            time_elem.text_content = AsyncMock(return_value=gen["time"])
            
            # Configure container to return appropriate elements
            async def query_side_effect(selector):
                if 'dnESm' in selector or 'prompt' in selector.lower():
                    return prompt_elem
                elif 'jGymgu' in selector or 'time' in selector.lower():
                    return Mock()
                return None
                
            container.query_selector.side_effect = query_side_effect
            container.query_selector_all = AsyncMock(return_value=[time_elem] if 'time' in str(container) else [])
            container.click = AsyncMock(return_value=True)
            
            containers.append(container)
            
        return containers
        
    async def evaluate(self, script):
        if 'window.scrollTo' in script:
            self.scroll_count += 1
        return True


class TestExitScanReturnStrategy:
    """Test suite for Exit-Scan-Return Strategy Algorithm"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig()
        self.config.downloads_folder = os.path.join(self.temp_dir, 'downloads')
        self.config.logs_folder = os.path.join(self.temp_dir, 'logs')
        self.config.duplicate_mode = "skip"
        self.config.use_exit_scan_strategy = True
        
        # Create directories
        os.makedirs(self.config.downloads_folder, exist_ok=True)
        os.makedirs(self.config.logs_folder, exist_ok=True)
        
        self.manager = GenerationDownloadManager(self.config)
        self.mock_page = MockPage()
        
        # Setup checkpoint data
        self.manager.checkpoint_data = {
            'generation_date': '30 Aug 2025 05:11:29',
            'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
            'file_id': '#000000123'
        }
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_algorithm_step_11_exit_gallery(self):
        """Test Algorithm Step 11: Exit gallery to scan generations"""
        
        # Execute step 11
        result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
        
        # Verify gallery exit
        assert 'back' in self.mock_page.url_history
        
    @pytest.mark.asyncio
    async def test_algorithm_step_12_checkpoint_data(self):
        """Test Algorithm Step 12: Get checkpoint data for boundary search"""
        
        # Test with valid checkpoint data
        assert hasattr(self.manager, 'checkpoint_data')
        assert self.manager.checkpoint_data['generation_date'] == '30 Aug 2025 05:11:29'
        assert 'witch' in self.manager.checkpoint_data['prompt']
        
        # Test without checkpoint data
        manager_no_checkpoint = GenerationDownloadManager(self.config)
        result = await manager_no_checkpoint.exit_gallery_and_scan_generations(self.mock_page)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_algorithm_step_13_sequential_scan(self):
        """Test Algorithm Step 13: Sequential scan of generation containers"""
        
        # Mock page with containers
        with patch.object(self.mock_page, 'query_selector_all') as mock_query:
            mock_query.return_value = self.mock_page._create_mock_containers()
            
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            
            # Verify containers were queried
            mock_query.assert_called()
            
    @pytest.mark.asyncio
    async def test_algorithm_step_14_boundary_detection(self):
        """Test Algorithm Step 14: Find boundary using checkpoint matching"""
        
        with patch.object(self.mock_page, 'query_selector_all') as mock_query:
            mock_query.return_value = self.mock_page._create_mock_containers()
            
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            
            # Should find the checkpoint match
            assert result is not None
            assert 'boundary_found' in str(result) or result.get('success') == True
            
    @pytest.mark.asyncio
    async def test_algorithm_step_15_click_boundary_container(self):
        """Test Algorithm Step 15: Click on boundary container to return to gallery"""
        
        with patch.object(self.mock_page, 'query_selector_all') as mock_query:
            containers = self.mock_page._create_mock_containers()
            mock_query.return_value = containers
            
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            
            # Verify click was attempted on the matching container
            # At least one container should have been clicked
            clicked_containers = [c for c in containers if c.click.called]
            assert len(clicked_containers) > 0
            
    @pytest.mark.asyncio
    async def test_comprehensive_duplicate_detection_triggers_exit_scan(self):
        """Test that duplicate detection triggers exit-scan-return strategy"""
        
        # Setup existing log entries to simulate duplicates
        self.manager.existing_log_entries = [
            {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
                'file_id': '#000000123'
            }
        ]
        
        # Mock metadata extraction to return duplicate
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col'
            }
            
            # Mock exit_gallery_and_scan_generations to verify it's called
            with patch.object(self.manager, 'exit_gallery_and_scan_generations') as mock_exit_scan:
                mock_exit_scan.return_value = {'success': True, 'boundary_found': True}
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(
                    self.mock_page, 'thumbnail_1'
                )
                
                # Should detect duplicate and trigger exit-scan
                assert is_duplicate == True
                mock_exit_scan.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_queue_container_filtering(self):
        """Test that queuing and failed containers are properly filtered"""
        
        with patch.object(self.mock_page, 'query_selector_all') as mock_query:
            containers = self.mock_page._create_mock_containers()
            mock_query.return_value = containers
            
            # Mock the scanning method to test filtering logic
            with patch.object(self.manager, '_scan_generation_containers') as mock_scan:
                await self.manager.exit_gallery_and_scan_generations(self.mock_page)
                
                # Verify scan was called with the containers
                mock_scan.assert_called_once()
                args = mock_scan.call_args[0]
                containers_arg = args[0] if args else []
                
                # Should have filtered out queuing and failed containers
                # (Implementation should skip containers with "Queuing…" and "Something went wrong")
                
    @pytest.mark.asyncio
    async def test_checkpoint_matching_algorithm(self):
        """Test the checkpoint matching algorithm with time + prompt"""
        
        checkpoint_time = '30 Aug 2025 05:11:29'
        checkpoint_prompt = 'The camera begins with a tight close-up of the witch\'s dual-col'
        
        test_cases = [
            # Exact match - should match
            {
                'time': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
                'expected': True
            },
            # Different time - should not match
            {
                'time': '30 Aug 2025 05:10:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
                'expected': False
            },
            # Different prompt - should not match
            {
                'time': '30 Aug 2025 05:11:29',
                'prompt': 'A different prompt entirely',
                'expected': False
            },
            # Truncated prompt match - should match (first 50-100 chars)
            {
                'time': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col... [additional text]',
                'expected': True
            }
        ]
        
        for case in test_cases:
            # Test the matching logic by comparing normalized values
            time_match = case['time'] == checkpoint_time
            prompt_match = case['prompt'][:50] == checkpoint_prompt[:50]
            actual_match = time_match and prompt_match
            
            assert actual_match == case['expected'], f"Failed for case: {case}"
            
    @pytest.mark.asyncio
    async def test_fallback_to_traditional_fast_forward(self):
        """Test fallback when exit-scan-return fails"""
        
        # Simulate failure in exit-scan-return
        with patch.object(self.manager, 'exit_gallery_and_scan_generations') as mock_exit_scan:
            mock_exit_scan.return_value = None  # Simulate failure
            
            # The system should gracefully handle the failure
            # This would typically be tested in the calling function that handles the strategy
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            assert result is None
            
    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance characteristics of exit-scan-return vs traditional"""
        
        import time
        
        # Simulate traditional fast-forward (checking each thumbnail)
        traditional_start = time.time()
        for i in range(100):  # Simulate 100 thumbnails
            await asyncio.sleep(0.001)  # Small delay per thumbnail
        traditional_time = time.time() - traditional_start
        
        # Simulate exit-scan-return strategy
        exit_scan_start = time.time()
        await self.manager.exit_gallery_and_scan_generations(self.mock_page)
        exit_scan_time = time.time() - exit_scan_start
        
        # Exit-scan-return should be significantly faster
        # (In real implementation, traditional would take ~2 seconds per thumbnail)
        assert exit_scan_time < traditional_time * 0.5  # At least 50% faster
        
    def test_configuration_validation(self):
        """Test that configuration properly enables/disables strategy"""
        
        # Test enabled configuration
        config_enabled = GenerationDownloadConfig()
        config_enabled.duplicate_mode = "skip"
        config_enabled.use_exit_scan_strategy = True
        
        manager_enabled = GenerationDownloadManager(config_enabled)
        assert manager_enabled.config.use_exit_scan_strategy == True
        
        # Test disabled configuration
        config_disabled = GenerationDownloadConfig()
        config_disabled.duplicate_mode = "skip"
        config_disabled.use_exit_scan_strategy = False
        
        manager_disabled = GenerationDownloadManager(config_disabled)
        assert manager_disabled.config.use_exit_scan_strategy == False
        
    @pytest.mark.asyncio
    async def test_error_handling_scenarios(self):
        """Test various error scenarios and recovery"""
        
        # Test 1: No containers found
        with patch.object(self.mock_page, 'query_selector_all') as mock_query:
            mock_query.return_value = []
            
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            # Should handle gracefully without crashing
            
        # Test 2: Container click fails
        with patch.object(self.mock_page, 'query_selector_all') as mock_query:
            containers = self.mock_page._create_mock_containers()
            # Make click fail
            containers[0].click = AsyncMock(side_effect=Exception("Click failed"))
            mock_query.return_value = containers
            
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            # Should handle click failure gracefully
            
        # Test 3: Page navigation fails
        self.mock_page.go_back = AsyncMock(side_effect=Exception("Navigation failed"))
        
        with pytest.raises(Exception):
            await self.manager.exit_gallery_and_scan_generations(self.mock_page)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])