#!/usr/bin/env python3
"""
Integration Test for Fast Generation Downloader
Tests the integration between the enhanced algorithm and fast downloader interface.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from scripts.fast_generation_downloader import FastGenerationDownloader


class TestFastDownloaderIntegration(unittest.TestCase):
    """Test integration between fast downloader and enhanced algorithm"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test configuration
        config_data = {
            "name": "Test Enhanced Algorithm",
            "url": "https://example.com",
            "headless": True,
            "actions": [
                {
                    "type": "start_generation_downloads",
                    "description": "Test enhanced download with new algorithm",
                    "value": {
                        "downloads_folder": os.path.join(self.temp_dir, "downloads"),
                        "logs_folder": os.path.join(self.temp_dir, "logs"),
                        "max_downloads": 3,
                        "duplicate_mode": "skip",
                        "duplicate_check_enabled": True,
                        "use_descriptive_naming": True
                    }
                }
            ]
        }
        
        with open(self.temp_config, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def test_fast_downloader_initialization(self):
        """Test FastGenerationDownloader initialization with new features"""
        downloader = FastGenerationDownloader(
            config_path=self.temp_config,
            duplicate_mode="skip",
            max_downloads=5
        )
        
        # Check initialization
        self.assertEqual(downloader.duplicate_mode, "skip")
        self.assertEqual(downloader.max_downloads, 5)
        self.assertIsNotNone(downloader.config_path)
        
    def test_duplicate_mode_configuration(self):
        """Test duplicate mode configuration modification"""
        downloader = FastGenerationDownloader(
            config_path=self.temp_config,
            duplicate_mode="skip"
        )
        
        # Load and modify config
        with open(self.temp_config, 'r') as f:
            config_data = json.load(f)
            
        modified_config = downloader.modify_config_for_duplicate_mode(config_data)
        
        # Check SKIP mode settings
        action = modified_config['actions'][0]
        self.assertTrue(action['value']['duplicate_check_enabled'])
        self.assertFalse(action['value']['stop_on_duplicate'])
        self.assertEqual(action['value']['duplicate_mode'], 'skip')
        self.assertTrue(action['value']['skip_duplicates'])
        
    def test_finish_mode_configuration(self):
        """Test FINISH mode configuration"""
        downloader = FastGenerationDownloader(
            config_path=self.temp_config,
            duplicate_mode="finish"
        )
        
        # Load and modify config
        with open(self.temp_config, 'r') as f:
            config_data = json.load(f)
            
        modified_config = downloader.modify_config_for_duplicate_mode(config_data)
        
        # Check FINISH mode settings
        action = modified_config['actions'][0]
        self.assertTrue(action['value']['duplicate_check_enabled'])
        self.assertTrue(action['value']['stop_on_duplicate'])
        self.assertEqual(action['value']['duplicate_mode'], 'finish')
        self.assertFalse(action['value']['skip_duplicates'])
        
    def test_start_from_parameter(self):
        """Test start_from parameter handling"""
        start_from = "03 Sep 2025 16:15:18"
        downloader = FastGenerationDownloader(
            config_path=self.temp_config,
            duplicate_mode="skip",
            start_from=start_from
        )
        
        self.assertEqual(downloader.start_from, start_from)
        
        # Load and modify config
        with open(self.temp_config, 'r') as f:
            config_data = json.load(f)
            
        modified_config = downloader.modify_config_for_duplicate_mode(config_data)
        
        # Check start_from is added
        action = modified_config['actions'][0]
        self.assertEqual(action['value']['start_from'], start_from)
        
    def test_max_downloads_override(self):
        """Test max_downloads command line override"""
        downloader = FastGenerationDownloader(
            config_path=self.temp_config,
            duplicate_mode="skip",
            max_downloads=10
        )
        
        # Load and modify config
        with open(self.temp_config, 'r') as f:
            config_data = json.load(f)
            
        modified_config = downloader.modify_config_for_duplicate_mode(config_data)
        
        # Check max_downloads is overridden
        action = modified_config['actions'][0]
        self.assertEqual(action['value']['max_downloads'], 10)
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    print("🔗 Running Fast Downloader Integration Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)