#!/usr/bin/env python3.11

"""
Alternative Scrolling Strategies Test Script

This script tests all implemented alternative scrolling strategies on the main /generate page
to identify which methods successfully load older generations when standard scrolling fails.

Purpose:
1. Login to the main /generate page
2. Test each alternative scrolling strategy individually
3. Measure effectiveness of each strategy
4. Recommend the best strategy for implementation
5. Provide fallback strategy combinations
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from playwright.async_api import async_playwright
from utils.credential_manager import CredentialManager

class AlternativeScrollingTester:
    """Test alternative scrolling strategies on /generate page"""
    
    def __init__(self, show_browser=True):
        self.show_browser = show_browser
        self.credential_manager = CredentialManager()
        self.test_results = {}
        
    async def setup_browser_and_login(self):
        """Setup browser and login to /generate page"""
        print("🚀 STARTING ALTERNATIVE SCROLLING STRATEGY TEST")
        print("=" * 80)
        
        # Launch browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=not self.show_browser)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("📱 Browser launched and configured")
        
        # Navigate to main page - UPDATE THIS URL FOR YOUR WEBSITE
        target_url = input("🔄 Enter the target URL (e.g., https://example.com/generate): ").strip()
        if not target_url:
            print("❌ No URL provided")
            return None, None, None
            
        print(f"🔄 Navigating to: {target_url}")
        await page.goto(target_url)
        await page.wait_for_load_state("networkidle")
        
        # Ask if login is needed
        needs_login = input("🔐 Does this page require login? (y/N): ").lower().strip() == 'y'
        
        if needs_login:
            credential_id = input("Enter credential ID (e.g., 'website_name'): ").strip() or "website_login"
            
            print(f"🔐 Attempting automatic login with credential ID: {credential_id}")
            
            # Load credentials and attempt login
            credentials = self.credential_manager.get_credential(credential_id)
            if not credentials:
                print(f"❌ No credentials found for '{credential_id}'")
                print(f"💡 Run this first: python3.11 scripts/setup_credentials.py")
                print(f"   (or store credentials manually for ID: {credential_id})")
                return None, None, None
        
            # Check if already logged in or login is needed
            if needs_login:
                login_success_indicator = input("🔍 Enter text/selector that indicates successful login (e.g., 'Dashboard', 'Welcome'): ").strip()
                
                try:
                    await page.wait_for_selector(f"text={login_success_indicator}", timeout=3000)
                    print("✅ Already logged in")
                except:
                    # Attempt login
                    try:
                        print("🔄 Attempting login...")
                        
                        # Wait for and fill email/username
                        email_selector = input("📝 Enter email/username field selector (default: 'input[type=\"email\"]'): ").strip() or 'input[type="email"]'
                        await page.wait_for_selector(email_selector, timeout=10000)
                        await page.fill(email_selector, credentials['username'])  # CredentialManager stores email in 'username' field
                        print(f"✅ Email/Username filled: {credentials['username']}")
                        
                        # Wait for and fill password
                        password_selector = input("🔑 Enter password field selector (default: 'input[type=\"password\"]'): ").strip() or 'input[type="password"]'
                        await page.wait_for_selector(password_selector, timeout=5000)
                        await page.fill(password_selector, credentials['password'])
                        print("✅ Password filled")
                        
                        # Click login button
                        login_button_selector = input("🔘 Enter login button selector (default: 'button[type=\"submit\"]'): ").strip() or 'button[type="submit"]'
                        await page.click(login_button_selector)
                        print("🔄 Login button clicked")
                        
                        # Wait for successful login
                        await page.wait_for_selector(f"text={login_success_indicator}", timeout=15000)
                        print("✅ Login successful")
                        
                    except Exception as e:
                        print(f"❌ Login failed: {e}")
                        print("💡 You can continue without login or press Ctrl+C to exit and fix login")
                        input("Press Enter to continue without login or Ctrl+C to exit...")
            else:
                print("📄 No login required, proceeding with page analysis")
        
        # Wait for page to fully load
        await page.wait_for_timeout(3000)
        print("✅ Target page loaded successfully")
        
        return playwright, browser, page
    
    async def get_baseline_metrics(self, page):
        """Get baseline metrics before testing strategies"""
        print("\n📊 COLLECTING BASELINE METRICS")
        print("-" * 50)
        
        baseline = {
            'document_height': await page.evaluate("document.body.scrollHeight"),
            'viewport_height': await page.evaluate("window.innerHeight"),
            'current_scroll': await page.evaluate("window.pageYOffset"),
            'total_divs': len(await page.query_selector_all("div")),
            'generation_containers': 0,
            'oldest_visible_date': None,
            'newest_visible_date': None
        }
        
        # Try to find generation containers using common selectors
        generation_selectors = [
            "[class*='generation']", "[class*='item']", "[class*='card']",
            "[class*='container']", "[data-*='generation']", "article"
        ]
        
        max_containers = 0
        best_selector = None
        
        for selector in generation_selectors:
            try:
                containers = await page.query_selector_all(selector)
                container_count = len(containers)
                if container_count > max_containers:
                    max_containers = container_count
                    best_selector = selector
            except:
                continue
        
        baseline['generation_containers'] = max_containers
        baseline['best_container_selector'] = best_selector
        
        print(f"   📏 Document height: {baseline['document_height']}px")
        print(f"   📱 Viewport height: {baseline['viewport_height']}px")
        print(f"   📊 Total DIVs: {baseline['total_divs']}")
        print(f"   🎯 Generation containers: {baseline['generation_containers']} (using {best_selector})")
        print(f"   📍 Current scroll: {baseline['current_scroll']}px")
        
        return baseline
    
    async def test_strategy_1_custom_containers(self, page, baseline):
        """Test Strategy 1: Custom scroll containers"""
        print("\n🎯 STRATEGY 1: CUSTOM SCROLL CONTAINERS")
        print("-" * 50)
        
        result = {
            'strategy': 'custom_containers',
            'success': False,
            'containers_found': 0,
            'scrollable_containers': 0,
            'content_loaded': False,
            'height_increase': 0,
            'container_increase': 0,
            'best_container': None,
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            scroll_container_selectors = [
                "[class*='scroll']", "[id*='scroll']", 
                "[class*='container']", "[class*='list']", 
                "[class*='content']", "[class*='infinite']",
                "div[style*='overflow']", "div[style*='scroll']",
                "[class*='feed']", "[class*='timeline']"
            ]
            
            best_container_info = None
            max_content_increase = 0
            
            for selector in scroll_container_selectors:
                try:
                    containers = await page.query_selector_all(selector)
                    result['containers_found'] += len(containers)
                    
                    print(f"   🔍 Testing selector: {selector} ({len(containers)} containers)")
                    
                    for i, container in enumerate(containers):
                        try:
                            # Check if element is scrollable
                            scroll_height = await container.evaluate("el => el.scrollHeight")
                            client_height = await container.evaluate("el => el.clientHeight")
                            current_scroll = await container.evaluate("el => el.scrollTop")
                            
                            if scroll_height > client_height and client_height > 0:
                                result['scrollable_containers'] += 1
                                print(f"      🎯 Scrollable container #{i}: height={scroll_height}, visible={client_height}, scroll={current_scroll}")
                                
                                # Test scrolling this container
                                initial_doc_height = await page.evaluate("document.body.scrollHeight")
                                initial_containers = len(await page.query_selector_all("div"))
                                
                                # Scroll the container to bottom
                                await container.evaluate("el => el.scrollTop = el.scrollHeight")
                                await page.wait_for_timeout(3000)  # Wait for potential content loading
                                
                                # Check for changes
                                new_doc_height = await page.evaluate("document.body.scrollHeight")
                                new_containers = len(await page.query_selector_all("div"))
                                
                                height_increase = new_doc_height - initial_doc_height
                                container_increase = new_containers - initial_containers
                                
                                print(f"         📊 Results: height +{height_increase}px, containers +{container_increase}")
                                
                                if height_increase > 0 or container_increase > 0:
                                    content_increase = height_increase + (container_increase * 10)  # Weight containers more
                                    if content_increase > max_content_increase:
                                        max_content_increase = content_increase
                                        best_container_info = {
                                            'selector': selector,
                                            'index': i,
                                            'scroll_height': scroll_height,
                                            'client_height': client_height,
                                            'height_increase': height_increase,
                                            'container_increase': container_increase
                                        }
                                        result['success'] = True
                                        result['content_loaded'] = True
                                        
                        except Exception as container_e:
                            continue  # Try next container
                            
                except Exception as selector_e:
                    print(f"      ❌ Selector failed: {selector_e}")
                    continue
                    
            result['execution_time'] = time.time() - start_time
            result['best_container'] = best_container_info
            result['height_increase'] = max_content_increase
            
            if result['success']:
                print(f"   ✅ SUCCESS: Best container loaded content")
                print(f"      📍 Selector: {best_container_info['selector']}")
                print(f"      📊 Height increase: +{best_container_info['height_increase']}px")
                print(f"      📦 Container increase: +{best_container_info['container_increase']}")
            else:
                print(f"   ❌ No scrollable containers loaded new content")
                
        except Exception as e:
            print(f"   ❌ Strategy failed with exception: {e}")
            result['execution_time'] = time.time() - start_time
        
        print(f"   ⏱️ Execution time: {result['execution_time']:.2f}s")
        print(f"   📊 Summary: {result['containers_found']} total, {result['scrollable_containers']} scrollable")
        
        return result
    
    async def test_strategy_2_load_more_buttons(self, page, baseline):
        """Test Strategy 2: Load More buttons"""
        print("\n🎯 STRATEGY 2: LOAD MORE BUTTONS")
        print("-" * 50)
        
        result = {
            'strategy': 'load_more_buttons',
            'success': False,
            'buttons_found': 0,
            'clickable_buttons': 0,
            'content_loaded': False,
            'height_increase': 0,
            'container_increase': 0,
            'best_button': None,
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            load_more_selectors = [
                "button:has-text('Load More')", "button:has-text('Show More')",
                "button:has-text('Load Previous')", "button:has-text('Show Older')",
                "[class*='load']:visible", "[class*='more']:visible", 
                "[id*='load']:visible", "[id*='more']:visible",
                "button[class*='pagination']", "a[class*='next']",
                "button[class*='expand']", "button[class*='see-more']",
                "[role='button']:has-text('more')", "[role='button']:has-text('load')"
            ]
            
            best_button_info = None
            max_content_increase = 0
            
            for selector in load_more_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    result['buttons_found'] += len(buttons)
                    
                    print(f"   🔍 Testing selector: {selector} ({len(buttons)} buttons)")
                    
                    for i, button in enumerate(buttons):
                        try:
                            is_visible = await button.is_visible()
                            is_enabled = await button.is_enabled()
                            
                            if is_visible and is_enabled:
                                result['clickable_buttons'] += 1
                                
                                # Get button text for identification
                                button_text = await button.text_content()
                                print(f"      🎯 Clickable button #{i}: '{button_text}'")
                                
                                # Measure before clicking
                                initial_doc_height = await page.evaluate("document.body.scrollHeight")
                                initial_containers = len(await page.query_selector_all("div"))
                                
                                # Click the button
                                await button.click()
                                print(f"         🖱️ Clicked button")
                                await page.wait_for_timeout(5000)  # Wait longer for content loading
                                
                                # Measure after clicking
                                new_doc_height = await page.evaluate("document.body.scrollHeight")
                                new_containers = len(await page.query_selector_all("div"))
                                
                                height_increase = new_doc_height - initial_doc_height
                                container_increase = new_containers - initial_containers
                                
                                print(f"         📊 Results: height +{height_increase}px, containers +{container_increase}")
                                
                                if height_increase > 0 or container_increase > 0:
                                    content_increase = height_increase + (container_increase * 10)
                                    if content_increase > max_content_increase:
                                        max_content_increase = content_increase
                                        best_button_info = {
                                            'selector': selector,
                                            'index': i,
                                            'text': button_text,
                                            'height_increase': height_increase,
                                            'container_increase': container_increase
                                        }
                                        result['success'] = True
                                        result['content_loaded'] = True
                                        
                        except Exception as button_e:
                            print(f"         ❌ Button click failed: {button_e}")
                            continue
                            
                except Exception as selector_e:
                    print(f"      ❌ Selector failed: {selector_e}")
                    continue
            
            result['execution_time'] = time.time() - start_time
            result['best_button'] = best_button_info
            result['height_increase'] = max_content_increase
            
            if result['success']:
                print(f"   ✅ SUCCESS: Best button loaded content")
                print(f"      📍 Selector: {best_button_info['selector']}")
                print(f"      📝 Text: '{best_button_info['text']}'")
                print(f"      📊 Height increase: +{best_button_info['height_increase']}px")
                print(f"      📦 Container increase: +{best_button_info['container_increase']}")
            else:
                print(f"   ❌ No buttons loaded new content")
                
        except Exception as e:
            print(f"   ❌ Strategy failed with exception: {e}")
            result['execution_time'] = time.time() - start_time
        
        print(f"   ⏱️ Execution time: {result['execution_time']:.2f}s")
        print(f"   📊 Summary: {result['buttons_found']} total, {result['clickable_buttons']} clickable")
        
        return result
    
    async def test_strategy_3_extended_wait(self, page, baseline):
        """Test Strategy 3: Extended wait with automatic loading"""
        print("\n🎯 STRATEGY 3: EXTENDED WAIT & AUTOMATIC LOADING")
        print("-" * 50)
        
        result = {
            'strategy': 'extended_wait',
            'success': False,
            'content_loaded': False,
            'height_increase': 0,
            'container_increase': 0,
            'wait_time': 15,  # seconds
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            # Measure initial state
            initial_doc_height = await page.evaluate("document.body.scrollHeight")
            initial_containers = len(await page.query_selector_all("div"))
            initial_generation_containers = 0
            
            # Try to count generation-specific containers
            if baseline.get('best_container_selector'):
                initial_generation_containers = len(await page.query_selector_all(baseline['best_container_selector']))
            
            print(f"   📊 Initial state:")
            print(f"      📏 Document height: {initial_doc_height}px")
            print(f"      📦 Total containers: {initial_containers}")
            print(f"      🎯 Generation containers: {initial_generation_containers}")
            
            # Wait and monitor for automatic content loading
            wait_time = result['wait_time']
            print(f"   ⏳ Waiting {wait_time} seconds for automatic content loading...")
            
            # Monitor in smaller intervals
            for i in range(wait_time):
                await page.wait_for_timeout(1000)  # 1 second intervals
                
                if i % 5 == 4:  # Check every 5 seconds
                    current_doc_height = await page.evaluate("document.body.scrollHeight")
                    current_containers = len(await page.query_selector_all("div"))
                    
                    height_change = current_doc_height - initial_doc_height
                    container_change = current_containers - initial_containers
                    
                    print(f"      ⏳ After {i+1}s: height +{height_change}px, containers +{container_change}")
                    
                    if height_change > 0 or container_change > 0:
                        print(f"      🎉 Content loading detected early!")
                        break
            
            # Final measurement
            final_doc_height = await page.evaluate("document.body.scrollHeight")
            final_containers = len(await page.query_selector_all("div"))
            final_generation_containers = 0
            
            if baseline.get('best_container_selector'):
                final_generation_containers = len(await page.query_selector_all(baseline['best_container_selector']))
            
            result['height_increase'] = final_doc_height - initial_doc_height
            result['container_increase'] = final_containers - initial_containers
            generation_increase = final_generation_containers - initial_generation_containers
            
            print(f"   📊 Final results:")
            print(f"      📏 Height increase: +{result['height_increase']}px")
            print(f"      📦 Container increase: +{result['container_increase']}")
            print(f"      🎯 Generation increase: +{generation_increase}")
            
            if result['height_increase'] > 0 or result['container_increase'] > 0:
                result['success'] = True
                result['content_loaded'] = True
                print(f"   ✅ SUCCESS: Automatic content loading detected")
            else:
                print(f"   ❌ No automatic content loading detected")
            
            result['execution_time'] = time.time() - start_time
            
        except Exception as e:
            print(f"   ❌ Strategy failed with exception: {e}")
            result['execution_time'] = time.time() - start_time
        
        print(f"   ⏱️ Execution time: {result['execution_time']:.2f}s")
        
        return result
    
    async def test_strategy_4_hover_triggers(self, page, baseline):
        """Test Strategy 4: Element hover triggers"""
        print("\n🎯 STRATEGY 4: ELEMENT HOVER TRIGGERS")
        print("-" * 50)
        
        result = {
            'strategy': 'hover_triggers',
            'success': False,
            'elements_tested': 0,
            'hover_successful': 0,
            'content_loaded': False,
            'height_increase': 0,
            'container_increase': 0,
            'best_element': None,
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            trigger_selectors = [
                "div:last-child", "article:last-child", 
                "[class*='item']:last-child", "[class*='card']:last-child",
                "footer", "div[class*='bottom']", "[class*='container']:last-child",
                "[class*='generation']:last-child", "[class*='feed']:last-child"
            ]
            
            best_element_info = None
            max_content_increase = 0
            
            for selector in trigger_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    result['elements_tested'] += len(elements)
                    
                    print(f"   🔍 Testing selector: {selector} ({len(elements)} elements)")
                    
                    for i, element in enumerate(elements[:3]):  # Test max 3 per selector
                        try:
                            is_visible = await element.is_visible()
                            
                            if is_visible:
                                print(f"      🎯 Hovering over element #{i}")
                                
                                # Measure before hovering
                                initial_doc_height = await page.evaluate("document.body.scrollHeight")
                                initial_containers = len(await page.query_selector_all("div"))
                                
                                # Hover over the element
                                await element.hover()
                                result['hover_successful'] += 1
                                await page.wait_for_timeout(3000)  # Wait for potential loading
                                
                                # Measure after hovering
                                new_doc_height = await page.evaluate("document.body.scrollHeight")
                                new_containers = len(await page.query_selector_all("div"))
                                
                                height_increase = new_doc_height - initial_doc_height
                                container_increase = new_containers - initial_containers
                                
                                print(f"         📊 Results: height +{height_increase}px, containers +{container_increase}")
                                
                                if height_increase > 0 or container_increase > 0:
                                    content_increase = height_increase + (container_increase * 10)
                                    if content_increase > max_content_increase:
                                        max_content_increase = content_increase
                                        best_element_info = {
                                            'selector': selector,
                                            'index': i,
                                            'height_increase': height_increase,
                                            'container_increase': container_increase
                                        }
                                        result['success'] = True
                                        result['content_loaded'] = True
                                        
                        except Exception as element_e:
                            print(f"         ❌ Hover failed: {element_e}")
                            continue
                            
                except Exception as selector_e:
                    print(f"      ❌ Selector failed: {selector_e}")
                    continue
            
            result['execution_time'] = time.time() - start_time
            result['best_element'] = best_element_info
            result['height_increase'] = max_content_increase
            
            if result['success']:
                print(f"   ✅ SUCCESS: Best element hover loaded content")
                print(f"      📍 Selector: {best_element_info['selector']}")
                print(f"      📊 Height increase: +{best_element_info['height_increase']}px")
                print(f"      📦 Container increase: +{best_element_info['container_increase']}")
            else:
                print(f"   ❌ No hover triggers loaded new content")
                
        except Exception as e:
            print(f"   ❌ Strategy failed with exception: {e}")
            result['execution_time'] = time.time() - start_time
        
        print(f"   ⏱️ Execution time: {result['execution_time']:.2f}s")
        print(f"   📊 Summary: {result['elements_tested']} tested, {result['hover_successful']} hovered")
        
        return result
    
    async def test_strategy_5_url_manipulation(self, page, baseline):
        """Test Strategy 5: URL parameter manipulation"""
        print("\n🎯 STRATEGY 5: URL PARAMETER MANIPULATION")
        print("-" * 50)
        
        result = {
            'strategy': 'url_manipulation',
            'success': False,
            'urls_tested': 0,
            'successful_urls': 0,
            'content_loaded': False,
            'height_increase': 0,
            'container_increase': 0,
            'best_url': None,
            'execution_time': 0
        }
        
        start_time = time.time()
        
        try:
            current_url = page.url
            print(f"   📍 Current URL: {current_url}")
            
            # Measure initial state
            initial_doc_height = await page.evaluate("document.body.scrollHeight")
            initial_containers = len(await page.query_selector_all("div"))
            
            param_variations = [
                "?page=2", "?offset=50", "?limit=100", 
                "?before=2025-09-03", "?older=true", "?skip=50",
                "&page=2" if "?" in current_url else "?page=2",
                "&offset=50" if "?" in current_url else "?offset=50",
                "&older=true" if "?" in current_url else "?older=true"
            ]
            
            best_url_info = None
            max_content_increase = 0
            
            for param in param_variations:
                try:
                    result['urls_tested'] += 1
                    new_url = current_url + param
                    
                    print(f"   🔍 Testing URL: {param}")
                    
                    # Navigate to new URL
                    await page.goto(new_url, wait_until="networkidle", timeout=10000)
                    await page.wait_for_timeout(3000)  # Wait for content to load
                    
                    # Measure content
                    new_doc_height = await page.evaluate("document.body.scrollHeight")
                    new_containers = len(await page.query_selector_all("div"))
                    
                    height_increase = new_doc_height - initial_doc_height
                    container_increase = new_containers - initial_containers
                    
                    print(f"      📊 Results: height +{height_increase}px, containers +{container_increase}")
                    
                    if height_increase > 0 or container_increase > 0 or new_containers > 50:
                        result['successful_urls'] += 1
                        content_increase = height_increase + (container_increase * 10)
                        
                        if content_increase > max_content_increase or new_containers > 50:
                            max_content_increase = max(content_increase, new_containers)
                            best_url_info = {
                                'param': param,
                                'full_url': new_url,
                                'height_increase': height_increase,
                                'container_increase': container_increase,
                                'total_containers': new_containers
                            }
                            result['success'] = True
                            result['content_loaded'] = True
                            
                    # Return to original URL for next test
                    await page.goto(current_url, wait_until="networkidle", timeout=10000)
                    await page.wait_for_timeout(1000)
                    
                except Exception as url_e:
                    print(f"      ❌ URL test failed: {url_e}")
                    # Try to return to original URL
                    try:
                        await page.goto(current_url, wait_until="networkidle", timeout=10000)
                    except:
                        pass
                    continue
            
            result['execution_time'] = time.time() - start_time
            result['best_url'] = best_url_info
            if best_url_info:
                result['height_increase'] = best_url_info['height_increase']
                result['container_increase'] = best_url_info['container_increase']
            
            if result['success']:
                print(f"   ✅ SUCCESS: Best URL loaded content")
                print(f"      📍 Parameter: {best_url_info['param']}")
                print(f"      📊 Height increase: +{best_url_info['height_increase']}px")
                print(f"      📦 Container increase: +{best_url_info['container_increase']}")
                print(f"      📊 Total containers: {best_url_info['total_containers']}")
            else:
                print(f"   ❌ No URL parameters loaded new content")
                
        except Exception as e:
            print(f"   ❌ Strategy failed with exception: {e}")
            result['execution_time'] = time.time() - start_time
        
        print(f"   ⏱️ Execution time: {result['execution_time']:.2f}s")
        print(f"   📊 Summary: {result['urls_tested']} tested, {result['successful_urls']} successful")
        
        return result
    
    def analyze_results_and_recommend(self):
        """Analyze all test results and provide recommendations"""
        print("\n🎯 COMPREHENSIVE RESULTS ANALYSIS")
        print("=" * 80)
        
        # Score each strategy
        strategies = []
        
        for strategy_name, result in self.test_results.items():
            if result.get('success'):
                # Calculate effectiveness score
                content_score = (result.get('height_increase', 0) / 100) + (result.get('container_increase', 0) * 2)
                speed_score = max(0, (10 - result.get('execution_time', 10)) / 10)  # Favor faster methods
                reliability_score = 1.0  # Assume all successful methods are reliable for now
                
                total_score = (content_score * 0.5) + (speed_score * 0.3) + (reliability_score * 0.2)
                
                strategies.append({
                    'name': strategy_name,
                    'result': result,
                    'content_score': content_score,
                    'speed_score': speed_score,
                    'total_score': total_score
                })
        
        # Sort by effectiveness
        strategies.sort(key=lambda x: x['total_score'], reverse=True)
        
        print(f"📊 STRATEGY EFFECTIVENESS RANKING:")
        print("-" * 50)
        
        if not strategies:
            print("❌ No strategies were successful")
            print("🔍 Recommendations:")
            print("   1. Check if the page requires specific authentication")
            print("   2. Verify that generation containers are actually present")
            print("   3. Try manual scrolling to see if any content loads")
            print("   4. Inspect the page source for alternative loading mechanisms")
            return None
        
        for i, strategy in enumerate(strategies, 1):
            result = strategy['result']
            print(f"{i}. 🏆 {strategy['name'].upper().replace('_', ' ')}")
            print(f"   📊 Overall Score: {strategy['total_score']:.2f}/10")
            print(f"   📈 Content Added: +{result.get('height_increase', 0)}px height, +{result.get('container_increase', 0)} containers")
            print(f"   ⚡ Speed: {result.get('execution_time', 0):.2f}s")
            
            if strategy['name'] == 'custom_containers' and result.get('best_container'):
                container = result['best_container']
                print(f"   🎯 Best Container: {container['selector']}")
            elif strategy['name'] == 'load_more_buttons' and result.get('best_button'):
                button = result['best_button']
                print(f"   🎯 Best Button: {button['selector']} ('{button['text']}')")
            elif strategy['name'] == 'url_manipulation' and result.get('best_url'):
                url = result['best_url']
                print(f"   🎯 Best URL: {url['param']}")
            
            print()
        
        # Provide implementation recommendation
        best_strategy = strategies[0]
        print(f"🎯 IMPLEMENTATION RECOMMENDATION:")
        print("-" * 50)
        print(f"✅ Primary Strategy: {best_strategy['name'].upper().replace('_', ' ')}")
        print(f"   Score: {best_strategy['total_score']:.2f}/10")
        print(f"   Reason: Best combination of effectiveness and speed")
        
        if len(strategies) > 1:
            print(f"🔄 Fallback Strategy: {strategies[1]['name'].upper().replace('_', ' ')}")
            print(f"   Score: {strategies[1]['total_score']:.2f}/10")
            print(f"   Reason: Reliable alternative if primary fails")
        
        # Generate implementation code suggestions
        self.generate_implementation_code(best_strategy)
        
        return strategies
    
    def generate_implementation_code(self, best_strategy):
        """Generate code recommendations for the best strategy"""
        print(f"\n💻 IMPLEMENTATION CODE SUGGESTION:")
        print("-" * 50)
        
        strategy_name = best_strategy['name']
        result = best_strategy['result']
        
        if strategy_name == 'custom_containers' and result.get('best_container'):
            container = result['best_container']
            print(f"# Custom Container Scrolling Implementation")
            print(f"container_selector = '{container['selector']}'")
            print(f"containers = await page.query_selector_all(container_selector)")
            print(f"if containers:")
            print(f"    container = containers[{container['index']}]")
            print(f"    await container.evaluate('el => el.scrollTop = el.scrollHeight')")
            print(f"    await page.wait_for_timeout(3000)")
            
        elif strategy_name == 'load_more_buttons' and result.get('best_button'):
            button = result['best_button']
            print(f"# Load More Button Implementation")
            print(f"button_selector = '{button['selector']}'")
            print(f"button = await page.query_selector(button_selector)")
            print(f"if button and await button.is_visible():")
            print(f"    await button.click()")
            print(f"    await page.wait_for_timeout(5000)")
            
        elif strategy_name == 'extended_wait':
            print(f"# Extended Wait Implementation")
            print(f"await page.wait_for_timeout({result.get('wait_time', 15)}000)")
            print(f"# Check for content changes after wait")
            
        elif strategy_name == 'hover_triggers' and result.get('best_element'):
            element = result['best_element']
            print(f"# Hover Trigger Implementation")
            print(f"element_selector = '{element['selector']}'")
            print(f"element = await page.query_selector(element_selector)")
            print(f"if element:")
            print(f"    await element.hover()")
            print(f"    await page.wait_for_timeout(3000)")
            
        elif strategy_name == 'url_manipulation' and result.get('best_url'):
            url = result['best_url']
            print(f"# URL Manipulation Implementation")
            print(f"current_url = page.url")
            print(f"new_url = current_url + '{url['param']}'")
            print(f"await page.goto(new_url, wait_until='networkidle')")
            print(f"await page.wait_for_timeout(3000)")
    
    async def run_comprehensive_test(self):
        """Run all tests and provide comprehensive analysis"""
        playwright, browser, page = await self.setup_browser_and_login()
        
        if not page:
            print("❌ Failed to setup browser and login")
            return
        
        try:
            # Get baseline metrics
            baseline = await self.get_baseline_metrics(page)
            
            # Test each strategy
            print("\n🧪 RUNNING STRATEGY TESTS")
            print("=" * 80)
            
            self.test_results['custom_containers'] = await self.test_strategy_1_custom_containers(page, baseline)
            self.test_results['load_more_buttons'] = await self.test_strategy_2_load_more_buttons(page, baseline) 
            self.test_results['extended_wait'] = await self.test_strategy_3_extended_wait(page, baseline)
            self.test_results['hover_triggers'] = await self.test_strategy_4_hover_triggers(page, baseline)
            self.test_results['url_manipulation'] = await self.test_strategy_5_url_manipulation(page, baseline)
            
            # Analyze results
            recommendations = self.analyze_results_and_recommend()
            
            # Save results to file
            self.save_test_results(baseline, recommendations)
            
        finally:
            await browser.close()
            print(f"\n✅ ALTERNATIVE SCROLLING STRATEGY TEST COMPLETE")
            
    def save_test_results(self, baseline, recommendations):
        """Save test results to JSON file for future reference"""
        results_file = Path(__file__).parent / "alternative_scrolling_test_results.json"
        
        full_results = {
            'timestamp': datetime.now().isoformat(),
            'baseline': baseline,
            'test_results': self.test_results,
            'recommendations': [
                {
                    'rank': i+1,
                    'strategy': rec['name'],
                    'score': rec['total_score'],
                    'details': rec['result']
                } for i, rec in enumerate(recommendations)
            ] if recommendations else []
        }
        
        with open(results_file, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        print(f"💾 Test results saved to: {results_file}")

async def main():
    """Main test execution"""
    tester = AlternativeScrollingTester(show_browser=True)
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())