#!/usr/bin/env python3.11
"""
Login and Scroll Testing Script
================================
A responsible web automation tool for testing login and scrolling functionality.

IMPORTANT: This script is for testing and development purposes only.
- Always ensure you have permission to automate interactions with a website
- Respect robots.txt and terms of service
- Use appropriate delays to avoid overwhelming servers
- Never use for unauthorized access or malicious purposes
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from playwright.async_api import (
    Page,
    Browser,
    async_playwright,
    ElementHandle,
    TimeoutError as PlaywrightTimeoutError
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scroll_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScrollTestResult:
    """Container for scroll test results"""
    def __init__(self, method_name: str):
        self.method_name = method_name
        self.success = False
        self.scroll_distance = 0
        self.execution_time = 0.0
        self.requires_mouse = False
        self.requires_keyboard = False
        self.error_message = ""
        self.user_confirmed = None
        
    def to_dict(self) -> Dict:
        return {
            'method_name': self.method_name,
            'success': self.success,
            'scroll_distance': self.scroll_distance,
            'execution_time': self.execution_time,
            'requires_mouse': self.requires_mouse,
            'requires_keyboard': self.requires_keyboard,
            'error_message': self.error_message,
            'user_confirmed': self.user_confirmed
        }


class LoginScrollTester:
    """Main automation class for login and scroll testing"""
    
    def __init__(self, url: str, email: str, password: str):
        self.url = url
        self.email = email
        self.password = password
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
        self.test_results: List[ScrollTestResult] = []
        
    async def initialize_browser(self):
        """Initialize the browser with appropriate settings"""
        logger.info("Initializing browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser for testing
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        
        # Add console message listener for debugging
        self.page.on("console", lambda msg: logger.debug(f"Console: {msg.text}"))
        
    async def verify_url_safety(self) -> bool:
        """Verify the URL appears legitimate and safe"""
        parsed = urlparse(self.url)
        
        # Basic safety checks
        if not parsed.scheme in ['http', 'https']:
            logger.error(f"Invalid URL scheme: {parsed.scheme}")
            return False
            
        if not parsed.netloc:
            logger.error("Invalid URL: no domain specified")
            return False
            
        # Check for obvious phishing indicators
        suspicious_patterns = ['phishing', 'fake', 'scam']
        if any(pattern in parsed.netloc.lower() for pattern in suspicious_patterns):
            logger.warning(f"Suspicious domain detected: {parsed.netloc}")
            return False
            
        return True
        
    async def debug_page_elements(self):
        """Debug helper to identify form elements on the page"""
        logger.info("=== DEBUG: Analyzing page elements ===")
        
        # Find all input elements
        inputs = await self.page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, button');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName,
                    type: el.type || 'none',
                    name: el.name || 'none',
                    id: el.id || 'none',
                    placeholder: el.placeholder || 'none',
                    dataTestId: el.getAttribute('data-test-id') || 'none',
                    text: el.innerText || el.value || 'none',
                    disabled: el.disabled
                }));
            }
        """)
        
        logger.info("Found elements:")
        for elem in inputs:
            logger.info(f"  {elem['tag']} - type:{elem['type']}, name:{elem['name']}, "
                       f"id:{elem['id']}, data-test-id:{elem['dataTestId']}, "
                       f"text:{elem['text']}, disabled:{elem['disabled']}")
    
    async def perform_login(self) -> bool:
        """Perform the login action"""
        logger.info(f"Navigating to {self.url}")
        
        try:
            # Navigate with timeout
            await self.page.goto(self.url, wait_until='networkidle', timeout=30000)
            
            # Add delay to respect server
            await asyncio.sleep(2)
            
            # Debug mode - analyze page elements
            if logger.level == logging.DEBUG:
                await self.debug_page_elements()
            
            # Find and fill email field
            logger.info("Looking for email input field...")
            email_selectors = [
                '[data-test-id="login-form-box-address"]',  # EXACT data-test-id for email
                'input[data-test-id="login-form-box-address"]',  # More specific
                'input[placeholder="Email address"]',  # Exact placeholder match
                '[data-test-id*="email"]',  # data-test-id with email
                '[data-test-id*="username"]',  # data-test-id with username
                '[data-test-id*="address"]',  # data-test-id with address
                'input[type="email"]',
                'input[name*="email" i]',
                'input[name*="username" i]',
                'input[id*="email" i]',
                'input[id*="username" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="username" i]'
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = await self.page.wait_for_selector(selector, timeout=2000)
                    if email_field:
                        logger.info(f"Found email field using selector: {selector}")
                        break
                except:
                    continue
                    
            if not email_field:
                logger.error("Could not find email input field")
                return False
                
            await email_field.fill(self.email)
            logger.info(f"Filled email field with: {self.email}")
            
            # Small delay to let the page react
            await asyncio.sleep(0.5)
            
            # Find and fill password field
            logger.info("Looking for password input field...")
            password_selectors = [
                '[data-test-id="login-form-box-password"]',  # EXACT data-test-id for password
                'input[data-test-id="login-form-box-password"]',  # More specific
                'input[placeholder="Password"]',  # Exact placeholder match
                '[data-test-id*="password"]',  # data-test-id with password
                'input[type="password"]',
                'input[name*="password" i]',
                'input[id*="password" i]',
                'input[placeholder*="password" i]'
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await self.page.wait_for_selector(selector, timeout=2000)
                    if password_field:
                        logger.info(f"Found password field using selector: {selector}")
                        break
                except:
                    continue
                    
            if not password_field:
                logger.error("Could not find password input field")
                return False
                
            await password_field.fill(self.password)
            logger.info("Filled password field")
            
            # Small delay to let the form validate and enable the button
            await asyncio.sleep(1)
            
            # Find and click login button
            logger.info("Looking for login button...")
            login_selectors = [
                '[data-test-id="login-form-button-submit"]',  # Specific data-test-id
                'button[data-test-id*="login"]',  # Any button with login in data-test-id
                'button[data-test-id*="submit"]',  # Any button with submit in data-test-id
                'button:has-text("Log In")',
                'button:has-text("Log in")',
                'button:has-text("LOGIN")',
                'button:has-text("Sign In")',
                'button:has-text("Sign in")',
                'button[type="submit"]:has-text("Log in")',  # More specific
                'button[type="submit"]',
                'input[type="submit"]'
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if login_button:
                        logger.info(f"Found login button using selector: {selector}")
                        break
                except:
                    continue
                    
            if not login_button:
                logger.error("Could not find login button")
                return False
                
            # Wait for button to be enabled (if it's disabled initially)
            try:
                # Check if button is disabled
                is_disabled = await login_button.get_attribute('disabled')
                if is_disabled is not None or is_disabled == '':
                    logger.info("Login button is disabled, waiting for it to be enabled...")
                    
                    # Try multiple approaches to wait for button to be enabled
                    max_wait = 10  # seconds
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait:
                        # Re-check the button state
                        current_disabled = await login_button.get_attribute('disabled')
                        if current_disabled is None:
                            logger.info("Login button is now enabled")
                            break
                            
                        # Try triggering form validation by pressing Tab or Enter in fields
                        await password_field.press('Tab')
                        await asyncio.sleep(0.5)
                        
                        # Check again
                        current_disabled = await login_button.get_attribute('disabled')
                        if current_disabled is None:
                            logger.info("Login button is now enabled")
                            break
                            
                        await asyncio.sleep(0.5)
                    else:
                        logger.warning("Login button did not become enabled within timeout, attempting click anyway")
                        
            except Exception as e:
                logger.debug(f"Button enable check: {e}")
                
            # Click login button
            await login_button.click()
            logger.info("Clicked login button")
            
            # Wait for navigation or element indicating successful login
            logger.info("Waiting for login to complete...")
            await asyncio.sleep(3)
            
            # Check for the favorites sidebar element
            try:
                await self.page.wait_for_selector(
                    '[data-test-id*="sidebar-menuitem-button-Favorites"]',
                    timeout=10000
                )
                logger.info("Login successful - Favorites sidebar element found")
                return True
            except PlaywrightTimeoutError:
                logger.warning("Favorites element not found, checking for other indicators...")
                
                # Check if URL changed (common login indicator)
                current_url = self.page.url
                if current_url != self.url:
                    logger.info(f"URL changed to {current_url}, assuming login successful")
                    return True
                    
                return False
                
        except Exception as e:
            logger.error(f"Login failed with error: {e}")
            return False
            
    async def detect_scrollable_containers(self) -> List[Dict]:
        """Detect all potentially scrollable containers on the page"""
        logger.info("Detecting scrollable containers...")
        
        js_code = """
        () => {
            const containers = [];
            const elements = document.querySelectorAll('*');
            
            for (const el of elements) {
                const style = window.getComputedStyle(el);
                const isScrollable = (
                    style.overflow === 'scroll' || 
                    style.overflow === 'auto' ||
                    style.overflowY === 'scroll' || 
                    style.overflowY === 'auto' ||
                    style.overflowX === 'scroll' || 
                    style.overflowX === 'auto'
                );
                
                if (isScrollable || el.scrollHeight > el.clientHeight) {
                    containers.push({
                        tag: el.tagName,
                        id: el.id || 'none',
                        classes: el.className || 'none',
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight,
                        scrollTop: el.scrollTop,
                        isBody: el === document.body,
                        isHtml: el === document.documentElement,
                        selector: el.id ? `#${el.id}` : 
                                 el.className ? `.${el.className.split(' ')[0]}` : 
                                 el.tagName.toLowerCase()
                    });
                }
            }
            
            return containers;
        }
        """
        
        containers = await self.page.evaluate(js_code)
        logger.info(f"Found {len(containers)} potentially scrollable containers")
        
        for container in containers:
            logger.debug(f"Container: {container}")
            
        return containers
        
    async def get_scroll_position(self) -> Dict:
        """Get current scroll position of all scrollable elements"""
        js_code = """
        () => {
            const positions = [];
            
            // Window scroll
            positions.push({
                element: 'window',
                scrollY: window.scrollY,
                scrollX: window.scrollX
            });
            
            // Document scroll
            positions.push({
                element: 'document',
                scrollTop: document.documentElement.scrollTop,
                scrollLeft: document.documentElement.scrollLeft
            });
            
            // Body scroll
            positions.push({
                element: 'body',
                scrollTop: document.body.scrollTop,
                scrollLeft: document.body.scrollLeft
            });
            
            // All scrollable elements
            const elements = document.querySelectorAll('*');
            for (const el of elements) {
                if (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth) {
                    positions.push({
                        element: el.tagName + (el.id ? '#' + el.id : ''),
                        scrollTop: el.scrollTop,
                        scrollLeft: el.scrollLeft,
                        scrollHeight: el.scrollHeight,
                        clientHeight: el.clientHeight
                    });
                }
            }
            
            return positions;
        }
        """
        
        return await self.page.evaluate(js_code)
        
    async def test_scroll_method_1_window_scroll(self) -> ScrollTestResult:
        """Test Method 1: window.scrollBy()"""
        result = ScrollTestResult("window.scrollBy()")
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Scroll down by viewport height
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Check if scroll happened
            window_pos_initial = next((p for p in initial_pos if p['element'] == 'window'), {})
            window_pos_final = next((p for p in final_pos if p['element'] == 'window'), {})
            
            result.scroll_distance = window_pos_final.get('scrollY', 0) - window_pos_initial.get('scrollY', 0)
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_2_smooth_scroll(self) -> ScrollTestResult:
        """Test Method 2: window.scrollTo() with smooth behavior"""
        result = ScrollTestResult("window.scrollTo(smooth)")
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Smooth scroll down
            await self.page.evaluate("""
                window.scrollTo({
                    top: window.scrollY + window.innerHeight,
                    behavior: 'smooth'
                })
            """)
            await asyncio.sleep(1.5)  # Wait for smooth animation
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            window_pos_initial = next((p for p in initial_pos if p['element'] == 'window'), {})
            window_pos_final = next((p for p in final_pos if p['element'] == 'window'), {})
            
            result.scroll_distance = window_pos_final.get('scrollY', 0) - window_pos_initial.get('scrollY', 0)
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_3_element_scroll(self) -> ScrollTestResult:
        """Test Method 3: Element.scrollIntoView()"""
        result = ScrollTestResult("Element.scrollIntoView()")
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Find elements and scroll to them
            await self.page.evaluate("""
                const elements = document.querySelectorAll('*');
                const viewportHeight = window.innerHeight;
                let targetElement = null;
                
                // Find an element that's below the current viewport
                for (const el of elements) {
                    const rect = el.getBoundingClientRect();
                    if (rect.top > viewportHeight) {
                        targetElement = el;
                        break;
                    }
                }
                
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'instant', block: 'start' });
                }
            """)
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Calculate scroll distance
            for i, initial in enumerate(initial_pos):
                if i < len(final_pos):
                    final = final_pos[i]
                    if initial['element'] == final['element']:
                        diff = final.get('scrollTop', 0) - initial.get('scrollTop', 0)
                        if diff > 0:
                            result.scroll_distance = max(result.scroll_distance, diff)
                            
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_4_container_scroll(self) -> ScrollTestResult:
        """Test Method 4: Direct container scrollTop manipulation"""
        result = ScrollTestResult("container.scrollTop")
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Find and scroll the main scrollable container
            scrolled = await self.page.evaluate("""
                () => {
                    const containers = document.querySelectorAll('*');
                    let scrolled = false;
                    
                    for (const container of containers) {
                        if (container.scrollHeight > container.clientHeight) {
                            const oldScroll = container.scrollTop;
                            container.scrollTop += container.clientHeight;
                            if (container.scrollTop > oldScroll) {
                                scrolled = true;
                                break;
                            }
                        }
                    }
                    
                    return scrolled;
                }
            """)
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Calculate scroll distance
            for i, initial in enumerate(initial_pos):
                if i < len(final_pos):
                    final = final_pos[i]
                    if initial['element'] == final['element']:
                        diff = final.get('scrollTop', 0) - initial.get('scrollTop', 0)
                        if diff > 0:
                            result.scroll_distance = max(result.scroll_distance, diff)
                            
            result.success = scrolled and result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_5_keyboard(self) -> ScrollTestResult:
        """Test Method 5: Keyboard navigation (Page Down)"""
        result = ScrollTestResult("Keyboard (PageDown)")
        result.requires_keyboard = True
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Press Page Down
            await self.page.keyboard.press('PageDown')
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Calculate scroll distance
            window_pos_initial = next((p for p in initial_pos if p['element'] == 'window'), {})
            window_pos_final = next((p for p in final_pos if p['element'] == 'window'), {})
            
            result.scroll_distance = window_pos_final.get('scrollY', 0) - window_pos_initial.get('scrollY', 0)
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_6_mouse_wheel(self) -> ScrollTestResult:
        """Test Method 6: Mouse wheel simulation"""
        result = ScrollTestResult("Mouse Wheel")
        result.requires_mouse = True
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Get viewport center
            viewport = self.page.viewport_size
            center_x = viewport['width'] // 2
            center_y = viewport['height'] // 2
            
            # Simulate mouse wheel
            await self.page.mouse.move(center_x, center_y)
            await self.page.mouse.wheel(0, 500)  # Scroll down 500 pixels
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Calculate scroll distance
            window_pos_initial = next((p for p in initial_pos if p['element'] == 'window'), {})
            window_pos_final = next((p for p in final_pos if p['element'] == 'window'), {})
            
            result.scroll_distance = window_pos_final.get('scrollY', 0) - window_pos_initial.get('scrollY', 0)
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_7_document_scroll(self) -> ScrollTestResult:
        """Test Method 7: document.documentElement.scrollTop"""
        result = ScrollTestResult("documentElement.scrollTop")
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Scroll using documentElement
            await self.page.evaluate("""
                document.documentElement.scrollTop += window.innerHeight;
            """)
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Check document scroll
            doc_pos_initial = next((p for p in initial_pos if p['element'] == 'document'), {})
            doc_pos_final = next((p for p in final_pos if p['element'] == 'document'), {})
            
            result.scroll_distance = doc_pos_final.get('scrollTop', 0) - doc_pos_initial.get('scrollTop', 0)
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def test_scroll_method_8_custom_event(self) -> ScrollTestResult:
        """Test Method 8: Custom scroll event dispatch"""
        result = ScrollTestResult("Custom Scroll Event")
        logger.info(f"Testing {result.method_name}...")
        
        try:
            start_time = time.time()
            initial_pos = await self.get_scroll_position()
            
            # Dispatch custom scroll event
            await self.page.evaluate("""
                () => {
                    // Try to find the main scrollable container
                    let scrollContainer = document.body;
                    const containers = document.querySelectorAll('*');
                    
                    for (const container of containers) {
                        if (container.scrollHeight > container.clientHeight && 
                            container.scrollTop >= 0) {
                            scrollContainer = container;
                            break;
                        }
                    }
                    
                    // Create and dispatch scroll event
                    const scrollEvent = new WheelEvent('wheel', {
                        deltaY: window.innerHeight,
                        bubbles: true,
                        cancelable: true
                    });
                    
                    scrollContainer.dispatchEvent(scrollEvent);
                    
                    // Also try direct manipulation as fallback
                    if (scrollContainer.scrollTop !== undefined) {
                        scrollContainer.scrollTop += window.innerHeight;
                    }
                }
            """)
            await asyncio.sleep(0.5)
            
            final_pos = await self.get_scroll_position()
            result.execution_time = time.time() - start_time
            
            # Calculate scroll distance
            for i, initial in enumerate(initial_pos):
                if i < len(final_pos):
                    final = final_pos[i]
                    if initial['element'] == final['element']:
                        diff = max(
                            final.get('scrollTop', 0) - initial.get('scrollTop', 0),
                            final.get('scrollY', 0) - initial.get('scrollY', 0)
                        )
                        if diff > 0:
                            result.scroll_distance = max(result.scroll_distance, diff)
                            
            result.success = result.scroll_distance > 0
            
        except Exception as e:
            result.error_message = str(e)
            logger.error(f"Error in {result.method_name}: {e}")
            
        return result
        
    async def confirm_with_user(self, method_name: str) -> bool:
        """Ask user to confirm if scrolling was successful"""
        print(f"\n{'='*60}")
        print(f"Method tested: {method_name}")
        print("Did you observe scrolling on the page? (y/n): ", end='', flush=True)
        
        # Get user input with timeout
        try:
            # Using asyncio for non-blocking input
            user_input = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, input),
                timeout=30
            )
            return user_input.lower().strip() in ['y', 'yes']
        except asyncio.TimeoutError:
            print("\nNo response received, assuming no scroll observed")
            return False
            
    async def run_all_tests(self):
        """Run all scroll tests and gather results"""
        logger.info("Starting scroll method tests...")
        
        # Test all methods
        test_methods = [
            self.test_scroll_method_1_window_scroll,
            self.test_scroll_method_2_smooth_scroll,
            self.test_scroll_method_3_element_scroll,
            self.test_scroll_method_4_container_scroll,
            self.test_scroll_method_5_keyboard,
            self.test_scroll_method_6_mouse_wheel,
            self.test_scroll_method_7_document_scroll,
            self.test_scroll_method_8_custom_event,
        ]
        
        for test_method in test_methods:
            try:
                # Reset scroll position before each test
                await self.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
                
                # Run test
                result = await test_method()
                
                # Get user confirmation
                result.user_confirmed = await self.confirm_with_user(result.method_name)
                
                # Log immediate result
                logger.info(f"{result.method_name}: "
                          f"Success={result.success}, "
                          f"Distance={result.scroll_distance}px, "
                          f"Time={result.execution_time:.2f}s, "
                          f"User confirmed={result.user_confirmed}")
                
                self.test_results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to test {test_method.__name__}: {e}")
                
    def rank_results(self) -> List[ScrollTestResult]:
        """Rank test results by performance"""
        # Scoring function
        def score_result(result: ScrollTestResult) -> float:
            score = 0.0
            
            # Success and user confirmation are most important
            if result.success:
                score += 30
            if result.user_confirmed:
                score += 40
                
            # Scroll distance (normalized to 0-10 points)
            if result.scroll_distance > 0:
                score += min(10, result.scroll_distance / 100)
                
            # Speed (faster is better, up to 10 points)
            if result.execution_time > 0:
                score += max(0, 10 - result.execution_time)
                
            # Prefer methods that don't require mouse/keyboard (10 points each)
            if not result.requires_mouse:
                score += 5
            if not result.requires_keyboard:
                score += 5
                
            return score
            
        # Sort by score
        ranked = sorted(self.test_results, key=score_result, reverse=True)
        return ranked
        
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        ranked_results = self.rank_results()
        
        report = []
        report.append("\n" + "="*80)
        report.append("SCROLL METHOD TEST RESULTS SUMMARY")
        report.append("="*80)
        report.append(f"Test completed at: {datetime.now().isoformat()}")
        report.append(f"URL tested: {self.url}")
        report.append(f"Total methods tested: {len(self.test_results)}")
        report.append("")
        
        report.append("PERFORMANCE RANKING:")
        report.append("-"*80)
        
        for i, result in enumerate(ranked_results, 1):
            report.append(f"\nRank #{i}: {result.method_name}")
            report.append(f"  ✓ Success: {result.success}")
            report.append(f"  ✓ User Confirmed: {result.user_confirmed}")
            report.append(f"  ✓ Scroll Distance: {result.scroll_distance}px")
            report.append(f"  ✓ Execution Time: {result.execution_time:.3f}s")
            report.append(f"  ✓ Requires Mouse: {result.requires_mouse}")
            report.append(f"  ✓ Requires Keyboard: {result.requires_keyboard}")
            if result.error_message:
                report.append(f"  ✗ Error: {result.error_message}")
                
        report.append("\n" + "="*80)
        report.append("RECOMMENDATIONS:")
        report.append("-"*80)
        
        if ranked_results:
            best = ranked_results[0]
            if best.success and best.user_confirmed:
                report.append(f"✓ BEST METHOD: {best.method_name}")
                report.append(f"  - Reliable and confirmed by user")
                report.append(f"  - Scroll distance: {best.scroll_distance}px")
                report.append(f"  - Fast execution: {best.execution_time:.3f}s")
                
                # Find best non-interfering method
                non_interfering = [r for r in ranked_results 
                                  if not r.requires_mouse and not r.requires_keyboard 
                                  and r.success]
                if non_interfering:
                    report.append(f"\n✓ BEST NON-INTERFERING METHOD: {non_interfering[0].method_name}")
                    report.append(f"  - Doesn't require mouse or keyboard")
                    report.append(f"  - Can run in background")
        
        report.append("\n" + "="*80)
        return "\n".join(report)
        
    async def save_results(self):
        """Save test results to files"""
        # Save detailed JSON results
        json_path = Path("scroll_test_results.json")
        with open(json_path, 'w') as f:
            json.dump(
                {
                    'timestamp': datetime.now().isoformat(),
                    'url': self.url,
                    'results': [r.to_dict() for r in self.test_results],
                    'ranked_results': [r.to_dict() for r in self.rank_results()]
                },
                f,
                indent=2
            )
        logger.info(f"Detailed results saved to {json_path}")
        
        # Save human-readable report
        report = self.generate_report()
        report_path = Path("scroll_test_report.txt")
        with open(report_path, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to {report_path}")
        
        # Also print to console
        print(report)
        
    async def cleanup(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
            
    async def run(self) -> bool:
        """Main execution flow"""
        try:
            # Safety check
            if not await self.verify_url_safety():
                logger.error("URL failed safety verification")
                return False
                
            # Initialize browser
            await self.initialize_browser()
            
            # Perform login
            if not await self.perform_login():
                logger.error("Login failed, aborting tests")
                return False
                
            # Wait a bit after login
            await asyncio.sleep(2)
            
            # Detect scrollable containers
            containers = await self.detect_scrollable_containers()
            
            # Run all scroll tests
            await self.run_all_tests()
            
            # Save results
            await self.save_results()
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
            
        finally:
            await self.cleanup()


def validate_args(args):
    """Validate command line arguments"""
    # Check URL format
    parsed = urlparse(args.url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL format: {args.url}")
        
    # Basic email validation
    if '@' not in args.email:
        raise ValueError(f"Invalid email format: {args.email}")
        
    # Password minimum length
    if len(args.password) < 1:
        raise ValueError("Password cannot be empty")
        
    return True


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Login and Scroll Testing Tool - For authorized testing only',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
IMPORTANT NOTICE:
This tool is for authorized testing and development purposes only.
- Ensure you have permission to automate interactions with the target website
- Respect robots.txt and terms of service
- Use appropriate delays between requests
- Never use for unauthorized access or malicious purposes

Example usage:
  python login_scroll_tester.py --url https://example.com/login --email user@example.com --password mypass
        """
    )
    
    parser.add_argument('--url', required=True, help='Login page URL')
    parser.add_argument('--email', required=True, help='Email for login')
    parser.add_argument('--password', required=True, help='Password for login')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate arguments
        validate_args(args)
        
        # Show disclaimer
        print("="*80)
        print("LOGIN AND SCROLL TESTING TOOL")
        print("="*80)
        print("This tool will:")
        print("1. Log into the specified website")
        print("2. Detect scrollable containers")
        print("3. Test multiple scroll methods")
        print("4. Ask for your confirmation after each test")
        print("5. Generate a comprehensive report")
        print("\nIMPORTANT: Only use on websites you have permission to test!")
        print("="*80)
        print("\nPress Enter to continue or Ctrl+C to abort...", end='', flush=True)
        input()
        
        # Run the tester
        tester = LoginScrollTester(args.url, args.email, args.password)
        success = await tester.run()
        
        if success:
            logger.info("✓ All tests completed successfully!")
            return 0
        else:
            logger.error("✗ Tests failed or were incomplete")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nTests aborted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)