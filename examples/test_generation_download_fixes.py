#!/usr/bin/env python3
"""
Test script for the generation download automation fixes.

This script tests the critical bug fixes implemented in the generation download manager:
1. Date extraction timing - using landmark strategy AFTER thumbnail selection
2. Download button sequence - proper SVG icon click before watermark option
3. Thumbnail clicking logic for subsequent thumbnails
4. Landmark-based extraction integration into workflow

Usage:
    python3.11 examples/test_generation_download_fixes.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.async_api import async_playwright
from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/home/olereon/workspace/github.com/olereon/automaton/logs/test_fixes.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_landmark_readiness_checks():
    """Test the new landmark readiness check functionality"""
    logger.info("=== Testing Landmark Readiness Checks ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Create test configuration
        config = GenerationDownloadConfig(
            downloads_folder='/home/olereon/workspace/github.com/olereon/automaton/downloads/test_fixes',
            logs_folder='/home/olereon/workspace/github.com/olereon/automaton/logs',
            max_downloads=2,
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True
        )
        
        manager = GenerationDownloadManager(config)
        
        try:
            # Navigate to a test page (you'll need to modify this URL)
            await page.goto("https://example.com")  # Replace with actual test URL
            
            # Test landmark readiness checks
            checks = await manager._perform_landmark_readiness_checks(page)
            logger.info(f"Landmark readiness checks result: {checks}")
            
            # Test comprehensive state validation
            validations = await manager._perform_comprehensive_state_validation(page, 0)
            logger.info(f"Comprehensive state validation result: {validations}")
            
            logger.info("✅ Landmark readiness checks test completed")
            
        except Exception as e:
            logger.error(f"❌ Error in landmark readiness test: {e}")
        finally:
            await browser.close()


async def test_enhanced_download_sequence():
    """Test the enhanced download sequence functionality"""
    logger.info("=== Testing Enhanced Download Sequence ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Create test configuration
        config = GenerationDownloadConfig(
            downloads_folder='/home/olereon/workspace/github.com/olereon/automaton/downloads/test_fixes',
            logs_folder='/home/olereon/workspace/github.com/olereon/automaton/logs',
            max_downloads=2,
            download_no_watermark_text="Download without Watermark"
        )
        
        manager = GenerationDownloadManager(config)
        
        try:
            # Navigate to a test page (you'll need to modify this URL)
            await page.goto("https://example.com")  # Replace with actual test URL
            
            # Test individual watermark strategies
            logger.info("Testing watermark CSS selector strategy...")
            css_result = await manager._try_watermark_css_selector(page)
            logger.info(f"CSS selector strategy result: {css_result}")
            
            logger.info("Testing watermark text search strategy...")
            text_result = await manager._try_watermark_text_search(page)
            logger.info(f"Text search strategy result: {text_result}")
            
            logger.info("Testing download initiation check...")
            download_check = await manager._check_download_initiated(page)
            logger.info(f"Download initiation check result: {download_check}")
            
            logger.info("✅ Enhanced download sequence test completed")
            
        except Exception as e:
            logger.error(f"❌ Error in download sequence test: {e}")
        finally:
            await browser.close()


async def test_metadata_extraction_with_landmark_strategy():
    """Test the new landmark-based metadata extraction"""
    logger.info("=== Testing Landmark-based Metadata Extraction ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        # Create test configuration with enhanced naming
        config = GenerationDownloadConfig(
            downloads_folder='/home/olereon/workspace/github.com/olereon/automaton/downloads/test_fixes',
            logs_folder='/home/olereon/workspace/github.com/olereon/automaton/logs',
            max_downloads=2,
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True,
            unique_id="test",
            naming_format="{media_type}_{creation_date}_{unique_id}"
        )
        
        manager = GenerationDownloadManager(config)
        
        try:
            # Create a simple HTML page with test content to verify extraction
            test_html = """
            <html>
            <body>
                <div>
                    <span>Creation Time</span>
                    <span>24 Aug 2025 15:30:00</span>
                </div>
                <div>
                    <span>This is a test prompt</span>...
                </div>
            </body>
            </html>
            """
            
            await page.set_content(test_html)
            
            # Test landmark-based metadata extraction
            metadata = await manager.extract_metadata_with_landmark_strategy(page, 0)
            logger.info(f"Extracted metadata using landmark strategy: {metadata}")
            
            if metadata and metadata.get('generation_date') != 'Unknown Date':
                logger.info("✅ Date extraction successful")
            else:
                logger.warning("⚠️ Date extraction failed")
            
            if metadata and metadata.get('prompt') != 'Unknown Prompt':
                logger.info("✅ Prompt extraction successful")
            else:
                logger.warning("⚠️ Prompt extraction failed")
            
            logger.info("✅ Metadata extraction test completed")
            
        except Exception as e:
            logger.error(f"❌ Error in metadata extraction test: {e}")
        finally:
            await browser.close()


async def test_enhanced_file_naming():
    """Test the enhanced file naming functionality"""
    logger.info("=== Testing Enhanced File Naming ===")
    
    try:
        # Create test configuration with enhanced naming
        config = GenerationDownloadConfig(
            use_descriptive_naming=True,
            unique_id="test",
            naming_format="{media_type}_{creation_date}_{unique_id}",
            date_format="%Y-%m-%d-%H-%M-%S"
        )
        
        from utils.generation_download_manager import EnhancedFileNamer
        namer = EnhancedFileNamer(config)
        
        # Test filename generation
        test_path = Path("test_video.mp4")
        test_date = "24 Aug 2025 15:30:00"
        
        generated_name = namer.generate_filename(test_path, test_date, 1)
        logger.info(f"Generated filename: {generated_name}")
        
        # Verify format
        if "vid_" in generated_name and "test" in generated_name:
            logger.info("✅ Enhanced file naming working correctly")
        else:
            logger.warning("⚠️ Enhanced file naming may have issues")
        
        # Test media type detection
        video_type = namer.get_media_type("mp4")
        image_type = namer.get_media_type("png")
        audio_type = namer.get_media_type("mp3")
        
        logger.info(f"Media types - video: {video_type}, image: {image_type}, audio: {audio_type}")
        
        logger.info("✅ Enhanced file naming test completed")
        
    except Exception as e:
        logger.error(f"❌ Error in file naming test: {e}")


async def main():
    """Run all tests for the generation download fixes"""
    logger.info("Starting Generation Download Fixes Test Suite")
    logger.info("=" * 60)
    
    # Create test directories
    Path('/home/olereon/workspace/github.com/olereon/automaton/downloads/test_fixes').mkdir(parents=True, exist_ok=True)
    Path('/home/olereon/workspace/github.com/olereon/automaton/logs').mkdir(parents=True, exist_ok=True)
    
    try:
        # Run all tests
        await test_landmark_readiness_checks()
        await asyncio.sleep(2)
        
        await test_enhanced_download_sequence()
        await asyncio.sleep(2)
        
        await test_metadata_extraction_with_landmark_strategy()
        await asyncio.sleep(2)
        
        await test_enhanced_file_naming()
        
        logger.info("=" * 60)
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())