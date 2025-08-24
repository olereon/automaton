#!/usr/bin/env python3.11
"""
Test script to verify prompt extraction improvements
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

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/olereon/workspace/github.com/olereon/automaton/logs/prompt_extraction_test.log')
    ]
)

async def test_prompt_extraction():
    """Test the enhanced prompt extraction functionality"""
    
    print("🧪 Testing Enhanced Prompt Extraction System")
    print("=" * 50)
    
    # Create config
    config = GenerationDownloadConfig(
        downloads_folder="/home/olereon/workspace/github.com/olereon/automaton/downloads/test_vids",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        max_downloads=1  # Just one for testing
    )
    
    # Create manager
    manager = GenerationDownloadManager(config)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Keep visible for debugging
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            # Create context and page
            context = await browser.new_context()
            page = await context.new_page()
            
            print("🌐 Please navigate to the completed tasks page manually")
            print("📋 Click on a generation item to load its details")
            print("⏳ Once loaded, press Enter to test prompt extraction...")
            
            # Wait for user to set up the page
            input()
            
            print("🔍 Testing prompt extraction methods...")
            
            # Test metadata extraction
            metadata = await manager.extract_metadata_from_page(page)
            
            if metadata:
                print("\n✅ EXTRACTION RESULTS:")
                print(f"📅 Date: {metadata.get('generation_date', 'Not found')}")
                print(f"📝 Prompt Length: {len(metadata.get('prompt', ''))} characters")
                print(f"📝 Prompt Content: {metadata.get('prompt', 'Not found')[:200]}...")
                
                if len(metadata.get('prompt', '')) > 102:
                    print("🎉 SUCCESS: Full prompt extracted!")
                else:
                    print("⚠️  WARNING: Prompt appears to be truncated")
                    
            else:
                print("❌ FAILED: No metadata extracted")
            
            print("\n🔍 Press Enter to close browser...")
            input()
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_prompt_extraction())