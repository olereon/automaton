"""Execution context and block information classes for web automation"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BlockType(Enum):
    """Types of control blocks"""
    IF = "if"
    WHILE = "while"


@dataclass
class BlockInfo:
    """Information about a control block (IF, WHILE, etc.)"""
    
    block_type: BlockType
    start_index: int
    end_index: int = -1
    condition: Optional[str] = None
    condition_met: bool = False
    has_executed: bool = False
    iteration_count: int = 0
    
    def __post_init__(self):
        """Validate block info after initialization"""
        if not isinstance(self.block_type, BlockType):
            raise ValueError(f"Invalid block type: {self.block_type}")
        
        if self.start_index < 0:
            raise ValueError("Start index must be non-negative")
    
    def reset(self):
        """Reset block state for new execution"""
        self.condition_met = False
        self.has_executed = False
        self.iteration_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block info to dictionary representation"""
        return {
            "block_type": self.block_type.value,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "condition": self.condition,
            "condition_met": self.condition_met,
            "has_executed": self.has_executed,
            "iteration_count": self.iteration_count,
        }


@dataclass
class ExecutionContext:
    """Context for automation execution including variables and control flow"""
    
    # Execution state
    instruction_pointer: int = 0
    should_increment: bool = True
    last_check_result: Optional[Dict[str, Any]] = None
    continue_on_error: bool = False
    
    # Control flags
    break_flag: bool = False
    continue_flag: bool = False
    
    # Variables
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Control flow
    block_stack: List[BlockInfo] = field(default_factory=list)
    
    # Outputs
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate execution context after initialization"""
        if self.instruction_pointer < 0:
            raise ValueError("Instruction pointer must be non-negative")
    
    def reset(self):
        """Reset execution context for new run"""
        self.instruction_pointer = 0
        self.should_increment = True
        self.last_check_result = None
        self.break_flag = False
        self.continue_flag = False
        self.variables.clear()
        self.block_stack.clear()
        self.outputs.clear()
        self.errors.clear()
    
    def set_variable(self, name: str, value: Any):
        """Set a variable in the execution context"""
        if not name:
            raise ValueError("Variable name cannot be empty")
        
        self.variables[name] = value
        logger.debug(f"Set variable '{name}' = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the execution context"""
        return self.variables.get(name, default)
    
    def increment_variable(self, name: str, amount: Union[int, float] = 1):
        """Increment a numeric variable"""
        current_value = self.get_variable(name, 0)
        
        if not isinstance(current_value, (int, float)):
            raise ValueError(f"Variable '{name}' is not numeric: {current_value}")
        
        new_value = current_value + amount
        self.set_variable(name, new_value)
        logger.debug(f"Incremented variable '{name}' from {current_value} to {new_value}")
    
    def push_block(self, block_type: BlockType, start_index: int, 
                   condition: Optional[str] = None) -> BlockInfo:
        """Push a new control block onto the stack"""
        block = BlockInfo(
            block_type=block_type,
            start_index=start_index,
            condition=condition,
        )
        self.block_stack.append(block)
        logger.debug(f"Pushed {block_type.value} block at index {start_index}")
        return block
    
    def pop_block(self) -> Optional[BlockInfo]:
        """Pop the top control block from the stack"""
        if not self.block_stack:
            return None
        
        block = self.block_stack.pop()
        logger.debug(f"Popped {block.block_type.value} block")
        return block
    
    def current_block(self) -> Optional[BlockInfo]:
        """Get the current (top) control block"""
        if not self.block_stack:
            return None
        return self.block_stack[-1]
    
    def find_block_end(self, actions: List[Any], start_index: int, 
                       block_type: BlockType) -> int:
        """Find the end index of a control block"""
        depth = 0
        for i in range(start_index + 1, len(actions)):
            action = actions[i]
            
            # Handle nested blocks of the same type
            if block_type == BlockType.IF:
                if hasattr(action, 'type') and action.type.value in ["if_begin", "IF_BEGIN"]:
                    depth += 1
                elif hasattr(action, 'type') and action.type.value in ["if_end", "IF_END"]:
                    if depth == 0:
                        return i
                    depth -= 1
            elif block_type == BlockType.WHILE:
                if hasattr(action, 'type') and action.type.value in ["while_begin", "WHILE_BEGIN"]:
                    depth += 1
                elif hasattr(action, 'type') and action.type.value in ["while_end", "WHILE_END"]:
                    if depth == 0:
                        return i
                    depth -= 1
        
        # If no end found, return the end of actions
        return len(actions)
    
    def add_error(self, error: str):
        """Add an error to the execution context"""
        self.errors.append(error)
        logger.error(f"Execution error: {error}")
    
    def add_output(self, key: str, value: Any):
        """Add an output value to the execution context"""
        self.outputs[key] = value
        logger.debug(f"Added output '{key}' = {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution context to dictionary representation"""
        return {
            "instruction_pointer": self.instruction_pointer,
            "should_increment": self.should_increment,
            "last_check_result": self.last_check_result,
            "continue_on_error": self.continue_on_error,
            "break_flag": self.break_flag,
            "continue_flag": self.continue_flag,
            "variables": self.variables,
            "block_stack": [block.to_dict() for block in self.block_stack],
            "outputs": self.outputs,
            "errors": self.errors,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionContext':
        """Create execution context from dictionary representation"""
        context = cls(
            instruction_pointer=data.get("instruction_pointer", 0),
            should_increment=data.get("should_increment", True),
            last_check_result=data.get("last_check_result"),
            continue_on_error=data.get("continue_on_error", False),
            break_flag=data.get("break_flag", False),
            continue_flag=data.get("continue_flag", False),
            variables=data.get("variables", {}),
            outputs=data.get("outputs", {}),
            errors=data.get("errors", []),
        )
        
        # Reconstruct block stack
        for block_data in data.get("block_stack", []):
            block = BlockInfo(
                block_type=BlockType(block_data["block_type"]),
                start_index=block_data["start_index"],
                end_index=block_data.get("end_index", -1),
                condition=block_data.get("condition"),
                condition_met=block_data.get("condition_met", False),
                has_executed=block_data.get("has_executed", False),
                iteration_count=block_data.get("iteration_count", 0),
            )
            context.block_stack.append(block)
        
        return context
    
    def substitute_variables(self, text: str) -> str:
        """Substitute variables in text using ${variable} syntax"""
        if not text or not isinstance(text, str):
            return text
        
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return str(self.get_variable(var_name, ""))
        
        # Replace ${variable} patterns
        result = re.sub(r'\$\{([^}]+)\}', replace_var, text)
        return result