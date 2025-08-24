#!/usr/bin/env python3.11
"""
Test script for infinite scroll generation download functionality
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
from playwright.async_api import async_playwright

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/olereon/workspace/github.com/olereon/automaton/logs/infinite_scroll_test.log')
    ]
)

async def test_infinite_scroll():
    """Test the infinite scroll functionality"""
    
    print("🔄 Testing Infinite Scroll Generation Download System")
    print("=" * 60)
    
    # Create config with small batch size for testing
    config = GenerationDownloadConfig(
        downloads_folder="/home/olereon/workspace/github.com/olereon/automaton/downloads/test_scroll_vids",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        max_downloads=25,  # Test with 25 downloads to ensure multiple scrolls
        scroll_batch_size=5,  # Scroll every 5 downloads for testing
        scroll_amount=400,  # Smaller scroll for testing
        scroll_wait_time=1500,  # Shorter wait for testing
        max_scroll_attempts=3,
        scroll_detection_threshold=2  # Lower threshold for testing
    )
    
    # Create manager
    manager = GenerationDownloadManager(config)
    
    print(f"📋 Test Configuration:")
    print(f"   • Max Downloads: {config.max_downloads}")
    print(f"   • Scroll Batch Size: {config.scroll_batch_size}")
    print(f"   • Scroll Amount: {config.scroll_amount}px")
    print(f"   • Downloads Directory: {config.downloads_folder}")
    print()
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Keep visible to observe scrolling
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            # Create context and page
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🌐 Please navigate to the generation gallery page and ensure you're on the completed tasks section")
            print("📋 The test will run automatically once you press Enter...")
            input()
            
            print("🚀 Starting infinite scroll test...")
            
            # Run the download automation with scrolling
            results = await manager.run_download_automation(page)
            
            print("\n" + "=" * 60)
            print("🎯 TEST RESULTS")
            print("=" * 60)
            
            print(f"✅ Success: {results['success']}")
            print(f"📥 Downloads Completed: {results['downloads_completed']}")
            print(f"🔄 Scrolls Performed: {results['scrolls_performed']}")
            print(f"📊 Total Thumbnails Processed: {results['total_thumbnails_processed']}")
            print(f"⏱️ Duration: {results['start_time']} → {results['end_time']}")
            
            if results['errors']:
                print(f"❌ Errors ({len(results['errors'])}):")
                for i, error in enumerate(results['errors'], 1):
                    print(f"   {i}. {error}")
            else:
                print("✅ No errors encountered")
            
            # Calculate scroll efficiency
            if results['scrolls_performed'] > 0:
                downloads_per_scroll = results['downloads_completed'] / results['scrolls_performed']
                print(f"📈 Downloads per scroll: {downloads_per_scroll:.1f}")
            
            # Calculate success rate
            if results['total_thumbnails_processed'] > 0:
                success_rate = (results['downloads_completed'] / results['total_thumbnails_processed']) * 100
                print(f"📊 Success rate: {success_rate:.1f}%")
            
            print("\n🔍 Press Enter to close browser...")
            input()
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_infinite_scroll())