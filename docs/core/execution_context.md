# Execution Context Module

## Overview

The `execution_context.py` module provides classes for managing execution context and control flow information in Automaton. It handles variables, control blocks (IF, WHILE), error tracking, and instruction pointer management during automation execution.

## Core Classes

### BlockType Enum

The `BlockType` enumeration defines types of control blocks supported in automation:

- `IF` - Conditional (if/elif/else) blocks
- `WHILE` - Loop blocks

### BlockInfo Class

The `BlockInfo` class stores information about a control block (IF, WHILE, etc.):

#### Properties
- `block_type` (BlockType): Type of control block
- `start_index` (int): Starting index of the block in the action sequence
- `end_index` (int): Ending index of the block in the action sequence (default: -1)
- `condition` (Optional[str]): Condition expression for the block
- `condition_met` (bool): Whether the condition was met (default: False)
- `has_executed` (bool): Whether the block has executed (default: False)
- `iteration_count` (int): Number of iterations (for loops) (default: 0)

#### Methods
- `reset()`: Reset block state for new execution
- `to_dict()`: Convert block info to dictionary representation

### ExecutionContext Class

The `ExecutionContext` class manages context for automation execution including variables and control flow:

#### Properties

##### Execution State
- `instruction_pointer` (int): Current position in the action sequence (default: 0)
- `should_increment` (bool): Whether to increment the instruction pointer (default: True)
- `last_check_result` (Optional[Dict[str, Any]]): Result of the last condition check
- `continue_on_error` (bool): Whether to continue execution on errors (default: False)

##### Control Flags
- `break_flag` (bool): Whether to break out of current loop (default: False)
- `continue_flag` (bool): Whether to continue to next loop iteration (default: False)

##### Variables and Data
- `variables` (Dict[str, Any]): Storage for runtime variables
- `block_stack` (List[BlockInfo]): Stack of active control blocks
- `outputs` (Dict[str, Any]): Output values from execution
- `errors` (List[str]): Error messages encountered during execution

#### Methods

##### Context Management
- `reset()`: Reset execution context for new run
- `to_dict()`: Convert execution context to dictionary representation
- `from_dict(data)`: Create execution context from dictionary representation

##### Variable Management
- `set_variable(name, value)`: Set a variable in the execution context
- `get_variable(name, default)`: Get a variable from the execution context
- `increment_variable(name, amount)`: Increment a numeric variable
- `substitute_variables(text)`: Substitute variables in text using ${variable} syntax

##### Control Flow Management
- `push_block(block_type, start_index, condition)`: Push a new control block onto the stack
- `pop_block()`: Pop the top control block from the stack
- `current_block()`: Get the current (top) control block
- `find_block_end(actions, start_index, block_type)`: Find the end index of a control block

##### Output and Error Handling
- `add_output(key, value)`: Add an output value to the execution context
- `add_error(error)`: Add an error to the execution context

## Usage Examples

### Basic Variable Management

```python
from src.core.execution_context import ExecutionContext

# Create execution context
context = ExecutionContext()

# Set variables
context.set_variable("username", "testuser")
context.set_variable("counter", 0)

# Get variables
username = context.get_variable("username")
counter = context.get_variable("counter", 0)  # Default value if not found

# Increment variable
context.increment_variable("counter", 5)
counter = context.get_variable("counter")  # Now 5

# Substitute variables in text
template = "Hello, ${username}! Your count is ${counter}."
result = context.substitute_variables(template)
# Result: "Hello, testuser! Your count is 5."
```

### Working with Control Blocks

```python
from src.core.execution_context import ExecutionContext, BlockType

# Create execution context
context = ExecutionContext()

# Push an IF block
if_block = context.push_block(
    block_type=BlockType.IF,
    start_index=5,
    condition="${username} == 'admin'"
)

# Get current block
current = context.current_block()
print(f"Current block type: {current.block_type.value}")
print(f"Block condition: {current.condition}")

# Push a WHILE block inside the IF
while_block = context.push_block(
    block_type=BlockType.WHILE,
    start_index=10,
    condition="${counter} < 10"
)

# Check block stack depth
print(f"Block stack depth: {len(context.block_stack)}")

# Pop blocks
context.pop_block()  # Removes the WHILE block
context.pop_block()  # Removes the IF block
```

### Error Handling and Outputs

```python
from src.core.execution_context import ExecutionContext

# Create execution context
context = ExecutionContext()

# Add outputs
context.add_output("status", "success")
context.add_output("result_count", 42)

# Add errors
context.add_error("Warning: Element not found")
context.add_error("Error: Login failed")

# Check outputs and errors
status = context.get_variable("status")  # "success"
errors = context.errors  # List of error messages

# Convert to dictionary for serialization
context_dict = context.to_dict()
```

### Finding Block End Indices

```python
from src.core.execution_context import ExecutionContext, BlockType
from src.core.action_types import Action, ActionType

# Create a mock action sequence
actions = [
    Action(type=ActionType.IF_BEGIN, value="${count} > 0"),
    Action(type=ActionType.SET_VARIABLE, value={"name": "count", "value": 1}),
    Action(type=ActionType.IF_END)
]

# Create execution context
context = ExecutionContext()

# Find the end of the IF block
end_index = context.find_block_end(actions, 0, BlockType.IF)
print(f"IF block ends at index: {end_index}")  # Output: 2
```

### Serialization and Deserialization

```python
from src.core.execution_context import ExecutionContext, BlockType

# Create and populate an execution context
context = ExecutionContext()
context.set_variable("user", "admin")
context.set_variable("count", 5)
context.push_block(BlockType.IF, 0, "${user} == 'admin'")
context.add_output("status", "running")

# Serialize to dictionary
context_dict = context.to_dict()

# Deserialize from dictionary
new_context = ExecutionContext.from_dict(context_dict)

# Verify deserialization
print(f"User variable: {new_context.get_variable('user')}")
print(f"Current block: {new_context.current_block().block_type.value}")
```

## Advanced Features

### Variable Substitution

The `substitute_variables` method supports complex variable substitution patterns:

```python
context = ExecutionContext()
context.set_variable("name", "Alice")
context.set_variable("age", 30)
context.set_variable("status", "active")

# Simple substitution
text = "Name: ${name}"
result = context.substitute_variables(text)  # "Name: Alice"

# Multiple substitutions
text = "${name} is ${age} years old and is ${status}"
result = context.substitute_variables(text)  # "Alice is 30 years old and is active"

# Missing variables default to empty string
text = "Missing: ${nonexistent}"
result = context.substitute_variables(text)  # "Missing: "
```

### Nested Control Blocks

The execution context properly handles nested control blocks:

```python
context = ExecutionContext()

# Create nested blocks
context.push_block(BlockType.IF, 0, "${condition1}")
context.push_block(BlockType.WHILE, 5, "${condition2}")
context.push_block(BlockType.IF, 10, "${condition3}")

# Block stack has 3 items
print(f"Stack depth: {len(context.block_stack)}")

# Current block is the innermost IF
current = context.current_block()
print(f"Current block: {current.block_type.value} at index {current.start_index}")

# Pop blocks in LIFO order
context.pop_block()  # Removes innermost IF
context.pop_block()  # Removes WHILE
context.pop_block()  # Removes outermost IF
```

## Integration with Other Modules

The `execution_context.py` module is used by:
- `engine.py` - For tracking execution state during automation
- `action_types.py` - For variable substitution and control flow
- `controller.py` - For managing automation state and variables