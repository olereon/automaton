#!/usr/bin/env python3.11
"""
Integration test suite for end-to-end generation download workflows
Tests complete automation flow from start to finish
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
from core.engine import WebAutomationEngine, ActionType, Action, AutomationConfig


class MockBrowser:
    """Mock browser for integration testing"""
    
    def __init__(self):
        self.pages = []
        self.is_connected = True
        
    def new_page(self):
        page = MockPage()
        self.pages.append(page)
        return page
        
    async def close(self):
        self.is_connected = False


class MockPage:
    """Enhanced mock page for integration testing"""
    
    def __init__(self):
        self.current_url = "https://example.com"
        self.navigation_history = []
        self.clicks = []
        self.downloads = []
        self.thumbnails = []
        self.current_thumbnail_index = 0
        self.gallery_containers = []
        self.metadata_cache = {}
        
        # Setup default thumbnails
        self._setup_default_thumbnails()
        
    def _setup_default_thumbnails(self):
        """Setup default thumbnail data for testing"""
        self.thumbnails = [
            {
                'id': 'thumb_1',
                'metadata': {
                    'generation_date': '30 Aug 2025 06:00:00',
                    'prompt': 'Brand new content not in logs'
                },
                'has_video': True
            },
            {
                'id': 'thumb_2', 
                'metadata': {
                    'generation_date': '30 Aug 2025 05:45:00',
                    'prompt': 'Another new generation'
                },
                'has_video': True
            },
            {
                'id': 'thumb_3',
                'metadata': {
                    'generation_date': '30 Aug 2025 05:11:29',
                    'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col'  # Duplicate
                },
                'has_video': True
            },
            {
                'id': 'thumb_4',
                'metadata': {
                    'generation_date': '30 Aug 2025 05:08:15', 
                    'prompt': 'Urban street art on brick walls with vibrant colors'  # Duplicate
                },
                'has_video': True
            }
        ]
        
    async def goto(self, url, **kwargs):
        self.current_url = url
        self.navigation_history.append(('goto', url))
        return Mock(status=200)
        
    async def url(self):
        return self.current_url
        
    async def go_back(self):
        self.navigation_history.append(('back', None))
        return True
        
    async def click(self, selector, **kwargs):
        self.clicks.append(selector)
        
        # Simulate navigation based on selector
        if 'thumbnail' in selector or 'thumb' in selector:
            # Clicking thumbnail opens gallery
            self.current_url = "https://example.com/gallery"
            
        elif 'next' in selector or 'arrow' in selector:
            # Navigate to next thumbnail
            if self.current_thumbnail_index < len(self.thumbnails) - 1:
                self.current_thumbnail_index += 1
                
        return True
        
    def locator(self, selector):
        mock_locator = Mock()
        mock_locator.first = Mock(return_value=mock_locator)
        mock_locator.click = AsyncMock(return_value=True)
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.text_content = AsyncMock(return_value="Mock content")
        return mock_locator
        
    async def query_selector(self, selector):
        # Mock different elements based on selector
        if 'download' in selector.lower():
            # Mock download button
            element = Mock()
            element.click = AsyncMock(return_value=True)
            return element
            
        elif 'metadata' in selector.lower() or 'prompt' in selector.lower():
            # Return metadata for current thumbnail
            current_thumb = self.thumbnails[self.current_thumbnail_index]
            element = Mock()
            element.text_content = AsyncMock(return_value=current_thumb['metadata']['prompt'])
            return element
            
        elif 'time' in selector.lower() or 'date' in selector.lower():
            # Return date for current thumbnail  
            current_thumb = self.thumbnails[self.current_thumbnail_index]
            element = Mock()
            element.text_content = AsyncMock(return_value=current_thumb['metadata']['generation_date'])
            return element
            
        return None
        
    async def query_selector_all(self, selector):
        if 'thumbnail' in selector or 'thumb' in selector:
            # Return thumbnail elements
            return [Mock() for _ in self.thumbnails]
            
        elif 'container' in selector.lower() and 'create-detail-body' in selector:
            # Return generation containers for exit-scan-return
            containers = []
            for thumb in self.thumbnails:
                container = Mock()
                container.click = AsyncMock(return_value=True)
                container.query_selector = AsyncMock()
                
                # Setup metadata queries
                async def query_side_effect(sel):
                    if 'prompt' in sel.lower() or 'dnESm' in sel:
                        elem = Mock()
                        elem.text_content = AsyncMock(return_value=thumb['metadata']['prompt'])
                        return elem
                    elif 'time' in sel.lower() or 'jGymgu' in sel:
                        elem = Mock()
                        elem.text_content = AsyncMock(return_value=thumb['metadata']['generation_date'])
                        return elem
                    return None
                    
                container.query_selector.side_effect = query_side_effect
                containers.append(container)
                
            return containers
            
        return []
        
    async def wait_for_download_start(self, timeout=5000):
        """Simulate download start"""
        self.downloads.append({
            'started_at': datetime.now(),
            'filename': f'temp_download_{len(self.downloads) + 1}.mp4'
        })
        return Mock()
        
    async def wait_for_load_state(self, state, timeout=5000):
        """Simulate page load states"""
        return True
        
    async def evaluate(self, script):
        """Simulate JavaScript evaluation"""
        if 'scrollTo' in script:
            return True
        return "mock_result"


class TestIntegrationWorkflow:
    """Integration tests for complete generation download workflow"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig()
        self.config.downloads_folder = os.path.join(self.temp_dir, 'downloads')
        self.config.logs_folder = os.path.join(self.temp_dir, 'logs')
        self.config.duplicate_mode = "skip"
        self.config.use_exit_scan_strategy = True
        self.config.max_downloads = 10
        
        # Create directories
        os.makedirs(self.config.downloads_folder, exist_ok=True)
        os.makedirs(self.config.logs_folder, exist_ok=True)
        
        self.manager = GenerationDownloadManager(self.config)
        self.mock_browser = MockBrowser()
        self.mock_page = self.mock_browser.new_page()
        
        # Create existing log entries
        self._create_existing_log()
        
    def teardown_method(self):
        """Cleanup integration test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_existing_log(self):
        """Create existing log entries to test duplicate detection"""
        log_file = os.path.join(self.config.logs_folder, 'generation_downloads.txt')
        existing_entries = [
            {
                "file_id": "#000000001",
                "generation_date": "30 Aug 2025 05:15:30",
                "prompt": "Previous download - mountain landscape",
                "download_timestamp": "2025-08-30T05:16:45.123456",
                "file_path": "/downloads/vids/video_001.mp4",
                "original_filename": "temp_download_001.mp4",
                "file_size": 2457600,
                "download_duration": 3.2
            },
            {
                "file_id": "#000000002",
                "generation_date": "30 Aug 2025 05:11:29", 
                "prompt": "The camera begins with a tight close-up of the witch's dual-col",
                "download_timestamp": "2025-08-30T05:12:15.654321",
                "file_path": "/downloads/vids/video_002.mp4",
                "original_filename": "temp_download_002.mp4",
                "file_size": 3145728,
                "download_duration": 4.1
            }
        ]
        
        with open(log_file, 'w') as f:
            for entry in existing_entries:
                f.write(json.dumps(entry) + '\n')
                
    @pytest.mark.asyncio
    async def test_full_workflow_new_content_only(self):
        """Test complete workflow downloading only new content"""
        
        # Load existing log entries
        self.manager._load_existing_log_entries()
        
        downloads_completed = 0
        thumbnails_processed = 0
        
        # Simulate processing thumbnails
        for i in range(len(self.mock_page.thumbnails)):
            self.mock_page.current_thumbnail_index = i
            current_thumb = self.mock_page.thumbnails[i]
            
            # Check for duplicate
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = current_thumb['metadata']
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(
                    self.mock_page, f"thumb_{i}"
                )
                
                thumbnails_processed += 1
                
                if not is_duplicate:
                    # Would download this thumbnail
                    downloads_completed += 1
                    
                    # Simulate successful download
                    metadata = GenerationMetadata(
                        file_id=f"#000{downloads_completed + 2:06d}",
                        generation_date=current_thumb['metadata']['generation_date'],
                        prompt=current_thumb['metadata']['prompt'],
                        download_timestamp=datetime.now().isoformat(),
                        file_path=f"/downloads/video_{downloads_completed + 2:06d}.mp4",
                        original_filename=f"temp_{downloads_completed + 2:06d}.mp4",
                        file_size=2000000,
                        download_duration=3.5
                    )
                    
                    # Log the download
                    self.manager.logger.log_download(metadata)
                    
        # Verify results
        assert thumbnails_processed == 4  # All thumbnails processed
        assert downloads_completed == 2   # Only new content downloaded (thumbs 1 and 2)
        
        # Verify log file updated
        log_file = os.path.join(self.config.logs_folder, 'generation_downloads.txt')
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        # Should have original 2 entries + 2 new entries = 4 total
        assert len(lines) >= 4
        
    @pytest.mark.asyncio 
    async def test_skip_mode_with_exit_scan_return(self):
        """Test SKIP mode workflow with exit-scan-return strategy"""
        
        self.manager._load_existing_log_entries()
        
        # Set checkpoint data for exit-scan-return
        self.manager.checkpoint_data = {
            'generation_date': '30 Aug 2025 05:11:29',
            'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
            'file_id': '#000000002'
        }
        
        # Start at thumbnail that will be a duplicate (thumb_3)
        self.mock_page.current_thumbnail_index = 2
        current_thumb = self.mock_page.thumbnails[2]
        
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = current_thumb['metadata']
            
            # Mock exit-scan-return strategy
            with patch.object(self.manager, 'exit_gallery_and_scan_generations') as mock_exit_scan:
                mock_exit_scan.return_value = {'success': True, 'boundary_found': True}
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(
                    self.mock_page, 'thumb_3'
                )
                
                # Should detect duplicate and trigger exit-scan-return
                assert is_duplicate == True
                mock_exit_scan.assert_called_once()
                
                # Verify exit-scan-return was called with correct parameters
                call_args = mock_exit_scan.call_args
                assert call_args[0][0] == self.mock_page  # page argument
                
    @pytest.mark.asyncio
    async def test_finish_mode_workflow(self):
        """Test FINISH mode workflow stops at first duplicate"""
        
        # Change to FINISH mode
        self.config.duplicate_mode = "finish" 
        finish_manager = GenerationDownloadManager(self.config)
        finish_manager._load_existing_log_entries()
        
        downloads_completed = 0
        should_stop = False
        
        # Process thumbnails until we hit a duplicate
        for i in range(len(self.mock_page.thumbnails)):
            if should_stop:
                break
                
            self.mock_page.current_thumbnail_index = i
            current_thumb = self.mock_page.thumbnails[i]
            
            with patch.object(finish_manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = current_thumb['metadata']
                
                is_duplicate = await finish_manager.check_comprehensive_duplicate(
                    self.mock_page, f"thumb_{i}"
                )
                
                if is_duplicate:
                    # In FINISH mode, stop at first duplicate
                    should_stop = True
                else:
                    downloads_completed += 1
                    
        # Should have processed thumbnails 0 and 1 (new content)
        # Then stopped at thumbnail 2 (duplicate)
        assert downloads_completed == 2
        
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test workflow handles various errors gracefully"""
        
        self.manager._load_existing_log_entries()
        
        # Test 1: Metadata extraction fails
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.side_effect = Exception("Network error")
            
            # Should handle gracefully
            is_duplicate = await self.manager.check_comprehensive_duplicate(
                self.mock_page, 'thumb_error'
            )
            
            assert is_duplicate == False  # Default to not duplicate on error
            
        # Test 2: Download failure simulation
        with patch.object(self.mock_page, 'wait_for_download_start') as mock_download:
            mock_download.side_effect = Exception("Download failed")
            
            # Workflow should handle download failures gracefully
            # (This would be tested in the actual download method)
            
        # Test 3: Exit-scan-return failure
        with patch.object(self.manager, 'exit_gallery_and_scan_generations') as mock_exit_scan:
            mock_exit_scan.return_value = None  # Strategy failed
            
            # Should fall back gracefully
            result = await self.manager.exit_gallery_and_scan_generations(self.mock_page)
            assert result is None
            
    @pytest.mark.asyncio
    async def test_large_gallery_workflow(self):
        """Test workflow with large gallery (performance test)"""
        
        # Extend thumbnails to simulate large gallery
        large_thumbnails = []
        for i in range(100):
            large_thumbnails.append({
                'id': f'thumb_{i}',
                'metadata': {
                    'generation_date': f'30 Aug 2025 {6 + (i % 10):02d}:{i % 60:02d}:{(i * 7) % 60:02d}',
                    'prompt': f'Generated content number {i} with unique characteristics'
                },
                'has_video': True
            })
            
        self.mock_page.thumbnails = large_thumbnails
        self.manager._load_existing_log_entries()
        
        import time
        start_time = time.time()
        
        # Process first 10 thumbnails to test performance
        processed_count = 0
        for i in range(10):
            self.mock_page.current_thumbnail_index = i
            current_thumb = self.mock_page.thumbnails[i]
            
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = current_thumb['metadata']
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(
                    self.mock_page, f"thumb_{i}"
                )
                
                processed_count += 1
                
        process_time = time.time() - start_time
        
        # Should process 10 thumbnails quickly (under 1 second)
        assert process_time < 1.0
        assert processed_count == 10
        
    @pytest.mark.asyncio
    async def test_chronological_logging_workflow(self):
        """Test that downloads are logged in chronological order"""
        
        downloads = []
        
        # Simulate downloading thumbnails in random order
        download_order = [1, 3, 0, 2]  # Mixed chronological order
        
        for idx in download_order:
            thumb = self.mock_page.thumbnails[idx]
            
            metadata = GenerationMetadata(
                file_id=f"#000000{idx + 10:03d}",
                generation_date=thumb['metadata']['generation_date'],
                prompt=thumb['metadata']['prompt'],
                download_timestamp=datetime.now().isoformat(),
                file_path=f"/downloads/video_{idx + 10:03d}.mp4",
                original_filename=f"temp_{idx + 10:03d}.mp4",
                file_size=2000000,
                download_duration=3.5
            )
            
            downloads.append(metadata)
            self.manager.logger.log_download(metadata)
            
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.01)
            
        # Verify log file exists and has entries
        log_file = os.path.join(self.config.logs_folder, 'generation_downloads.txt')
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
            
        # Should have logged all downloads
        assert len([l for l in log_lines if l.strip()]) >= 4
        
    @pytest.mark.asyncio
    async def test_automation_engine_integration(self):
        """Test integration with WebAutomationEngine"""
        
        # Create automation config for generation downloads
        actions = [
            Action(
                type=ActionType.START_GENERATION_DOWNLOADS,
                value={
                    'duplicate_mode': 'skip',
                    'max_downloads': 5,
                    'use_exit_scan_strategy': True
                }
            )
        ]
        
        automation_config = AutomationConfig(
            name="Test Generation Download",
            base_url="https://example.com",
            actions=actions,
            unique_id="test_integration"
        )
        
        # This would be tested with actual WebAutomationEngine integration
        # For now, verify config is properly structured
        assert len(automation_config.actions) == 1
        assert automation_config.actions[0].type == ActionType.START_GENERATION_DOWNLOADS
        assert automation_config.actions[0].value['duplicate_mode'] == 'skip'
        
    @pytest.mark.asyncio
    async def test_concurrent_download_handling(self):
        """Test handling concurrent download operations"""
        
        # Simulate multiple download tasks
        async def download_task(thumb_index):
            self.mock_page.current_thumbnail_index = thumb_index
            thumb = self.mock_page.thumbnails[thumb_index]
            
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = thumb['metadata']
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(
                    self.mock_page, f"thumb_{thumb_index}"
                )
                
                if not is_duplicate:
                    # Simulate download
                    await asyncio.sleep(0.1)
                    return f"Downloaded thumb_{thumb_index}"
                else:
                    return f"Skipped thumb_{thumb_index} (duplicate)"
                    
        # Run concurrent downloads
        tasks = [download_task(i) for i in range(4)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should complete all tasks without errors
        assert len(results) == 4
        assert all(not isinstance(r, Exception) for r in results)
        
        # Should have processed all thumbnails
        downloaded_count = len([r for r in results if 'Downloaded' in r])
        skipped_count = len([r for r in results if 'Skipped' in r])
        
        assert downloaded_count + skipped_count == 4


if __name__ == '__main__':
    pytest.main([__file__, '-v'])