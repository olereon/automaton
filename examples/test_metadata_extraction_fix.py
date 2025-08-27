#!/usr/bin/env python3
"""
Test script specifically for testing and fixing metadata extraction issues
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from playwright.async_api import async_playwright
from utils.generation_download_manager import GenerationDownloadConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MetadataExtractionTester:
    """Advanced tester for metadata extraction with visual debugging"""
    
    def __init__(self, config):
        self.config = config
        self.test_results = []
        
    async def test_all_extraction_methods(self, page):
        """Test all possible metadata extraction methods"""
        print("\n🧪 COMPREHENSIVE METADATA EXTRACTION TEST")
        print("="*60)
        
        # Test 1: Date extraction methods
        print("\n📅 TESTING DATE EXTRACTION METHODS")
        print("-"*40)
        await self._test_date_extraction_methods(page)
        
        # Test 2: Prompt extraction methods  
        print("\n💬 TESTING PROMPT EXTRACTION METHODS")
        print("-"*40)
        await self._test_prompt_extraction_methods(page)
        
        # Test 3: Element visibility analysis
        print("\n👁️ TESTING ELEMENT VISIBILITY")
        print("-"*40)
        await self._test_element_visibility(page)
        
        # Test 4: Selection strategy comparison
        print("\n🎯 TESTING SELECTION STRATEGIES")
        print("-"*40)
        await self._test_selection_strategies(page)
        
        return self.test_results
    
    async def _test_date_extraction_methods(self, page):
        """Test different date extraction approaches"""
        
        # Method 1: Current landmark approach
        print("1. Testing current landmark approach...")
        try:
            creation_time_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
            print(f"   Found {len(creation_time_elements)} Creation Time elements")
            
            for i, element in enumerate(creation_time_elements):
                is_visible = await element.is_visible()
                parent = await element.evaluate_handle("el => el.parentElement")
                spans = await parent.query_selector_all("span")
                
                print(f"   Element {i+1}: visible={is_visible}, parent has {len(spans)} spans")
                
                date_text = "No date"
                if len(spans) >= 2:
                    date_text = await spans[1].text_content()
                    span_visible = await spans[1].is_visible()
                    print(f"   └─ Date: '{date_text}' (span visible: {span_visible})")
                
                self.test_results.append({
                    "method": "landmark_approach",
                    "element_index": i,
                    "visible": is_visible,
                    "date_text": date_text,
                    "span_count": len(spans)
                })
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 2: CSS selector approach
        print("\n2. Testing CSS selector approach...")
        try:
            date_elements = await page.query_selector_all(self.config.generation_date_selector)
            print(f"   Found {len(date_elements)} elements with CSS selector")
            
            for i, element in enumerate(date_elements):
                date_text = await element.text_content()
                is_visible = await element.is_visible()
                print(f"   Element {i+1}: '{date_text}' (visible: {is_visible})")
                
                self.test_results.append({
                    "method": "css_selector",
                    "element_index": i,
                    "visible": is_visible,
                    "date_text": date_text or "No text"
                })
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 3: Comprehensive date pattern search
        print("\n3. Testing comprehensive date pattern search...")
        try:
            await self._search_date_patterns(page)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def _search_date_patterns(self, page):
        """Search for date patterns across all page elements"""
        
        date_patterns = [
            r'\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}:\d{2}',  # "24 Aug 2025 01:37:01"
            r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}',        # "2025-08-24 01:37:01"
            r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}',    # "24/08/2025 01:37:01"
            r'\d{1,2}\s+\w{3}\s+\d{4}',                         # "24 Aug 2025"
            r'20\d{2}',                                         # Any year 2000+
        ]
        
        import re
        
        # Get all text content from the page
        page_text = await page.evaluate("() => document.body.textContent")
        
        print("   Searching for date patterns in page text...")
        for pattern in date_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"   Pattern '{pattern}':")
                for match in matches[:5]:  # Show first 5 matches
                    print(f"      └─ '{match}'")
                
                # Find elements containing these matches
                for match in matches[:3]:  # Check first 3 matches
                    try:
                        elements = await page.query_selector_all(f"*:has-text('{match}')")
                        print(f"         Elements containing '{match}': {len(elements)}")
                        for i, element in enumerate(elements[:2]):  # Show first 2
                            is_visible = await element.is_visible()
                            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                            print(f"           {i+1}. <{tag_name}> (visible: {is_visible})")
                    except Exception as e:
                        print(f"         ❌ Error finding elements: {e}")
    
    async def _test_prompt_extraction_methods(self, page):
        """Test different prompt extraction approaches"""
        
        # Method 1: Current ellipsis pattern approach
        print("1. Testing current ellipsis pattern approach...")
        try:
            containers = await page.query_selector_all("div")
            found_patterns = 0
            
            for container in containers[:50]:  # Limit to first 50 divs
                try:
                    html_content = await container.evaluate("el => el.innerHTML")
                    if self.config.prompt_ellipsis_pattern in html_content and "aria-describedby" in html_content:
                        found_patterns += 1
                        print(f"   Found pattern in container {found_patterns}")
                        
                        # Try to extract prompt
                        spans = await container.query_selector_all("span[aria-describedby]")
                        for i, span in enumerate(spans):
                            text_content = await span.text_content()
                            inner_text = await span.evaluate("el => el.innerText")
                            is_visible = await span.is_visible()
                            
                            print(f"      Span {i+1}: visible={is_visible}")
                            print(f"      └─ text_content: '{text_content[:50]}...' ({len(text_content)} chars)")
                            print(f"      └─ inner_text: '{inner_text[:50]}...' ({len(inner_text)} chars)")
                            
                            if found_patterns >= 3:  # Stop after finding 3 patterns
                                break
                        
                        if found_patterns >= 3:
                            break
                            
                except Exception:
                    continue
            
            print(f"   Total containers with pattern: {found_patterns}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 2: Direct aria-describedby search
        print("\n2. Testing direct aria-describedby search...")
        try:
            aria_elements = await page.query_selector_all("span[aria-describedby]")
            print(f"   Found {len(aria_elements)} span[aria-describedby] elements")
            
            for i, element in enumerate(aria_elements[:5]):  # Show first 5
                text_content = await element.text_content()
                is_visible = await element.is_visible()
                aria_value = await element.get_attribute("aria-describedby")
                
                print(f"   Element {i+1}: visible={is_visible}, aria-describedby='{aria_value}'")
                print(f"   └─ Text: '{text_content[:100]}...' ({len(text_content)} chars)")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 3: CSS selector approach
        print("\n3. Testing CSS selector approach...")
        try:
            prompt_elements = await page.query_selector_all(self.config.prompt_selector)
            print(f"   Found {len(prompt_elements)} elements with CSS selector")
            
            for i, element in enumerate(prompt_elements):
                text_content = await element.text_content()
                is_visible = await element.is_visible()
                print(f"   Element {i+1}: '{text_content[:50]}...' (visible: {is_visible})")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 4: Alternative extraction techniques
        print("\n4. Testing alternative extraction techniques...")
        await self._test_alternative_prompt_extraction(page)
    
    async def _test_alternative_prompt_extraction(self, page):
        """Test alternative prompt extraction techniques"""
        
        # Technique 1: Look for title attributes
        print("   a) Checking title attributes...")
        try:
            title_elements = await page.query_selector_all("[title*='camera'], [title*='giant'], [title*='frost']")
            for i, element in enumerate(title_elements):
                title = await element.get_attribute("title")
                print(f"      Element {i+1}: '{title[:50]}...' ({len(title)} chars)")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        # Technique 2: Look for aria-label attributes  
        print("   b) Checking aria-label attributes...")
        try:
            aria_elements = await page.query_selector_all("[aria-label*='camera'], [aria-label*='giant']")
            for i, element in enumerate(aria_elements):
                aria_label = await element.get_attribute("aria-label")
                print(f"      Element {i+1}: '{aria_label[:50]}...' ({len(aria_label)} chars)")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        # Technique 3: CSS truncation removal
        print("   c) Testing CSS truncation removal...")
        try:
            truncated_elements = await page.query_selector_all("span[aria-describedby]")
            for i, element in enumerate(truncated_elements[:2]):  # Test first 2
                print(f"      Testing element {i+1}...")
                
                # Get original text
                original_text = await element.text_content()
                
                # Try to remove CSS truncation
                full_text = await element.evaluate("""el => {
                    const originalStyles = {
                        textOverflow: el.style.textOverflow,
                        overflow: el.style.overflow,
                        whiteSpace: el.style.whiteSpace,
                        maxWidth: el.style.maxWidth,
                        width: el.style.width
                    };
                    
                    // Remove truncation
                    el.style.textOverflow = 'clip';
                    el.style.overflow = 'visible';
                    el.style.whiteSpace = 'normal';
                    el.style.maxWidth = 'none';
                    el.style.width = 'auto';
                    
                    const fullText = el.textContent || el.innerText;
                    
                    // Restore styles
                    Object.keys(originalStyles).forEach(prop => {
                        if (originalStyles[prop]) {
                            el.style[prop] = originalStyles[prop];
                        } else {
                            el.style.removeProperty(prop.replace(/([A-Z])/g, '-$1').toLowerCase());
                        }
                    });
                    
                    return fullText;
                }""")
                
                print(f"         Original: '{original_text[:30]}...' ({len(original_text)} chars)")
                print(f"         Expanded: '{full_text[:30]}...' ({len(full_text)} chars)")
                print(f"         Improvement: {len(full_text) - len(original_text)} chars")
        
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    async def _test_element_visibility(self, page):
        """Test element visibility and accessibility"""
        
        print("Testing element visibility patterns...")
        
        # Test Creation Time elements visibility
        try:
            creation_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
            print(f"Creation Time elements visibility analysis:")
            
            for i, element in enumerate(creation_elements):
                is_visible = await element.is_visible()
                bounding_box = await element.bounding_box()
                computed_style = await element.evaluate("""el => {
                    const style = window.getComputedStyle(el);
                    return {
                        display: style.display,
                        visibility: style.visibility,
                        opacity: style.opacity,
                        position: style.position
                    };
                }""")
                
                print(f"   Element {i+1}:")
                print(f"   └─ Visible: {is_visible}")
                print(f"   └─ Bounding box: {bounding_box}")
                print(f"   └─ Computed style: {computed_style}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test prompt elements visibility
        try:
            prompt_elements = await page.query_selector_all("span[aria-describedby]")
            visible_count = 0
            for element in prompt_elements:
                if await element.is_visible():
                    visible_count += 1
            
            print(f"\nPrompt elements visibility: {visible_count}/{len(prompt_elements)} visible")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    async def _test_selection_strategies(self, page):
        """Test different element selection strategies"""
        
        strategies = [
            ("first_visible", "Select first visible Creation Time element"),
            ("last_visible", "Select last visible Creation Time element"),
            ("center_screen", "Select element closest to screen center"),
            ("largest_date", "Select element with longest date text"),
            ("most_recent", "Select element with most recent date")
        ]
        
        for strategy_name, description in strategies:
            print(f"\nTesting strategy: {strategy_name}")
            print(f"Description: {description}")
            
            try:
                result = await self._apply_selection_strategy(page, strategy_name)
                if result:
                    print(f"   ✅ Result: '{result['date']}' (confidence: {result.get('confidence', 'N/A')})")
                    print(f"   └─ Source: {result.get('source', 'Unknown')}")
                else:
                    print("   ❌ No result")
            
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    async def _apply_selection_strategy(self, page, strategy: str):
        """Apply a specific selection strategy"""
        
        creation_elements = await page.query_selector_all(f"span:has-text('{self.config.creation_time_text}')")
        
        if strategy == "first_visible":
            for i, element in enumerate(creation_elements):
                if await element.is_visible():
                    return await self._extract_date_from_element(element, f"first_visible_{i}")
        
        elif strategy == "last_visible":
            visible_elements = []
            for i, element in enumerate(creation_elements):
                if await element.is_visible():
                    visible_elements.append((i, element))
            if visible_elements:
                i, element = visible_elements[-1]
                return await self._extract_date_from_element(element, f"last_visible_{i}")
        
        elif strategy == "center_screen":
            # Find element closest to screen center
            viewport = await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
            center_x, center_y = viewport["width"] / 2, viewport["height"] / 2
            
            closest_element = None
            min_distance = float('inf')
            
            for i, element in enumerate(creation_elements):
                if await element.is_visible():
                    box = await element.bounding_box()
                    if box:
                        element_x = box["x"] + box["width"] / 2
                        element_y = box["y"] + box["height"] / 2
                        distance = ((element_x - center_x) ** 2 + (element_y - center_y) ** 2) ** 0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_element = (i, element)
            
            if closest_element:
                i, element = closest_element
                result = await self._extract_date_from_element(element, f"center_screen_{i}")
                if result:
                    result["distance_from_center"] = min_distance
                return result
        
        elif strategy == "largest_date":
            best_element = None
            max_date_length = 0
            
            for i, element in enumerate(creation_elements):
                if await element.is_visible():
                    date_result = await self._extract_date_from_element(element, f"largest_date_{i}")
                    if date_result and len(date_result["date"]) > max_date_length:
                        max_date_length = len(date_result["date"])
                        best_element = date_result
            
            return best_element
        
        elif strategy == "most_recent":
            # This would require parsing dates and comparing - simplified for now
            dates_with_elements = []
            
            for i, element in enumerate(creation_elements):
                if await element.is_visible():
                    date_result = await self._extract_date_from_element(element, f"most_recent_{i}")
                    if date_result:
                        dates_with_elements.append(date_result)
            
            # For now, just return the first one (would need date parsing for real comparison)
            return dates_with_elements[0] if dates_with_elements else None
        
        return None
    
    async def _extract_date_from_element(self, element, source: str):
        """Extract date from a Creation Time element"""
        try:
            parent = await element.evaluate_handle("el => el.parentElement")
            spans = await parent.query_selector_all("span")
            
            if len(spans) >= 2:
                date_text = await spans[1].text_content()
                is_visible = await spans[1].is_visible()
                
                return {
                    "date": date_text.strip() if date_text else "Unknown",
                    "source": source,
                    "span_visible": is_visible,
                    "confidence": 0.8 if is_visible else 0.3
                }
        
        except Exception as e:
            return None
        
        return None


async def run_metadata_extraction_test():
    """Main test runner"""
    
    config = GenerationDownloadConfig(
        creation_time_text="Creation Time",
        prompt_ellipsis_pattern="</span>...",
        completed_task_selector="div[id$='__9']",
        thumbnail_selector=".thumsItem, .thumbnail-item"
    )
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=['--start-maximized'])
        context = await browser.new_context(viewport={'width': 2560, 'height': 1440})
        page = await context.new_page()
        
        try:
            print("🧪 METADATA EXTRACTION TEST SUITE")
            print("="*50)
            print("📋 Instructions:")
            print("1. Navigate to the generation page")
            print("2. Log in if needed")
            print("3. Go to completed tasks")
            print("4. Click on a thumbnail to show details")
            print("5. Press Enter to start testing")
            
            input("\nPress Enter when ready...")
            
            tester = MetadataExtractionTester(config)
            results = await tester.test_all_extraction_methods(page)
            
            print("\n🏁 TEST COMPLETED!")
            print(f"📊 Total test results: {len(results)}")
            
            # Save results to file
            results_file = Path(__file__).parent.parent / "logs" / f"metadata_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_file.parent.mkdir(exist_ok=True)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"💾 Results saved to: {results_file}")
            
            input("\nPress Enter to close browser...")
        
        finally:
            await browser.close()


if __name__ == "__main__":
    print("🚀 Starting Metadata Extraction Test Suite...")
    try:
        asyncio.run(run_metadata_extraction_test())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print("❌ Critical error: {e}")
        import traceback
        traceback.print_exc()