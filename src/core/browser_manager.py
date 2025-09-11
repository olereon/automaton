"""Browser management for web automation"""

import asyncio
import logging
import os
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Configuration for browser settings"""
    headless: bool = True
    viewport: Optional[Dict[str, int]] = None
    user_agent: Optional[str] = None
    timeout: int = 30000
    keep_browser_open: bool = False
    browser_path: Optional[str] = None
    
    def __post_init__(self):
        """Validate browser config after initialization"""
        if self.viewport is None:
            self.viewport = {"width": 1280, "height": 720}
        
        if not isinstance(self.viewport, dict) or "width" not in self.viewport or "height" not in self.viewport:
            raise ValueError("Viewport must be a dictionary with 'width' and 'height' keys")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")


class BrowserManager:
    """Manages browser lifecycle and operations"""
    
    def __init__(self, config: BrowserConfig):
        """Initialize browser manager with configuration"""
        self.config = config
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize browser and context"""
        try:
            logger.info("Initializing browser manager")
            
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser with appropriate options
            browser_options = {
                "headless": self.config.headless,
            }
            
            if self.config.browser_path:
                browser_options["executable_path"] = self.config.browser_path
            
            self.browser = await self.playwright.chromium.launch(**browser_options)
            
            # Create browser context
            context_options = {
                "viewport": self.config.viewport,
            }
            
            if self.config.user_agent:
                context_options["user_agent"] = self.config.user_agent
            
            self.context = await self.browser.new_context(**context_options)
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(self.config.timeout)
            
            self._is_initialized = True
            logger.info("Browser manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser manager: {str(e)}")
            await self.close()
            return False
    
    async def close(self):
        """Close browser and cleanup resources"""
        try:
            if self.page and not self.config.keep_browser_open:
                await self.page.close()
                self.page = None
            
            if self.context and not self.config.keep_browser_open:
                await self.context.close()
                self.context = None
            
            if self.browser and not self.config.keep_browser_open:
                await self.browser.close()
                self.browser = None
            
            if self.playwright and not self.config.keep_browser_open:
                await self.playwright.stop()
                self.playwright = None
            
            self._is_initialized = False
            logger.info("Browser manager closed")
            
        except Exception as e:
            logger.error(f"Error closing browser manager: {str(e)}")
    
    async def cleanup(self, close_browser: bool = True):
        """Cleanup browser resources - alias for close method"""
        try:
            if close_browser:
                await self.close()
            else:
                # Just reset the initialization state but keep browser open
                self._is_initialized = False
                logger.info("Browser manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during browser manager cleanup: {str(e)}")
    
    def is_initialized(self) -> bool:
        """Check if browser manager is initialized"""
        return self._is_initialized and all([
            self.playwright is not None,
            self.browser is not None,
            self.context is not None,
            self.page is not None
        ])
    
    async def navigate_to(self, url: str) -> bool:
        """Navigate to a specific URL"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return False
        
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, timeout=self.config.timeout)
            logger.info("Navigation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {str(e)}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Wait for an element to be visible on the page"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return False
        
        try:
            wait_timeout = timeout or self.config.timeout
            logger.debug(f"Waiting for element: {selector} (timeout: {wait_timeout}ms)")
            
            await self.page.wait_for_selector(selector, timeout=wait_timeout)
            logger.debug(f"Element found: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"Element not found: {selector} - {str(e)}")
            return False
    
    async def get_page_content(self) -> str:
        """Get the current page content as HTML"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return ""
        
        try:
            return await self.page.content()
            
        except Exception as e:
            logger.error(f"Failed to get page content: {str(e)}")
            return ""
    
    async def take_screenshot(self, path: str) -> bool:
        """Take a screenshot of the current page"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return False
        
        try:
            await self.page.screenshot(path=path)
            logger.info(f"Screenshot saved to: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return False
    
    async def evaluate_script(self, script: str) -> Any:
        """Evaluate JavaScript on the page"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return None
        
        try:
            return await self.page.evaluate(script)
            
        except Exception as e:
            logger.error(f"Failed to evaluate script: {str(e)}")
            return None
    
    async def get_element_text(self, selector: str) -> Optional[str]:
        """Get text content of an element"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return None
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get element text: {str(e)}")
            return None
    
    async def get_element_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get attribute value of an element"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return None
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get element attribute: {str(e)}")
            return None
    
    async def is_element_visible(self, selector: str) -> bool:
        """Check if an element is visible on the page"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return False
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.is_visible()
            return False
            
        except Exception as e:
            logger.error(f"Failed to check element visibility: {str(e)}")
            return False
    
    async def get_page_url(self) -> str:
        """Get the current page URL"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return ""
        
        try:
            return self.page.url
            
        except Exception as e:
            logger.error(f"Failed to get page URL: {str(e)}")
            return ""
    
    async def wait_for_navigation(self, timeout: Optional[int] = None) -> bool:
        """Wait for page navigation to complete"""
        if not self.is_initialized():
            logger.error("Browser manager not initialized")
            return False
        
        try:
            wait_timeout = timeout or self.config.timeout
            await self.page.wait_for_load_state("networkidle", timeout=wait_timeout)
            return True
            
        except Exception as e:
            logger.error(f"Failed to wait for navigation: {str(e)}")
            return False
    
    @classmethod
    def create_from_env(cls) -> 'BrowserManager':
        """Create browser manager from environment variables"""
        config = BrowserConfig(
            headless=os.getenv("AUTOMATON_HEADLESS", "true").lower() == "true",
            browser_path=os.getenv("AUTOMATON_BROWSER_PATH"),
            user_agent=os.getenv("AUTOMATON_USER_AGENT"),
            timeout=int(os.getenv("AUTOMATON_TIMEOUT", "30000")),
            keep_browser_open=os.getenv("AUTOMATON_KEEP_BROWSER_OPEN", "false").lower() == "true",
        )
        
        return cls(config)