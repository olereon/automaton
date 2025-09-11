# Action Types Module

## Overview

The `action_types.py` module defines the core action types and related classes for web automation in Automaton. It provides the fundamental building blocks for creating automation sequences, including action definitions, validation, and configuration management.

## Core Classes

### ActionType Enum

The `ActionType` enumeration defines all supported automation action types, categorized into three main groups:

#### Basic Actions
- `EXPAND_DIALOG` - Click to expand a dialog or panel
- `INPUT_TEXT` - Enter text into an input field
- `UPLOAD_IMAGE` - Upload an image file
- `TOGGLE_SETTING` - Toggle a checkbox or switch
- `CLICK_BUTTON` - Click a button element
- `CHECK_QUEUE` - Check queue status for completion
- `DOWNLOAD_FILE` - Download a file
- `REFRESH_PAGE` - Refresh the current page
- `SWITCH_PANEL` - Switch to a different panel or tab
- `WAIT` - Wait for specified milliseconds
- `WAIT_FOR_ELEMENT` - Wait for an element to appear

#### Advanced Actions
- `CHECK_ELEMENT` - Validate element content or attributes
- `SET_VARIABLE` - Store a value in a variable
- `INCREMENT_VARIABLE` - Increment a numeric variable
- `LOG_MESSAGE` - Write a message to log file
- `LOGIN` - Perform login with credentials

#### Flow Control Actions
- `IF_BEGIN` - Begin conditional block
- `ELIF` - Else-if condition branch
- `ELSE` - Else condition branch
- `IF_END` - End conditional block
- `WHILE_BEGIN` - Begin loop block
- `WHILE_END` - End loop block
- `BREAK` - Break out of loop
- `CONTINUE` - Continue to next loop iteration
- `CONDITIONAL_WAIT` - Wait and retry based on condition
- `SKIP_IF` - Skip actions based on condition
- `STOP_AUTOMATION` - Stop automation execution

#### Generation Download Actions
- `START_GENERATION_DOWNLOADS` - Begin generation downloads
- `STOP_GENERATION_DOWNLOADS` - Stop generation downloads
- `CHECK_GENERATION_STATUS` - Check generation download status

### Action Class

The `Action` class represents a single automation action with the following properties:

#### Properties
- `type` (ActionType): The type of action
- `selector` (Optional[str]): CSS selector for target element
- `value` (Optional[Any]): Value for the action (specific to action type)
- `timeout` (int): Timeout in milliseconds (default: 10000)
- `description` (Optional[str]): Human-readable description

#### Methods
- `to_dict()`: Convert action to dictionary representation
- `from_dict(data)`: Create action from dictionary representation

#### Validation
The `Action` class automatically validates required parameters based on the action type:
- Some actions require a `selector` parameter
- Some actions require a `value` parameter

### AutomationConfig Class

The `AutomationConfig` class represents configuration for an automation sequence:

#### Properties
- `name` (str): Name of the automation
- `url` (str): Starting URL for the automation
- `actions` (List[Action]): List of actions to execute
- `headless` (bool): Run browser in headless mode (default: True)
- `viewport` (Optional[Dict[str, int]]): Browser viewport dimensions
- `keep_browser_open` (bool): Keep browser open after completion (default: True)

#### Methods
- `to_dict()`: Convert configuration to dictionary representation
- `from_dict(data)`: Create configuration from dictionary representation

## Utility Functions

### get_action_description(action_type: ActionType) -> str

Returns a human-readable description for an action type.

```python
from src.core.action_types import ActionType, get_action_description

description = get_action_description(ActionType.CLICK_BUTTON)
# Returns: "Click a button element"
```

### get_required_parameters(action_type: ActionType) -> Dict[str, str]

Returns a dictionary of required parameters for an action type, with parameter names as keys and descriptions as values.

```python
from src.core.action_types import ActionType, get_required_parameters

params = get_required_parameters(ActionType.INPUT_TEXT)
# Returns: {"selector": "CSS selector for target element", 
#           "value": "Value for the action (specific to action type)"}
```

## Usage Examples

### Creating a Simple Action

```python
from src.core.action_types import Action, ActionType

# Create a click action
click_action = Action(
    type=ActionType.CLICK_BUTTON,
    selector="#submit-button",
    description="Click the submit button"
)

# Convert to dictionary
action_dict = click_action.to_dict()
```

### Creating an Automation Configuration

```python
from src.core.action_types import Action, ActionType, AutomationConfig

# Create a sequence of actions
actions = [
    Action(
        type=ActionType.NAVIGATE_TO,
        value="https://example.com"
    ),
    Action(
        type=ActionType.INPUT_TEXT,
        selector="#username",
        value="testuser"
    ),
    Action(
        type=ActionType.INPUT_TEXT,
        selector="#password",
        value="testpass"
    ),
    Action(
        type=ActionType.CLICK_BUTTON,
        selector="#login-button"
    )
]

# Create automation configuration
config = AutomationConfig(
    name="Login Automation",
    url="https://example.com",
    actions=actions
)

# Convert to dictionary
config_dict = config.to_dict()
```

### Working with Variables

```python
from src.core.action_types import Action, ActionType

# Set a variable
set_var_action = Action(
    type=ActionType.SET_VARIABLE,
    value={"name": "counter", "value": 0}
)

# Increment the variable
increment_action = Action(
    type=ActionType.INCREMENT_VARIABLE,
    value={"name": "counter", "amount": 1}
)

# Use the variable in a conditional
conditional_action = Action(
    type=ActionType.IF_BEGIN,
    value="${counter} > 5"
)
```

## Error Handling

The module includes validation for actions and configurations:

- Invalid action types raise `ValueError`
- Missing required parameters raise `ValueError`
- Empty automation names or URLs raise `ValueError`

## Integration with Other Modules

The `action_types.py` module is used by:
- `execution_context.py` - For executing actions and managing variables
- `engine.py` - For processing automation sequences
- `controller.py` - For managing automation state