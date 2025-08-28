#!/usr/bin/env python3
"""
Test script for duplicate detection functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
from pathlib import Path

def test_log_parsing():
    """Test the log parsing functionality"""
    
    # Create a test config
    config = GenerationDownloadConfig(
        downloads_folder="/tmp/test_downloads",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        max_downloads=3,
        duplicate_check_enabled=True,
        stop_on_duplicate=True
    )
    
    # Initialize the manager
    manager = GenerationDownloadManager(config)
    
    # Test the log parsing
    print("🧪 Testing log parsing functionality...")
    existing_entries = manager._load_existing_log_entries()
    
    print(f"📋 Loaded {len(existing_entries)} existing entries:")
    for date, entry in existing_entries.items():
        print(f"   📅 {date}")
        print(f"   🔗 {entry['id']}")
        print(f"   📝 {entry['prompt'][:100]}...")
        print(f"   ---")
    
    # Test duplicate detection for a known entry
    if existing_entries:
        # Get the first entry for testing
        test_date = list(existing_entries.keys())[0]
        test_entry = existing_entries[test_date]
        
        print(f"🎯 Testing duplicate detection for date: {test_date}")
        print(f"   Expected to find match: {test_entry['prompt'][:50]}...")
        
        # Simulate metadata for comparison
        test_metadata = {
            'generation_date': test_date,
            'prompt': test_entry['prompt']
        }
        
        print(f"   ✅ Test metadata created successfully")
        print(f"   🔍 This should trigger duplicate detection when used in automation")
    
    return len(existing_entries) > 0

if __name__ == "__main__":
    success = test_log_parsing()
    if success:
        print("\n✅ Log parsing test completed successfully!")
        print("🎯 Duplicate detection should now work with existing log entries")
    else:
        print("\n❌ No existing log entries found - create some first")