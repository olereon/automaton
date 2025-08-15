#!/usr/bin/env python3
"""
CSS Selector Finder Tool
This tool helps you find the correct CSS selectors for your target website.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from playwright.async_api import async_playwright

class SelectorFinder:
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
        
    async def analyze_page_elements(self, comprehensive=False):
        """Analyze and display common elements on the page"""
        print(f"\n🔍 ANALYZING PAGE ELEMENTS ({await self.page.title()})")
        print(f"🌐 URL: {self.page.url}")
        print("=" * 70)
        
        if comprehensive:
            # Comprehensive analysis for full page discovery
            await self._find_navigation_elements()
            await self._find_interactive_elements()
            await self._find_content_elements()
            await self._find_dynamic_elements()
        
        # Standard analysis
        await self._find_login_elements()
        await self._find_input_elements()
        await self._find_button_elements()
        await self._find_form_elements()
        await self._find_link_elements()
        await self._find_clickable_elements()
        
    async def _find_login_elements(self):
        """Find potential login-related elements"""
        print("\n🔐 LOGIN ELEMENTS:")
        print("-" * 20)
        
        # Common login selectors
        login_patterns = [
            ("Username/Email fields", ["input[name*='user']", "input[name*='email']", "input[name*='login']", 
                               "input[id*='user']", "input[id*='email']", "input[id*='login']",
                               "input[type='email']", "input[placeholder*='username']", "input[placeholder*='email']",
                               "input[placeholder*='Email']", "input[placeholder='Email address']", "input[type='text'][placeholder*='email']",
                               "input[type='text'][placeholder*='Email']"]),
            ("Password fields", ["input[type='password']", "input[name*='pass']", "input[id*='pass']",
                               "input[placeholder*='password']"]),
            ("Login buttons", ["button[type='submit']", "input[type='submit']", "button[name*='login']",
                             "button[id*='login']", "[role='button'][name*='login']", "a[href*='login']"])
        ]
        
        for category, selectors in login_patterns:
            print(f"\n📝 {category}:")
            found_any = False
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    found_any = True
                    print(f"  ✅ {selector} → {len(elements)} element(s)")
                    for i, element in enumerate(elements[:2]):  # Show first 2
                        attrs = await element.evaluate("""
                            el => ({
                                tag: el.tagName.toLowerCase(),
                                id: el.id,
                                name: el.name,
                                class: el.className,
                                type: el.type,
                                placeholder: el.placeholder,
                                value: el.value
                            })
                        """)
                        print(f"     Element {i+1}: {attrs}")
            
            if not found_any:
                print(f"  ❌ No {category.lower()} found with common patterns")
    
    async def _find_input_elements(self):
        """Find all input elements"""
        print("\n📝 ALL INPUT ELEMENTS:")
        print("-" * 25)
        
        inputs = await self.page.query_selector_all("input")
        print(f"Total inputs found: {len(inputs)}")
        
        for i, inp in enumerate(inputs):
            attrs = await inp.evaluate("""
                el => ({
                    id: el.id,
                    name: el.name,
                    type: el.type,
                    class: el.className,
                    placeholder: el.placeholder,
                    required: el.required,
                    visible: !el.hidden && el.offsetParent !== null
                })
            """)
            
            # Generate possible selectors
            selectors = []
            if attrs['id']:
                selectors.append(f"#{attrs['id']}")
            if attrs['name']:
                selectors.append(f"input[name='{attrs['name']}']")
            if attrs['type']:
                selectors.append(f"input[type='{attrs['type']}']")
            
            print(f"\n  Input {i+1}: {attrs}")
            print(f"    Suggested selectors: {selectors}")
    
    async def _find_button_elements(self):
        """Find all button elements"""
        print("\n🔘 ALL BUTTON ELEMENTS:")
        print("-" * 25)
        
        # Find buttons and button-like elements
        button_selectors = ["button", "input[type='submit']", "input[type='button']", "[role='button']"]
        
        for selector in button_selectors:
            elements = await self.page.query_selector_all(selector)
            if elements:
                print(f"\n{selector} → {len(elements)} element(s)")
                for i, btn in enumerate(elements):
                    attrs = await btn.evaluate("""
                        el => ({
                            tag: el.tagName.toLowerCase(),
                            id: el.id,
                            name: el.name,
                            type: el.type,
                            class: el.className,
                            text: el.textContent?.trim(),
                            value: el.value,
                            visible: !el.hidden && el.offsetParent !== null
                        })
                    """)
                    
                    # Generate selectors
                    selectors = []
                    if attrs['id']:
                        selectors.append(f"#{attrs['id']}")
                    if attrs['name']:
                        selectors.append(f"{attrs['tag']}[name='{attrs['name']}']")
                    if attrs['text']:
                        selectors.append(f"{attrs['tag']}:has-text('{attrs['text'][:20]}')")
                    
                    print(f"    Button {i+1}: {attrs}")
                    print(f"      Suggested selectors: {selectors}")
    
    async def _find_form_elements(self):
        """Find form elements"""
        print("\n📋 FORM ELEMENTS:")
        print("-" * 18)
        
        forms = await self.page.query_selector_all("form")
        print(f"Forms found: {len(forms)}")
        
        for i, form in enumerate(forms):
            attrs = await form.evaluate("""
                el => ({
                    id: el.id,
                    name: el.name,
                    action: el.action,
                    method: el.method,
                    class: el.className
                })
            """)
            
            print(f"\n  Form {i+1}: {attrs}")
            
            # Find inputs within this form
            form_inputs = await form.query_selector_all("input")
            print(f"    Inputs in form: {len(form_inputs)}")
    
    async def _find_navigation_elements(self):
        """Find navigation elements like menus, tabs, breadcrumbs"""
        print("\n🧭 NAVIGATION ELEMENTS:")
        print("-" * 25)
        
        nav_patterns = [
            ("Navigation menus", ["nav", "[role='navigation']", ".nav", ".navbar", ".menu", ".navigation"]),
            ("Tab elements", ["[role='tab']", ".tab", ".tabs", "[data-tab]", ".tab-content", ".tab-pane"]),
            ("Menu items", ["[role='menuitem']", ".menu-item", ".nav-item", "li a", ".dropdown-item"]),
            ("Breadcrumbs", [".breadcrumb", "[aria-label*='breadcrumb']", ".breadcrumbs", ".crumb"]),
            ("Dropdowns", [".dropdown", ".select", "[role='combobox']", ".dropdown-menu"])
        ]
        
        for category, selectors in nav_patterns:
            print(f"\n📝 {category}:")
            found_any = False
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    found_any = True
                    print(f"  ✅ {selector} → {len(elements)} element(s)")
                    for i, element in enumerate(elements[:2]):
                        try:
                            attrs = await element.evaluate("""
                                el => ({
                                    tag: el.tagName.toLowerCase(),
                                    id: el.id,
                                    class: el.className,
                                    text: el.textContent?.trim()?.substring(0, 50),
                                    href: el.href,
                                    visible: !el.hidden && el.offsetParent !== null
                                })
                            """)
                            print(f"     Element {i+1}: {attrs}")
                        except:
                            print(f"     Element {i+1}: Could not analyze")
            
            if not found_any:
                print(f"  ❌ No {category.lower()} found")
    
    async def _find_interactive_elements(self):
        """Find all interactive elements like dropdowns, modals, etc."""
        print("\n⚡ INTERACTIVE ELEMENTS:")
        print("-" * 28)
        
        interactive_patterns = [
            ("Dropdown selects", ["select", "[role='listbox']", ".select", ".dropdown-select"]),
            ("Checkboxes", ["input[type='checkbox']", "[role='checkbox']", ".checkbox"]),
            ("Radio buttons", ["input[type='radio']", "[role='radio']", ".radio"]),
            ("Sliders/Ranges", ["input[type='range']", "[role='slider']", ".slider", ".range"]),
            ("File uploads", ["input[type='file']", ".file-upload", ".upload"]),
            ("Toggle switches", [".toggle", ".switch", "[role='switch']", ".toggle-switch"]),
            ("Modal triggers", ["[data-toggle='modal']", "[data-target*='modal']", ".modal-trigger"]),
            ("Accordion items", [".accordion", ".collapse", "[data-toggle='collapse']"])
        ]
        
        for category, selectors in interactive_patterns:
            print(f"\n📝 {category}:")
            found_any = False
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    found_any = True
                    print(f"  ✅ {selector} → {len(elements)} element(s)")
                    
            if not found_any:
                print(f"  ❌ No {category.lower()} found")
    
    async def _find_link_elements(self):
        """Find all link elements"""
        print("\n🔗 LINK ELEMENTS:")
        print("-" * 18)
        
        links = await self.page.query_selector_all("a[href]")
        print(f"Total links found: {len(links)}")
        
        # Categorize links
        internal_links = []
        external_links = []
        anchor_links = []
        
        current_domain = self.page.url.split('/')[2] if '/' in self.page.url else ''
        
        for link in links[:20]:  # Analyze first 20 links
            try:
                attrs = await link.evaluate("""
                    el => ({
                        href: el.href,
                        text: el.textContent?.trim()?.substring(0, 30),
                        id: el.id,
                        class: el.className,
                        target: el.target,
                        visible: !el.hidden && el.offsetParent !== null
                    })
                """)
                
                if attrs['href'].startswith('#'):
                    anchor_links.append(attrs)
                elif current_domain in attrs['href']:
                    internal_links.append(attrs)
                else:
                    external_links.append(attrs)
                    
            except:
                continue
        
        print(f"\n📍 Internal links: {len(internal_links)}")
        for i, link in enumerate(internal_links[:5]):
            print(f"  {i+1}. {link['text']} → {link['href']}")
            
        print(f"\n🌐 External links: {len(external_links)}")
        for i, link in enumerate(external_links[:3]):
            print(f"  {i+1}. {link['text']} → {link['href']}")
            
        print(f"\n⚓ Anchor links: {len(anchor_links)}")
        for i, link in enumerate(anchor_links[:3]):
            print(f"  {i+1}. {link['text']} → {link['href']}")
    
    async def _find_clickable_elements(self):
        """Find all clickable elements that aren't buttons or links"""
        print("\n👆 OTHER CLICKABLE ELEMENTS:")
        print("-" * 32)
        
        clickable_patterns = [
            ("Clickable divs/spans", ["div[onclick]", "span[onclick]", "[role='button']"]),
            ("Images with links", ["img[onclick]", "a img", ".clickable-image"]),
            ("List items", ["li[onclick]", ".clickable-item", "[role='option']"]),
            ("Table rows/cells", ["tr[onclick]", "td[onclick]", ".clickable-row"]),
            ("Cards/Panels", [".card[onclick]", ".panel[onclick]", ".clickable-card"])
        ]
        
        for category, selectors in clickable_patterns:
            print(f"\n📝 {category}:")
            found_any = False
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    found_any = True
                    print(f"  ✅ {selector} → {len(elements)} element(s)")
                    
            if not found_any:
                print(f"  ❌ No {category.lower()} found")
    
    async def _find_content_elements(self):
        """Find content elements that might be relevant for automation"""
        print("\n📄 CONTENT ELEMENTS:")
        print("-" * 22)
        
        # Find headings
        headings = await self.page.query_selector_all("h1, h2, h3, h4, h5, h6")
        print(f"\n📝 Headings found: {len(headings)}")
        for i, heading in enumerate(headings[:5]):
            try:
                text = await heading.text_content()
                tag = await heading.evaluate("el => el.tagName.toLowerCase()")
                print(f"  {tag.upper()}: {text.strip()[:50]}")
            except:
                continue
        
        # Find tables
        tables = await self.page.query_selector_all("table")
        print(f"\n📊 Tables found: {len(tables)}")
        
        # Find lists
        lists = await self.page.query_selector_all("ul, ol")
        print(f"\n📋 Lists found: {len(lists)}")
    
    async def _find_dynamic_elements(self):
        """Find elements that might be dynamically loaded"""
        print("\n🔄 DYNAMIC ELEMENTS:")
        print("-" * 22)
        
        dynamic_patterns = [
            ("Loading indicators", [".loading", ".spinner", "[aria-busy='true']", ".progress"]),
            ("Popup/Modal containers", [".modal", ".popup", ".overlay", ".dialog"]),
            ("AJAX containers", ["[data-load]", ".ajax-content", ".dynamic-content"]),
            ("Infinite scroll", [".infinite-scroll", "[data-scroll]", ".lazy-load"])
        ]
        
        for category, selectors in dynamic_patterns:
            print(f"\n📝 {category}:")
            found_any = False
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    found_any = True
                    print(f"  ✅ {selector} → {len(elements)} element(s)")
                    
            if not found_any:
                print(f"  ❌ No {category.lower()} found")
    
    async def find_combined(self, element_type: str, text: str):
        """Find elements by combining element type and text"""
        print(f"\n🎯 COMBINED SEARCH: {element_type.upper()} containing '{text}'")
        print("-" * 60)
        
        # Define element type patterns
        element_patterns = {
            'button': ['button', 'input[type="button"]', 'input[type="submit"]', '[role="button"]'],
            'link': ['a', '[role="link"]'],
            'input': ['input', 'textarea'],
            'dropdown': ['select', '[role="combobox"]', '.ant-select', '[role="listbox"]'],
            'div': ['div'],
            'span': ['span'],
            'label': ['label'],
            'clickable': ['button', 'a', '[onclick]', '[role="button"]', '[style*="cursor: pointer"]']
        }
        
        if element_type not in element_patterns:
            print(f"❌ Unknown element type: {element_type}")
            print(f"Available types: {', '.join(element_patterns.keys())}")
            return []
        
        try:
            found_elements = []
            
            # Search with combined criteria
            for base_selector in element_patterns[element_type]:
                search_patterns = [
                    (f"{base_selector}:has-text('{text}')", f"{base_selector} with exact text"),
                    (f"{base_selector}:has-text('{text.lower()}')", f"{base_selector} with text (case-insensitive)"),
                    (f"{base_selector}[title*='{text}']", f"{base_selector} with title containing text"),
                    (f"{base_selector}[aria-label*='{text}']", f"{base_selector} with aria-label containing text"),
                ]
                
                if element_type == 'input':
                    search_patterns.append((f"{base_selector}[placeholder*='{text}']", f"{base_selector} with placeholder containing text"))
                
                for selector, description in search_patterns:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            print(f"\n✅ {description}: {len(elements)} found")
                            for i, element in enumerate(elements[:3]):
                                attrs = await element.evaluate("""
                                    el => ({
                                        tag: el.tagName.toLowerCase(),
                                        id: el.id,
                                        class: el.className,
                                        text: el.textContent?.trim()?.substring(0, 60),
                                        title: el.title,
                                        ariaLabel: el.getAttribute('aria-label'),
                                        visible: !el.hidden && el.offsetParent !== null,
                                        clickable: !el.disabled && (el.tagName === 'BUTTON' || 
                                                  el.tagName === 'A' || el.onclick || 
                                                  el.style.cursor === 'pointer' ||
                                                  el.role === 'button'),
                                        rect: el.getBoundingClientRect()
                                    })
                                """)
                                
                                # Generate the best selector for this element
                                best_selector = self._generate_best_selector(attrs, text)
                                attrs['best_selector'] = best_selector
                                attrs['search_selector'] = selector
                                
                                print(f"  {i+1}. {attrs['tag']} - \"{attrs['text'][:40]}\"")
                                print(f"     Best Selector: {best_selector}")
                                print(f"     Search Selector: {selector}")
                                print(f"     Position: {attrs['rect']['x']:.0f}, {attrs['rect']['y']:.0f}")
                                if attrs['clickable']:
                                    print(f"     ✓ Clickable")
                                if not attrs['visible']:
                                    print(f"     ⚠️ Hidden")
                                
                                found_elements.append(attrs)
                    except Exception as e:
                        continue
            
            if not found_elements:
                print(f"\n❌ No {element_type} elements found with text: '{text}'")
                print("\n💡 Try:")
                print(f"   - Different element type: button, link, div, span, clickable")
                print(f"   - Partial text: '{text[:len(text)//2]}'")
                print(f"   - Case variations or single words")
            else:
                print(f"\n📊 Total {element_type} elements found: {len(found_elements)}")
                
            return found_elements
            
        except Exception as e:
            print(f"❌ Error in combined search: {e}")
            return []
    
    async def find_by_text(self, text: str, store_results: bool = True):
        """Find elements by their visible text content"""
        print(f"\n🔍 SEARCHING FOR TEXT: '{text}'")
        print("-" * 50)
        
        try:
            # Search strategies for text
            search_patterns = [
                (f"*:has-text('{text}')", "Elements containing exact text"),
                (f"*:has-text('{text.lower()}')", "Elements containing text (case-insensitive)"),
                (f"[title*='{text}']", "Elements with title attribute"),
                (f"[aria-label*='{text}']", "Elements with aria-label"),
                (f"[placeholder*='{text}']", "Input placeholders"),
                (f"button:has-text('{text}')", "Buttons with text"),
                (f"span:has-text('{text}')", "Spans with text"),
                (f"div:has-text('{text}')", "Divs with text"),
                (f"label:has-text('{text}')", "Labels with text"),
                (f"a:has-text('{text}')", "Links with text")
            ]
            
            # Store search results for iterative testing
            search_results = {}
            all_found_elements = []
            
            for search_index, (selector, description) in enumerate(search_patterns):
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"\n✅ [{search_index + 1}] {description}: {len(elements)} found")
                        
                        # Store all elements for this category
                        category_elements = []
                        
                        for i, element in enumerate(elements):
                            try:
                                attrs = await element.evaluate("""
                                    el => ({
                                        tag: el.tagName.toLowerCase(),
                                        id: el.id,
                                        class: el.className,
                                        text: el.textContent?.trim()?.substring(0, 60),
                                        title: el.title,
                                        visible: !el.hidden && el.offsetParent !== null,
                                        clickable: !el.disabled && (el.tagName === 'BUTTON' || 
                                                  el.tagName === 'A' || el.onclick || 
                                                  el.style.cursor === 'pointer' ||
                                                  el.role === 'button'),
                                        rect: el.getBoundingClientRect()
                                    })
                                """)
                                
                                # Generate the best selector for this element
                                best_selector = self._generate_best_selector(attrs, text)
                                attrs['best_selector'] = best_selector
                                attrs['original_selector'] = selector
                                attrs['element_index'] = i
                                
                                category_elements.append(attrs)
                                all_found_elements.append(attrs)
                                
                            except:
                                continue
                        
                        # Store category results
                        if category_elements:
                            search_results[search_index + 1] = {
                                'description': description,
                                'selector': selector,
                                'elements': category_elements
                            }
                        
                        # Show first 3 elements for preview
                        for i, attrs in enumerate(category_elements[:3]):
                            print(f"  {i+1}. {attrs['tag']} - \"{attrs['text'][:40]}\"")
                            print(f"     Position: ({attrs['rect']['x']:.0f}, {attrs['rect']['y']:.0f})")
                            print(f"     Selector: {attrs['best_selector']}")
                            if attrs['clickable']:
                                print(f"     ✓ Clickable")
                        
                        if len(category_elements) > 3:
                            print(f"  ... and {len(category_elements) - 3} more")
                            
                except:
                    continue
            
            # Store results for iterative testing
            if store_results and search_results:
                self.last_search_results = search_results
                self.last_search_text = text
                
                print(f"\n📊 TOTAL: {len(all_found_elements)} elements found across {len(search_results)} categories")
                print("\n💡 Use iterative testing:")
                print("   'iterate <category> -r <range>'  - Test specific category")
                print("   'iterate all -r 1-5'             - Test first 5 from all categories")
                print("   'iterate 1 -r all'              - Test all from category 1")
                print("   'show-categories'                - List available categories")
            
            if not all_found_elements:
                print(f"\n❌ No elements found with text: '{text}'")
                print("\n💡 Try:")
                print(f"   - Partial text: '{text[:len(text)//2]}'")
                print(f"   - Single word from the text")
                print(f"   - Check if text is in a dropdown/modal")
            
            return all_found_elements
            
        except Exception as e:
            print(f"❌ Error searching for text: {e}")
            return []
    
    def _generate_best_selector(self, attrs, text):
        """Generate the most reliable selector for an element"""
        # Priority order for selectors
        if attrs.get('id'):
            return f"#{attrs['id']}"
        elif attrs.get('title'):
            return f"{attrs['tag']}[title='{attrs['title']}']"
        elif text and len(text) < 30:
            return f"{attrs['tag']}:has-text('{text}')"
        elif attrs.get('class'):
            # Use the most specific class
            classes = attrs['class'].split()
            if classes:
                return f"{attrs['tag']}.{classes[0]}"
        else:
            return f"{attrs['tag']}"
    
    def _parse_range(self, range_str: str, max_count: int):
        """Parse range string like '1-5', '3,7,12', 'all'"""
        if range_str.lower() == 'all':
            return list(range(max_count))
        
        indices = []
        parts = range_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                try:
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip())
                    indices.extend(range(max(0, start_idx), min(max_count, end_idx)))
                except ValueError:
                    continue
            else:
                try:
                    idx = int(part) - 1
                    if 0 <= idx < max_count:
                        indices.append(idx)
                except ValueError:
                    continue
        
        return sorted(list(set(indices)))
    
    async def show_search_categories(self):
        """Show available search categories from last search"""
        if not hasattr(self, 'last_search_results'):
            print("❌ No recent search results. Run a text search first.")
            return
        
        print(f"\n📋 SEARCH CATEGORIES for '{self.last_search_text}':")
        print("-" * 50)
        
        for category_id, category_data in self.last_search_results.items():
            print(f"[{category_id}] {category_data['description']}")
            print(f"    Elements: {len(category_data['elements'])}")
            print(f"    Selector: {category_data['selector']}")
    
    async def iterate_test_elements(self, category: str, range_str: str):
        """Iteratively test elements from search results"""
        if not hasattr(self, 'last_search_results'):
            print("❌ No recent search results. Run a text search first.")
            return
        
        print(f"\n🔄 ITERATIVE TESTING: Category {category}, Range {range_str}")
        print("=" * 60)
        
        # Determine which elements to test
        elements_to_test = []
        
        if category.lower() == 'all':
            # Collect elements from all categories
            for cat_data in self.last_search_results.values():
                elements_to_test.extend(cat_data['elements'])
        else:
            # Specific category
            try:
                category_id = int(category)
                if category_id in self.last_search_results:
                    elements_to_test = self.last_search_results[category_id]['elements']
                else:
                    print(f"❌ Category {category_id} not found.")
                    await self.show_search_categories()
                    return
            except ValueError:
                print("❌ Invalid category. Use number or 'all'.")
                return
        
        if not elements_to_test:
            print("❌ No elements found for testing.")
            return
        
        # Parse range
        indices = self._parse_range(range_str, len(elements_to_test))
        if not indices:
            print(f"❌ Invalid range: {range_str}")
            print("💡 Examples: '1-5', '3,7,12', 'all'")
            return
        
        print(f"📊 Testing {len(indices)} elements from {len(elements_to_test)} available")
        
        # Iterative testing
        successful_selector = None
        for i, element_idx in enumerate(indices):
            if element_idx >= len(elements_to_test):
                continue
                
            element = elements_to_test[element_idx]
            
            print(f"\n🔄 [{i+1}/{len(indices)}] Testing Element #{element_idx + 1}")
            print("-" * 40)
            print(f"Text: \"{element['text'][:50]}\"")
            print(f"Tag: {element['tag']}")
            print(f"Position: ({element['rect']['x']:.0f}, {element['rect']['y']:.0f})")
            print(f"Selector: {element['best_selector']}")
            print(f"Clickable: {element['clickable']}")
            
            if element['clickable']:
                # Perform click test
                try:
                    print(f"\n👆 Attempting click on: {element['best_selector']}")
                    
                    # Find the element again (fresh reference)
                    page_elements = await self.page.query_selector_all(element['original_selector'])
                    if element['element_index'] < len(page_elements):
                        target_element = page_elements[element['element_index']]
                        
                        # Try clicking
                        old_url = self.page.url
                        old_title = await self.page.title()
                        
                        await target_element.click(timeout=5000)
                        await self.page.wait_for_timeout(1500)
                        
                        new_url = self.page.url
                        new_title = await self.page.title()
                        
                        # Report results
                        if old_url != new_url:
                            print(f"✅ Click succeeded - Navigation to: {new_url}")
                        elif old_title != new_title:
                            print(f"✅ Click succeeded - Title changed: {new_title}")
                        else:
                            print("✅ Click succeeded - No navigation detected")
                            
                            # Check for modals/dropdowns
                            modal = await self.page.query_selector('.modal, .dropdown, .popup, [role="dialog"], .ant-dropdown')
                            if modal:
                                print("✨ Modal/dropdown appeared")
                        
                        # User verification
                        verification = input(f"\n❓ Did this click achieve what you expected? (y/n/s=skip remaining): ").strip().lower()
                        
                        if verification == 'y':
                            print(f"✅ SUCCESS! Use this selector: {element['best_selector']}")
                            successful_selector = element['best_selector']
                            
                            # Ask if user wants to continue testing or stop here
                            continue_testing = input("Continue testing remaining elements? (y/n): ").strip().lower()
                            if continue_testing != 'y':
                                print("🎯 Stopping iterative testing - successful element found!")
                                return successful_selector
                                
                        elif verification == 's':
                            print("⏭️ Skipping remaining elements")
                            break
                        else:
                            print("❌ Not the expected result, continuing...")
                    
                except Exception as e:
                    print(f"❌ Click failed: {e}")
                    
                    # Ask user if they want to continue
                    continue_testing = input("Continue with next element? (y/n): ").strip().lower()
                    if continue_testing != 'y':
                        break
            else:
                print("⚠️ Element not clickable - skipping")
            
            # Pause between tests (except for last one)
            if i < len(indices) - 1:
                input("\nPress Enter to test next element (or Ctrl+C to stop)...")
        
        print("\n🏁 Iterative testing completed!")
        if successful_selector:
            print(f"🎯 Recommended selector: {successful_selector}")
        return successful_selector
    
    async def find_all_visible_text(self):
        """Find all visible text elements on the page"""
        print("\n📝 VISIBLE TEXT ELEMENTS:")
        print("-" * 30)
        
        try:
            # Get all text-containing elements
            text_elements = await self.page.evaluate("""
                () => {
                    const elements = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    const seen = new Set();
                    
                    while (node = walker.nextNode()) {
                        const text = node.textContent.trim();
                        if (text.length > 2 && text.length < 100 && !seen.has(text)) {
                            seen.add(text);
                            const parent = node.parentElement;
                            if (parent && parent.offsetParent !== null) {
                                elements.push({
                                    text: text,
                                    tag: parent.tagName.toLowerCase(),
                                    id: parent.id,
                                    class: parent.className,
                                    clickable: parent.onclick || 
                                             parent.style.cursor === 'pointer' ||
                                             parent.tagName === 'BUTTON' ||
                                             parent.tagName === 'A' ||
                                             parent.role === 'button'
                                });
                            }
                        }
                    }
                    return elements.slice(0, 50); // Return first 50 unique text elements
                }
            """)
            
            # Group by category
            buttons = []
            links = []
            labels = []
            other = []
            
            for elem in text_elements:
                if elem['tag'] in ['button', 'a'] or elem['clickable']:
                    buttons.append(elem)
                elif elem['tag'] == 'a':
                    links.append(elem)
                elif elem['tag'] in ['label', 'span']:
                    labels.append(elem)
                else:
                    other.append(elem)
            
            if buttons:
                print("\n🔘 Clickable Text Elements:")
                for elem in buttons[:10]:
                    print(f"  • {elem['text'][:40]} ({elem['tag']})")
            
            if labels:
                print("\n🏷️ Labels/Text:")
                for elem in labels[:10]:
                    print(f"  • {elem['text'][:40]} ({elem['tag']})")
            
            print(f"\n📊 Total visible text elements: {len(text_elements)}")
            print("💡 Use 'text <your text>' to search for specific text")
            
            return text_elements
            
        except Exception as e:
            print(f"❌ Error finding visible text: {e}")
            return []
    
    async def test_selector(self, selector: str):
        """Test if a specific selector works"""
        print(f"\n🧪 TESTING SELECTOR: {selector}")
        print("-" * 40)
        
        try:
            elements = await self.page.query_selector_all(selector)
            print(f"✅ Found {len(elements)} element(s)")
            
            if elements:
                for i, element in enumerate(elements[:3]):  # Show first 3
                    attrs = await element.evaluate("""
                        el => ({
                            tag: el.tagName.toLowerCase(),
                            id: el.id,
                            name: el.name,
                            class: el.className,
                            text: el.textContent?.trim()?.substring(0, 50),
                            visible: !el.hidden && el.offsetParent !== null,
                            clickable: !el.disabled
                        })
                    """)
                    print(f"  Element {i+1}: {attrs}")
            else:
                print("❌ No elements found with this selector")
                
                # Suggest alternatives
                print("\n💡 Suggestions:")
                if "#" in selector:
                    base = selector.replace("#", "")
                    print(f"   Try: [id*='{base}'] (partial ID match)")
                if "." in selector:
                    base = selector.replace(".", "")
                    print(f"   Try: [class*='{base}'] (partial class match)")
                if selector.startswith("input"):
                    print("   Try: input (get all inputs first)")
                    
        except Exception as e:
            print(f"❌ Selector syntax error: {e}")
    
    async def interactive_mode(self):
        """Interactive mode for testing selectors and navigating"""
        print("\n🎯 INTERACTIVE MODE")
        print("=" * 60)
        print("Available commands:")
        print("\n📝 Text Search (NEW!):")
        print("  'text <text>'             - Find elements by visible text")
        print("  'button <text>'           - Find buttons containing text")
        print("  'link <text>'             - Find links containing text") 
        print("  'clickable <text>'        - Find clickable elements with text")
        print("  'dropdown <text>'         - Find dropdowns with text")
        print("  'visible'                 - Show all visible text on page")
        print("\n🔍 Analysis:")
        print("  'analyze' or 'a'          - Re-analyze current page")
        print("  'comprehensive' or 'c'    - Full comprehensive analysis")
        print("\n🧭 Navigation:")
        print("  'navigate <url>' or 'go'  - Navigate to new page")
        print("  'refresh' or 'r'          - Refresh current page")
        print("  'click <selector>'        - Click an element")
        print("\n🔄 Iterative Testing:")
        print("  'iterate <cat> -r <range>' - Test elements from search category")
        print("  'show-categories'          - List available categories")
        print("\n🔧 Selector Optimization (NEW!):")
        print("  'optimize <complex-selector>' - Optimize complex browser selector")
        print("  'parse <selector>'          - Parse and analyze any selector")
        print("\n🛠️ Utilities:")
        print("  'export'                  - Export discovered elements")
        print("  'page-info'               - Show current page information")
        print("  'test-multi <selector>'   - Test multiple elements with same selector")
        print("  '<css-selector>'          - Test any CSS selector")
        print("  'quit' or 'q'             - Exit")
        print("\n💡 Examples:")
        print("  text Settings              - Find elements with 'Settings'")
        print("  iterate 1 -r 1-3          - Test first 3 from category 1")
        print("  optimize '#root > div > ...' - Simplify complex selector")
        print("  button Settings            - Find only buttons with 'Settings'")
        
        while True:
            try:
                page_title = await self.page.title()
                command = input(f"\n🔍 [{page_title[:30]}] Enter command: ").strip()
                
                if command.lower() in ['quit', 'q']:
                    break
                elif command.lower() in ['analyze', 'a']:
                    await self.analyze_page_elements()
                elif command.lower() in ['comprehensive', 'c']:
                    await self.analyze_page_elements(comprehensive=True)
                elif command.lower().startswith('navigate ') or command.lower().startswith('go '):
                    url = command.split(' ', 1)[1] if ' ' in command else input("Enter URL: ")
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    print(f"🌐 Navigating to: {url}")
                    await self.page.goto(url, wait_until="networkidle")
                    print(f"✅ Loaded: {await self.page.title()}")
                elif command.lower() in ['refresh', 'r']:
                    print("🔄 Refreshing page...")
                    await self.page.reload(wait_until="networkidle")
                    print(f"✅ Refreshed: {await self.page.title()}")
                elif command.lower() == 'page-info':
                    await self._show_page_info()
                elif command.lower().startswith('text '):
                    text = command.split(' ', 1)[1] if ' ' in command else input("Enter text to search: ")
                    await self.find_by_text(text)
                elif command.lower().startswith('button '):
                    text = command.split(' ', 1)[1] if ' ' in command else input("Enter button text: ")
                    await self.find_combined('button', text)
                elif command.lower().startswith('link '):
                    text = command.split(' ', 1)[1] if ' ' in command else input("Enter link text: ")
                    await self.find_combined('link', text)
                elif command.lower().startswith('clickable '):
                    text = command.split(' ', 1)[1] if ' ' in command else input("Enter clickable text: ")
                    await self.find_combined('clickable', text)
                elif command.lower().startswith('dropdown '):
                    text = command.split(' ', 1)[1] if ' ' in command else input("Enter dropdown text: ")
                    await self.find_combined('dropdown', text)
                elif command.lower() == 'visible':
                    await self.find_all_visible_text()
                elif command.lower() == 'show-categories':
                    await self.show_search_categories()
                elif command.lower().startswith('iterate '):
                    # Parse iterate command: iterate <category> -r <range>
                    parts = command.split()
                    if len(parts) >= 4 and parts[2] == '-r':
                        category = parts[1]
                        range_str = ' '.join(parts[3:])
                        await self.iterate_test_elements(category, range_str)
                    else:
                        print("❌ Invalid iterate syntax")
                        print("💡 Usage: iterate <category|all> -r <range>")
                        print("💡 Examples:")
                        print("   iterate 1 -r 1-3        # Test first 3 from category 1")
                        print("   iterate all -r 5,8,13   # Test elements 5, 8, 13 from all")
                        print("   iterate 2 -r all        # Test all from category 2")
                elif command.lower().startswith('test-multi '):
                    selector = command.split(' ', 1)[1]
                    await self._test_click_multiple(selector)
                elif command.lower().startswith('click '):
                    selector = command.split(' ', 1)[1]
                    await self._test_click(selector)
                elif command.lower() == 'export':
                    await self._export_elements()
                elif command:
                    await self.test_selector(command)
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("💡 Tip: Make sure you're still on a valid page")
    
    async def _show_page_info(self):
        """Show current page information"""
        print("\n📄 CURRENT PAGE INFO:")
        print("-" * 25)
        print(f"Title: {await self.page.title()}")
        print(f"URL: {self.page.url}")
        print(f"Viewport: {self.page.viewport_size}")
        
        # Check for iframes
        frames = self.page.frames
        print(f"Frames: {len(frames)} (including main frame)")
        if len(frames) > 1:
            for i, frame in enumerate(frames[1:], 1):
                print(f"  Frame {i}: {frame.url}")
    
    async def _test_click(self, selector, element_index: int = 0):
        """Test clicking an element with improved timeout handling"""
        print(f"\n👆 TESTING CLICK: {selector}")
        if element_index > 0:
            print(f"   (Testing element #{element_index + 1})")
        print("-" * 40)
        
        try:
            elements = await self.page.query_selector_all(selector)
            if not elements:
                print("❌ No elements found with this selector")
                return
            
            if element_index >= len(elements):
                print(f"❌ Element index {element_index + 1} not found. Only {len(elements)} elements available.")
                return
                
            print(f"Found {len(elements)} element(s). Testing element {element_index + 1}...")
            
            # Get element info before clicking
            element = elements[element_index]
            attrs = await element.evaluate("""
                el => ({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent?.trim()?.substring(0, 50),
                    href: el.href,
                    clickable: !el.disabled && el.offsetParent !== null,
                    visible: !el.hidden && el.offsetParent !== null,
                    rect: el.getBoundingClientRect(),
                    classes: el.className
                })
            """)
            
            print(f"Element details:")
            print(f"  Tag: {attrs['tag']}")
            print(f"  Text: \"{attrs['text']}\"")
            print(f"  Classes: {attrs['classes']}")
            print(f"  Position: ({attrs['rect']['x']:.0f}, {attrs['rect']['y']:.0f})")
            print(f"  Visible: {attrs['visible']}")
            print(f"  Clickable: {attrs['clickable']}")
            
            if not attrs['visible']:
                print("⚠️ Element is not visible, click may fail")
            
            if attrs['clickable']:
                old_url = self.page.url
                old_title = await self.page.title()
                
                print("\n🔄 Attempting click...")
                
                # Try multiple click strategies
                click_success = False
                
                # Strategy 1: Normal click with short timeout
                try:
                    await element.click(timeout=5000)
                    click_success = True
                    print("✅ Standard click succeeded")
                except Exception as e1:
                    print(f"❌ Standard click failed: {e1}")
                    
                    # Strategy 2: Force click (ignore intercepting elements)
                    try:
                        print("🔄 Trying force click...")
                        await element.click(force=True, timeout=3000)
                        click_success = True
                        print("✅ Force click succeeded")
                    except Exception as e2:
                        print(f"❌ Force click failed: {e2}")
                        
                        # Strategy 3: JavaScript click
                        try:
                            print("🔄 Trying JavaScript click...")
                            await element.evaluate("el => el.click()")
                            click_success = True
                            print("✅ JavaScript click succeeded")
                        except Exception as e3:
                            print(f"❌ JavaScript click failed: {e3}")
                
                if click_success:
                    # Wait for potential changes
                    await self.page.wait_for_timeout(2000)
                    
                    new_url = self.page.url
                    new_title = await self.page.title()
                    
                    if old_url != new_url:
                        print(f"🌐 Navigation detected: {new_url}")
                        print(f"📄 New page title: {new_title}")
                    elif old_title != new_title:
                        print(f"📄 Page title changed: {new_title}")
                    else:
                        print("📍 No navigation detected (possible modal/dropdown opened)")
                        
                        # Check for new elements that might have appeared
                        try:
                            modal = await self.page.query_selector('.modal, .dropdown, .popup, [role="dialog"]')
                            if modal:
                                print("✨ Modal/dropdown/popup detected")
                        except:
                            pass
                else:
                    print("❌ All click strategies failed")
            else:
                print("⚠️ Element exists but may not be clickable")
                
        except Exception as e:
            print(f"❌ Click test failed: {e}")
            
    async def _test_click_multiple(self, selector):
        """Test clicking multiple elements with the same selector"""
        try:
            elements = await self.page.query_selector_all(selector)
            if not elements:
                print("❌ No elements found")
                return
                
            print(f"\n📋 Found {len(elements)} elements. Which one to test?")
            for i, element in enumerate(elements):
                try:
                    attrs = await element.evaluate("""
                        el => ({
                            text: el.textContent?.trim()?.substring(0, 40),
                            visible: !el.hidden && el.offsetParent !== null,
                            rect: el.getBoundingClientRect()
                        })
                    """)
                    print(f"  {i+1}. \"{attrs['text']}\" (Position: {attrs['rect']['x']:.0f}, {attrs['rect']['y']:.0f}) {'✓ Visible' if attrs['visible'] else '❌ Hidden'}")
                except:
                    print(f"  {i+1}. [Could not analyze]")
            
            choice = input(f"\nEnter element number to test (1-{len(elements)}) or 'all': ").strip()
            
            if choice.lower() == 'all':
                for i in range(len(elements)):
                    await self._test_click(selector, i)
                    if i < len(elements) - 1:
                        input("\nPress Enter to test next element...")
            else:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(elements):
                        await self._test_click(selector, index)
                    else:
                        print("❌ Invalid element number")
                except ValueError:
                    print("❌ Invalid input")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _export_elements(self):
        """Export discovered elements to a file"""
        print("\n💾 EXPORTING ELEMENTS...")
        print("-" * 25)
        
        try:
            # Create a comprehensive element map
            element_map = {
                "page_info": {
                    "title": await self.page.title(),
                    "url": self.page.url,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                },
                "elements": {}
            }
            
            # Export different element types
            element_types = [
                ("inputs", "input"),
                ("buttons", "button"),
                ("links", "a[href]"),
                ("forms", "form"),
                ("selects", "select"),
                ("textareas", "textarea")
            ]
            
            for element_type, selector in element_types:
                elements = await self.page.query_selector_all(selector)
                element_map["elements"][element_type] = []
                
                for element in elements:
                    try:
                        attrs = await element.evaluate("""
                            el => ({
                                tag: el.tagName.toLowerCase(),
                                id: el.id,
                                name: el.name,
                                class: el.className,
                                type: el.type,
                                placeholder: el.placeholder,
                                text: el.textContent?.trim()?.substring(0, 50),
                                href: el.href,
                                value: el.value,
                                visible: !el.hidden && el.offsetParent !== null
                            })
                        """)
                        
                        # Generate suggested selectors
                        selectors = []
                        if attrs['id']:
                            selectors.append(f"#{attrs['id']}")
                        if attrs['name']:
                            selectors.append(f"{attrs['tag']}[name='{attrs['name']}']")
                        if attrs['type']:
                            selectors.append(f"{attrs['tag']}[type='{attrs['type']}']")
                        if attrs['placeholder']:
                            selectors.append(f"{attrs['tag']}[placeholder=\"{attrs['placeholder']}\"]")
                        
                        attrs['suggested_selectors'] = selectors
                        element_map["elements"][element_type].append(attrs)
                        
                    except:
                        continue
            
            # Save to file
            import json
            filename = f"/tmp/page_elements_{__import__('time').time():.0f}.json"
            with open(filename, 'w') as f:
                json.dump(element_map, f, indent=2)
            
            print(f"✅ Elements exported to: {filename}")
            print(f"📊 Total elements found: {sum(len(elements) for elements in element_map['elements'].values())}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    async def close(self):
        """Close browser"""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            print(f"Warning: Error closing browser: {e}")
            pass  # Ignore cleanup errors

async def main():
    print("🔍 CSS SELECTOR FINDER TOOL")
    print("=" * 40)
    print("This tool helps you find the correct CSS selectors for web automation.")
    
    url = input("\n🌐 Enter the website URL: ").strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    finder = SelectorFinder()
    
    try:
        await finder.start_browser(url)
        
        print("\n📖 INSTRUCTIONS:")
        print("1. The browser window is now open")
        print("2. Navigate to the exact page you want to automate")
        print("3. Press Enter here when ready to analyze")
        
        input("\nPress Enter when page is ready...")
        
        await finder.analyze_page_elements()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Review the suggested selectors above")
        print("2. Test specific selectors if needed")
        print("3. Use the working selectors in your automation config")
        
        test_more = input("\nWould you like to enter interactive mode? (y/n): ")
        if test_more.lower() == 'y':
            print("\n🎮 Entering interactive mode...")
            print("Tip: Use Ctrl+C to exit interactive mode safely")
            await finder.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n🛑 Selector finder interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔄 Closing browser...")
        await finder.close()
        print("✅ Selector finder closed")

if __name__ == "__main__":
    asyncio.run(main())