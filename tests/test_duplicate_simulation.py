#!/usr/bin/env python3
"""
Simulate duplicate detection during automation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
import asyncio
from pathlib import Path

class MockPage:
    """Mock Playwright page for testing"""
    def __init__(self):
        self.url = "https://wan.video/generate"
        
async def mock_extract_metadata_from_page(self, page):
    """Mock metadata extraction that returns known duplicate data"""
    return {
        'generation_date': '28 Aug 2025 02:10:30',  # This matches entry #1 in logs
        'prompt': 'The camera begins with a medium shot of the shadow knight as he slashes his twin void blades. The blades and his eyes emanating purple void flames.'
    }

async def test_duplicate_detection():
    """Test the full duplicate detection workflow"""
    
    # Create a test config with duplicate detection enabled
    config = GenerationDownloadConfig(
        downloads_folder="/tmp/test_downloads",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        max_downloads=3,
        duplicate_check_enabled=True,
        stop_on_duplicate=True
    )
    
    # Initialize the manager
    manager = GenerationDownloadManager(config)
    
    # Mock the metadata extraction to return a known duplicate
    manager.extract_metadata_from_page = lambda page: mock_extract_metadata_from_page(manager, page)
    
    # Create mock page
    mock_page = MockPage()
    
    # Test comprehensive duplicate detection
    print("🧪 Testing comprehensive duplicate detection...")
    is_duplicate = await manager.check_comprehensive_duplicate(mock_page, "test_thumbnail_001", set())
    
    if is_duplicate:
        print("✅ SUCCESS: Duplicate detected as expected!")
        print("🛑 Automation would stop here with proper message")
        return True
    else:
        print("❌ FAILED: Duplicate not detected when it should have been")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_duplicate_detection())
    if result:
        print("\n🎉 Duplicate detection test passed!")
        print("✅ The automation will now properly detect and stop on duplicates")
    else:
        print("\n💥 Duplicate detection test failed!")
        print("❌ Check the implementation")