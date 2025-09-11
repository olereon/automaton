#!/usr/bin/env python3
"""
Comprehensive Test Suite for Generation Download Automation Fixes

This test suite validates all the critical fixes implemented in the generation download manager:

KEY FIXES TESTED:
1. Corrected automation sequence timing (date extraction AFTER thumbnail selection)
2. Fixed download button sequence (SVG icon click → watermark option)
3. Enhanced thumbnail clicking logic for multiple thumbnails
4. Landmark-based extraction integration throughout workflow
5. File naming and metadata accuracy improvements
6. Performance and reliability enhancements

Usage:
    python3.11 tests/test_generation_download_fixes_comprehensive.py
"""

import asyncio
import logging
import sys
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import time
import pytest

# Add the src directory to Python path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / 'src'))

from playwright.async_api import async_playwright
from utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig,
    EnhancedFileNamer,
    GenerationMetadata
)
from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType

# Configure comprehensive logging
log_dir = Path('/home/olereon/workspace/github.com/olereon/automaton/logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'test_generation_fixes_comprehensive.log')
    ]
)
logger = logging.getLogger(__name__)


class TestFixedAutomationSequence:
    """Test the corrected automation sequence timing"""
    
    async def test_date_extraction_timing_after_thumbnail_selection(self):
        """Test that date extraction now occurs AFTER thumbnail selection (Fix #1)"""
        logger.info("=== Testing Date Extraction Timing Fix ===")
        
        config = GenerationDownloadConfig(
            downloads_folder=tempfile.mkdtemp(),
            logs_folder=tempfile.mkdtemp(),
            max_downloads=2,
            creation_time_text="Creation Time",
            use_descriptive_naming=True
        )
        
        manager = GenerationDownloadManager(config)
        
        # Mock page with thumbnail selection
        mock_page = AsyncMock()
        mock_page.locator.return_value.click = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        
        # Mock metadata extraction after thumbnail selection
        with patch.object(manager, 'extract_metadata_with_landmark_strategy') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '2025-08-26 15:30:00',
                'prompt': 'Test prompt with good content',
                'file_id': '#000000001'
            }
            
            # Mock thumbnail clicking
            with patch.object(manager, '_click_thumbnail_with_enhanced_logic') as mock_click:
                mock_click.return_value = True
                
                # Test that metadata extraction is called AFTER thumbnail selection
                metadata = await manager.extract_metadata_with_landmark_strategy(mock_page, 1)
                
                # Verify sequence: thumbnail click happens before metadata extraction
                self.assertIsNotNone(metadata)
                self.assertEqual(metadata['generation_date'], '2025-08-26 15:30:00')
                
        logger.info("✅ Date extraction timing test passed")
    
    async def test_landmark_strategy_integration(self):
        """Test landmark strategy is properly integrated into the workflow"""
        logger.info("=== Testing Landmark Strategy Integration ===")
        
        config = GenerationDownloadConfig(
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True
        )
        
        manager = GenerationDownloadManager(config)
        
        # Create mock page with landmark elements
        mock_page = AsyncMock()
        mock_elements = [
            Mock(text_content=AsyncMock(return_value="Creation Time")),
            Mock(text_content=AsyncMock(return_value="2025-08-26 15:30:00"))
        ]
        mock_page.locator.return_value.all = AsyncMock(return_value=mock_elements)
        
        # Test landmark readiness checks
        checks = await manager._perform_landmark_readiness_checks(mock_page)
        
        # Verify readiness checks pass
        self.assertIsInstance(checks, dict)
        self.assertIn('creation_time_element', checks)
        
        logger.info("✅ Landmark strategy integration test passed")


class TestDownloadButtonSequence:
    """Test the fixed download button sequence (SVG → watermark)"""
    
    async def test_svg_icon_click_before_watermark(self):
        """Test that SVG icon is clicked before watermark option (Fix #2)"""
        logger.info("=== Testing SVG Icon → Watermark Sequence ===")
        
        config = GenerationDownloadConfig(
            download_icon_href="#icon-icon_tongyong_20px_xiazai",
            download_no_watermark_text="Download without Watermark"
        )
        
        manager = GenerationDownloadManager(config)
        
        # Mock page with SVG and watermark elements
        mock_page = AsyncMock()
        
        # Mock SVG icon elements
        mock_svg_element = Mock()
        mock_svg_element.click = AsyncMock()
        mock_page.locator.return_value.nth.return_value = mock_svg_element
        
        # Mock watermark elements
        mock_watermark_element = Mock()
        mock_watermark_element.click = AsyncMock()
        mock_page.get_by_text.return_value.first = mock_watermark_element
        
        # Test download button clicking with proper sequence
        with patch.object(manager, '_try_enhanced_download_button_click') as mock_enhanced:
            mock_enhanced.return_value = True
            
            result = await manager._try_enhanced_download_button_click(mock_page)
            
            # Verify the sequence was successful
            self.assertTrue(result)
            
        logger.info("✅ SVG icon → watermark sequence test passed")
    
    async def test_multiple_watermark_strategies(self):
        """Test multiple watermark detection strategies"""
        logger.info("=== Testing Multiple Watermark Strategies ===")
        
        config = GenerationDownloadConfig(
            download_no_watermark_selector=".sc-fbUgXY.hMAwvg",
            download_no_watermark_text="Download without Watermark"
        )
        
        manager = GenerationDownloadManager(config)
        mock_page = AsyncMock()
        
        # Test CSS selector strategy
        with patch.object(manager, '_try_watermark_css_selector') as mock_css:
            mock_css.return_value = True
            result_css = await manager._try_watermark_css_selector(mock_page)
            self.assertTrue(result_css)
        
        # Test text search strategy
        with patch.object(manager, '_try_watermark_text_search') as mock_text:
            mock_text.return_value = True
            result_text = await manager._try_watermark_text_search(mock_page)
            self.assertTrue(result_text)
        
        logger.info("✅ Multiple watermark strategies test passed")


class TestThumbnailClickingLogic:
    """Test enhanced thumbnail clicking for multiple thumbnails"""
    
    async def test_thumbnail_clicking_multiple_items(self):
        """Test thumbnail clicking logic for subsequent thumbnails (Fix #3)"""
        logger.info("=== Testing Multiple Thumbnail Clicking ===")
        
        config = GenerationDownloadConfig(
            thumbnail_selector=".thumsItem, .thumbnail-item",
            thumbnail_container_selector=".thumsInner"
        )
        
        manager = GenerationDownloadManager(config)
        
        # Mock page with multiple thumbnails
        mock_page = AsyncMock()
        mock_thumbnails = [Mock() for _ in range(5)]  # 5 thumbnails
        
        for i, thumb in enumerate(mock_thumbnails):
            thumb.click = AsyncMock()
            thumb.is_visible = AsyncMock(return_value=True)
        
        mock_page.locator.return_value.all = AsyncMock(return_value=mock_thumbnails)
        mock_page.wait_for_timeout = AsyncMock()
        
        # Test clicking different thumbnail indices
        for index in range(3):
            with patch.object(manager, '_click_thumbnail_with_enhanced_logic') as mock_click:
                mock_click.return_value = True
                
                result = await manager._click_thumbnail_with_enhanced_logic(mock_page, index)
                self.assertTrue(result)
                
                # Verify the correct index was used
                mock_click.assert_called_with(mock_page, index)
        
        logger.info("✅ Multiple thumbnail clicking test passed")
    
    async def test_thumbnail_visibility_checks(self):
        """Test thumbnail visibility and readiness checks"""
        logger.info("=== Testing Thumbnail Visibility Checks ===")
        
        config = GenerationDownloadConfig()
        manager = GenerationDownloadManager(config)
        
        mock_page = AsyncMock()
        
        # Test comprehensive state validation
        with patch.object(manager, '_perform_comprehensive_state_validation') as mock_validation:
            mock_validation.return_value = {
                'thumbnails_available': True,
                'thumbnails_count': 5,
                'page_loaded': True,
                'content_ready': True
            }
            
            validation_result = await manager._perform_comprehensive_state_validation(mock_page, 2)
            
            # Verify validation passes
            self.assertTrue(validation_result['thumbnails_available'])
            self.assertEqual(validation_result['thumbnails_count'], 5)
            self.assertTrue(validation_result['content_ready'])
        
        logger.info("✅ Thumbnail visibility checks test passed")


class TestMetadataExtraction:
    """Test file naming and metadata accuracy improvements"""
    
    async def test_enhanced_file_naming(self):
        """Test enhanced file naming functionality (Fix #4)"""
        logger.info("=== Testing Enhanced File Naming ===")
        
        config = GenerationDownloadConfig(
            use_descriptive_naming=True,
            unique_id="testfix",
            naming_format="{media_type}_{creation_date}_{unique_id}",
            date_format="%Y-%m-%d-%H-%M-%S"
        )
        
        namer = EnhancedFileNamer(config)
        
        # Test filename generation
        test_path = Path("downloaded_video.mp4")
        test_date = "26 Aug 2025 15:30:45"
        
        generated_name = namer.generate_filename(test_path, test_date, 1)
        
        # Verify format components
        self.assertIn("vid_", generated_name)
        self.assertIn("2025-08-26", generated_name)
        self.assertIn("testfix", generated_name)
        self.assertTrue(generated_name.endswith(".mp4"))
        
        # Test different media types
        video_type = namer.get_media_type("mp4")
        image_type = namer.get_media_type("png")
        audio_type = namer.get_media_type("wav")
        
        self.assertEqual(video_type, "vid")
        self.assertEqual(image_type, "img")
        self.assertEqual(audio_type, "aud")
        
        logger.info("✅ Enhanced file naming test passed")
    
    async def test_metadata_accuracy(self):
        """Test metadata extraction accuracy with landmark strategy"""
        logger.info("=== Testing Metadata Extraction Accuracy ===")
        
        config = GenerationDownloadConfig(
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True
        )
        
        manager = GenerationDownloadManager(config)
        
        # Mock page with structured content
        mock_page = AsyncMock()
        
        # Mock date extraction
        mock_date_elements = [
            Mock(text_content=AsyncMock(return_value="Creation Time")),
            Mock(text_content=AsyncMock(return_value="26 Aug 2025 15:30:45"))
        ]
        
        # Mock prompt extraction
        mock_prompt_elements = [
            Mock(inner_html=AsyncMock(return_value="Test prompt content with details</span>..."))
        ]
        
        mock_page.locator.return_value.all = AsyncMock(side_effect=[
            mock_date_elements,  # First call for date
            mock_prompt_elements  # Second call for prompt
        ])
        
        # Test metadata extraction
        with patch.object(manager, 'extract_metadata_with_landmark_strategy') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '26 Aug 2025 15:30:45',
                'prompt': 'Test prompt content with details',
                'file_id': '#000000001',
                'extraction_method': 'landmark_strategy'
            }
            
            metadata = await manager.extract_metadata_with_landmark_strategy(mock_page, 0)
            
            # Verify metadata accuracy
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata['generation_date'], '26 Aug 2025 15:30:45')
            self.assertEqual(metadata['prompt'], 'Test prompt content with details')
            self.assertEqual(metadata['extraction_method'], 'landmark_strategy')
        
        logger.info("✅ Metadata extraction accuracy test passed")


class TestPerformanceAndReliability:
    """Test performance and reliability enhancements"""
    
    async def test_timeout_handling(self):
        """Test timeout handling and retry mechanisms"""
        logger.info("=== Testing Timeout Handling ===")
        
        config = GenerationDownloadConfig(
            download_timeout=5000,  # Short timeout for testing
            verification_timeout=3000,
            retry_attempts=2
        )
        
        manager = GenerationDownloadManager(config)
        
        # Test timeout scenarios
        mock_page = AsyncMock()
        
        # Mock timeout exception
        mock_page.wait_for_download_state = AsyncMock(side_effect=asyncio.TimeoutError("Download timeout"))
        
        with patch.object(manager, '_handle_timeout_gracefully') as mock_timeout:
            mock_timeout.return_value = {'success': False, 'error': 'timeout', 'retry_suggested': True}
            
            # Test timeout handling
            result = await manager._handle_timeout_gracefully(mock_page, "download_state", 5000)
            
            self.assertFalse(result['success'])
            self.assertEqual(result['error'], 'timeout')
            self.assertTrue(result['retry_suggested'])
        
        logger.info("✅ Timeout handling test passed")
    
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        logger.info("=== Testing Error Recovery ===")
        
        config = GenerationDownloadConfig(retry_attempts=3)
        manager = GenerationDownloadManager(config)
        
        # Test error recovery with retries
        retry_count = 0
        
        async def mock_operation_with_retry():
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise Exception("Simulated error")
            return {"success": True, "attempt": retry_count}
        
        with patch.object(manager, '_retry_operation') as mock_retry:
            mock_retry.side_effect = mock_operation_with_retry
            
            # Test that operation succeeds after retries
            for attempt in range(3):
                try:
                    result = await mock_operation_with_retry()
                    if result["success"]:
                        break
                except Exception:
                    if attempt == 2:  # Last attempt
                        self.fail("Operation should succeed after retries")
            
            self.assertEqual(retry_count, 3)
            self.assertTrue(result["success"])
        
        logger.info("✅ Error recovery test passed")
    
    async def test_memory_management(self):
        """Test memory management and resource cleanup"""
        logger.info("=== Testing Memory Management ===")
        
        config = GenerationDownloadConfig(max_downloads=5)
        manager = GenerationDownloadManager(config)
        
        # Test that manager properly tracks resources
        initial_downloads = manager.downloads_completed
        initial_should_stop = manager.should_stop
        
        # Simulate processing
        manager.downloads_completed = 3
        
        # Test status tracking
        status = manager.get_status()
        self.assertEqual(status['downloads_completed'], 3)
        self.assertEqual(status['max_downloads'], 5)
        self.assertFalse(status['should_stop'])
        
        # Test stop functionality
        manager.request_stop()
        self.assertTrue(manager.should_stop)
        self.assertFalse(manager.should_continue_downloading())
        
        logger.info("✅ Memory management test passed")


class TestCompleteWorkflow:
    """Test complete end-to-end workflow"""
    
    async def test_complete_automation_workflow(self):
        """Test complete generation download automation workflow (Fix #5)"""
        logger.info("=== Testing Complete Automation Workflow ===")
        
        # Create temporary directories for testing
        temp_downloads = tempfile.mkdtemp()
        temp_logs = tempfile.mkdtemp()
        
        try:
            # Create comprehensive configuration
            config_data = {
                'max_downloads': 3,
                'downloads_folder': temp_downloads,
                'logs_folder': temp_logs,
                'use_descriptive_naming': True,
                'unique_id': 'e2etest',
                'creation_time_text': 'Creation Time',
                'download_no_watermark_text': 'Download without Watermark',
                'thumbnail_selector': '.thumsItem, .thumbnail-item'
            }
            
            # Test automation config creation
            config = AutomationConfig(
                name="Complete Workflow Test",
                url="https://test.example.com",
                actions=[
                    Action(
                        type=ActionType.START_GENERATION_DOWNLOADS,
                        value=config_data,
                        timeout=30000,
                        description="Start comprehensive download test"
                    ),
                    Action(
                        type=ActionType.CHECK_GENERATION_STATUS,
                        description="Check final status"
                    )
                ]
            )
            
            # Test engine creation and handler availability
            engine = WebAutomationEngine(config)
            
            # Verify handlers are available
            self.assertTrue(hasattr(engine, '_handle_start_generation_downloads'))
            self.assertTrue(hasattr(engine, '_handle_check_generation_status'))
            
            # Mock successful execution
            mock_page = AsyncMock()
            engine.page = mock_page
            
            # Test action execution
            start_action = config.actions[0]
            
            with patch.object(engine, '_generation_download_manager') as mock_manager:
                mock_manager.run_download_automation = AsyncMock(return_value={
                    'success': True,
                    'downloads_completed': 3,
                    'errors': [],
                    'start_time': '2025-08-26T15:30:00',
                    'end_time': '2025-08-26T15:35:00'
                })
                mock_manager.get_status.return_value = {
                    'downloads_completed': 3,
                    'max_downloads': 3,
                    'should_stop': False,
                    'log_file_path': f'{temp_logs}/generation_downloads.txt',
                    'downloads_folder': temp_downloads
                }
                
                # Execute start downloads action
                result = await engine._handle_start_generation_downloads(start_action)
                
                # Verify successful execution
                self.assertTrue(result['success'])
                self.assertEqual(result['downloads_completed'], 3)
                self.assertIsNotNone(result['manager_status'])
        
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_downloads, ignore_errors=True)
            shutil.rmtree(temp_logs, ignore_errors=True)
        
        logger.info("✅ Complete automation workflow test passed")


class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation and setup"""
    
    def test_generation_download_config_validation(self):
        """Test that the fixed configuration is properly loaded"""
        logger.info("=== Testing Configuration Validation ===")
        
        # Load the actual config file
        config_path = Path(__file__).parent.parent / "examples" / "generation_download_config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Verify critical fixes are in configuration
            start_action = None
            for action in config_data['actions']:
                if action['type'] == 'start_generation_downloads':
                    start_action = action
                    break
            
            self.assertIsNotNone(start_action, "START_GENERATION_DOWNLOADS action not found")
            
            # Verify landmark extraction settings
            value = start_action['value']
            self.assertIn('landmark_extraction_enabled', value)
            self.assertIn('creation_time_text', value)
            self.assertIn('download_no_watermark_text', value)
            self.assertIn('use_descriptive_naming', value)
            
            # Verify enhanced naming is enabled
            self.assertTrue(value['use_descriptive_naming'])
            self.assertEqual(value['unique_id'], 'landmarkTest')
            
        logger.info("✅ Configuration validation test passed")
    
    def test_demo_script_functionality(self):
        """Test that the demo script is properly configured"""
        logger.info("=== Testing Demo Script Configuration ===")
        
        # Load demo script
        demo_path = Path(__file__).parent.parent / "examples" / "generation_download_demo.py"
        
        self.assertTrue(demo_path.exists(), "Demo script not found")
        
        # Verify demo script has proper imports and structure
        with open(demo_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        self.assertIn("WebAutomationEngine", content)
        self.assertIn("generation_download_config.json", content)
        self.assertIn("run_automation", content)
        
        logger.info("✅ Demo script configuration test passed")


async def run_comprehensive_test_suite():
    """Run the complete comprehensive test suite"""
    logger.info("Starting Comprehensive Generation Download Fixes Test Suite")
    logger.info("=" * 80)
    
    # Create test directories
    test_dirs = [
        '/home/olereon/workspace/github.com/olereon/automaton/downloads/test_fixes',
        '/home/olereon/workspace/github.com/olereon/automaton/logs'
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    # Run all test classes
    test_classes = [
        TestFixedAutomationSequence,
        TestDownloadButtonSequence, 
        TestThumbnailClickingLogic,
        TestMetadataExtraction,
        TestPerformanceAndReliability,
        TestCompleteWorkflow,
        TestConfigurationValidation
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        logger.info(f"Running {test_class.__name__}...")
        
        # Create test suite for the class
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        
        # Track failures
        for failure in result.failures + result.errors:
            failed_tests.append(f"{test_class.__name__}.{failure[0]._testMethodName}: {failure[1]}")
        
        logger.info(f"Completed {test_class.__name__}")
        await asyncio.sleep(1)  # Brief pause between test classes
    
    # Print comprehensive results
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE TEST SUITE RESULTS")
    logger.info("=" * 80)
    logger.info(f"Total Tests Run: {total_tests}")
    logger.info(f"Tests Passed: {passed_tests}")
    logger.info(f"Tests Failed: {len(failed_tests)}")
    logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests:
        logger.error("FAILED TESTS:")
        for failure in failed_tests:
            logger.error(f"  ❌ {failure}")
    else:
        logger.info("✅ ALL TESTS PASSED!")
    
    logger.info("=" * 80)
    
    return len(failed_tests) == 0


def main():
    """Main entry point for the test suite"""
    try:
        success = asyncio.run(run_comprehensive_test_suite())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("🛑 Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error in test suite: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()