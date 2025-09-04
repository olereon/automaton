#!/usr/bin/env python3.11
"""
Test Scroll Amount Config Fix
============================
Tests that all config files now use 2500px scroll_amount instead of 800px
"""

import pytest
import json
import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import GenerationDownloadConfig
from src.core.generation_download_handlers import GenerationDownloadHandlers


class TestScrollAmountConfigFix:
    """Test that scroll_amount config fixes are working correctly"""
    
    def test_default_config_scroll_amount(self):
        """Test that default GenerationDownloadConfig uses 2500px"""
        config = GenerationDownloadConfig()
        assert config.scroll_amount == 2500, f"Expected 2500px, got {config.scroll_amount}px"
        print("✅ DEFAULT CONFIG: scroll_amount = 2500px")
    
    def test_fast_generation_config_file(self):
        """Test that fast_generation_config.json has correct scroll_amount"""
        with open('scripts/fast_generation_config.json', 'r') as f:
            config_data = json.load(f)
        
        # Find the START_GENERATION_DOWNLOADS action
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                scroll_amount = action['value']['scroll_amount']
                assert scroll_amount == 2500, f"Expected 2500px, got {scroll_amount}px"
                print("✅ FAST CONFIG: scroll_amount = 2500px")
                break
        else:
            pytest.fail("START_GENERATION_DOWNLOADS action not found")
    
    def test_quick_test_config_file(self):
        """Test that quick_test_config.json has correct scroll_amount"""
        with open('scripts/quick_test_config.json', 'r') as f:
            config_data = json.load(f)
        
        # Find the START_GENERATION_DOWNLOADS action
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                scroll_amount = action['value']['scroll_amount']
                assert scroll_amount == 2500, f"Expected 2500px, got {scroll_amount}px"
                print("✅ QUICK TEST CONFIG: scroll_amount = 2500px")
                break
        else:
            pytest.fail("START_GENERATION_DOWNLOADS action not found")
    
    def test_fast_generation_skip_config_file(self):
        """Test that fast_generation_skip_config.json has correct scroll_amount"""
        with open('scripts/fast_generation_skip_config.json', 'r') as f:
            config_data = json.load(f)
        
        # Find the START_GENERATION_DOWNLOADS action
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                scroll_amount = action['value']['scroll_amount']
                assert scroll_amount == 2500, f"Expected 2500px, got {scroll_amount}px"
                print("✅ SKIP CONFIG: scroll_amount = 2500px")
                break
        else:
            pytest.fail("START_GENERATION_DOWNLOADS action not found")
    
    def test_config_loading_integration(self):
        """Test that GenerationDownloadHandlers loads config with correct scroll_amount"""
        handlers = GenerationDownloadHandlers()
        
        # Test loading the fast generation config
        config_data = {}
        with open('scripts/fast_generation_config.json', 'r') as f:
            config_data = json.load(f)
        
        # Extract the generation download config from the action
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                generation_config = handlers.create_generation_config(action['value'])
                assert generation_config.scroll_amount == 2500, f"Expected 2500px, got {generation_config.scroll_amount}px"
                print("✅ INTEGRATION: Config loading uses 2500px")
                break
        else:
            pytest.fail("START_GENERATION_DOWNLOADS action not found")
    
    def test_boundary_scroll_manager_config(self):
        """Test that BoundaryScrollManager has correct min_scroll_distance"""
        from src.utils.boundary_scroll_manager import BoundaryScrollManager
        from unittest.mock import Mock
        
        mock_page = Mock()
        scroll_manager = BoundaryScrollManager(mock_page)
        assert scroll_manager.min_scroll_distance == 2500, f"Expected 2500px, got {scroll_manager.min_scroll_distance}px"
        print("✅ BOUNDARY SCROLL MANAGER: min_scroll_distance = 2500px")


def test_comprehensive_scroll_fix():
    """Comprehensive test for the scroll amount fix"""
    print("\n🔍 COMPREHENSIVE SCROLL AMOUNT FIX TEST")
    print("=" * 50)
    
    # Test default config
    config = GenerationDownloadConfig()
    print(f"📊 Default Config scroll_amount: {config.scroll_amount}px")
    assert config.scroll_amount == 2500
    
    # Test config files
    config_files = [
        'scripts/fast_generation_config.json',
        'scripts/quick_test_config.json',
        'scripts/fast_generation_skip_config.json'
    ]
    
    for config_file in config_files:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                scroll_amount = action['value']['scroll_amount']
                print(f"📊 {config_file}: scroll_amount = {scroll_amount}px")
                assert scroll_amount == 2500
                break
    
    print("\n✅ ALL SCROLL AMOUNT FIXES VERIFIED!")
    print("🎯 The user should now see 'Attempting scroll of 2500px' instead of 800px")
    return True


if __name__ == "__main__":
    test_comprehensive_scroll_fix()
    pytest.main([__file__, "-v"])