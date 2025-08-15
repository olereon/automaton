#!/usr/bin/env python3
"""
CSS Selector Optimizer Tool
Takes complex selectors from browser Inspect tool and creates reliable automation selectors.
"""

import sys
import asyncio
import re
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from playwright.async_api import async_playwright

class SelectorOptimizer:
    def __init__(self):
        self.browser = None
        self.page = None
        
    async def start_browser(self, url: str):
        """Start browser and navigate to target URL"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context(viewport={"width": 1280, "height": 720})
        self.page = await context.new_page()
        
        print(f"🌐 Opening: {url}")
        await self.page.goto(url, wait_until="networkidle")
        print(f"📄 Page loaded: {await self.page.title()}")
    
    def parse_complex_selector(self, selector: str):
        """Parse complex selector and extract useful components"""
        print(f"\n🔍 ANALYZING COMPLEX SELECTOR:")
        print(f"Original: {selector}")
        print("-" * 60)
        
        # Break down the selector
        parts = selector.split(' > ')
        
        print(f"📊 Selector has {len(parts)} nested levels:")
        for i, part in enumerate(parts):
            print(f"  Level {i+1}: {part}")
        
        # Extract different types of identifiers
        identifiers = {
            'ids': [],
            'classes': [],
            'elements': [],
            'ant_classes': [],
            'specific_classes': []
        }
        
        for part in parts:
            # Extract IDs
            if '#' in part:
                id_match = re.findall(r'#([^.\s>]+)', part)
                identifiers['ids'].extend(id_match)
            
            # Extract classes
            class_matches = re.findall(r'\.([^.\s>]+)', part)
            for class_name in class_matches:
                identifiers['classes'].append(class_name)
                
                # Categorize classes
                if class_name.startswith('ant-'):
                    identifiers['ant_classes'].append(class_name)
                elif len(class_name) > 10 and any(c.isupper() for c in class_name):
                    identifiers['specific_classes'].append(class_name)
            
            # Extract element types
            element_match = re.match(r'^([a-zA-Z]+)', part)
            if element_match:
                identifiers['elements'].append(element_match.group(1))
        
        return parts, identifiers
    
    async def generate_selector_alternatives(self, original_selector: str):
        """Generate multiple selector alternatives from complex selector"""
        parts, identifiers = self.parse_complex_selector(original_selector)
        
        alternatives = []
        
        # SKIP root ID - it's never useful for specific elements
        root_ids = ['root', 'app', 'main', 'container']
        useful_ids = [id_name for id_name in identifiers['ids'] if id_name not in root_ids]
        
        # Strategy 1: Use useful IDs only
        if useful_ids:
            for id_name in useful_ids:
                alternatives.append(f"#{id_name}")
        
        # Strategy 2: Focus on last few levels (most specific)
        if len(parts) >= 2:
            # Last level only
            alternatives.append(parts[-1])
            
            # Last 2 levels
            if len(parts) >= 3:
                alternatives.append(' > '.join(parts[-2:]))
            
            # Last 3 levels  
            if len(parts) >= 4:
                alternatives.append(' > '.join(parts[-3:]))
        
        # Strategy 3: Use specific classes from last few levels
        last_level_classes = []
        for part in parts[-3:]:  # Focus on last 3 levels
            class_matches = re.findall(r'\.([^.\s>:]+)', part)
            last_level_classes.extend(class_matches)
        
        # Remove common/generic classes
        generic_classes = ['container', 'wrapper', 'content', 'main']
        specific_classes = [cls for cls in last_level_classes if cls not in generic_classes and len(cls) > 3]
        
        for class_name in specific_classes[-5:]:  # Last 5 specific classes
            alternatives.append(f".{class_name}")
        
        # Strategy 4: Element + class combinations from last levels
        for part in parts[-3:]:
            element_match = re.match(r'^([a-zA-Z]+)', part)
            class_matches = re.findall(r'\.([^.\s>:]+)', part)
            
            if element_match and class_matches:
                element = element_match.group(1)
                for class_name in class_matches:
                    if class_name not in generic_classes:
                        alternatives.append(f"{element}.{class_name}")
        
        # Strategy 5: nth-child selectors (preserve position) - Focus on last level
        nth_parts = [part for part in parts if ':nth-child' in part]
        if nth_parts:
            # Focus on the nth-child selector in the context of its immediate parent
            for i, part in enumerate(parts):
                if ':nth-child' in part:
                    # Add just the nth-child part
                    alternatives.append(part)
                    
                    # Add with immediate parent context
                    if i > 0:
                        parent_part = parts[i-1]
                        alternatives.append(f"{parent_part} > {part}")
                    
                    # Add with parent's parent for more context (last 2 levels)
                    if i > 1:
                        grandparent_part = parts[i-2]
                        parent_part = parts[i-1]
                        alternatives.append(f"{grandparent_part} > {parent_part} > {part}")
        
        # Strategy 6: Multi-class combinations from same element
        for part in parts[-3:]:
            class_matches = re.findall(r'\.([^.\s>:]+)', part)
            if len(class_matches) >= 2:
                combo = '.' + '.'.join(class_matches)
                alternatives.append(combo)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            if alt not in seen:
                seen.add(alt)
                unique_alternatives.append(alt)
        
        return unique_alternatives
    
    async def test_selector_alternatives(self, alternatives: list, original_selector: str):
        """Test all selector alternatives and rank them by reliability"""
        print(f"\n🧪 TESTING SELECTOR ALTERNATIVES:")
        print("=" * 50)
        
        results = []
        
        # Test original selector first
        try:
            original_elements = await self.page.query_selector_all(original_selector)
            print(f"✅ Original selector: {len(original_elements)} element(s)")
            if original_elements:
                results.append({
                    'selector': original_selector,
                    'count': len(original_elements),
                    'type': 'original',
                    'reliability': 'low',  # Complex selectors are fragile
                    'element': original_elements[0]
                })
        except Exception as e:
            print(f"❌ Original selector failed: {e}")
        
        # Test alternatives
        for i, selector in enumerate(alternatives, 1):
            try:
                elements = await self.page.query_selector_all(selector)
                
                if elements:
                    # Get element details
                    element_details = await elements[0].evaluate("""
                        el => {
                            const computedStyle = window.getComputedStyle(el);
                            const rect = el.getBoundingClientRect();
                            const text = el.textContent?.trim() || '';
                            const isClickable = !el.disabled && (
                                el.tagName === 'BUTTON' || 
                                el.tagName === 'A' || 
                                el.onclick || 
                                computedStyle.cursor === 'pointer' ||
                                el.role === 'button' ||
                                el.hasAttribute('onclick') ||
                                el.classList.contains('btn') ||
                                el.classList.contains('button') ||
                                (rect.width > 20 && rect.height > 20 && text.length > 0)
                            );
                            
                            return {
                                tag: el.tagName.toLowerCase(),
                                text: text.substring(0, 40),
                                visible: !el.hidden && el.offsetParent !== null && rect.width > 0 && rect.height > 0,
                                clickable: isClickable,
                                rect: rect,
                                hasText: text.length > 0,
                                classes: Array.from(el.classList).join(' ')
                            };
                        }
                    """)
                    
                    # Determine reliability score
                    reliability = self._assess_reliability(selector, len(elements), element_details)
                    
                    print(f"✅ [{i:2d}] {selector}")
                    print(f"     Elements: {len(elements)} | Reliability: {reliability}")
                    print(f"     Text: \"{element_details['text']}\" | Clickable: {element_details['clickable']}")
                    print(f"     Classes: {element_details['classes']}")
                    print(f"     Position: ({element_details['rect']['x']:.0f}, {element_details['rect']['y']:.0f})")
                    
                    results.append({
                        'selector': selector,
                        'count': len(elements),
                        'type': self._categorize_selector(selector),
                        'reliability': reliability,
                        'element': elements[0],
                        'details': element_details
                    })
                else:
                    print(f"❌ [{i:2d}] {selector} - No elements found")
                    
            except Exception as e:
                print(f"❌ [{i:2d}] {selector} - Error: {e}")
        
        return results
    
    def _assess_reliability(self, selector: str, element_count: int, element_details: dict = None):
        """Assess reliability of a selector based on specificity and element characteristics"""
        # Immediate disqualifiers
        if element_count > 5:
            return 'low'  # Too many matches
        
        # Check for root/container IDs that should be avoided
        root_identifiers = ['root', 'app', 'main', 'container', 'wrapper', 'content']
        if selector.startswith('#') and any(root_id in selector.lower() for root_id in root_identifiers):
            return 'low'  # Root containers are not useful targets
        
        # Check element characteristics if available
        if element_details:
            # Strongly penalize non-clickable elements for button searches
            if not element_details.get('clickable', False):
                return 'very_low'
            
            # Check if element has meaningful text (not just whitespace)
            text = element_details.get('text', '').strip()
            if len(text) == 0 and element_count == 1:
                return 'low'  # Empty elements are less reliable targets
        
        # Assess by element count and selector type
        if element_count == 1:
            if selector.startswith('#') and not any(root_id in selector.lower() for root_id in root_identifiers):
                return 'high'  # Specific non-root ID
            elif selector.count('.') == 1 and len(selector) < 30:
                return 'high'  # Simple class match
            elif 'ant-' in selector:
                return 'medium'  # Framework class
            elif ':nth-child' in selector:
                return 'medium'  # Position-based selector
            else:
                return 'medium'
        elif element_count <= 3:
            if selector.startswith('#'):
                return 'medium'  # ID with multiple matches is suspicious
            elif 'ant-' in selector or selector.count('.') <= 2:
                return 'medium'
            else:
                return 'low'
        else:
            return 'low'
    
    def _categorize_selector(self, selector: str):
        """Categorize selector type"""
        if selector.startswith('#'):
            return 'id'
        elif selector.startswith('.') and selector.count('.') == 1:
            return 'single_class'
        elif selector.startswith('.') and selector.count('.') > 1:
            return 'multi_class'
        elif 'ant-' in selector:
            return 'framework'
        elif '[' in selector:
            return 'attribute'
        elif ' > ' in selector:
            return 'path'
        else:
            return 'element'
    
    def rank_selectors(self, results: list):
        """Rank selectors by reliability and usability"""
        print(f"\n🏆 RECOMMENDED SELECTORS (Best to Worst):")
        print("=" * 55)
        
        # Sort by reliability and specificity, prioritizing clickable elements
        reliability_order = {'very_high': 4, 'high': 3, 'medium': 2, 'low': 1, 'very_low': 0}
        
        sorted_results = sorted(results, key=lambda x: (
            reliability_order.get(x['reliability'], 0),
            bool(x.get('details', {}).get('clickable', False)),  # Prioritize clickable elements
            bool(x.get('details', {}).get('hasText', False)),    # Prioritize elements with text
            -x['count'],  # Prefer fewer matches
            -len(str(x.get('details', {}).get('text', ''))),    # Prefer elements with more text
            len(x['selector'])  # Prefer shorter selectors
        ), reverse=True)
        
        recommendations = []
        
        for i, result in enumerate(sorted_results[:5], 1):
            reliability_icon = {
                'very_high': '🟢',
                'high': '🟡', 
                'medium': '🟠',
                'low': '🔴'
            }.get(result['reliability'], '⚫')
            
            details = result.get('details', {})
            clickable_icon = "👆" if details.get('clickable') else "❌"
            text_preview = f'"{details.get("text", "")}"' if details.get('text') else "(no text)"
            
            print(f"{reliability_icon} [{i}] {result['selector']}")
            print(f"    Type: {result['type']} | Elements: {result['count']} | Reliability: {result['reliability']}")
            print(f"    {clickable_icon} Clickable: {details.get('clickable', False)} | Text: {text_preview}")
            
            if i <= 5:  # Top 5 recommendations
                recommendations.append(result['selector'])
        
        return recommendations
    
    async def test_recommended_selector(self, selector: str):
        """Test a recommended selector interactively"""
        print(f"\n🎯 TESTING RECOMMENDED SELECTOR: {selector}")
        print("-" * 50)
        
        try:
            elements = await self.page.query_selector_all(selector)
            
            if not elements:
                print("❌ No elements found")
                return False
            
            element = elements[0]
            details = await element.evaluate("""
                el => {
                    const computedStyle = window.getComputedStyle(el);
                    const text = el.textContent?.trim() || '';
                    const isClickable = !el.disabled && (
                        el.tagName === 'BUTTON' || 
                        el.tagName === 'A' || 
                        el.onclick || 
                        computedStyle.cursor === 'pointer' ||
                        el.role === 'button' ||
                        el.hasAttribute('onclick') ||
                        el.classList.contains('btn') ||
                        el.classList.contains('button') ||
                        (el.getBoundingClientRect().width > 20 && el.getBoundingClientRect().height > 20 && text.length > 0)
                    );
                    
                    return {
                        tag: el.tagName.toLowerCase(),
                        text: text,
                        clickable: isClickable,
                        rect: el.getBoundingClientRect()
                    };
                }
            """)
            
            print(f"✅ Found element: {details['tag']}")
            print(f"   Text: \"{details['text'][:50]}\"")
            print(f"   Position: ({details['rect']['x']:.0f}, {details['rect']['y']:.0f})")
            print(f"   Clickable: {details['clickable']}")
            
            if details['clickable']:
                test_click = input("\n👆 Test click this element? (y/n): ").strip().lower()
                if test_click == 'y':
                    old_url = self.page.url
                    old_title = await self.page.title()
                    
                    await element.click(timeout=5000)
                    await self.page.wait_for_timeout(2000)
                    
                    new_url = self.page.url
                    new_title = await self.page.title()
                    
                    if old_url != new_url:
                        print(f"✅ Click successful - Navigation to: {new_url}")
                    elif old_title != new_title:
                        print(f"✅ Click successful - Title changed")
                    else:
                        print("✅ Click successful - No navigation detected")
                        
                        # Check for modals/dropdowns
                        modal = await self.page.query_selector('.modal, .dropdown, .popup, [role="dialog"]')
                        if modal:
                            print("✨ Modal/dropdown appeared")
                    
                    success = input("Did this achieve the expected result? (y/n): ").strip().lower()
                    return success == 'y'
            else:
                # For non-clickable elements, ask the user if this is the right element
                print(f"\n⚠️ This element is not clickable.")
                verify = input("Is this the element you were looking for? (y/n): ").strip().lower()
                return verify == 'y'
            
        except Exception as e:
            print(f"❌ Error testing selector: {e}")
            return False
    
    async def close(self):
        """Close browser"""
        try:
            if self.browser:
                await self.browser.close()
        except:
            pass

async def test_selector_list(optimizer, selectors, list_type="selector", show_details=False, results_data=None):
    """Test selectors from a list (recommended or complete)"""
    print(f"Testing {list_type}s one by one to find the right element")
    print("-" * 50)
    
    for i, selector in enumerate(selectors, 1):
        # Show additional details for complete list
        details_info = ""
        if show_details and results_data:
            # Find the result data for this selector
            selector_data = next((r for r in results_data if r['selector'] == selector), None)
            if selector_data:
                reliability = selector_data['reliability']
                text = selector_data['details']['text'][:30]
                clickable = selector_data['details']['clickable']
                details_info = f" | Reliability: {reliability} | Text: \"{text}\" | Clickable: {clickable}"
        
        test_choice = input(f"\nTest {list_type} #{i}: {selector}{details_info}\n(y/n/quit): ").strip().lower()
        
        if test_choice == 'quit' or test_choice == 'q':
            print("🛑 Testing stopped by user")
            break
        elif test_choice == 'y':
            success = await optimizer.test_recommended_selector(selector)
            if success:
                print(f"\n🎉 SUCCESS! Use this selector for automation:")
                print(f"✨ {selector}")
                return True
            else:
                print(f"❌ This wasn't the right element")
                if i < len(selectors):
                    continue_testing = input(f"Continue testing other {list_type}s? (y/n): ").strip().lower()
                    if continue_testing != 'y':
                        break
        else:
            print(f"⏭️ Skipping {list_type} #{i}")
    
    return False

async def test_custom_selector(optimizer):
    """Test a user-provided custom selector"""
    print(f"\n🔧 CUSTOM SELECTOR TESTING:")
    print("Enter your own CSS selector to test")
    print("💡 Tip: Looking for an element with text '0'? Try selectors like:")
    print("   • div.sc-eDOMzu.gfvVdd")
    print("   • .sc-eDOMzu")  
    print("   • .gfvVdd")
    print("-" * 50)
    
    while True:
        custom_selector = input("\n📝 Enter custom selector (or 'back' to return): ").strip()
        
        if custom_selector.lower() == 'back' or not custom_selector:
            print("🔙 Returning to main testing menu")
            break
            
        try:
            # Test the custom selector
            print(f"\n🧪 Testing custom selector: {custom_selector}")
            
            # Get element details first
            elements = await optimizer.page.query_selector_all(custom_selector)
            
            if not elements:
                print(f"❌ No elements found with selector: {custom_selector}")
                retry = input("Try another custom selector? (y/n): ").strip().lower()
                if retry != 'y':
                    break
                continue
            
            # Get element details
            element = elements[0]
            element_details = await optimizer.page.evaluate(f"""
                (selector) => {{
                    const el = document.querySelector(selector);
                    if (!el) return null;
                    
                    const computedStyle = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    const text = el.textContent?.trim() || '';
                    const isClickable = !el.disabled && (
                        el.tagName === 'BUTTON' || 
                        el.tagName === 'A' || 
                        el.onclick || 
                        computedStyle.cursor === 'pointer' ||
                        el.role === 'button' ||
                        el.hasAttribute('onclick') ||
                        el.classList.contains('btn') ||
                        el.classList.contains('button') ||
                        (rect.width > 20 && rect.height > 20 && text.length > 0)
                    );
                    
                    return {{
                        tag: el.tagName.toLowerCase(),
                        text: text.substring(0, 100),
                        visible: !el.hidden && el.offsetParent !== null && rect.width > 0 && rect.height > 0,
                        clickable: isClickable,
                        rect: rect,
                        hasText: text.length > 0,
                        classes: Array.from(el.classList).join(' ')
                    }};
                }}
            """, custom_selector)
            
            # Display element information
            print(f"✅ Found {len(elements)} element(s)")
            print(f"📋 Element details:")
            print(f"    Text: \"{element_details['text']}\"")
            print(f"    Tag: <{element_details['tag']}>")
            print(f"    Classes: {element_details['classes']}")
            print(f"    Clickable: {element_details['clickable']}")
            print(f"    Position: ({element_details['rect']['x']:.0f}, {element_details['rect']['y']:.0f})")
            print(f"    Visible: {element_details['visible']}")
            
            # Test with highlight
            test_choice = input(f"\nTest this custom selector (highlight element)? (y/n): ").strip().lower()
            if test_choice == 'y':
                success = await optimizer.test_recommended_selector(custom_selector)
                if success:
                    print(f"\n🎉 SUCCESS! Your custom selector works:")
                    print(f"✨ {custom_selector}")
                    return True
                else:
                    print(f"❌ This wasn't the right element")
            
            # Ask if they want to try another custom selector
            retry = input("\nTry another custom selector? (y/n): ").strip().lower()
            if retry != 'y':
                break
                
        except Exception as e:
            print(f"❌ Error testing custom selector: {e}")
            retry = input("Try another custom selector? (y/n): ").strip().lower()
            if retry != 'y':
                break
    
    return False

async def optimize_single_selector(optimizer, complex_selector):
    """Optimize a single complex selector and return success status"""
    print(f"\n🔄 OPTIMIZING NEW SELECTOR...")
    print("=" * 60)
    
    # Generate alternatives
    alternatives = await optimizer.generate_selector_alternatives(complex_selector)
    
    # Test alternatives
    results = await optimizer.test_selector_alternatives(alternatives, complex_selector)
    
    if results:
        # Rank and recommend
        recommendations = optimizer.rank_selectors(results)
        
        print(f"\n🎯 TOP RECOMMENDATIONS FOR AUTOMATION:")
        print("-" * 45)
        for i, selector in enumerate(recommendations, 1):
            print(f"{i}. {selector}")
        
        # Enhanced interactive testing with multiple options
        if recommendations:
            print(f"\n🎯 INTERACTIVE TESTING:")
            print("Choose your testing approach:")
            print("1. Test recommended selectors (filtered, high reliability)")
            print("2. Test from complete list (all selectors including low reliability)")
            print("3. Test a custom selector")
            print("4. Skip testing (just show results)")
            print("-" * 60)
            
            testing_choice = input("Choose testing option (1-4): ").strip()
            
            if testing_choice == "1":
                # Test recommended selectors
                print(f"\n📋 Testing recommended selectors (high reliability):")
                await test_selector_list(optimizer, recommendations, "recommendation")
                
            elif testing_choice == "2":
                # Test from complete list
                print(f"\n📋 Testing from complete selector list (including low reliability):")
                print("💡 This includes the 'very_low' reliability selectors you saw in the analysis")
                all_selectors = [result['selector'] for result in results]
                await test_selector_list(optimizer, all_selectors, "selector from complete list", show_details=True, results_data=results)
                
            elif testing_choice == "3":
                # Test custom selector
                await test_custom_selector(optimizer)
                
            elif testing_choice == "4":
                print("⏭️ Skipping interactive testing")
                
            else:
                print("❌ Invalid choice, skipping testing")
                
            # Always show final summary
            print(f"\n📋 SUMMARY - All available selectors:")
            print(f"🏆 Recommended (high reliability): {len(recommendations)} selectors")
            print(f"📋 Complete list (all): {len(results)} selectors")
    else:
        print("❌ No working selectors found")
    
    return False

async def main():
    print("🔧 CSS SELECTOR OPTIMIZER")
    print("=" * 40)
    print("Convert complex browser selectors into automation-friendly ones")
    print("✨ Supports multiple selector optimizations in one session!")
    
    # Get initial inputs
    url = input("\n🌐 Enter website URL: ").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    optimizer = SelectorOptimizer()
    
    try:
        await optimizer.start_browser(url)
        
        print("\n📖 Navigate to the exact page where the element exists, then press Enter...")
        input()
        
        # Main optimization loop
        while True:
            print("\n" + "=" * 60)
            complex_selector = input("\n📋 Paste the complex selector from Inspect tool:\n").strip()
            
            if not complex_selector:
                print("❌ No selector provided")
                continue
            
            # Optimize the selector
            await optimize_single_selector(optimizer, complex_selector)
            
            # Ask if user wants to continue
            print("\n" + "=" * 60)
            print("🔄 SESSION CONTINUATION")
            continue_choice = input("\nOptimize another selector? (y/n): ").strip().lower()
            
            if continue_choice != 'y':
                print("👋 Closing selector optimizer...")
                break
            
            # Ask about page navigation
            print("\nWhere is the next element?")
            print("1. Same page (continue on current page)")
            print("2. Different page (navigate to new page)")
            
            page_choice = input("Choose option (1/2): ").strip()
            
            if page_choice == '2':
                print("\n🌐 Navigate to the page with your next element...")
                print("Press Enter when you're ready to continue...")
                input()
                
                # Verify new page loaded
                current_url = optimizer.page.url
                current_title = await optimizer.page.title()
                print(f"📄 Current page: {current_title}")
                print(f"🔗 URL: {current_url}")
            else:
                print("✅ Continuing on current page...")
        
    except KeyboardInterrupt:
        print("\n🛑 Selector optimization cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await optimizer.close()
        print("\n✅ Browser closed. Session ended.")

if __name__ == "__main__":
    asyncio.run(main())