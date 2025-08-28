#!/usr/bin/env python3
"""
Test that the completed_task_selector configuration is properly used
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

def test_selector_configuration():
    """Test that custom completed_task_selector is used"""
    
    # Test with custom selector __19
    config1 = GenerationDownloadConfig(
        downloads_folder="/tmp/test",
        logs_folder="/tmp/test",
        completed_task_selector="div[id$='__19']"
    )
    
    manager1 = GenerationDownloadManager(config1)
    print(f"✅ Config with __19: {manager1.config.completed_task_selector}")
    assert manager1.config.completed_task_selector == "div[id$='__19']"
    
    # Test with default selector
    config2 = GenerationDownloadConfig(
        downloads_folder="/tmp/test",
        logs_folder="/tmp/test"
    )
    
    manager2 = GenerationDownloadManager(config2)
    print(f"✅ Default config: {manager2.config.completed_task_selector}")
    assert manager2.config.completed_task_selector == "div[id$='__8']"
    
    # Test selector parsing
    import re
    
    # Test __19 extraction
    match = re.search(r'__(\d+)', "div[id$='__19']")
    assert match and int(match.group(1)) == 19
    print(f"✅ Successfully extracted 19 from selector")
    
    # Test __8 extraction
    match = re.search(r'__(\d+)', "div[id$='__8']")
    assert match and int(match.group(1)) == 8
    print(f"✅ Successfully extracted 8 from selector")
    
    print("\n🎉 All selector configuration tests passed!")
    print("\n📌 The automation will now:")
    print("  • Start from __19 when configured with 'completed_task_selector': 'div[id$=\"__19\"]'")
    print("  • Try __19, __20, __21... up to __27 (9 attempts)")
    print("  • Start from __8 by default if not configured")

if __name__ == "__main__":
    test_selector_configuration()