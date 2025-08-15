# Web Automation App
# Core automation engine with modular action system

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from playwright.async_api import async_playwright, Page, Browser, ElementHandle

# Import credential manager for secure credential handling
try:
    from utils.credential_manager import CredentialManager
    CREDENTIAL_MANAGER_AVAILABLE = True
except ImportError:
    CREDENTIAL_MANAGER_AVAILABLE = False
    logger.warning("Credential manager not available. Using plaintext credentials (SECURITY RISK)")

# Import performance monitoring
try:
    from utils.performance_monitor import get_monitor, track_performance
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False
    logger.warning("Performance monitoring not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BlockInfo:
    """Information about a control block"""
    type: str  # "if", "while", "else", "elif"
    start_index: int
    end_index: int = None
    condition_result: bool = False
    has_executed: bool = False  # For IF blocks
    iteration_count: int = 0  # For WHILE loops

class ExecutionContext:
    """Context for block-based execution"""
    def __init__(self):
        self.instruction_pointer = 0
        self.block_stack = []  # Stack of active blocks
        self.last_check_result = None
        self.should_increment = True
        self.break_flag = False
        self.continue_flag = False
        self.continue_on_error = True
        self.variables = {}  # For future variable support
        
    def push_block(self, block_type: str, start_index: int) -> BlockInfo:
        """Push a new block onto the stack"""
        block = BlockInfo(type=block_type, start_index=start_index)
        self.block_stack.append(block)
        return block
    
    def pop_block(self) -> BlockInfo:
        """Pop the top block from the stack"""
        if self.block_stack:
            return self.block_stack.pop()
        return None
    
    def current_block(self) -> BlockInfo:
        """Get the current block without popping"""
        if self.block_stack:
            return self.block_stack[-1]
        return None
    
    def find_block_end(self, actions: list, start_index: int, block_type: str) -> int:
        """Find the matching end for a block"""
        depth = 1
        current = start_index + 1
        
        begin_types = {
            "if": ActionType.IF_BEGIN,
            "while": ActionType.WHILE_BEGIN
        }
        
        end_types = {
            "if": ActionType.IF_END,
            "while": ActionType.WHILE_END
        }
        
        begin_type = begin_types.get(block_type)
        end_type = end_types.get(block_type)
        
        while current < len(actions) and depth > 0:
            action = actions[current]
            if action.type == begin_type:
                depth += 1
            elif action.type == end_type:
                depth -= 1
                if depth == 0:
                    return current
            current += 1
        
        return len(actions)  # If no matching end found

def evaluate_condition(check_result: dict, condition_config: dict) -> bool:
    """Evaluate a condition based on check result"""
    if not check_result:
        return False
    
    condition = condition_config.get("condition", "check_passed")
    
    if condition == "check_passed":
        return check_result.get("success", False)
    elif condition == "check_failed":
        return not check_result.get("success", True)
    elif condition == "value_equals":
        expected = condition_config.get("expected_value", "")
        actual = check_result.get("actual_value", "")
        return str(actual) == str(expected)
    elif condition == "value_not_equals":
        expected = condition_config.get("expected_value", "")
        actual = check_result.get("actual_value", "")
        return str(actual) != str(expected)
    elif condition == "value_greater":
        expected = condition_config.get("expected_value", "0")
        actual = check_result.get("actual_value", "0")
        try:
            return float(actual) > float(expected)
        except (ValueError, TypeError):
            return False
    elif condition == "value_less":
        expected = condition_config.get("expected_value", "0")
        actual = check_result.get("actual_value", "0")
        try:
            return float(actual) < float(expected)
        except (ValueError, TypeError):
            return False
    
    return False

class ActionType(Enum):
    """Enumeration of supported action types"""
    LOGIN = "login"
    EXPAND_DIALOG = "expand_dialog"
    INPUT_TEXT = "input_text"
    UPLOAD_IMAGE = "upload_image"
    TOGGLE_SETTING = "toggle_setting"
    CLICK_BUTTON = "click_button"
    CHECK_QUEUE = "check_queue"
    CHECK_ELEMENT = "check_element"  # Check element value/attribute
    CONDITIONAL_WAIT = "conditional_wait"  # Wait and retry based on condition
    SKIP_IF = "skip_if"  # Skip next actions if condition met
    # Programming-like conditional blocks
    IF_BEGIN = "if_begin"        # Start IF block
    ELIF = "elif"                # ELIF condition
    ELSE = "else"                # ELSE block
    IF_END = "if_end"           # End IF block
    WHILE_BEGIN = "while_begin"  # Start WHILE loop
    WHILE_END = "while_end"     # End WHILE loop
    BREAK = "break"             # Break from loop
    CONTINUE = "continue"       # Continue loop
    # Regular actions
    DOWNLOAD_FILE = "download_file"
    REFRESH_PAGE = "refresh_page"
    SWITCH_PANEL = "switch_panel"
    WAIT = "wait"
    WAIT_FOR_ELEMENT = "wait_for_element"

@dataclass
class Action:
    """Represents a single automation action"""
    type: ActionType
    selector: Optional[str] = None
    value: Optional[Any] = None
    timeout: int = 10000  # milliseconds - reduced from 30s to 10s for better performance
    description: Optional[str] = None

@dataclass
class AutomationConfig:
    """Configuration for automation sequence"""
    name: str
    url: str
    actions: List[Action]
    headless: bool = True
    viewport: Dict[str, int] = None
    keep_browser_open: bool = True  # Keep browser open after automation by default
    
    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1280, "height": 720}

class WebAutomationEngine:
    """Core automation engine for web interactions"""
    
    def __init__(self, config: AutomationConfig):
        self.config = config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self.keep_browser_open = getattr(config, 'keep_browser_open', True)  # Default to keeping browser open
        
    async def initialize(self):
        """Initialize browser and page - reuse existing if available"""
        try:
            # Check if we already have a browser and it's still connected
            if self.browser and self.browser.is_connected():
                logger.info("Reusing existing browser window")
                
                # Check if page is still valid
                if self.page and not self.page.is_closed():
                    logger.info("Reusing existing page")
                    
                    # Wait for page to be ready
                    try:
                        await self.page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except:
                        pass  # Page might already be loaded
                    
                    # Just navigate to the new URL if needed
                    current_url = self.page.url
                    if current_url != self.config.url:
                        logger.info(f"Navigating from {current_url} to {self.config.url}")
                        await self.page.goto(self.config.url, wait_until="networkidle")
                    else:
                        logger.info(f"Already on {self.config.url}, performing minimal page state check...")
                        # For reused pages on same URL, do minimal checking to avoid hanging
                        
                        # Quick responsiveness test
                        try:
                            logger.info("Testing page responsiveness...")
                            await asyncio.wait_for(
                                self.page.evaluate("1 + 1"), 
                                timeout=1.0
                            )
                            logger.info("Page is responsive, skipping detailed state checks")
                        except (asyncio.TimeoutError, Exception) as e:
                            logger.warning(f"Page responsiveness test failed: {e}, but continuing anyway...")
                        
                        logger.info("Page state check completed for reused page")
                else:
                    # Page was closed, create a new one in existing context
                    logger.info("Creating new page in existing browser")
                    if not self.context or self.context._impl_obj._is_closed:
                        self.context = await self.browser.new_context(
                            viewport=self.config.viewport,
                            accept_downloads=True
                        )
                    self.page = await self.context.new_page()
                    # Navigate to the target URL for the new page
                    await self.page.goto(self.config.url, wait_until="networkidle")
            else:
                # No browser or browser was closed, create new one
                await self._create_new_browser()
                
        except Exception as e:
            logger.warning(f"Error reusing browser: {e}. Creating new browser instance.")
            # If anything fails, create a fresh browser
            await self._create_new_browser()
    
    async def _create_new_browser(self):
        """Create a new browser instance"""
        logger.info("Creating new browser instance")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=['--disable-dev-shm-usage', '--disable-extensions']
        )
        self.context = await self.browser.new_context(
            viewport=self.config.viewport,
            accept_downloads=True
        )
        self.page = await self.context.new_page()
        
    async def cleanup(self, close_browser=True):
        """Clean up browser resources
        
        Args:
            close_browser: If False, keeps browser and page open after automation
        """
        if close_browser:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        else:
            logger.info("Browser and page kept open after automation completion")
    
    async def close_browser(self):
        """Manually close the browser and clean up resources"""
        logger.info("Manually closing browser...")
        await self.cleanup(close_browser=True)
        # Clear references so next run creates new browser
        self.browser = None
        self.page = None
        self.context = None
    
    def _resolve_credentials(self, login_data: dict) -> tuple:
        """
        Resolve credentials from secure storage or fallback to plaintext
        Returns (username, password) tuple
        """
        # Check for secure credential reference
        if 'credential_id' in login_data and CREDENTIAL_MANAGER_AVAILABLE:
            try:
                cm = CredentialManager()
                creds = cm.get_credential(login_data['credential_id'])
                if creds:
                    logger.info(f"✅ Using secure credentials for: {login_data['credential_id']}")
                    return creds['username'], creds['password']
                else:
                    logger.warning(f"⚠️ Credential '{login_data['credential_id']}' not found in secure storage")
            except Exception as e:
                logger.error(f"❌ Error loading secure credentials: {e}")
        
        # Fallback to plaintext credentials (with warning)
        if 'username' in login_data and 'password' in login_data:
            logger.warning("⚠️ SECURITY WARNING: Using plaintext credentials from configuration")
            logger.warning("   Consider migrating to secure credential storage")
            return login_data['username'], login_data['password']
        
        # Handle template-style references (${credential_id.field})
        username = login_data.get('username', '')
        password = login_data.get('password', '')
        
        if username.startswith('${') and CREDENTIAL_MANAGER_AVAILABLE:
            try:
                # Extract credential_id from ${credential_id.username}
                cred_ref = username.strip('${}')
                if '.' in cred_ref:
                    cred_id, field = cred_ref.split('.', 1)
                    cm = CredentialManager()
                    creds = cm.get_credential(cred_id)
                    if creds and field in creds:
                        username = creds[field]
                        logger.info(f"✅ Resolved secure credential reference: {cred_ref}")
            except Exception as e:
                logger.warning(f"⚠️ Could not resolve credential reference {username}: {e}")
        
        if password.startswith('${') and CREDENTIAL_MANAGER_AVAILABLE:
            try:
                # Extract credential_id from ${credential_id.password}
                cred_ref = password.strip('${}')
                if '.' in cred_ref:
                    cred_id, field = cred_ref.split('.', 1)
                    cm = CredentialManager()
                    creds = cm.get_credential(cred_id)
                    if creds and field in creds:
                        password = creds[field]
                        logger.info(f"✅ Resolved secure credential reference: {cred_ref}")
            except Exception as e:
                logger.warning(f"⚠️ Could not resolve credential reference {password}: {e}")
        
        if not username or not password:
            raise ValueError("No valid credentials found. Please configure secure credentials or provide plaintext values.")
        
        return username, password
    
    async def _smart_wait(self, condition_check, max_wait_ms: int = 5000, check_interval_ms: int = 100):
        """
        Smart waiting that checks condition and returns as soon as it's met
        instead of using fixed delays
        """
        start_time = asyncio.get_event_loop().time()
        max_wait_seconds = max_wait_ms / 1000
        check_interval_seconds = check_interval_ms / 1000
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_seconds:
            try:
                if await condition_check():
                    return True
            except Exception:
                pass
            
            await asyncio.sleep(check_interval_seconds)
        
        return False
    
    async def _wait_for_page_stability(self, timeout_ms: int = 3000):
        """
        Wait for page to be in a stable state instead of using fixed delays
        """
        async def is_page_stable():
            try:
                # Check if page is loaded and ready
                ready_state = await self.page.evaluate("document.readyState")
                return ready_state == "complete"
            except Exception:
                return False
        
        stable = await self._smart_wait(is_page_stable, timeout_ms)
        if stable:
            logger.info("✅ Page reached stable state")
        else:
            logger.warning("⚠️ Page stability timeout, continuing anyway")
            
    async def navigate_to_url(self):
        """Navigate to the target URL if not already there"""
        logger.info("=== STARTING NAVIGATION ===")
        current_url = self.page.url if self.page else None
        logger.info(f"Current URL: {current_url}")
        logger.info(f"Target URL: {self.config.url}")
        
        if current_url == self.config.url:
            logger.info(f"Already on target URL: {self.config.url}")
        else:
            logger.info(f"Navigating to {self.config.url}")
            await self.page.goto(self.config.url, wait_until="networkidle")
        
        logger.info("=== NAVIGATION COMPLETED ===") 
        
    async def execute_action(self, action: Action) -> Any:
        """Execute a single action"""
        logger.info(f"Executing action: {action.type.value} - {action.description or ''}")
        logger.info(f"Action selector: {action.selector}")
        logger.info(f"Action value: {action.value}")
        logger.info(f"Action timeout: {action.timeout}")
        
        try:
            # Pre-action debugging information
            logger.info(f"Current page URL: {self.page.url}")
            try:
                page_title = await asyncio.wait_for(self.page.title(), timeout=3.0)
                logger.info(f"Page title: {page_title}")
            except asyncio.TimeoutError:
                logger.warning("Page title retrieval timed out")
            except Exception as e:
                logger.warning(f"Could not get page title: {e}")
            
            # Check if page is still responsive
            try:
                await asyncio.wait_for(
                    self.page.evaluate("1 + 1"), 
                    timeout=2.0
                )
                logger.info("Page is responsive")
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"Page responsiveness check failed: {e}")
                # Try to recover with shorter timeout
                try:
                    logger.info("Attempting to refresh page state...")
                    await asyncio.wait_for(
                        self.page.wait_for_load_state("domcontentloaded", timeout=3000),
                        timeout=5.0
                    )
                    logger.info("Page state refreshed")
                except Exception as recovery_error:
                    logger.warning(f"Page recovery failed: {recovery_error}, continuing anyway...")
            
            # Track performance if monitoring is available
            if PERFORMANCE_MONITORING_AVAILABLE:
                async with track_performance(action.type.value, action.description):
                    await self._execute_single_action(action)
            else:
                await self._execute_single_action(action)
    
    async def _execute_single_action(self, action):
        """Execute a single action with performance tracking"""
        if action.type == ActionType.LOGIN:
            # Handle login action with secure credential support
            # Expected value format: {"credential_id": "id", "username_selector": "#username", "password_selector": "#password", "submit_selector": "#login-btn"}
            # OR legacy: {"username": "user", "password": "pass", "username_selector": "#username", "password_selector": "#password", "submit_selector": "#login-btn"}
            login_data = action.value
            
            # Resolve credentials securely
            username, password = self._resolve_credentials(login_data)
            
            # Fill username field
            await self.page.fill(login_data["username_selector"], username, timeout=action.timeout)
            
            # Fill password field
            await self.page.fill(login_data["password_selector"], password, timeout=action.timeout)
            
            # Click submit button
            await self.page.click(login_data["submit_selector"], timeout=action.timeout)
            
            # Wait for navigation or login completion
            await self.page.wait_for_load_state("networkidle")
                
            elif action.type == ActionType.EXPAND_DIALOG:
                await self.page.click(action.selector, timeout=action.timeout)
                await self.page.wait_for_load_state("networkidle")
                
            elif action.type == ActionType.INPUT_TEXT:
                await self.page.fill(action.selector, action.value, timeout=action.timeout)
                
            elif action.type == ActionType.UPLOAD_IMAGE:
                await self.page.set_input_files(action.selector, action.value, timeout=action.timeout)
                
            elif action.type == ActionType.TOGGLE_SETTING:
                element = await self.page.query_selector(action.selector)
                if element:
                    is_checked = await element.is_checked()
                    if is_checked != action.value:
                        await element.click()
                        
            elif action.type == ActionType.CLICK_BUTTON:
                # Enhanced click action with comprehensive debugging
                logger.info(f"Starting CLICK_BUTTON action for selector: {action.selector}")
                
                # Wait for page stability instead of fixed delay
                logger.info("Checking page stability...")
                try:
                    await self._wait_for_page_stability(3000)
                except Exception as e:
                    logger.warning(f"Page stability check failed: {e}, continuing anyway...")
                
                # Wrap entire click action in timeout to prevent hanging
                try:
                    await asyncio.wait_for(self._execute_click_action(action), timeout=45.0)
                except asyncio.TimeoutError:
                    logger.error(f"Click action timed out after 45 seconds for selector: {action.selector}")
                    raise Exception(f"Click action timeout: {action.selector}")
                    
            elif action.type == ActionType.CHECK_QUEUE:
                # Check queue status and return completion status
                queue_items = await self.page.query_selector_all(action.selector)
                completed = []
                for item in queue_items:
                    text = await item.text_content()
                    if action.value and action.value in text:
                        completed.append(text)
                return completed
                
            elif action.type == ActionType.CHECK_ELEMENT:
                # Check element value/attribute against expected conditions
                element = await self.page.wait_for_selector(action.selector, timeout=action.timeout)
                if not element:
                    logger.error(f"Element not found: {action.selector}")
                    return {"success": False, "error": "Element not found"}
                
                # Get element properties
                element_info = await element.evaluate("""
                    el => ({
                        text: el.textContent?.trim() || '',
                        value: el.value || el.getAttribute('value') || '',
                        innerText: el.innerText?.trim() || '',
                        innerHTML: el.innerHTML?.trim() || '',
                        attributes: Array.from(el.attributes).reduce((acc, attr) => {
                            acc[attr.name] = attr.value;
                            return acc;
                        }, {})
                    })
                """)
                
                # Parse the check condition from action.value
                # Format: {"check": "equals|not_equals|greater|less|contains", "value": "expected_value", "attribute": "text|value|attr_name"}
                check_config = action.value if isinstance(action.value, dict) else {"check": "equals", "value": str(action.value), "attribute": "text"}
                
                check_type = check_config.get("check", "equals")
                expected_value = check_config.get("value", "")
                attribute = check_config.get("attribute", "text")
                
                # Get the actual value to check
                if attribute == "text":
                    actual_value = element_info["text"] or element_info["innerText"]
                elif attribute == "value":
                    actual_value = element_info["value"]
                elif attribute in element_info["attributes"]:
                    actual_value = element_info["attributes"][attribute]
                else:
                    actual_value = element_info.get(attribute, "")
                
                # Perform the check
                check_passed = False
                if check_type == "equals":
                    check_passed = str(actual_value) == str(expected_value)
                elif check_type == "not_equals":
                    check_passed = str(actual_value) != str(expected_value)
                elif check_type == "greater":
                    try:
                        check_passed = float(actual_value) > float(expected_value)
                    except (ValueError, TypeError):
                        check_passed = False
                elif check_type == "less":
                    try:
                        check_passed = float(actual_value) < float(expected_value)
                    except (ValueError, TypeError):
                        check_passed = False
                elif check_type == "contains":
                    check_passed = str(expected_value) in str(actual_value)
                elif check_type == "not_zero":
                    try:
                        check_passed = float(actual_value) != 0
                    except (ValueError, TypeError):
                        check_passed = actual_value != "0" and actual_value != ""
                
                logger.info(f"Check element: {attribute}='{actual_value}' {check_type} '{expected_value}' => {check_passed}")
                
                result = {
                    "success": check_passed,
                    "actual_value": actual_value,
                    "expected_value": expected_value,
                    "check_type": check_type,
                    "attribute": attribute
                }
                
                # Store for conditional actions
                self._last_check_result = result
                
                return result
                
            elif action.type == ActionType.CONDITIONAL_WAIT:
                # Wait and retry based on previous check result
                # Format: {"condition": "check_failed|check_passed", "wait_time": ms, "max_retries": n, "retry_from_action": action_index}
                config = action.value if isinstance(action.value, dict) else {}
                
                condition = config.get("condition", "check_failed")
                wait_time = config.get("wait_time", 5000)
                max_retries = config.get("max_retries", 3)
                retry_from = config.get("retry_from_action", 0)
                
                # Get the last check result from context
                last_check = getattr(self, '_last_check_result', None)
                if not last_check:
                    # Try to get from the previous action if it was a CHECK_ELEMENT
                    logger.warning("No previous check result for conditional wait")
                    return {"retry": False}
                
                # Store last check for this instance
                self._last_check_result = last_check
                
                # Increment retry counter
                if not hasattr(self, '_retry_count'):
                    self._retry_count = 0
                
                # Check condition
                should_retry = False
                if condition == "check_failed" and not last_check.get("success", True):
                    should_retry = True
                elif condition == "check_passed" and last_check.get("success", False):
                    should_retry = True
                elif condition == "value_equals":
                    expected = config.get("expected_value", "")
                    actual = last_check.get("actual_value", "")
                    should_retry = str(actual) == str(expected)
                elif condition == "value_not_equals":
                    expected = config.get("expected_value", "")
                    actual = last_check.get("actual_value", "")
                    should_retry = str(actual) != str(expected)
                
                if should_retry and self._retry_count < max_retries:
                    self._retry_count += 1
                    logger.info(f"Conditional wait: Retry {self._retry_count}/{max_retries} after {wait_time}ms")
                    await self.page.wait_for_timeout(wait_time)
                    return {"retry": True, "retry_from_action": retry_from}
                else:
                    if self._retry_count >= max_retries:
                        logger.warning(f"Max retries ({max_retries}) reached")
                    self._retry_count = 0  # Reset for next time
                    return {"retry": False}
            
            elif action.type == ActionType.SKIP_IF:
                # Skip next actions based on previous check result
                # Format: {"condition": "check_failed|check_passed|value_equals", "skip_count": n, "expected_value": val}
                config = action.value if isinstance(action.value, dict) else {}
                
                condition = config.get("condition", "check_failed")
                skip_count = config.get("skip_count", 1)
                
                # Get the last check result
                last_check = getattr(self, '_last_check_result', None)
                if not last_check:
                    logger.warning("No previous check result for skip condition")
                    return {"skip": False}
                
                # Check condition
                should_skip = False
                if condition == "check_failed" and not last_check.get("success", True):
                    should_skip = True
                elif condition == "check_passed" and last_check.get("success", False):
                    should_skip = True
                elif condition == "value_equals":
                    expected = config.get("expected_value", "")
                    actual = last_check.get("actual_value", "")
                    should_skip = str(actual) == str(expected)
                elif condition == "value_not_equals":
                    expected = config.get("expected_value", "")
                    actual = last_check.get("actual_value", "")
                    should_skip = str(actual) != str(expected)
                
                if should_skip:
                    logger.info(f"Skip condition met, will skip next {skip_count} actions")
                    return {"skip": True, "skip_count": skip_count}
                else:
                    return {"skip": False}
                
            elif action.type == ActionType.DOWNLOAD_FILE:
                # Start download
                async with self.page.expect_download(timeout=action.timeout) as download_info:
                    await self.page.click(action.selector)
                download = await download_info.value
                
                # Save to downloads folder
                download_path = Path("downloads") / download.suggested_filename
                download_path.parent.mkdir(exist_ok=True)
                await download.save_as(download_path)
                logger.info(f"Downloaded file to: {download_path}")
                return str(download_path)
                
            elif action.type == ActionType.REFRESH_PAGE:
                await self.page.reload(wait_until="networkidle")
                
            elif action.type == ActionType.SWITCH_PANEL:
                await self.page.click(action.selector, timeout=action.timeout)
                await self.page.wait_for_load_state("networkidle")
                
            elif action.type == ActionType.WAIT:
                await asyncio.sleep(action.value / 1000)  # Convert to seconds
                
            elif action.type == ActionType.WAIT_FOR_ELEMENT:
                logger.info(f"Waiting for element: {action.selector}")
                try:
                    await self.page.wait_for_selector(action.selector, timeout=action.timeout)
                    logger.info(f"Element found: {action.selector}")
                except Exception as e:
                    # Check if element exists at all
                    elements = await self.page.query_selector_all(action.selector)
                    logger.error(f"Wait for element failed: {action.selector}")
                    logger.error(f"Found {len(elements)} matching elements")
                    if len(elements) == 0:
                        logger.error("Element selector not found on page")
                        # Log available elements for debugging
                        all_inputs = await self.page.query_selector_all("input")
                        all_buttons = await self.page.query_selector_all("button")
                        logger.error(f"Available inputs on page: {len(all_inputs)}")
                        logger.error(f"Available buttons on page: {len(all_buttons)}")
                    raise
                
        except Exception as e:
            error_details = {
                "action_type": action.type.value,
                "selector": action.selector,
                "value": str(action.value) if action.value else None,
                "timeout": action.timeout,
                "description": action.description,
                "error_message": str(e),
                "error_type": type(e).__name__,
                "page_url": self.page.url if self.page else "Unknown",
                "page_title": await self.page.title() if self.page else "Unknown"
            }
            logger.error(f"DETAILED ERROR for {action.type.value}:")
            logger.error(f"  Selector: {action.selector}")
            logger.error(f"  Error: {str(e)}")
            logger.error(f"  Error Type: {type(e).__name__}")
            logger.error(f"  Page URL: {error_details['page_url']}")
            logger.error(f"  Page Title: {error_details['page_title']}")
            
            # Add element debugging for selector-based actions
            if action.selector and self.page:
                try:
                    elements = await self.page.query_selector_all(action.selector)
                    logger.error(f"  Elements found with selector '{action.selector}': {len(elements)}")
                    
                    if len(elements) == 0:
                        # Suggest similar selectors
                        logger.error("  DEBUGGING: Checking for similar elements...")
                        if "#" in action.selector:
                            id_part = action.selector.replace("#", "")
                            similar = await self.page.query_selector_all(f"[id*='{id_part}']")
                            logger.error(f"    Elements with similar ID: {len(similar)}")
                        if "." in action.selector:
                            class_part = action.selector.replace(".", "")
                            similar = await self.page.query_selector_all(f"[class*='{class_part}']")
                            logger.error(f"    Elements with similar class: {len(similar)}")
                        if action.selector.startswith("input"):
                            all_inputs = await self.page.query_selector_all("input")
                            logger.error(f"    Total input elements on page: {len(all_inputs)}")
                            for i, inp in enumerate(all_inputs[:5]):  # Log first 5 inputs
                                attrs = await inp.evaluate("el => ({name: el.name, id: el.id, class: el.className, type: el.type})")
                                logger.error(f"      Input {i+1}: {attrs}")
                except Exception as debug_error:
                    logger.error(f"  Could not debug selector: {debug_error}")
            
            raise
    
    async def _execute_click_action(self, action):
        """Execute click action with comprehensive error handling"""
        try:
            # First check if page is ready and responsive with timeout
            try:
                logger.info("Checking page state with timeout...")
                page_state = await asyncio.wait_for(
                    self.page.evaluate("document.readyState"), 
                    timeout=3.0
                )
                logger.info(f"Page ready state: {page_state}")
            except asyncio.TimeoutError:
                logger.warning("Page state check timed out, but continuing...")
                page_state = "unknown"
            except Exception as e:
                logger.warning(f"Could not check page state: {e}")
                page_state = "unknown"
            
            # Validate and potentially convert data-test-id selector
            selector = action.selector
            if selector.startswith('data-test-id='):
                # Convert data-test-id=value to [data-test-id="value"]
                test_id = selector.replace('data-test-id=', '').strip('"\'')
                selector = f'[data-test-id="{test_id}"]'
                logger.info(f"Converted selector to: {selector}")
            
            # Wait for the selector to be present with multiple attempts
            element = None
            for attempt in range(3):
                logger.info(f"Attempt {attempt + 1}: Looking for element with selector: {selector}")
                
                # Check if element exists first
                element = await self.page.query_selector(selector)
                if element:
                    logger.info(f"Element found on attempt {attempt + 1}")
                    break
                
                # If not found, wait and try again
                logger.warning(f"Element not found on attempt {attempt + 1}, waiting...")
                await asyncio.sleep(0.5)  # Reduced from 1.5s to 500ms
            
            if not element:
                # Final attempt with explicit wait
                logger.info(f"Final attempt: Waiting for selector with timeout: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=action.timeout, state="attached")
            
            if element:
                # Log element details for debugging with timeout
                try:
                    logger.info("Getting element details...")
                    element_info = await asyncio.wait_for(
                        element.evaluate("""
                            el => ({
                                tagName: el.tagName,
                                id: el.id,
                                className: el.className,
                                textContent: el.textContent?.trim().substring(0, 50) || '',
                                visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
                                disabled: el.disabled || el.hasAttribute('disabled'),
                                dataTestId: el.getAttribute('data-test-id')
                            })
                        """),
                        timeout=5.0
                    )
                    logger.info(f"Element details: {element_info}")
                except asyncio.TimeoutError:
                    logger.warning("Element details evaluation timed out, using basic info")
                    element_info = {"tagName": "UNKNOWN", "className": "timeout"}
                except Exception as e:
                    logger.warning(f"Could not get element details: {e}")
                    element_info = {"tagName": "ERROR", "className": str(e)}
                
                # Check if element is visible and enabled with timeout
                try:
                    logger.info("Checking element visibility and state...")
                    is_visible = await asyncio.wait_for(element.is_visible(), timeout=3.0)
                    is_enabled = await asyncio.wait_for(element.is_enabled(), timeout=3.0)
                    logger.info(f"Element visible: {is_visible}, enabled: {is_enabled}")
                except asyncio.TimeoutError:
                    logger.warning("Element state check timed out, assuming visible and enabled")
                    is_visible = True
                    is_enabled = True
                except Exception as e:
                    logger.warning(f"Element state check failed: {e}, assuming visible and enabled")
                    is_visible = True
                    is_enabled = True
                
                if not is_visible:
                    logger.info("Element not visible, scrolling into view...")
                    await element.scroll_into_view_if_needed()
                    # Wait a bit after scrolling
                    await asyncio.sleep(0.2)  # Reduced from 500ms to 200ms
                    is_visible = await asyncio.wait_for(element.is_visible(), timeout=3.0)
                    logger.info(f"Element visible after scroll: {is_visible}")
                
                if not is_enabled:
                    logger.warning("Element is disabled, but attempting click anyway...")
                
                # Attempt to click the element
                logger.info(f"Attempting to click element: {selector}")
                await element.click(timeout=action.timeout, force=True)
                logger.info("Click completed successfully")
                
                # Wait for any page changes with smart waiting
                async def check_page_ready():
                    try:
                        return await self.page.evaluate("document.readyState === 'complete'")
                    except:
                        return False
                
                await self._smart_wait(check_page_ready, 1000)  # Max 1s wait
                
            else:
                raise Exception(f"Element not found after all attempts: {selector}")
                
        except Exception as e:
            logger.error(f"Primary click method failed for {selector}: {str(e)}")
            
            # Try alternative methods
            try:
                logger.info(f"Trying page.click() method for: {selector}")
                await self.page.click(selector, timeout=action.timeout, force=True)
                logger.info("Alternative page.click() succeeded")
            except Exception as e2:
                logger.error(f"Alternative page.click() also failed: {str(e2)}")
                
                # Try JavaScript click as last resort
                try:
                    logger.info(f"Trying JavaScript click for: {selector}")
                    await self.page.evaluate(f"""
                        const element = document.querySelector('{selector}');
                        if (element) {{
                            element.click();
                            console.log('JavaScript click executed');
                        }} else {{
                            throw new Error('Element not found for JavaScript click');
                        }}
                    """)
                    logger.info("JavaScript click succeeded")
                except Exception as e3:
                    logger.error(f"JavaScript click also failed: {str(e3)}")
                    raise Exception(f"All click methods failed for {selector}: Primary: {str(e)}, Alternative: {str(e2)}, JavaScript: {str(e3)}")
            
    async def run_automation(self) -> Dict[str, Any]:
        """Run automation with block-based conditional flow control"""
        results = {
            "success": False,
            "actions_completed": 0,
            "total_actions": len(self.config.actions),
            "errors": [],
            "outputs": {}
        }
        
        try:
            logger.info("=== STARTING AUTOMATION RUN ===")
            await self.initialize()
            logger.info("Browser initialization completed")
            
            await self.navigate_to_url()
            logger.info("Navigation completed")
            
            # Initialize execution context for block-based flow
            context = ExecutionContext()
            logger.info(f"Starting execution of {len(self.config.actions)} actions")
            
            while context.instruction_pointer < len(self.config.actions):
                logger.info(f"=== Executing action {context.instruction_pointer + 1}/{len(self.config.actions)} ===")
                
                if context.break_flag or context.continue_flag:
                    # Handle loop control
                    if context.break_flag:
                        context.instruction_pointer = self._find_loop_end(context.instruction_pointer)
                        context.break_flag = False
                    elif context.continue_flag:
                        context.instruction_pointer = self._find_loop_start(context.instruction_pointer)
                        context.continue_flag = False
                    context.should_increment = False
                
                action = self.config.actions[context.instruction_pointer]
                logger.info(f"Action type: {action.type.value}, Description: {action.description or 'No description'}")
                
                try:
                    # Handle block control actions
                    if action.type in [ActionType.IF_BEGIN, ActionType.ELIF, ActionType.ELSE, ActionType.IF_END,
                                     ActionType.WHILE_BEGIN, ActionType.WHILE_END, ActionType.BREAK, ActionType.CONTINUE]:
                        await self._handle_block_action(action, context)
                    else:
                        # Regular action execution
                        if self._should_execute_action(context):
                            logger.info(f"Executing regular action: {action.type.value}")
                            output = await self.execute_action(action)
                            logger.info(f"Action completed successfully: {action.type.value}")
                            if output:
                                results["outputs"][f"action_{context.instruction_pointer}"] = output
                                # Store result for conditional blocks
                                if action.type == ActionType.CHECK_ELEMENT:
                                    context.last_check_result = output
                            results["actions_completed"] += 1
                        else:
                            logger.info(f"Action skipped due to execution context: {action.type.value}")
                
                except Exception as e:
                    error_info = {
                        "action_index": context.instruction_pointer,
                        "action_type": action.type.value,
                        "action_description": action.description or "No description",
                        "selector": action.selector,
                        "value": str(action.value) if action.value else None,
                        "timeout": action.timeout,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                    
                    # Add page context if available
                    if self.page:
                        try:
                            error_info["page_url"] = self.page.url
                            error_info["page_title"] = await self.page.title()
                        except:
                            error_info["page_url"] = "Unknown"
                            error_info["page_title"] = "Unknown"
                    
                    results["errors"].append(error_info)
                    logger.error(f"Action {context.instruction_pointer} failed: {error_info}")
                    
                    if not getattr(self, 'continue_on_error', True):
                        break
                
                # Move to next instruction
                if context.should_increment:
                    context.instruction_pointer += 1
                else:
                    context.should_increment = True
                        
            results["success"] = results["actions_completed"] == results["total_actions"]
            
        except Exception as e:
            results["errors"].append({"error": str(e)})
            logger.error(f"Automation failed: {e}")
        
        finally:
            # Keep browser open based on configuration (default: keep open)
            await self.cleanup(close_browser=not self.keep_browser_open)
            
            # Log performance summary if monitoring is available
            if PERFORMANCE_MONITORING_AVAILABLE:
                try:
                    monitor = get_monitor()
                    monitor.log_summary()
                    
                    # Add performance data to results
                    perf_summary = monitor.get_summary()
                    results["performance"] = {
                        "total_execution_time": perf_summary.get("total_execution_time", 0),
                        "average_time_per_action": perf_summary.get("average_time_per_action", 0),
                        "success_rate": perf_summary.get("success_rate", 0)
                    }
                except Exception as e:
                    logger.warning(f"Failed to generate performance summary: {e}")
        
        return results

    async def _execute_block_based(self, context: 'ExecutionContext', results: Dict[str, Any]):
        """Execute actions using block-based control flow"""
        
        while context.instruction_pointer < len(self.config.actions):
            action = self.config.actions[context.instruction_pointer]
            
            try:
                # Log execution trace
                results["execution_trace"].append({
                    "action_index": context.instruction_pointer,
                    "action_type": action.type.value,
                    "description": action.description,
                    "block_stack": [b.type for b in context.block_stack]
                })
                
                # Execute the action
                result = await self._execute_action_with_context(action, context, results)
                
                # Handle control flow based on action type
                if not await self._handle_control_flow(action, result, context, results):
                    break  # Break or return encountered
                    
                # Move to next action unless control flow changed it
                if context.should_increment:
                    context.instruction_pointer += 1
                else:
                    context.should_increment = True  # Reset for next iteration
                    
            except Exception as e:
                await self._handle_execution_error(e, context, results)
                if not context.continue_on_error:
                    break
                context.instruction_pointer += 1

    async def _execute_action_with_context(self, action: Action, context: 'ExecutionContext', 
                                         results: Dict[str, Any]) -> Any:
        """Execute a single action within the execution context"""
        
        # Handle block control actions
        if action.type in [ActionType.IF_BEGIN, ActionType.ELIF, ActionType.ELSE, ActionType.IF_END,
                          ActionType.WHILE_BEGIN, ActionType.WHILE_END, ActionType.BREAK, ActionType.CONTINUE]:
            return await self._execute_control_action(action, context, results)
        
        # Execute regular actions
        result = await self.execute_action(action)
        results["actions_completed"] += 1
        
        # Store outputs
        if action.type in [ActionType.CHECK_QUEUE, ActionType.CHECK_ELEMENT, ActionType.DOWNLOAD_FILE]:
            results["outputs"][f"action_{context.instruction_pointer}"] = result
            
            if action.type == ActionType.CHECK_ELEMENT:
                context.last_check_result = result
                self._last_check_result = result
        
        return result

    async def _execute_control_action(self, action: Action, context: 'ExecutionContext', 
                                    results: Dict[str, Any]) -> Any:
        """Execute control flow actions (IF, WHILE, etc.)"""
        
        if action.type == ActionType.IF_BEGIN:
            return await self._handle_if_begin(action, context)
        elif action.type == ActionType.ELIF:
            return await self._handle_elif(action, context)
        elif action.type == ActionType.ELSE:
            return await self._handle_else(action, context)
        elif action.type == ActionType.IF_END:
            return await self._handle_if_end(action, context)
        elif action.type == ActionType.WHILE_BEGIN:
            return await self._handle_while_begin(action, context)
        elif action.type == ActionType.WHILE_END:
            return await self._handle_while_end(action, context)
        elif action.type == ActionType.BREAK:
            return await self._handle_break(action, context)
        elif action.type == ActionType.CONTINUE:
            return await self._handle_continue(action, context)
        
        return None

    async def _handle_control_flow(self, action: Action, result: Any, context: 'ExecutionContext',
                                 results: Dict[str, Any]) -> bool:
        """Handle control flow after action execution. Returns False if should break execution."""
        
        # Handle legacy conditional actions
        if action.type == ActionType.CONDITIONAL_WAIT and result:
            if result.get("retry"):
                retry_from = result.get("retry_from_action", 0)
                logger.info(f"Conditional wait retry from action {retry_from}")
                context.instruction_pointer = retry_from
                context.should_increment = False
        
        elif action.type == ActionType.SKIP_IF and result:
            if result.get("skip"):
                skip_count = result.get("skip_count", 1)
                logger.info(f"Skipping next {skip_count} actions")
                context.instruction_pointer += skip_count
                context.should_increment = False
        
        # Check for break/continue flags
        if context.break_flag:
            return False
        
        return True

    async def _handle_execution_error(self, error: Exception, context: 'ExecutionContext', 
                                    results: Dict[str, Any]):
        """Handle execution errors with context information"""
        error_info = {
            "action_index": context.instruction_pointer,
            "action_type": self.config.actions[context.instruction_pointer].type.value,
            "error": str(error),
            "block_context": [b.type for b in context.block_stack],
            "instruction_pointer": context.instruction_pointer
        }
        
        results["errors"].append(error_info)
        logger.error(f"Action {context.instruction_pointer} failed: {error}")

    # Control Flow Handlers
    
    async def _handle_if_begin(self, action: Action, context: ExecutionContext):
        """Handle IF block start"""
        condition_config = action.value if isinstance(action.value, dict) else {}
        
        # Evaluate condition using last check result
        condition_result = evaluate_condition(context.last_check_result, condition_config)
        
        # Create and push block
        block = context.push_block("if", context.instruction_pointer)
        block.condition_result = condition_result
        block.end_index = context.find_block_end(self.config.actions, context.instruction_pointer, "if")
        
        logger.info(f"IF condition: {condition_result}")
        
        # If condition is false, skip to ELIF/ELSE/END
        if not condition_result:
            context.instruction_pointer = self._find_next_branch(context.instruction_pointer)
            context.should_increment = False
        
        return {"condition_result": condition_result}

    async def _handle_elif(self, action: Action, context: ExecutionContext):
        """Handle ELIF block"""
        current_block = context.current_block()
        
        if not current_block or current_block.type != "if":
            raise ValueError("ELIF without matching IF")
        
        # If previous IF/ELIF was executed, skip this ELIF
        if current_block.has_executed:
            context.instruction_pointer = self._find_next_branch(context.instruction_pointer)
            context.should_increment = False
            return {"skipped": True}
        
        # Evaluate ELIF condition
        condition_config = action.value if isinstance(action.value, dict) else {}
        condition_result = evaluate_condition(context.last_check_result, condition_config)
        
        logger.info(f"ELIF condition: {condition_result}")
        
        if not condition_result:
            # Skip to next ELIF/ELSE/END
            context.instruction_pointer = self._find_next_branch(context.instruction_pointer)
            context.should_increment = False
        else:
            # Mark block as executed
            current_block.has_executed = True
        
        return {"condition_result": condition_result}

    async def _handle_else(self, action: Action, context: ExecutionContext):
        """Handle ELSE block"""
        current_block = context.current_block()
        
        if not current_block or current_block.type != "if":
            raise ValueError("ELSE without matching IF")
        
        # If any previous IF/ELIF was executed, skip ELSE
        if current_block.has_executed:
            context.instruction_pointer = current_block.end_index
            context.should_increment = False
            return {"skipped": True}
        
        # Mark block as executed (ELSE will run)
        current_block.has_executed = True
        logger.info("ELSE block executing")
        
        return {"executing": True}

    async def _handle_if_end(self, action: Action, context: ExecutionContext):
        """Handle IF block end"""
        block = context.pop_block()
        
        if not block or block.type != "if":
            raise ValueError("IF_END without matching IF")
        
        logger.info(f"IF block completed")
        return {"block_completed": True}

    async def _handle_while_begin(self, action: Action, context: ExecutionContext):
        """Handle WHILE loop start"""
        condition_config = action.value if isinstance(action.value, dict) else {}
        
        # Check if this is a new loop or iteration
        current_block = context.current_block()
        
        if not current_block or current_block.type != "while" or current_block.start_index != context.instruction_pointer:
            # New WHILE loop
            block = context.push_block("while", context.instruction_pointer)
            block.end_index = context.find_block_end(self.config.actions, context.instruction_pointer, "while")
        else:
            # Continuing existing loop
            block = current_block
            block.iteration_count += 1
        
        # Evaluate condition
        condition_result = evaluate_condition(context.last_check_result, condition_config)
        block.condition_result = condition_result
        
        logger.info(f"WHILE condition (iteration {block.iteration_count}): {condition_result}")
        
        # If condition is false, exit loop
        if not condition_result:
            context.pop_block()  # Remove the while block
            context.instruction_pointer = block.end_index
            context.should_increment = False
        
        return {"condition_result": condition_result, "iteration": block.iteration_count}

    async def _handle_while_end(self, action: Action, context: ExecutionContext):
        """Handle WHILE loop end"""
        current_block = context.current_block()
        
        if not current_block or current_block.type != "while":
            raise ValueError("WHILE_END without matching WHILE")
        
        # Jump back to WHILE condition
        context.instruction_pointer = current_block.start_index
        context.should_increment = False
        
        logger.info(f"WHILE loop iteration {current_block.iteration_count} completed, checking condition")
        return {"loop_back": True}

    async def _handle_break(self, action: Action, context: ExecutionContext):
        """Handle BREAK statement"""
        # Find the innermost loop
        loop_block = None
        for block in reversed(context.block_stack):
            if block.type == "while":
                loop_block = block
                break
        
        if not loop_block:
            raise ValueError("BREAK outside of loop")
        
        # Exit the loop
        context.block_stack.remove(loop_block)
        context.instruction_pointer = loop_block.end_index
        context.should_increment = False
        
        logger.info("BREAK: Exiting loop")
        return {"break": True}

    async def _handle_continue(self, action: Action, context: ExecutionContext):
        """Handle CONTINUE statement"""
        # Find the innermost loop
        loop_block = None
        for block in reversed(context.block_stack):
            if block.type == "while":
                loop_block = block
                break
        
        if not loop_block:
            raise ValueError("CONTINUE outside of loop")
        
        # Jump to WHILE_END (which will jump back to condition)
        context.instruction_pointer = loop_block.end_index - 1  # -1 because we'll increment
        
        logger.info("CONTINUE: Jumping to next iteration")
        return {"continue": True}

    def _find_next_branch(self, current_index: int) -> int:
        """Find the next ELIF, ELSE, or IF_END at the same nesting level"""
        depth = 0
        
        for i in range(current_index + 1, len(self.config.actions)):
            action = self.config.actions[i]
            
            if action.type == ActionType.IF_BEGIN:
                depth += 1
            elif action.type == ActionType.IF_END:
                if depth == 0:
                    return i
                depth -= 1
            elif action.type in [ActionType.ELIF, ActionType.ELSE] and depth == 0:
                return i
        
        return len(self.config.actions)  # If nothing found, go to end
    
    async def _handle_block_action(self, action, context):
        """Handle block control actions (IF, WHILE, etc.)"""
        if action.type == ActionType.IF_BEGIN:
            await self._handle_if_begin(action, context)
        elif action.type == ActionType.ELIF:
            await self._handle_elif(action, context)
        elif action.type == ActionType.ELSE:
            await self._handle_else(action, context)
        elif action.type == ActionType.IF_END:
            await self._handle_if_end(action, context)
        elif action.type == ActionType.WHILE_BEGIN:
            await self._handle_while_begin(action, context)
        elif action.type == ActionType.WHILE_END:
            await self._handle_while_end(action, context)
        elif action.type == ActionType.BREAK:
            await self._handle_break(action, context)
        elif action.type == ActionType.CONTINUE:
            await self._handle_continue(action, context)
    
    async def _handle_if_begin(self, action, context):
        """Handle IF_BEGIN action"""
        condition = action.value.get('condition', 'check_passed')
        condition_met = self._evaluate_condition(condition, context)
        
        block_info = BlockInfo(
            block_type='if',
            start_index=context.instruction_pointer,
            condition=condition,
            condition_met=condition_met
        )
        context.block_stack.append(block_info)
        
        if not condition_met:
            # Skip to ELIF, ELSE, or IF_END
            context.instruction_pointer = self._find_next_branch(context.instruction_pointer)
            context.should_increment = False
    
    async def _handle_elif(self, action, context):
        """Handle ELIF action"""
        if not context.block_stack or context.block_stack[-1].block_type != 'if':
            raise ValueError("ELIF without matching IF_BEGIN")
        
        current_block = context.block_stack[-1]
        
        if current_block.condition_met:
            # Previous condition was true, skip to IF_END
            context.instruction_pointer = self._find_if_end(context.instruction_pointer)
            context.should_increment = False
        else:
            # Evaluate this ELIF condition
            condition = action.value.get('condition', 'check_passed')
            condition_met = self._evaluate_condition(condition, context)
            current_block.condition_met = condition_met
            
            if not condition_met:
                # Skip to next ELIF, ELSE, or IF_END
                context.instruction_pointer = self._find_next_branch(context.instruction_pointer)
                context.should_increment = False
    
    async def _handle_else(self, action, context):
        """Handle ELSE action"""
        if not context.block_stack or context.block_stack[-1].block_type != 'if':
            raise ValueError("ELSE without matching IF_BEGIN")
        
        current_block = context.block_stack[-1]
        
        if current_block.condition_met:
            # Previous condition was true, skip to IF_END
            context.instruction_pointer = self._find_if_end(context.instruction_pointer)
            context.should_increment = False
    
    async def _handle_if_end(self, action, context):
        """Handle IF_END action"""
        if not context.block_stack or context.block_stack[-1].block_type != 'if':
            raise ValueError("IF_END without matching IF_BEGIN")
        
        context.block_stack.pop()
    
    async def _handle_while_begin(self, action, context):
        """Handle WHILE_BEGIN action"""
        condition = action.value.get('condition', 'check_passed')
        condition_met = self._evaluate_condition(condition, context)
        
        block_info = BlockInfo(
            block_type='while',
            start_index=context.instruction_pointer,
            condition=condition,
            condition_met=condition_met
        )
        context.block_stack.append(block_info)
        
        if not condition_met:
            # Skip to WHILE_END
            context.instruction_pointer = self._find_while_end(context.instruction_pointer)
            context.should_increment = False
    
    async def _handle_while_end(self, action, context):
        """Handle WHILE_END action"""
        if not context.block_stack or context.block_stack[-1].block_type != 'while':
            raise ValueError("WHILE_END without matching WHILE_BEGIN")
        
        current_block = context.block_stack[-1]
        
        # Re-evaluate condition and loop back if true
        condition_met = self._evaluate_condition(current_block.condition, context)
        
        if condition_met:
            # Jump back to WHILE_BEGIN
            context.instruction_pointer = current_block.start_index
            context.should_increment = False
        else:
            # Exit loop
            context.block_stack.pop()
    
    async def _handle_break(self, action, context):
        """Handle BREAK action"""
        # Find the innermost loop to break from
        for i in range(len(context.block_stack) - 1, -1, -1):
            if context.block_stack[i].block_type == 'while':
                context.break_flag = True
                context.should_increment = False
                return
        
        raise ValueError("BREAK used outside of loop")
    
    async def _handle_continue(self, action, context):
        """Handle CONTINUE action"""
        # Find the innermost loop to continue
        for i in range(len(context.block_stack) - 1, -1, -1):
            if context.block_stack[i].block_type == 'while':
                context.continue_flag = True
                context.should_increment = False
                return
        
        raise ValueError("CONTINUE used outside of loop")
    
    def _should_execute_action(self, context):
        """Determine if the current action should be executed based on block context"""
        # If we're inside any IF blocks, check if all conditions are met
        for block in context.block_stack:
            if block.block_type == 'if' and not block.condition_met:
                return False
        return True
    
    def _evaluate_condition(self, condition, context):
        """Evaluate a condition based on the last check result"""
        if context.last_check_result is None:
            return False
        
        if condition == 'check_passed':
            return context.last_check_result.get('success', False)
        elif condition == 'check_failed':
            return not context.last_check_result.get('success', False)
        elif condition == 'value_equals':
            actual = context.last_check_result.get('actual_value', '')
            expected = context.last_check_result.get('expected_value', '')
            return str(actual) == str(expected)
        elif condition == 'value_not_equals':
            actual = context.last_check_result.get('actual_value', '')
            expected = context.last_check_result.get('expected_value', '')
            return str(actual) != str(expected)
        
        return False
    
    def _find_next_branch(self, start_index):
        """Find the next ELIF, ELSE, or IF_END at the same nesting level"""
        depth = 0
        for i in range(start_index + 1, len(self.config.actions)):
            action = self.config.actions[i]
            
            if action.type == ActionType.IF_BEGIN:
                depth += 1
            elif action.type == ActionType.IF_END:
                if depth == 0:
                    return i
                depth -= 1
            elif action.type in [ActionType.ELIF, ActionType.ELSE] and depth == 0:
                return i
        
        return len(self.config.actions)
    
    def _find_if_end(self, start_index):
        """Find the matching IF_END"""
        depth = 0
        for i in range(start_index + 1, len(self.config.actions)):
            action = self.config.actions[i]
            
            if action.type == ActionType.IF_BEGIN:
                depth += 1
            elif action.type == ActionType.IF_END:
                if depth == 0:
                    return i
                depth -= 1
        
        return len(self.config.actions)
    
    def _find_while_end(self, start_index):
        """Find the matching WHILE_END"""
        depth = 0
        for i in range(start_index + 1, len(self.config.actions)):
            action = self.config.actions[i]
            
            if action.type == ActionType.WHILE_BEGIN:
                depth += 1
            elif action.type == ActionType.WHILE_END:
                if depth == 0:
                    return i
                depth -= 1
        
        return len(self.config.actions)
    
    def _find_loop_end(self, start_index):
        """Find the end of the current loop for BREAK"""
        depth = 0
        for i in range(start_index, len(self.config.actions)):
            action = self.config.actions[i]
            
            if action.type == ActionType.WHILE_BEGIN:
                depth += 1
            elif action.type == ActionType.WHILE_END:
                depth -= 1
                if depth == 0:
                    return i + 1  # Move past the WHILE_END
        
        return len(self.config.actions)
    
    def _find_loop_start(self, start_index):
        """Find the start of the current loop for CONTINUE"""
        depth = 0
        for i in range(start_index, -1, -1):
            action = self.config.actions[i]
            
            if action.type == ActionType.WHILE_END:
                depth += 1
            elif action.type == ActionType.WHILE_BEGIN:
                if depth == 0:
                    return i  # Return to the WHILE_BEGIN
                depth -= 1
        
        return 0  # Fallback to beginning

class AutomationSequenceBuilder:
    """Builder class for creating automation sequences"""
    
    def __init__(self, name: str, url: str, keep_browser_open: bool = True):
        self.config = AutomationConfig(name=name, url=url, actions=[], keep_browser_open=keep_browser_open)
        
    def add_login(self, username: str, password: str, username_selector: str, password_selector: str, submit_selector: str, description: str = None):
        """Add login action with username and password"""
        login_data = {
            "username": username,
            "password": password,
            "username_selector": username_selector,
            "password_selector": password_selector,
            "submit_selector": submit_selector
        }
        self.config.actions.append(Action(
            type=ActionType.LOGIN,
            value=login_data,
            description=description
        ))
        return self
        
    def add_expand_dialog(self, selector: str, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.EXPAND_DIALOG,
            selector=selector,
            description=description
        ))
        return self
        
    def add_input_text(self, selector: str, text: str, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.INPUT_TEXT,
            selector=selector,
            value=text,
            description=description
        ))
        return self
        
    def add_upload_image(self, selector: str, file_path: str, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.UPLOAD_IMAGE,
            selector=selector,
            value=file_path,
            description=description
        ))
        return self
        
    def add_toggle_setting(self, selector: str, enabled: bool, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.TOGGLE_SETTING,
            selector=selector,
            value=enabled,
            description=description
        ))
        return self
        
    def add_click_button(self, selector: str, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.CLICK_BUTTON,
            selector=selector,
            description=description
        ))
        return self
        
    def add_check_queue(self, selector: str, completion_text: str = None, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.CHECK_QUEUE,
            selector=selector,
            value=completion_text,
            description=description
        ))
        return self
        
    def add_check_element(self, selector: str, check_type: str = "equals", expected_value: str = "", 
                         attribute: str = "text", description: str = None):
        """Add element value/attribute check action
        
        Args:
            selector: CSS selector for the element
            check_type: Type of check - "equals", "not_equals", "greater", "less", "contains", "not_zero"
            expected_value: Expected value to check against
            attribute: What to check - "text", "value", or any HTML attribute name
            description: Optional description
        """
        self.config.actions.append(Action(
            type=ActionType.CHECK_ELEMENT,
            selector=selector,
            value={
                "check": check_type,
                "value": expected_value,
                "attribute": attribute
            },
            description=description or f"Check {attribute} {check_type} {expected_value}"
        ))
        return self
        
    def add_conditional_wait(self, condition: str = "check_failed", wait_time: int = 5000,
                            max_retries: int = 3, retry_from_action: int = None, 
                            expected_value: str = None, description: str = None):
        """Add conditional wait and retry action
        
        Args:
            condition: When to retry - "check_failed", "check_passed", "value_equals", "value_not_equals"
            wait_time: How long to wait between retries (ms)
            max_retries: Maximum number of retry attempts
            retry_from_action: Which action index to retry from (None = previous check)
            expected_value: For value_equals/value_not_equals conditions
            description: Optional description
        """
        # If retry_from not specified, calculate it based on current action count
        if retry_from_action is None:
            # Assume we want to retry from the check before this action
            retry_from_action = max(0, len(self.config.actions) - 1)
        
        config = {
            "condition": condition,
            "wait_time": wait_time,
            "max_retries": max_retries,
            "retry_from_action": retry_from_action
        }
        
        if expected_value is not None:
            config["expected_value"] = expected_value
        
        self.config.actions.append(Action(
            type=ActionType.CONDITIONAL_WAIT,
            value=config,
            description=description or f"Wait and retry if {condition} (max {max_retries} times)"
        ))
        return self
    
    def add_skip_if(self, condition: str = "check_failed", skip_count: int = 1,
                   expected_value: str = None, description: str = None):
        """Add conditional skip action
        
        Args:
            condition: When to skip - "check_failed", "check_passed", "value_equals", "value_not_equals"  
            skip_count: Number of following actions to skip
            expected_value: For value_equals/value_not_equals conditions
            description: Optional description
        """
        config = {
            "condition": condition,
            "skip_count": skip_count
        }
        
        if expected_value is not None:
            config["expected_value"] = expected_value
        
        self.config.actions.append(Action(
            type=ActionType.SKIP_IF,
            value=config,
            description=description or f"Skip next {skip_count} actions if {condition}"
        ))
        return self
    
    # Block Control Methods
    def add_if_begin(self, condition: str, description: str = None):
        """Begin IF block - executes next actions only if condition is true
        
        Args:
            condition: Condition type - "check_passed", "check_failed", "value_equals", "value_not_equals"
            description: Optional description
        """
        config = {"condition": condition}
        self.config.actions.append(Action(
            type=ActionType.IF_BEGIN,
            value=config,
            description=description or f"IF ({condition})"
        ))
        return self
    
    def add_elif(self, condition: str, description: str = None):
        """Add ELIF condition to IF block"""
        config = {"condition": condition}
        self.config.actions.append(Action(
            type=ActionType.ELIF,
            value=config,
            description=description or f"ELIF ({condition})"
        ))
        return self
    
    def add_else(self, description: str = None):
        """Add ELSE to IF block"""
        self.config.actions.append(Action(
            type=ActionType.ELSE,
            value={},
            description=description or "ELSE"
        ))
        return self
    
    def add_if_end(self, description: str = None):
        """End IF block"""
        self.config.actions.append(Action(
            type=ActionType.IF_END,
            value={},
            description=description or "END IF"
        ))
        return self
    
    def add_while_begin(self, condition: str, description: str = None):
        """Begin WHILE loop - repeats actions while condition is true
        
        Args:
            condition: Condition type - "check_passed", "check_failed", "value_equals", "value_not_equals"
            description: Optional description
        """
        config = {"condition": condition}
        self.config.actions.append(Action(
            type=ActionType.WHILE_BEGIN,
            value=config,
            description=description or f"WHILE ({condition})"
        ))
        return self
    
    def add_while_end(self, description: str = None):
        """End WHILE loop"""
        self.config.actions.append(Action(
            type=ActionType.WHILE_END,
            value={},
            description=description or "END WHILE"
        ))
        return self
    
    def add_break(self, description: str = None):
        """Break out of current loop"""
        self.config.actions.append(Action(
            type=ActionType.BREAK,
            value={},
            description=description or "BREAK"
        ))
        return self
    
    def add_continue(self, description: str = None):
        """Continue to next iteration of loop"""
        self.config.actions.append(Action(
            type=ActionType.CONTINUE,
            value={},
            description=description or "CONTINUE"
        ))
        return self
        
    def add_download_file(self, selector: str, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.DOWNLOAD_FILE,
            selector=selector,
            description=description
        ))
        return self
        
    def add_refresh_page(self, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.REFRESH_PAGE,
            description=description
        ))
        return self
    
    def set_keep_browser_open(self, keep_open: bool = True):
        """Configure whether to keep browser open after automation completes
        
        Args:
            keep_open: If True (default), browser stays open after automation
        """
        self.config.keep_browser_open = keep_open
        return self
        
    def add_switch_panel(self, selector: str, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.SWITCH_PANEL,
            selector=selector,
            description=description
        ))
        return self
        
    def add_wait(self, milliseconds: int, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.WAIT,
            value=milliseconds,
            description=description
        ))
        return self
        
    def add_wait_for_element(self, selector: str, timeout: int = 30000, description: str = None):
        self.config.actions.append(Action(
            type=ActionType.WAIT_FOR_ELEMENT,
            selector=selector,
            timeout=timeout,
            description=description
        ))
        return self
        
    def set_headless(self, headless: bool):
        self.config.headless = headless
        return self
        
    def set_viewport(self, width: int, height: int):
        self.config.viewport = {"width": width, "height": height}
        return self
        
    def build(self) -> AutomationConfig:
        return self.config
        
    def save_to_file(self, file_path: str):
        """Save configuration to JSON file"""
        config_dict = {
            "name": self.config.name,
            "url": self.config.url,
            "headless": self.config.headless,
            "viewport": self.config.viewport,
            "actions": [
                {
                    "type": action.type.value,
                    "selector": action.selector,
                    "value": action.value,
                    "timeout": action.timeout,
                    "description": action.description
                }
                for action in self.config.actions
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
            
    @classmethod
    def load_from_file(cls, file_path: str) -> AutomationConfig:
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        config = AutomationConfig(
            name=data["name"],
            url=data["url"],
            headless=data.get("headless", True),
            viewport=data.get("viewport"),
            actions=[]
        )
        
        for action_data in data["actions"]:
            config.actions.append(Action(
                type=ActionType(action_data["type"]),
                selector=action_data.get("selector"),
                value=action_data.get("value"),
                timeout=action_data.get("timeout", 30000),
                description=action_data.get("description")
            ))
            
        return config

# Example usage
async def example_automation():
    """Example automation sequence"""
    
    # Build automation sequence
    builder = AutomationSequenceBuilder("Example Task", "https://example.com")
    
    sequence = (builder
        .set_headless(False)  # Show browser for debugging
        .add_wait_for_element("#main-panel", description="Wait for page load")
        .add_expand_dialog("#settings-dialog", description="Open settings")
        .add_toggle_setting("#enable-feature", True, description="Enable feature")
        .add_input_text("#task-name", "My Automation Task", description="Enter task name")
        .add_upload_image("#image-upload", "/path/to/image.jpg", description="Upload image")
        .add_click_button("#start-process", description="Start processing")
        .add_wait(5000, description="Wait for processing to start")
        .add_check_queue(".queue-item", "Completed", description="Check queue status")
        .add_download_file(".download-btn", description="Download result")
        .add_refresh_page(description="Refresh page")
        .add_switch_panel("#panel-2", description="Switch to panel 2")
        .build()
    )
    
    # Run automation
    engine = WebAutomationEngine(sequence)
    results = await engine.run_automation()
    
    print(f"Automation completed: {results['success']}")
    print(f"Actions completed: {results['actions_completed']}/{results['total_actions']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")

if __name__ == "__main__":
    asyncio.run(example_automation())
