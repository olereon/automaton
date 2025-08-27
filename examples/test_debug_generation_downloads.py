#!/usr/bin/env python3
"""
Test script for debugging generation downloads metadata extraction
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.async_api import async_playwright
from utils.generation_download_manager import GenerationDownloadConfig
from utils.metadata_extraction_debugger import MetadataExtractionDebugger
from utils.generation_debug_logger import GenerationDebugLogger
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_metadata_extraction_live():
    """Debug metadata extraction on a live page"""
    
    config = GenerationDownloadConfig(
        # Use your actual configuration
        downloads_folder="/home/olereon/workspace/github.com/olereon/automaton/downloads/vids",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        
        # Text landmarks
        creation_time_text="Creation Time",
        prompt_ellipsis_pattern="</span>...",
        
        # Selectors
        completed_task_selector="div[id$='__9']",  # Adjust as needed
        thumbnail_selector=".thumsItem, .thumbnail-item",
        
        # Debug mode
        use_descriptive_naming=True
    )
    
    async with async_playwright() as p:
        # Launch browser with GUI for debugging
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            viewport={'width': 2560, 'height': 1440}
        )
        
        page = await context.new_page()
        
        try:
            print("🚀 Starting debug session...")
            print("📋 Instructions:")
            print("1. Navigate to the generation page manually")
            print("2. Log in if needed")
            print("3. Go to the completed tasks section")
            print("4. Click on any thumbnail to show its details")
            print("5. Press Enter in this console to start debugging")
            
            # Wait for user to navigate and set up the page
            input("\nPress Enter when ready to debug...")
            
            # Initialize debug tools
            debugger = MetadataExtractionDebugger()
            debug_logger = GenerationDebugLogger()
            
            print("🔍 Starting comprehensive page analysis...")
            
            # Run comprehensive analysis
            results = await debugger.analyze_page_for_metadata(page, config)
            
            # Create visual report
            report = debugger.create_visual_report()
            print("\n" + "="*80)
            print("VISUAL DEBUG REPORT")
            print("="*80)
            print(report)
            
            # Save detailed element analysis
            print(f"\n💾 Detailed debug data saved to: {debugger.debug_file}")
            
            # Also test live element discovery
            print("\n🔍 Testing live element discovery...")
            
            search_patterns = ["Creation Time", "2025", "Aug", "..."]
            elements_info, date_candidates = await debug_logger.log_page_elements(
                page, -1, search_patterns
            )
            
            print(f"📊 Found {len(elements_info)} total elements")
            print(f"📅 Found {len(date_candidates)} potential date elements")
            
            # Show top date candidates
            print("\n🏆 Top Date Candidates:")
            for i, candidate in enumerate(date_candidates[:5]):
                print(f"  {i+1}. Confidence: {candidate['confidence']:.2f}")
                print(f"     Pattern: {candidate['pattern_matched']}")
                print(f"     Text: {candidate['full_text'][:50]}...")
                print(f"     Visible: {candidate['is_visible']}")
                print()
            
            # Test current extraction logic
            print("\n🧪 Testing current extraction logic...")
            
            # Simulate the current metadata extraction
            try:
                creation_time_elements = await page.query_selector_all(f"span:has-text('{config.creation_time_text}')")
                print(f"Found {len(creation_time_elements)} Creation Time elements")
                
                for i, element in enumerate(creation_time_elements):
                    print(f"\nCreation Time Element {i+1}:")
                    
                    # Get parent and find spans
                    parent = await element.evaluate_handle("el => el.parentElement")
                    spans = await parent.query_selector_all("span")
                    print(f"  Parent has {len(spans)} span children")
                    
                    for j, span in enumerate(spans):
                        text = await span.text_content()
                        is_visible = await span.is_visible()
                        print(f"    Span {j}: '{text[:50]}...' (visible: {is_visible})")
                    
                    # Extract associated date like the current logic does
                    if len(spans) >= 2:
                        date_text = await spans[1].text_content()
                        print(f"  🎯 Would extract date: '{date_text}'")
                        
                        # Check if this is the "correct" date
                        print("  ❓ Is this the correct date for the current thumbnail?")
            
            except Exception as e:
                print(f"❌ Error testing current logic: {e}")
            
            # Show recommendations
            recommendations = results.get("recommendations", [])
            if recommendations:
                print(f"\n💡 Top Recommendations ({len(recommendations)} total):")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. [{rec['priority'].upper()}] {rec['title']}")
                    print(f"     {rec['description']}")
                    print(f"     Implementation: {rec['implementation']}")
                    print()
            
            print("\n✅ Debug session completed!")
            print(f"📁 Debug files saved in: {Path(debugger.debug_file).parent}")
            
            # Keep browser open for manual inspection
            input("\nPress Enter to close browser...")
            
        except Exception as e:
            logger.error(f"Error in debug session: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


async def debug_element_comparison():
    """Compare different element selection strategies"""
    
    config = GenerationDownloadConfig()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 2560, 'height': 1440})
        page = await context.new_page()
        
        try:
            print("🔄 Element Comparison Debug Mode")
            print("Navigate to page, click on different thumbnails, then press Enter to compare")
            
            input("Press Enter when ready...")
            
            # Test multiple selection strategies
            strategies = {
                "first_creation_time": "Select first Creation Time element",
                "visible_creation_time": "Select first visible Creation Time element", 
                "last_creation_time": "Select last Creation Time element",
                "largest_date": "Select element with longest date text"
            }
            
            for strategy_name, description in strategies.items():
                print(f"\n🧪 Testing strategy: {strategy_name}")
                print(f"Description: {description}")
                
                try:
                    creation_elements = await page.query_selector_all("span:has-text('Creation Time')")
                    print(f"Found {len(creation_elements)} Creation Time elements")
                    
                    if strategy_name == "first_creation_time" and creation_elements:
                        element = creation_elements[0]
                    elif strategy_name == "visible_creation_time" and creation_elements:
                        element = None
                        for el in creation_elements:
                            if await el.is_visible():
                                element = el
                                break
                    elif strategy_name == "last_creation_time" and creation_elements:
                        element = creation_elements[-1]
                    elif strategy_name == "largest_date" and creation_elements:
                        element = None
                        max_date_length = 0
                        for el in creation_elements:
                            parent = await el.evaluate_handle("el => el.parentElement")
                            spans = await parent.query_selector_all("span")
                            if len(spans) >= 2:
                                date_text = await spans[1].text_content()
                                if date_text and len(date_text) > max_date_length:
                                    max_date_length = len(date_text)
                                    element = el
                    else:
                        element = None
                    
                    if element:
                        parent = await element.evaluate_handle("el => el.parentElement")
                        spans = await parent.query_selector_all("span")
                        if len(spans) >= 2:
                            date_text = await spans[1].text_content()
                            is_visible = await spans[1].is_visible()
                            print(f"  📅 Result: '{date_text}' (visible: {is_visible})")
                        else:
                            print("  ❌ No date spans found")
                    else:
                        print("  ❌ No suitable element found")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
            
            print("\n🏁 Element comparison completed")
            input("Press Enter to close...")
            
        finally:
            await browser.close()


async def main():
    """Main debug function"""
    print("🔧 Generation Downloads Debug Tool")
    print("="*50)
    print("1. Full metadata extraction debug")
    print("2. Element comparison debug")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        await debug_metadata_extraction_live()
    elif choice == "2":
        await debug_element_comparison()
    elif choice == "3":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        await main()


if __name__ == "__main__":
    print("🚀 Starting Generation Downloads Debug Tool...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Debug session interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()