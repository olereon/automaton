#!/usr/bin/env python3
"""
Manual Test Script for Metadata Extraction Fixes

This script provides interactive tests for validating metadata extraction fixes
with real browser interactions.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.async_api import async_playwright
from utils.generation_download_manager import GenerationDownloadConfig, GenerationDownloadManager
from utils.generation_debug_logger import GenerationDebugLogger

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MetadataExtractionValidator:
    """Manual validation tool for metadata extraction fixes"""
    
    def __init__(self):
        self.config = GenerationDownloadConfig(
            downloads_folder=str(Path.cwd() / "test_downloads"),
            logs_folder=str(Path.cwd() / "test_logs"),
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True,
            unique_id="manual_test",
            max_downloads=5
        )
        
        # Create test directories
        Path(self.config.downloads_folder).mkdir(exist_ok=True)
        Path(self.config.logs_folder).mkdir(exist_ok=True)
        
        self.manager = GenerationDownloadManager(self.config)
        self.test_results = []
    
    async def run_manual_tests(self):
        """Run manual tests with browser interaction"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False, 
                args=['--start-maximized', '--disable-web-security']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                print("\n" + "="*60)
                print("🧪 METADATA EXTRACTION VALIDATION TESTS")
                print("="*60)
                
                await self.show_instructions()
                
                # Test 1: Multiple Thumbnail Date Extraction
                await self.test_multiple_thumbnail_dates(page)
                
                # Test 2: Element Selection Validation
                await self.test_element_selection_validation(page)
                
                # Test 3: Debug Logger Validation  
                await self.test_debug_logger_functionality(page)
                
                # Test 4: Edge Cases
                await self.test_edge_cases(page)
                
                # Test 5: File Naming
                await self.test_file_naming_validation()
                
                # Generate final report
                await self.generate_test_report()
                
            finally:
                input("\nPress Enter to close browser...")
                await browser.close()
    
    async def show_instructions(self):
        """Show test instructions to user"""
        print("\n📋 INSTRUCTIONS:")
        print("1. Navigate to your generation website")
        print("2. Log in if required") 
        print("3. Go to the completed tasks/generations page")
        print("4. Make sure you can see multiple thumbnails with different dates")
        print("5. Follow the prompts for each test")
        
        input("\nPress Enter when ready to begin testing...")
    
    async def test_multiple_thumbnail_dates(self, page):
        """Test that different thumbnails extract different dates"""
        print("\n🔍 TEST 1: Multiple Thumbnail Date Extraction")
        print("-" * 50)
        
        thumbnail_count = int(input("How many thumbnails are visible? (3-10): ") or "3")
        
        extracted_dates = []
        
        for i in range(thumbnail_count):
            print(f"\n📌 Testing thumbnail {i+1}...")
            input(f"Click on thumbnail {i+1} to show its details, then press Enter...")
            
            # Give page time to update
            await page.wait_for_timeout(2000)
            
            # Extract metadata
            try:
                metadata = await self.manager.extract_metadata_from_page(page)
                
                if metadata:
                    date = metadata.get('generation_date', 'Unknown')
                    prompt = metadata.get('prompt', 'Unknown')[:50] + "..."
                    
                    print(f"   ✅ Extracted Date: {date}")
                    print(f"   ✅ Extracted Prompt: {prompt}")
                    
                    extracted_dates.append(date)
                    
                    self.test_results.append({
                        "test": "multiple_thumbnail_dates",
                        "thumbnail_index": i,
                        "extracted_date": date,
                        "extracted_prompt": prompt,
                        "success": date != "Unknown Date"
                    })
                else:
                    print(f"   ❌ Failed to extract metadata")
                    self.test_results.append({
                        "test": "multiple_thumbnail_dates", 
                        "thumbnail_index": i,
                        "success": False,
                        "error": "No metadata returned"
                    })
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.test_results.append({
                    "test": "multiple_thumbnail_dates",
                    "thumbnail_index": i, 
                    "success": False,
                    "error": str(e)
                })
        
        # Analyze results
        unique_dates = len(set(extracted_dates))
        print(f"\n📊 RESULT: Found {unique_dates} unique dates out of {len(extracted_dates)} thumbnails")
        
        if unique_dates == len(extracted_dates):
            print("   ✅ PERFECT: Each thumbnail has a different date!")
        elif unique_dates > 1:
            print("   ⚠️  PARTIAL: Some dates are different, but some duplicates exist")
        else:
            print("   ❌ FAILED: All thumbnails returned the same date")
        
        print("\n📝 Extracted dates:")
        for i, date in enumerate(extracted_dates):
            print(f"   Thumbnail {i+1}: {date}")
    
    async def test_element_selection_validation(self, page):
        """Test element selection accuracy"""
        print("\n🎯 TEST 2: Element Selection Validation")
        print("-" * 50)
        
        print("This test validates that we're selecting the correct elements...")
        input("Click on a thumbnail that has a UNIQUE date/time, then press Enter...")
        
        await page.wait_for_timeout(2000)
        
        try:
            # Take screenshot for debugging
            screenshot_path = Path(self.config.logs_folder) / f"element_validation_{datetime.now().strftime('%H%M%S')}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"   📸 Screenshot saved: {screenshot_path}")
            
            # Test element visibility
            creation_time_elements = await page.query_selector_all("span:has-text('Creation Time')")
            print(f"   🔍 Found {len(creation_time_elements)} Creation Time elements")
            
            for i, element in enumerate(creation_time_elements):
                is_visible = await element.is_visible()
                print(f"      Element {i+1}: visible={is_visible}")
                
                if is_visible:
                    parent = await element.evaluate_handle("el => el.parentElement")
                    spans = await parent.query_selector_all("span")
                    
                    if len(spans) >= 2:
                        date_text = await spans[1].text_content()
                        print(f"         → Date: {date_text}")
            
            # Test prompt elements
            prompt_elements = await page.query_selector_all("span[aria-describedby]")
            print(f"   💬 Found {len(prompt_elements)} prompt elements")
            
            for i, element in enumerate(prompt_elements[:3]):  # Show first 3
                text = await element.text_content()
                is_visible = await element.is_visible()
                print(f"      Element {i+1}: visible={is_visible}, text='{text[:30]}...'")
            
            self.test_results.append({
                "test": "element_selection_validation",
                "creation_time_elements": len(creation_time_elements),
                "prompt_elements": len(prompt_elements),
                "success": len(creation_time_elements) > 0 and len(prompt_elements) > 0
            })
            
        except Exception as e:
            print(f"   ❌ Error during element validation: {e}")
            self.test_results.append({
                "test": "element_selection_validation",
                "success": False,
                "error": str(e)
            })
    
    async def test_debug_logger_functionality(self, page):
        """Test debug logger captures information correctly"""
        print("\n🔍 TEST 3: Debug Logger Functionality")
        print("-" * 50)
        
        print("Testing debug logger...")
        input("Click on any thumbnail, then press Enter...")
        
        await page.wait_for_timeout(2000)
        
        try:
            # Check if debug logger is working
            if self.manager.debug_logger:
                debug_summary = self.manager.debug_logger.get_debug_summary()
                print(f"   📊 Debug steps logged: {debug_summary['total_steps']}")
                print(f"   📅 Date extractions: {debug_summary['date_extractions']}")
                print(f"   💬 Prompt extractions: {debug_summary['prompt_extractions']}")
                print(f"   👆 Thumbnail clicks: {debug_summary['thumbnail_clicks']}")
                print(f"   📁 Debug log file: {debug_summary['debug_log_file']}")
                
                self.test_results.append({
                    "test": "debug_logger_functionality",
                    "debug_summary": debug_summary,
                    "success": debug_summary['total_steps'] > 0
                })
            else:
                print("   ❌ Debug logger not available")
                self.test_results.append({
                    "test": "debug_logger_functionality",
                    "success": False,
                    "error": "Debug logger not initialized"
                })
                
        except Exception as e:
            print(f"   ❌ Error testing debug logger: {e}")
            self.test_results.append({
                "test": "debug_logger_functionality",
                "success": False,
                "error": str(e)
            })
    
    async def test_edge_cases(self, page):
        """Test edge cases and error conditions"""
        print("\n⚠️  TEST 4: Edge Cases")
        print("-" * 50)
        
        print("Testing edge cases...")
        
        # Test with empty page
        try:
            empty_page_mock = type('MockPage', (), {
                'url': 'https://empty.test',
                'query_selector_all': lambda self, selector: asyncio.create_task(asyncio.coroutine(lambda: [])())
            })()
            
            metadata = await self.manager.extract_metadata_from_page(empty_page_mock)
            
            if metadata:
                print(f"   🔍 Empty page test - Date: {metadata.get('generation_date')}")
                print(f"   🔍 Empty page test - Prompt: {metadata.get('prompt')}")
                
                success = (metadata.get('generation_date') == 'Unknown Date' and 
                          metadata.get('prompt') == 'Unknown Prompt')
            else:
                success = True  # None is also acceptable for empty page
                print("   🔍 Empty page test - Returned None (acceptable)")
            
            self.test_results.append({
                "test": "edge_cases_empty_page",
                "success": success
            })
            
        except Exception as e:
            print(f"   ❌ Edge case test error: {e}")
            self.test_results.append({
                "test": "edge_cases_empty_page",
                "success": False,
                "error": str(e)
            })
    
    def test_file_naming_validation(self):
        """Test file naming with extracted metadata"""
        print("\n📁 TEST 5: File Naming Validation")
        print("-" * 50)
        
        from utils.generation_download_manager import EnhancedFileNamer
        namer = EnhancedFileNamer(self.config)
        
        test_cases = [
            ("24 Aug 2025 01:37:01", "vid_2025-08-24-01-37-01_manual_test.mp4"),
            ("Invalid Date", None),  # Should use current time
            ("", None),  # Should use current time
        ]
        
        for date_input, expected in test_cases:
            try:
                test_file = Path("/tmp/test.mp4")
                result = namer.generate_filename(test_file, creation_date=date_input)
                
                if expected:
                    success = result == expected
                    print(f"   ✅ '{date_input}' → '{result}' (expected: '{expected}')")
                else:
                    success = len(result.split('-')) == 6  # Should be current timestamp format
                    print(f"   ✅ '{date_input}' → '{result}' (current timestamp format)")
                
                self.test_results.append({
                    "test": "file_naming_validation",
                    "input": date_input,
                    "output": result,
                    "expected": expected,
                    "success": success
                })
                
            except Exception as e:
                print(f"   ❌ File naming error for '{date_input}': {e}")
                self.test_results.append({
                    "test": "file_naming_validation",
                    "input": date_input,
                    "success": False,
                    "error": str(e)
                })
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 GENERATING TEST REPORT")
        print("="*60)
        
        # Count results
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get('success', False)])
        failed_tests = total_tests - successful_tests
        
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        # Group by test type
        test_groups = {}
        for result in self.test_results:
            test_type = result['test']
            if test_type not in test_groups:
                test_groups[test_type] = []
            test_groups[test_type].append(result)
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_type, results in test_groups.items():
            successful = len([r for r in results if r.get('success', False)])
            total = len(results)
            print(f"\n   {test_type}:")
            print(f"      Success: {successful}/{total}")
            
            for result in results:
                status = "✅" if result.get('success', False) else "❌"
                print(f"      {status} {result}")
        
        # Save report to file
        report_file = Path(self.config.logs_folder) / f"manual_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests, 
                    "failed_tests": failed_tests,
                    "success_rate": (successful_tests/total_tests*100) if total_tests > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Report saved to: {report_file}")


async def main():
    """Main test runner"""
    print("🚀 Starting Manual Metadata Extraction Tests...")
    
    validator = MetadataExtractionValidator()
    await validator.run_manual_tests()
    
    print("\n✅ Manual tests completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()