#!/usr/bin/env python3
"""
Test Enhanced Generation Download Algorithm
Tests the new 25-step algorithm implementation and chronological logging features.
"""

import unittest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig, 
    DuplicateMode,
    GenerationDownloadLogger
)


class TestEnhancedAlgorithm(unittest.TestCase):
    """Test the enhanced generation download algorithm"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_downloads = os.path.join(self.temp_dir, "downloads")
        self.temp_logs = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.temp_downloads, exist_ok=True)
        os.makedirs(self.temp_logs, exist_ok=True)
        
        # Create test configuration
        self.config = GenerationDownloadConfig(
            downloads_folder=self.temp_downloads,
            logs_folder=self.temp_logs,
            max_downloads=5,
            duplicate_mode=DuplicateMode.SKIP
        )
        
    def test_environment_validation(self):
        """Test environment validation functionality"""
        manager = GenerationDownloadManager(self.config)
        
        # Test validation
        result = asyncio.run(manager._validate_download_environment())
        self.assertTrue(result)
        
        # Check directories were created
        self.assertTrue(os.path.exists(self.temp_downloads))
        self.assertTrue(os.path.exists(self.temp_logs))
        
    def test_chronological_logging_initialization(self):
        """Test chronological logging system initialization"""
        logger = GenerationDownloadLogger(self.config)
        
        # Check initialization
        self.assertTrue(hasattr(logger, 'use_chronological_ordering'))
        self.assertTrue(logger.use_chronological_ordering)
        self.assertEqual(logger.placeholder_id, "#999999999")
        self.assertTrue(logger.support_enhanced_skip_mode)
        
    def test_placeholder_id_generation(self):
        """Test placeholder ID generation for new entries"""
        logger = GenerationDownloadLogger(self.config)
        
        # Test placeholder generation
        file_id = logger.get_next_file_id()
        self.assertEqual(file_id, "#999999999")
        
    def test_enhanced_skip_mode_initialization(self):
        """Test Enhanced SKIP mode v2 initialization"""
        manager = GenerationDownloadManager(self.config)
        
        # Test SKIP mode initialization
        skip_active = manager._initialize_enhanced_skip_mode_v2()
        self.assertTrue(skip_active)
        self.assertTrue(hasattr(manager, 'enhanced_skip_v2_active'))
        
    @patch('src.utils.generation_download_manager.logger')
    def test_algorithm_step_logging(self, mock_logger):
        """Test that algorithm steps are properly logged"""
        manager = GenerationDownloadManager(self.config)
        
        # Mock page object
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = [Mock(), Mock()]  # Mock thumbnails
        
        # Test step 1-7 execution
        results = asyncio.run(manager.run_download_automation_v2(mock_page))
        
        # Verify algorithm version is recorded
        self.assertEqual(results.get('algorithm_version'), '2.0')
        self.assertIsInstance(results.get('steps_completed'), list)
        
    def test_enhanced_duplicate_detection(self):
        """Test enhanced duplicate detection functionality"""
        manager = GenerationDownloadManager(self.config)
        
        # Test metadata
        metadata = {
            'generation_date': '27 Aug 2025 02:20:06',
            'prompt': 'Test prompt content'
        }
        
        # Test duplicate detection
        is_duplicate = manager._enhanced_duplicate_detection(metadata, set())
        self.assertIsInstance(is_duplicate, bool)
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestChronologicalLogging(unittest.TestCase):
    """Test chronological logging features"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_logs = os.path.join(self.temp_dir, "logs")
        os.makedirs(self.temp_logs, exist_ok=True)
        
        # Create test configuration
        self.config = GenerationDownloadConfig(
            logs_folder=self.temp_logs,
            duplicate_mode=DuplicateMode.SKIP
        )
        
    def test_logger_initialization_with_chronological_features(self):
        """Test logger initialization with enhanced features"""
        logger = GenerationDownloadLogger(self.config)
        
        # Check all enhanced features are initialized
        self.assertTrue(logger.use_chronological_ordering)
        self.assertEqual(logger.placeholder_id, "#999999999")
        self.assertTrue(logger.support_enhanced_skip_mode)
        
    def test_placeholder_id_handling(self):
        """Test handling of placeholder IDs in file generation"""
        logger = GenerationDownloadLogger(self.config)
        
        # Test multiple calls return same placeholder
        id1 = logger.get_next_file_id()
        id2 = logger.get_next_file_id() 
        
        self.assertEqual(id1, "#999999999")
        self.assertEqual(id2, "#999999999")
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    print("🧪 Running Enhanced Algorithm Tests")
    print("=" * 60)
    
    # Run specific test suites
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedAlgorithm)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestChronologicalLogging)
    
    runner = unittest.TextTestRunner(verbosity=2)
    
    print("\n📋 Testing Enhanced Algorithm...")
    result1 = runner.run(suite1)
    
    print("\n📝 Testing Chronological Logging...")
    result2 = runner.run(suite2)
    
    # Summary
    total_tests = result1.testsRun + result2.testsRun
    total_failures = len(result1.failures) + len(result2.failures)
    total_errors = len(result1.errors) + len(result2.errors)
    
    print("\n" + "=" * 60)
    print(f"🎯 TEST SUMMARY:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {total_tests - total_failures - total_errors}")
    print(f"   Failed: {total_failures}")
    print(f"   Errors: {total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        sys.exit(1)