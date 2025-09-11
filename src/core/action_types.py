"""Action types and related classes for web automation"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Enumeration of all supported automation action types"""
    
    # Basic Actions
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
    
    # Advanced Actions
    CHECK_ELEMENT = "check_element"
    SET_VARIABLE = "set_variable"
    INCREMENT_VARIABLE = "increment_variable"
    LOG_MESSAGE = "log_message"
    LOGIN = "login"
    
    # Flow Control Actions
    IF_BEGIN = "if_begin"
    ELIF = "elif"
    ELSE = "else"
    IF_END = "if_end"
    WHILE_BEGIN = "while_begin"
    WHILE_END = "while_end"
    BREAK = "break"
    CONTINUE = "continue"
    CONDITIONAL_WAIT = "conditional_wait"
    SKIP_IF = "skip_if"
    STOP_AUTOMATION = "stop_automation"
    
    # Generation Download Actions
    START_GENERATION_DOWNLOADS = "start_generation_downloads"
    STOP_GENERATION_DOWNLOADS = "stop_generation_downloads"
    CHECK_GENERATION_STATUS = "check_generation_status"


@dataclass
class Action:
    """Represents a single automation action"""
    
    type: ActionType
    selector: Optional[str] = None
    value: Optional[Any] = None
    timeout: int = 10000
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate action after initialization"""
        if not isinstance(self.type, ActionType):
            raise ValueError(f"Invalid action type: {self.type}")
        
        # Validate required parameters based on action type
        self._validate_action_parameters()
    
    def _validate_action_parameters(self):
        """Validate that required parameters are present for the action type"""
        # Actions that require a selector
        selector_required_actions = [
            ActionType.EXPAND_DIALOG,
            ActionType.INPUT_TEXT,
            ActionType.UPLOAD_IMAGE,
            ActionType.TOGGLE_SETTING,
            ActionType.CLICK_BUTTON,
            ActionType.CHECK_QUEUE,
            ActionType.DOWNLOAD_FILE,
            ActionType.SWITCH_PANEL,
            ActionType.WAIT_FOR_ELEMENT,
            ActionType.CHECK_ELEMENT,
        ]
        
        # Actions that require a value
        value_required_actions = [
            ActionType.INPUT_TEXT,
            ActionType.UPLOAD_IMAGE,
            ActionType.TOGGLE_SETTING,
            ActionType.CHECK_QUEUE,
            ActionType.WAIT,
            ActionType.SET_VARIABLE,
            ActionType.INCREMENT_VARIABLE,
            ActionType.LOG_MESSAGE,
            ActionType.LOGIN,
            ActionType.CONDITIONAL_WAIT,
            ActionType.SKIP_IF,
            ActionType.STOP_AUTOMATION,
            ActionType.START_GENERATION_DOWNLOADS,
            ActionType.STOP_GENERATION_DOWNLOADS,
            ActionType.CHECK_GENERATION_STATUS,
        ]
        
        # Check selector requirement
        if self.type in selector_required_actions and not self.selector:
            raise ValueError(f"Selector is required for {self.type.value} action")
        
        # Check value requirement
        if self.type in value_required_actions and self.value is None:
            raise ValueError(f"Value is required for {self.type.value} action")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary representation"""
        result = {
            "type": self.type.value,
            "timeout": self.timeout,
        }
        
        if self.selector is not None:
            result["selector"] = self.selector
        
        if self.value is not None:
            result["value"] = self.value
        
        if self.description is not None:
            result["description"] = self.description
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """Create action from dictionary representation"""
        try:
            action_type = ActionType(data["type"])
        except ValueError:
            raise ValueError(f"Unknown action type: {data['type']}")
        
        return cls(
            type=action_type,
            selector=data.get("selector"),
            value=data.get("value"),
            timeout=data.get("timeout", 10000),
            description=data.get("description"),
        )


def get_action_description(action_type: ActionType) -> str:
    """Get human-readable description for an action type"""
    descriptions = {
        ActionType.EXPAND_DIALOG: "Click to expand a dialog or panel",
        ActionType.INPUT_TEXT: "Enter text into an input field",
        ActionType.UPLOAD_IMAGE: "Upload an image file",
        ActionType.TOGGLE_SETTING: "Toggle a checkbox or switch",
        ActionType.CLICK_BUTTON: "Click a button element",
        ActionType.CHECK_QUEUE: "Check queue status for completion",
        ActionType.DOWNLOAD_FILE: "Download a file",
        ActionType.REFRESH_PAGE: "Refresh the current page",
        ActionType.SWITCH_PANEL: "Switch to a different panel or tab",
        ActionType.WAIT: "Wait for specified milliseconds",
        ActionType.WAIT_FOR_ELEMENT: "Wait for an element to appear",
        ActionType.CHECK_ELEMENT: "Validate element content or attributes",
        ActionType.SET_VARIABLE: "Store a value in a variable",
        ActionType.INCREMENT_VARIABLE: "Increment a numeric variable",
        ActionType.LOG_MESSAGE: "Write a message to log file",
        ActionType.LOGIN: "Perform login with credentials",
        ActionType.IF_BEGIN: "Begin conditional block",
        ActionType.ELIF: "Else-if condition branch",
        ActionType.ELSE: "Else condition branch",
        ActionType.IF_END: "End conditional block",
        ActionType.WHILE_BEGIN: "Begin loop block",
        ActionType.WHILE_END: "End loop block",
        ActionType.BREAK: "Break out of loop",
        ActionType.CONTINUE: "Continue to next loop iteration",
        ActionType.CONDITIONAL_WAIT: "Wait and retry based on condition",
        ActionType.SKIP_IF: "Skip actions based on condition",
        ActionType.STOP_AUTOMATION: "Stop automation execution",
        ActionType.START_GENERATION_DOWNLOADS: "Begin generation downloads",
        ActionType.STOP_GENERATION_DOWNLOADS: "Stop generation downloads",
        ActionType.CHECK_GENERATION_STATUS: "Check generation download status",
    }
    
    return descriptions.get(action_type, f"Unknown action: {action_type.value}")


def get_required_parameters(action_type: ActionType) -> Dict[str, str]:
    """Get required parameters for an action type"""
    required_params = {}
    
    # Actions that require a selector
    if action_type in [
        ActionType.EXPAND_DIALOG,
        ActionType.INPUT_TEXT,
        ActionType.UPLOAD_IMAGE,
        ActionType.TOGGLE_SETTING,
        ActionType.CLICK_BUTTON,
        ActionType.CHECK_QUEUE,
        ActionType.DOWNLOAD_FILE,
        ActionType.SWITCH_PANEL,
        ActionType.WAIT_FOR_ELEMENT,
        ActionType.CHECK_ELEMENT,
    ]:
        required_params["selector"] = "CSS selector for target element"
    
    # Actions that require a value
    if action_type in [
        ActionType.INPUT_TEXT,
        ActionType.UPLOAD_IMAGE,
        ActionType.TOGGLE_SETTING,
        ActionType.CHECK_QUEUE,
        ActionType.WAIT,
        ActionType.SET_VARIABLE,
        ActionType.INCREMENT_VARIABLE,
        ActionType.LOG_MESSAGE,
        ActionType.LOGIN,
        ActionType.CONDITIONAL_WAIT,
        ActionType.SKIP_IF,
        ActionType.STOP_AUTOMATION,
        ActionType.START_GENERATION_DOWNLOADS,
        ActionType.STOP_GENERATION_DOWNLOADS,
        ActionType.CHECK_GENERATION_STATUS,
    ]:
        required_params["value"] = "Value for the action (specific to action type)"
    
    return required_params


@dataclass
class AutomationConfig:
    """Configuration for an automation sequence"""
    
    name: str
    url: str
    actions: List[Action] = field(default_factory=list)
    headless: bool = True
    viewport: Optional[Dict[str, int]] = None
    keep_browser_open: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.name:
            raise ValueError("Automation name cannot be empty")
        
        if not self.url:
            raise ValueError("Automation URL cannot be empty")
        
        # Validate actions
        for i, action in enumerate(self.actions):
            if not isinstance(action, Action):
                raise ValueError(f"Invalid action at index {i}: {action}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary representation"""
        result = {
            "name": self.name,
            "url": self.url,
            "headless": self.headless,
            "actions": [action.to_dict() for action in self.actions],
        }
        
        if self.viewport is not None:
            result["viewport"] = self.viewport
        
        if self.keep_browser_open is not True:
            result["keep_browser_open"] = self.keep_browser_open
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationConfig':
        """Create configuration from dictionary representation"""
        actions = []
        for action_data in data.get("actions", []):
            actions.append(Action.from_dict(action_data))
        
        return cls(
            name=data["name"],
            url=data["url"],
            actions=actions,
            headless=data.get("headless", True),
            viewport=data.get("viewport"),
            keep_browser_open=data.get("keep_browser_open", True),
        )