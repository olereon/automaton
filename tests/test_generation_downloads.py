#!/usr/bin/env python3
"""
Test suite for Generation Download functionality
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig,
    GenerationDownloadLogger,
    GenerationFileManager,
    GenerationMetadata
)
from core.engine import ActionType, Action, AutomationConfig, WebAutomationEngine


class TestGenerationDownloadConfig(unittest.TestCase):
    """Test GenerationDownloadConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = GenerationDownloadConfig()
        
        # Check default paths
        self.assertTrue(config.downloads_folder.endswith('downloads/vids'))
        self.assertTrue(config.logs_folder.endswith('logs'))
        
        # Check default selectors
        self.assertEqual(config.completed_task_selector, "div[id$='__8']")
        self.assertEqual(config.id_format, "#{:09d}")
        
        # Check default limits
        self.assertEqual(config.max_downloads, 50)
        self.assertEqual(config.starting_file_id, 1)
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = GenerationDownloadConfig(
            max_downloads=100,
            downloads_folder="/custom/path",
            starting_file_id=1000
        )
        
        self.assertEqual(config.max_downloads, 100)
        self.assertEqual(config.downloads_folder, "/custom/path")
        self.assertEqual(config.starting_file_id, 1000)


class TestGenerationDownloadLogger(unittest.TestCase):
    """Test GenerationDownloadLogger"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig(
            logs_folder=self.temp_dir,
            log_filename="test_downloads.txt"
        )
        self.logger = GenerationDownloadLogger(self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_next_file_id_empty_log(self):
        """Test getting next file ID when log is empty"""
        file_id = self.logger.get_next_file_id()
        self.assertEqual(file_id, "#000000001")
    
    def test_get_next_file_id_with_existing_entries(self):
        """Test getting next file ID with existing log entries"""
        # Create test log with some entries
        log_content = """#000000001
2025-08-21 03:16:29
Test prompt 1
========================================
#000000005
2025-08-21 03:17:15
Test prompt 2
========================================
"""
        with open(self.logger.log_file_path, 'w') as f:
            f.write(log_content)
        
        file_id = self.logger.get_next_file_id()
        self.assertEqual(file_id, "#000000006")
    
    def test_log_download(self):
        """Test logging a download"""
        metadata = GenerationMetadata(
            file_id="#000000001",
            generation_date="2025-08-21 03:16:29",
            prompt="Test prompt for generation",
            download_timestamp="2025-08-21 03:20:00",
            file_path="/test/path/file.mp4"
        )
        
        success = self.logger.log_download(metadata)
        self.assertTrue(success)
        
        # Verify log file content
        with open(self.logger.log_file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("#000000001", content)
        self.assertIn("2025-08-21 03:16:29", content)
        self.assertIn("Test prompt for generation", content)
        self.assertIn("=" * 40, content)
    
    def test_get_download_count(self):
        """Test getting download count"""
        # Initially should be 0
        self.assertEqual(self.logger.get_download_count(), 0)
        
        # Add some entries
        metadata1 = GenerationMetadata(
            file_id="#000000001",
            generation_date="2025-08-21 03:16:29",
            prompt="Test prompt 1",
            download_timestamp="2025-08-21 03:20:00",
            file_path="/test/path/file1.mp4"
        )
        metadata2 = GenerationMetadata(
            file_id="#000000002",
            generation_date="2025-08-21 03:17:29",
            prompt="Test prompt 2",
            download_timestamp="2025-08-21 03:21:00",
            file_path="/test/path/file2.mp4"
        )
        
        self.logger.log_download(metadata1)
        self.logger.log_download(metadata2)
        
        # Should now be 2
        self.assertEqual(self.logger.get_download_count(), 2)


class TestGenerationFileManager(unittest.TestCase):
    """Test GenerationFileManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig(downloads_folder=self.temp_dir)
        self.file_manager = GenerationFileManager(self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_downloads_directory(self):
        """Test downloads directory creation"""
        self.assertTrue(Path(self.temp_dir).exists())
    
    def test_rename_file(self):
        """Test file renaming"""
        # Create a test file
        test_file = Path(self.temp_dir) / "test_download.mp4"
        test_file.write_text("test content")
        
        # Rename it
        new_path = self.file_manager.rename_file(test_file, "#000000001")
        
        self.assertIsNotNone(new_path)
        self.assertEqual(new_path.name, "#000000001.mp4")
        self.assertTrue(new_path.exists())
        self.assertFalse(test_file.exists())
    
    def test_verify_file_valid(self):
        """Test file verification with valid file"""
        # Create a test file with content
        test_file = Path(self.temp_dir) / "test_file.mp4"
        test_file.write_text("test content")
        
        self.assertTrue(self.file_manager.verify_file(test_file))
    
    def test_verify_file_empty(self):
        """Test file verification with empty file"""
        # Create an empty file
        test_file = Path(self.temp_dir) / "empty_file.mp4"
        test_file.touch()
        
        self.assertFalse(self.file_manager.verify_file(test_file))
    
    def test_verify_file_nonexistent(self):
        """Test file verification with non-existent file"""
        test_file = Path(self.temp_dir) / "nonexistent.mp4"
        
        self.assertFalse(self.file_manager.verify_file(test_file))


class TestGenerationDownloadManager(unittest.TestCase):
    """Test GenerationDownloadManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig(
            downloads_folder=self.temp_dir,
            logs_folder=self.temp_dir,
            max_downloads=5
        )
        self.manager = GenerationDownloadManager(self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_should_continue_downloading_initial(self):
        """Test initial state allows downloading"""
        self.assertTrue(self.manager.should_continue_downloading())
    
    def test_should_continue_downloading_max_reached(self):
        """Test stopping when max downloads reached"""
        self.manager.downloads_completed = 5
        self.assertFalse(self.manager.should_continue_downloading())
    
    def test_should_continue_downloading_stop_requested(self):
        """Test stopping when stop is requested"""
        self.manager.request_stop()
        self.assertFalse(self.manager.should_continue_downloading())
    
    def test_request_stop(self):
        """Test requesting stop"""
        self.assertFalse(self.manager.should_stop)
        self.manager.request_stop()
        self.assertTrue(self.manager.should_stop)
    
    def test_get_status(self):
        """Test getting manager status"""
        status = self.manager.get_status()
        
        self.assertIn('downloads_completed', status)
        self.assertIn('current_thumbnail_index', status)
        self.assertIn('should_stop', status)
        self.assertIn('max_downloads', status)
        self.assertIn('log_file_path', status)
        self.assertIn('downloads_folder', status)
        
        self.assertEqual(status['downloads_completed'], 0)
        self.assertEqual(status['max_downloads'], 5)
        self.assertFalse(status['should_stop'])


class TestGenerationDownloadIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for generation download automation"""
    
    async def test_action_handlers_available(self):
        """Test that action handlers are properly integrated"""
        # Test with dummy config
        config = AutomationConfig(
            name="Test",
            url="https://test.com",
            actions=[]
        )
        
        engine = WebAutomationEngine(config)
        
        # Check that handlers are available
        self.assertTrue(hasattr(engine, '_handle_start_generation_downloads'))
        self.assertTrue(hasattr(engine, '_handle_stop_generation_downloads'))
        self.assertTrue(hasattr(engine, '_handle_check_generation_status'))
    
    async def test_start_generation_downloads_action(self):
        """Test START_GENERATION_DOWNLOADS action"""
        config = AutomationConfig(
            name="Test Generation Downloads",
            url="https://test.com",
            actions=[]
        )
        
        engine = WebAutomationEngine(config)
        
        # Mock page object
        mock_page = AsyncMock()
        engine.page = mock_page
        
        # Create action
        action = Action(
            type=ActionType.START_GENERATION_DOWNLOADS,
            value={
                'max_downloads': 3,
                'downloads_folder': tempfile.mkdtemp(),
                'completed_task_selector': 'div[id$="__8"]'
            },
            timeout=30000,
            description="Start generation downloads"
        )
        
        # Mock the download automation to avoid actual browser interaction
        with patch.object(engine, '_generation_download_manager') as mock_manager:
            mock_manager.run_download_automation = AsyncMock(return_value={
                'success': True,
                'downloads_completed': 3,
                'errors': [],
                'start_time': '2025-08-21T03:00:00',
                'end_time': '2025-08-21T03:05:00'
            })
            mock_manager.get_status.return_value = {
                'downloads_completed': 3,
                'max_downloads': 3
            }
            
            result = await engine._handle_start_generation_downloads(action)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['downloads_completed'], 3)


class TestGenerationDownloadActions(unittest.TestCase):
    """Test generation download action types"""
    
    def test_action_types_exist(self):
        """Test that new action types are properly defined"""
        self.assertTrue(hasattr(ActionType, 'START_GENERATION_DOWNLOADS'))
        self.assertTrue(hasattr(ActionType, 'STOP_GENERATION_DOWNLOADS'))
        self.assertTrue(hasattr(ActionType, 'CHECK_GENERATION_STATUS'))
        
        self.assertEqual(ActionType.START_GENERATION_DOWNLOADS.value, 'start_generation_downloads')
        self.assertEqual(ActionType.STOP_GENERATION_DOWNLOADS.value, 'stop_generation_downloads')
        self.assertEqual(ActionType.CHECK_GENERATION_STATUS.value, 'check_generation_status')
    
    def test_action_creation(self):
        """Test creating generation download actions"""
        # Test START_GENERATION_DOWNLOADS action
        start_action = Action(
            type=ActionType.START_GENERATION_DOWNLOADS,
            value={
                'max_downloads': 25,
                'downloads_folder': '/test/path',
                'completed_task_selector': 'div[id$="__8"]'
            },
            timeout=120000,
            description="Start generation downloads"
        )
        
        self.assertEqual(start_action.type, ActionType.START_GENERATION_DOWNLOADS)
        self.assertIsInstance(start_action.value, dict)
        self.assertEqual(start_action.value['max_downloads'], 25)
        
        # Test STOP_GENERATION_DOWNLOADS action
        stop_action = Action(
            type=ActionType.STOP_GENERATION_DOWNLOADS,
            description="Stop generation downloads"
        )
        
        self.assertEqual(stop_action.type, ActionType.STOP_GENERATION_DOWNLOADS)
        
        # Test CHECK_GENERATION_STATUS action
        status_action = Action(
            type=ActionType.CHECK_GENERATION_STATUS,
            description="Check download status"
        )
        
        self.assertEqual(status_action.type, ActionType.CHECK_GENERATION_STATUS)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)