#!/usr/bin/env python3
"""
Automation Control System
Centralized control for automation execution with RUN/PAUSE/STOP functionality
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AutomationState(Enum):
    """Automation execution states"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class ControlSignal(Enum):
    """Control signals for automation"""
    PAUSE = "pause"
    RESUME = "resume" 
    STOP = "stop"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class AutomationCheckpoint:
    """Checkpoint data for pause/resume functionality"""
    config_name: str
    action_index: int
    variables: Dict[str, Any]
    execution_context: Dict[str, Any]
    browser_state: Optional[Dict[str, Any]]
    timestamp: str
    checkpoint_id: str

    def to_file(self, checkpoint_dir: Path) -> Path:
        """Save checkpoint to file"""
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = checkpoint_dir / f"{self.checkpoint_id}.json"
        
        with open(checkpoint_file, 'w') as f:
            json.dump(asdict(self), f, indent=2)
        
        return checkpoint_file

    @classmethod
    def from_file(cls, checkpoint_file: Path) -> 'AutomationCheckpoint':
        """Load checkpoint from file"""
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        return cls(**data)


class AutomationController:
    """Centralized control for automation execution"""
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.state = AutomationState.STOPPED
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Control signals
        self._pause_event = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._emergency_stop_event = asyncio.Event()
        
        # State tracking
        self.current_checkpoint: Optional[AutomationCheckpoint] = None
        self.progress_callback: Optional[Callable] = None
        self.state_change_callback: Optional[Callable] = None
        
        # Execution tracking
        self.total_actions = 0
        self.completed_actions = 0
        self.start_time: Optional[datetime] = None
        
        # Set initial state
        self._pause_event.set()  # Start in "resume" state
        
        logger.info("AutomationController initialized")

    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for progress updates: (completed, total, current_action)"""
        self.progress_callback = callback

    def set_state_change_callback(self, callback: Callable[[AutomationState], None]):
        """Set callback for state changes"""
        self.state_change_callback = callback

    def _update_state(self, new_state: AutomationState):
        """Update state and notify callbacks"""
        old_state = self.state
        self.state = new_state
        
        logger.info(f"State change: {old_state.value} → {new_state.value}")
        
        if self.state_change_callback:
            try:
                self.state_change_callback(new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")

    def _update_progress(self, completed: int, total: int, current_action: str = ""):
        """Update progress and notify callbacks"""
        self.completed_actions = completed
        self.total_actions = total
        
        if self.progress_callback:
            try:
                self.progress_callback(completed, total, current_action)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    # Public Control Methods

    def start_automation(self, total_actions: int = 0):
        """Start automation execution"""
        if self.state in [AutomationState.RUNNING, AutomationState.PAUSED]:
            logger.warning("Automation already running or paused")
            return False
        
        # Reset state
        self.total_actions = total_actions
        self.completed_actions = 0
        self.start_time = datetime.now()
        
        # Clear stop signals
        self._stop_event.clear()
        self._emergency_stop_event.clear()
        self._pause_event.set()  # Allow running
        
        self._update_state(AutomationState.RUNNING)
        return True

    def pause_automation(self) -> bool:
        """Pause automation execution"""
        if self.state != AutomationState.RUNNING:
            logger.warning(f"Cannot pause automation in state: {self.state.value}")
            return False
        
        self._pause_event.clear()  # Block execution
        self._update_state(AutomationState.PAUSED)
        logger.info("Automation paused")
        return True

    def resume_automation(self) -> bool:
        """Resume paused automation"""
        if self.state != AutomationState.PAUSED:
            logger.warning(f"Cannot resume automation in state: {self.state.value}")
            return False
        
        self._pause_event.set()  # Allow execution
        self._update_state(AutomationState.RUNNING)
        logger.info("Automation resumed")
        return True

    def stop_automation(self, emergency: bool = False) -> bool:
        """Stop automation execution"""
        if self.state == AutomationState.STOPPED:
            logger.warning("Automation already stopped")
            return False
        
        if emergency:
            self._emergency_stop_event.set()
            logger.warning("Emergency stop requested")
        else:
            self._stop_event.set()
            logger.info("Graceful stop requested")
        
        # Resume if paused to allow stop processing
        self._pause_event.set()
        
        self._update_state(AutomationState.STOPPING)
        return True

    def reset_automation(self):
        """Reset automation to stopped state"""
        self._stop_event.clear()
        self._emergency_stop_event.clear()
        self._pause_event.set()
        
        self.current_checkpoint = None
        self.completed_actions = 0
        self.total_actions = 0
        self.start_time = None
        
        self._update_state(AutomationState.STOPPED)
        logger.info("Automation reset")

    # Checkpoint Management

    def save_checkpoint(self, config_name: str, action_index: int, 
                       variables: Dict[str, Any], execution_context: Dict[str, Any],
                       browser_state: Optional[Dict[str, Any]] = None) -> str:
        """Save execution checkpoint"""
        checkpoint_id = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        checkpoint = AutomationCheckpoint(
            config_name=config_name,
            action_index=action_index,
            variables=variables,
            execution_context=execution_context,
            browser_state=browser_state,
            timestamp=datetime.now().isoformat(),
            checkpoint_id=checkpoint_id
        )
        
        checkpoint.to_file(self.checkpoint_dir)
        self.current_checkpoint = checkpoint
        
        logger.info(f"Checkpoint saved: {checkpoint_id}")
        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Optional[AutomationCheckpoint]:
        """Load execution checkpoint"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            logger.error(f"Checkpoint not found: {checkpoint_id}")
            return None
        
        try:
            checkpoint = AutomationCheckpoint.from_file(checkpoint_file)
            self.current_checkpoint = checkpoint
            logger.info(f"Checkpoint loaded: {checkpoint_id}")
            return checkpoint
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    def cleanup_checkpoints(self, config_name: Optional[str] = None):
        """Clean up checkpoint files"""
        pattern = f"{config_name}_*.json" if config_name else "*.json"
        
        for checkpoint_file in self.checkpoint_dir.glob(pattern):
            try:
                checkpoint_file.unlink()
                logger.debug(f"Deleted checkpoint: {checkpoint_file.name}")
            except Exception as e:
                logger.error(f"Failed to delete checkpoint {checkpoint_file}: {e}")

    def list_checkpoints(self) -> List[str]:
        """List available checkpoints"""
        checkpoints = []
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            checkpoints.append(checkpoint_file.stem)
        return sorted(checkpoints)

    # Control Check Methods (called by automation engine)

    async def check_should_pause(self) -> bool:
        """Check if automation should pause (non-blocking)"""
        return not self._pause_event.is_set()

    async def wait_if_paused(self):
        """Wait if automation is paused"""
        await self._pause_event.wait()

    async def check_should_stop(self) -> bool:
        """Check if automation should stop (non-blocking)"""
        return self._stop_event.is_set() or self._emergency_stop_event.is_set()

    async def check_emergency_stop(self) -> bool:
        """Check if emergency stop was requested (non-blocking)"""
        return self._emergency_stop_event.is_set()

    async def wait_for_control_signal(self, timeout: Optional[float] = None) -> Optional[ControlSignal]:
        """Wait for any control signal with optional timeout"""
        try:
            # Create tasks for all possible signals
            pause_task = asyncio.create_task(self._pause_event.wait())
            stop_task = asyncio.create_task(self._stop_event.wait())
            emergency_task = asyncio.create_task(self._emergency_stop_event.wait())
            
            # Wait for any signal
            done, pending = await asyncio.wait(
                [pause_task, stop_task, emergency_task],
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Check which signal was received
            if emergency_task in done:
                return ControlSignal.EMERGENCY_STOP
            elif stop_task in done:
                return ControlSignal.STOP
            elif pause_task in done and not self._pause_event.is_set():
                return ControlSignal.PAUSE
            elif pause_task in done and self._pause_event.is_set():
                return ControlSignal.RESUME
            
            return None  # Timeout
            
        except Exception as e:
            logger.error(f"Error waiting for control signal: {e}")
            return None

    # Status Methods

    def get_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        elapsed_time = None
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "state": self.state.value,
            "progress": {
                "completed": self.completed_actions,
                "total": self.total_actions,
                "percentage": (self.completed_actions / max(1, self.total_actions)) * 100
            },
            "timing": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "elapsed_seconds": elapsed_time
            },
            "checkpoint": {
                "has_checkpoint": self.current_checkpoint is not None,
                "checkpoint_id": self.current_checkpoint.checkpoint_id if self.current_checkpoint else None
            }
        }

    def is_running(self) -> bool:
        """Check if automation is currently running"""
        return self.state == AutomationState.RUNNING

    def is_paused(self) -> bool:
        """Check if automation is currently paused"""
        return self.state == AutomationState.PAUSED

    def is_stopped(self) -> bool:
        """Check if automation is stopped"""
        return self.state == AutomationState.STOPPED

    def can_pause(self) -> bool:
        """Check if automation can be paused"""
        return self.state == AutomationState.RUNNING

    def can_resume(self) -> bool:
        """Check if automation can be resumed"""
        return self.state == AutomationState.PAUSED

    def can_stop(self) -> bool:
        """Check if automation can be stopped"""
        return self.state in [AutomationState.RUNNING, AutomationState.PAUSED]

    def _update_progress(self, current_action: int, total_actions: int, status_message: str = None):
        """Update automation progress - called by engine during execution"""
        self.completed_actions = current_action
        self.total_actions = total_actions
        
        # Store progress info for GUI updates
        if not hasattr(self, 'progress_callbacks'):
            self.progress_callbacks = []
        
        # Call any registered progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(current_action, total_actions, status_message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    def register_progress_callback(self, callback: Callable):
        """Register a callback function for progress updates"""
        if not hasattr(self, 'progress_callbacks'):
            self.progress_callbacks = []
        self.progress_callbacks.append(callback)
    
    def unregister_progress_callback(self, callback: Callable):
        """Unregister a progress callback function"""
        if hasattr(self, 'progress_callbacks'):
            try:
                self.progress_callbacks.remove(callback)
            except ValueError:
                pass  # Callback wasn't registered

    def __str__(self) -> str:
        """String representation of controller state"""
        return f"AutomationController(state={self.state.value}, progress={self.completed_actions}/{self.total_actions})"