#!/usr/bin/env python3
"""
Debug Script: Boundary Detection Issue Investigation
===================================================

This script tests the incremental boundary detection to identify why the automation
is cycling between gallery and main page instead of finding the boundary.

Tests performed:
1. Check if boundary detection method is being called
2. Verify metadata extraction from main page containers  
3. Test log entry loading and comparison
4. Simulate the boundary scanning process
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_boundary_detection_debug():
    """Test boundary detection with actual configuration"""
    
    logger.info("🧪 Starting Boundary Detection Debug Test")
    logger.info("=" * 80)
    
    # Load the actual configuration that's causing issues
    config = GenerationDownloadConfig(
        max_downloads=100,
        downloads_folder="/home/olereon/workspace/github.com/olereon/automaton/downloads/vids",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        completed_task_selector="div[id$='__8']",  # Main page containers
        thumbnail_selector=".thumsItem,.thumbnail-item,.thumsCou,[class*='thumb'],img[src*='wan']",
        creation_time_text="Creation Time",
        stop_on_duplicate=False,  # SKIP mode
        duplicate_mode="skip"
    )
    
    manager = GenerationDownloadManager(config)
    
    # Test 1: Check log entry loading
    logger.info("\n🔍 TEST 1: Loading existing log entries")
    logger.info("-" * 50)
    
    log_entries = manager._load_existing_log_entries()
    logger.info(f"✅ Loaded {len(log_entries)} existing log entries")
    
    if len(log_entries) > 0:
        # Show first few entries
        logger.info("📋 Sample log entries:")
        for i, (time_key, entry) in enumerate(list(log_entries.items())[:3]):
            logger.info(f"   {i+1}. Time: {time_key}")
            logger.info(f"      ID: {entry.get('id', 'N/A')}")
            logger.info(f"      Prompt: {entry.get('prompt', 'N/A')[:50]}...")
            logger.info("")
    else:
        logger.warning("❌ No existing log entries found - this could be the issue!")
        logger.info("   The automation may think everything is new content")
        return False
    
    # Test 2: Check configuration selectors
    logger.info("\n🔍 TEST 2: Configuration validation")
    logger.info("-" * 50)
    
    logger.info(f"✅ Completed task selector: {config.completed_task_selector}")
    logger.info(f"✅ SKIP mode enabled: {not config.stop_on_duplicate}")
    logger.info(f"✅ Duplicate mode: {config.duplicate_mode}")
    logger.info(f"✅ Creation time text: {config.creation_time_text}")
    
    # Test 3: Simulate boundary detection logic
    logger.info("\n🔍 TEST 3: Boundary detection simulation")
    logger.info("-" * 50)
    
    # Create mock containers with sample data
    mock_containers = [
        {"creation_time": "03 Sep 2025 11:59:08", "prompt": "The camera begins with a medium shot..."},
        {"creation_time": "03 Sep 2025 11:58:45", "prompt": "A cinematic wide shot establishes..."},  
        {"creation_time": "02 Sep 2025 15:30:22", "prompt": "Close-up of character's face..."},
    ]
    
    duplicates_found = 0
    boundary_found = False
    boundary_index = -1
    
    for i, mock_container in enumerate(mock_containers):
        container_time = mock_container["creation_time"]
        container_prompt = mock_container["prompt"][:100]
        
        # Check if this matches any log entry
        has_matching_log_entry = False
        for log_time, log_entry in log_entries.items():
            log_prompt = log_entry.get('prompt', '')[:100]
            if log_time == container_time and log_prompt == container_prompt:
                has_matching_log_entry = True
                duplicates_found += 1
                logger.info(f"   Container {i+1}: ✓ DUPLICATE - {container_time}")
                break
        
        if not has_matching_log_entry:
            boundary_found = True
            boundary_index = i + 1
            logger.info(f"   Container {i+1}: 🎯 BOUNDARY FOUND - {container_time}")
            logger.info(f"      Prompt: {container_prompt[:50]}...")
            break
    
    if boundary_found:
        logger.info(f"✅ Boundary detection simulation SUCCESSFUL")
        logger.info(f"   Boundary at container: {boundary_index}")
        logger.info(f"   Duplicates before boundary: {duplicates_found}")
    else:
        logger.warning("❌ Boundary detection simulation FAILED")
        logger.info("   All containers appear to be duplicates")
    
    # Test 4: Check potential issues
    logger.info("\n🔍 TEST 4: Potential issue analysis")
    logger.info("-" * 50)
    
    potential_issues = []
    
    # Check if log entries are properly formatted
    sample_times = list(log_entries.keys())[:3]
    for time_key in sample_times:
        if not manager._is_valid_date_text(time_key):
            potential_issues.append(f"Invalid date format in log: {time_key}")
    
    # Check if selectors might be wrong
    if config.completed_task_selector == "div[id$='__8']":
        logger.info("✅ Using correct main page container selector")
    else:
        potential_issues.append(f"Unexpected container selector: {config.completed_task_selector}")
    
    if potential_issues:
        logger.warning("⚠️ Potential issues found:")
        for issue in potential_issues:
            logger.warning(f"   - {issue}")
    else:
        logger.info("✅ No obvious configuration issues detected")
    
    # Test 5: Check if the issue is in the return workflow
    logger.info("\n🔍 TEST 5: Return workflow analysis")
    logger.info("-" * 50)
    
    logger.info("The issue might be in the workflow after boundary detection:")
    logger.info("1. ✅ Exit gallery (Step 11) - likely working")
    logger.info("2. ✅ Return to main page (Step 12) - likely working") 
    logger.info("3. ✅ Boundary scanning (Step 13) - implemented correctly")
    logger.info("4. ❓ Click boundary container (Step 14) - might be failing")
    logger.info("5. ❓ Resume downloads (Step 15) - might not work")
    
    logger.info("\n💡 RECOMMENDATIONS:")
    logger.info("=" * 50)
    logger.info("1. Add more detailed logging to _click_boundary_container method")
    logger.info("2. Verify that clicking boundary container opens gallery at correct position")
    logger.info("3. Check if thumbnail navigation works after returning from boundary click")
    logger.info("4. Consider adding retry mechanism if boundary click fails")
    
    return True

async def run_debug_test():
    """Run the debug test"""
    try:
        success = await test_boundary_detection_debug()
        if success:
            logger.info("\n🎉 Debug analysis completed successfully!")
            logger.info("Check the recommendations above to fix the cycling issue.")
        else:
            logger.error("\n💥 Debug analysis failed!")
        return success
    except Exception as e:
        logger.error(f"Error running debug test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_debug_test())
    sys.exit(0 if success else 1)