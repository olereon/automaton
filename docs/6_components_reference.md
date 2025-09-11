# Automaton Components Reference

## Introduction

This document provides detailed information about the core components that make up the Automaton framework. Understanding these components is essential for advanced usage, customization, and extending the framework.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Action System](#action-system)
4. [Controller System](#controller-system)
5. [Browser Management](#browser-management)
6. [Variable System](#variable-system)
7. [Error Handling](#error-handling)
8. [Logging System](#logging-system)
9. [Configuration System](#configuration-system)
10. [Extending Components](#extending-components)

## Architecture Overview

Automaton follows a modular architecture with clear separation of concerns. The system is composed of several key components that work together to provide web automation capabilities.

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                    │
├─────────────────────────────────────────────────────────┤
│  CLI  │   GUI   │   API   │   Custom Integrations     │
├─────────────────────────────────────────────────────────┤
│                    Controller Layer                     │
├─────────────────────────────────────────────────────────┤
│  Action Executor  │  Variable Manager  │  Error Handler │
├─────────────────────────────────────────────────────────┤
│                    Browser Layer                        │
├─────────────────────────────────────────────────────────┤
│  Playwright  │  Browser Context  │  Page Management   │
├─────────────────────────────────────────────────────────┤
│                    System Layer                         │
├─────────────────────────────────────────────────────────┤
│  Configuration  │  Logging  │  File Management      │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### AutomationEngine

The `AutomationEngine` is the central component responsible for executing automation sequences. It coordinates all other components and manages the overall execution flow.

**Key Responsibilities**:
- Parsing and validating automation configurations
- Coordinating action execution
- Managing browser lifecycle
- Handling errors and exceptions
- Providing execution status and results

**Key Methods**:
```python
async def execute(self, config: AutomationConfig) -> ExecutionResult:
    """Execute an automation configuration"""
    
async def stop(self) -> None:
    """Stop the current automation execution"""
    
def get_status(self) -> ExecutionStatus:
    """Get the current execution status"""
```

### ActionExecutor

The `ActionExecutor` component is responsible for executing individual actions within an automation sequence. It maintains a registry of all available action types and their implementations.

**Key Responsibilities**:
- Maintaining action type registry
- Executing individual actions
- Providing action execution results
- Handling action-specific errors

**Key Methods**:
```python
async def execute_action(self, action: Action) -> ActionResult:
    """Execute a single action"""
    
def register_action(self, action_type: str, handler: ActionHandler):
    """Register a new action type handler"""
    
def get_available_actions(self) -> List[str]:
    """Get list of available action types"""
```

### VariableManager

The `VariableManager` component handles variable storage, retrieval, and manipulation throughout the automation execution.

**Key Responsibilities**:
- Storing and retrieving variables
- Handling variable substitution
- Managing variable scope and lifecycle
- Providing variable manipulation functions

**Key Methods**:
```python
def set_variable(self, name: str, value: Any) -> None:
    """Set a variable value"""
    
def get_variable(self, name: str) -> Any:
    """Get a variable value"""
    
def substitute_variables(self, text: str) -> str:
    """Substitute variable placeholders in text"""
    
def increment_variable(self, name: str, increment: Number = 1) -> None:
    """Increment a numeric variable"""
```

## Action System

### Action Base Class

All actions inherit from the `Action` base class, which provides common functionality and enforces a consistent interface.

```python
class Action:
    def __init__(self, action_type: str, selector: str = None, value: Any = None):
        self.type = action_type
        self.selector = selector
        self.value = value
        
    async def execute(self, context: ExecutionContext) -> ActionResult:
        """Execute the action"""
        raise NotImplementedError
        
    def validate(self) -> List[str]:
        """Validate the action configuration"""
        return []
```

### ActionHandler Interface

Action handlers implement the `ActionHandler` interface, which defines how specific action types are executed.

```python
class ActionHandler(ABC):
    @abstractmethod
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        """Execute the action"""
        pass
        
    @abstractmethod
    def validate(self, action: Action) -> List[str]:
        """Validate the action configuration"""
        pass
```

### Built-in Action Handlers

Automaton includes built-in handlers for common action types:

#### InputTextHandler

Handles text input to form fields:

```python
class InputTextHandler(ActionHandler):
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        page = context.page
        await page.fill(action.selector, action.value)
        return ActionResult(success=True)
        
    def validate(self, action: Action) -> List[str]:
        errors = []
        if not action.selector:
            errors.append("Selector is required for input_text action")
        if action.value is None:
            errors.append("Value is required for input_text action")
        return errors
```

#### ClickButtonHandler

Handles button clicks:

```python
class ClickButtonHandler(ActionHandler):
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        page = context.page
        await page.click(action.selector)
        return ActionResult(success=True)
        
    def validate(self, action: Action) -> List[str]:
        errors = []
        if not action.selector:
            errors.append("Selector is required for click_button action")
        return errors
```

## Controller System

### Controller

The `Controller` component manages the execution lifecycle of automations, including start, stop, and pause functionality.

**Key Responsibilities**:
- Managing execution state
- Handling start/stop signals
- Coordinating with other components
- Providing execution status updates

**Key Methods**:
```python
async def start_automation(self, config: AutomationConfig) -> None:
    """Start automation execution"""
    
async def stop_automation(self, reason: str = None) -> None:
    """Stop automation execution"""
    
def get_execution_state(self) -> ExecutionState:
    """Get current execution state"""
```

### ControlSignal

Control signals are used to communicate between components and manage execution flow:

```python
class ControlSignal(Enum):
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
```

### ExecutionState

The `ExecutionState` class tracks the current state of automation execution:

```python
class ExecutionState:
    def __init__(self):
        self.status = ExecutionStatus.IDLE
        self.current_action_index = 0
        self.variables = {}
        self.start_time = None
        self.end_time = None
        self.error = None
```

## Browser Management

### BrowserManager

The `BrowserManager` component handles browser lifecycle and context management.

**Key Responsibilities**:
- Creating and managing browser instances
- Handling browser contexts and pages
- Managing browser configuration
- Cleaning up browser resources

**Key Methods**:
```python
async def create_browser(self, config: BrowserConfig) -> Browser:
    """Create a new browser instance"""
    
async def create_context(self, browser: Browser) -> BrowserContext:
    """Create a new browser context"""
    
async def create_page(self, context: BrowserContext) -> Page:
    """Create a new page"""
    
async def close_browser(self, browser: Browser) -> None:
    """Close a browser instance"""
```

### BrowserContext

The `BrowserContext` class wraps Playwright's browser context and provides additional functionality:

```python
class BrowserContext:
    def __init__(self, playwright_context: PlaywrightContext):
        self.context = playwright_context
        self.pages = []
        
    async def new_page(self) -> Page:
        """Create a new page in this context"""
        
    async def close(self) -> None:
        """Close this context and all pages"""
```

### PageManager

The `PageManager` component handles page-level operations and interactions:

```python
class PageManager:
    def __init__(self, page: Page):
        self.page = page
        
    async def navigate(self, url: str) -> None:
        """Navigate to a URL"""
        
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> ElementHandle:
        """Wait for an element to be available"""
        
    async def execute_action(self, action: Action) -> ActionResult:
        """Execute an action on this page"""
```

## Variable System

### VariableStore

The `VariableStore` class manages variable storage and retrieval:

```python
class VariableStore:
    def __init__(self):
        self.variables = {}
        self.scopes = [{}]  # Stack of variable scopes
        
    def set_variable(self, name: str, value: Any, scope: str = "global") -> None:
        """Set a variable value"""
        
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable value"""
        
    def push_scope(self) -> None:
        """Push a new variable scope"""
        
    def pop_scope(self) -> None:
        """Pop the current variable scope"""
```

### VariableSubstitutor

The `VariableSubstitutor` class handles variable substitution in text:

```python
class VariableSubstitutor:
    def __init__(self, variable_store: VariableStore):
        self.variable_store = variable_store
        self.pattern = re.compile(r'\$\{([^}]+)\}')
        
    def substitute(self, text: str) -> str:
        """Substitute variable placeholders in text"""
        
    def get_referenced_variables(self, text: str) -> List[str]:
        """Get list of variables referenced in text"""
```

## Error Handling

### ErrorHandler

The `ErrorHandler` component manages error detection, reporting, and recovery:

```python
class ErrorHandler:
    def __init__(self):
        self.error_handlers = {}
        
    def register_handler(self, error_type: Type[Exception], handler: Errorhandler):
        """Register an error handler"""
        
    async def handle_error(self, error: Exception, context: ExecutionContext) -> ErrorResult:
        """Handle an error"""
        
    def should_continue(self, error: Exception) -> bool:
        """Determine if execution should continue after an error"""
```

### Error Types

Automaton defines several error types for different failure scenarios:

```python
class AutomatonError(Exception):
    """Base class for all Automaton errors"""
    
class ElementNotFoundError(AutomatonError):
    """Raised when an element is not found"""
    
class TimeoutError(AutomatonError):
    """Raised when an operation times out"""
    
class ValidationError(AutomatonError):
    """Raised when validation fails"""
```

### Error Recovery

Error recovery is handled through recovery strategies:

```python
class RecoveryStrategy(ABC):
    @abstractmethod
    async def recover(self, error: Exception, context: ExecutionContext) -> bool:
        """Attempt to recover from an error"""
        pass

class RetryStrategy(RecoveryStrategy):
    def __init__(self, max_attempts: int = 3, delay: float = 1.0):
        self.max_attempts = max_attempts
        self.delay = delay
        
    async def recover(self, error: Exception, context: ExecutionContext) -> bool:
        # Retry logic here
        pass
```

## Logging System

### Logger

The `Logger` component provides structured logging throughout the framework:

```python
class Logger:
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.level = level
        self.handlers = []
        
    def add_handler(self, handler: LogHandler) -> None:
        """Add a log handler"""
        
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message"""
        
    def info(self, message: str, **kwargs) -> None:
        """Log an info message"""
        
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message"""
        
    def error(self, message: str, **kwargs) -> None:
        """Log an error message"""
```

### Log Handlers

Log handlers determine where log messages are sent:

```python
class LogHandler(ABC):
    @abstractmethod
    def emit(self, record: LogRecord) -> None:
        """Emit a log record"""
        pass

class ConsoleHandler(LogHandler):
    def emit(self, record: LogRecord) -> None:
        print(f"{record.timestamp} - {record.level} - {record.message}")
        
class FileHandler(LogHandler):
    def __init__(self, filename: str):
        self.filename = filename
        
    def emit(self, record: LogRecord) -> None:
        with open(self.filename, 'a') as f:
            f.write(f"{record.timestamp} - {record.level} - {record.message}\n")
```

## Configuration System

### ConfigManager

The `ConfigManager` component handles loading, validating, and managing configuration:

```python
class ConfigManager:
    def __init__(self):
        self.config_sources = []
        self.config_cache = {}
        
    def add_source(self, source: ConfigSource) -> None:
        """Add a configuration source"""
        
    def load_config(self, config_type: Type[Config]) -> Config:
        """Load configuration of a specific type"""
        
    def validate_config(self, config: Config) -> List[str]:
        """Validate a configuration object"""
```

### Configuration Sources

Configuration can be loaded from various sources:

```python
class ConfigSource(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load configuration data"""
        pass

class FileConfigSource(ConfigSource):
    def __init__(self, filename: str):
        self.filename = filename
        
    def load(self) -> Dict[str, Any]:
        with open(self.filename, 'r') as f:
            return json.load(f)
            
class EnvConfigSource(ConfigSource):
    def load(self) -> Dict[str, Any]:
        return {key: value for key, value in os.environ.items() 
                if key.startswith('AUTOMATON_')}
```

## Extending Components

### Custom Actions

To create a custom action, implement the `ActionHandler` interface:

```python
class CustomActionHandler(ActionHandler):
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        # Custom action logic here
        return ActionResult(success=True)
        
    def validate(self, action: Action) -> List[str]:
        # Validation logic here
        return []

# Register the custom action
action_executor.register_action("custom_action", CustomActionHandler())
```

### Custom Error Handlers

To create a custom error handler:

```python
class CustomErrorHandler(ErrorHandler):
    async def handle_error(self, error: Exception, context: ExecutionContext) -> ErrorResult:
        # Custom error handling logic here
        return ErrorResult(should_continue=False, message="Custom error handling")

# Register the custom error handler
error_handler.register_handler(CustomException, CustomErrorHandler())
```

### Custom Log Handlers

To create a custom log handler:

```python
class CustomLogHandler(LogHandler):
    def emit(self, record: LogRecord) -> None:
        # Custom log handling logic here
        pass

# Add the custom log handler
logger.add_handler(CustomLogHandler())
```

## Next Steps

With this understanding of Automaton's components, you can:

1. [Explore Advanced Usage](7_advanced_usage.md) for complex scenarios
2. [Learn Troubleshooting Techniques](8_troubleshooting_guide.md) for common issues
3. [Check Contributing Guidelines](9_contributing_guide.md) for development information
4. [Review Deployment Options](10_deployment_guide.md) for production environments

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*