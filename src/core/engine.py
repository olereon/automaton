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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Enumeration of supported action types"""
    EXPAND_DIALOG = "expand_dialog"
    INPUT_TEXT = "input_text"
    UPLOAD_IMAGE = "upload_image"
    TOGGLE_SETTING = "toggle_setting"
    CLICK_BUTTON = "click_button"
    CHECK_QUEUE = "check_queue"
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
    timeout: int = 30000  # milliseconds
    description: Optional[str] = None

@dataclass
class AutomationConfig:
    """Configuration for automation sequence"""
    name: str
    url: str
    actions: List[Action]
    headless: bool = True
    viewport: Dict[str, int] = None
    
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
        
    async def initialize(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport=self.config.viewport,
            accept_downloads=True
        )
        self.page = await self.context.new_page()
        
    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
            
    async def navigate_to_url(self):
        """Navigate to the target URL"""
        logger.info(f"Navigating to {self.config.url}")
        await self.page.goto(self.config.url, wait_until="networkidle")
        
    async def execute_action(self, action: Action) -> Any:
        """Execute a single action"""
        logger.info(f"Executing action: {action.type.value} - {action.description or ''}")
        
        try:
            if action.type == ActionType.EXPAND_DIALOG:
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
                await self.page.click(action.selector, timeout=action.timeout)
                
            elif action.type == ActionType.CHECK_QUEUE:
                # Check queue status and return completion status
                queue_items = await self.page.query_selector_all(action.selector)
                completed = []
                for item in queue_items:
                    text = await item.text_content()
                    if action.value and action.value in text:
                        completed.append(text)
                return completed
                
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
                await self.page.wait_for_selector(action.selector, timeout=action.timeout)
                
        except Exception as e:
            logger.error(f"Error executing action {action.type.value}: {str(e)}")
            raise
            
    async def run_automation(self) -> Dict[str, Any]:
        """Run the complete automation sequence"""
        results = {
            "success": False,
            "actions_completed": 0,
            "total_actions": len(self.config.actions),
            "errors": [],
            "outputs": {}
        }
        
        try:
            await self.initialize()
            await self.navigate_to_url()
            
            for i, action in enumerate(self.config.actions):
                try:
                    result = await self.execute_action(action)
                    results["actions_completed"] += 1
                    
                    # Store outputs from certain actions
                    if action.type in [ActionType.CHECK_QUEUE, ActionType.DOWNLOAD_FILE]:
                        results["outputs"][f"action_{i}"] = result
                        
                except Exception as e:
                    results["errors"].append({
                        "action_index": i,
                        "action_type": action.type.value,
                        "error": str(e)
                    })
                    if not getattr(self, 'continue_on_error', True):
                        break
                        
            results["success"] = results["actions_completed"] == results["total_actions"]
            
        except Exception as e:
            results["errors"].append({"error": str(e)})
            
        finally:
            await self.cleanup()
            
        return results

class AutomationSequenceBuilder:
    """Builder class for creating automation sequences"""
    
    def __init__(self, name: str, url: str):
        self.config = AutomationConfig(name=name, url=url, actions=[])
        
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
